"""Strict, auditable constituent snapshot imports for market scanning.

This service never mutates the broker instrument master. It accepts a dated
constituent list copied from an official source, maps symbols only to exact
active NSE equity instruments, and atomically activates a complete snapshot.
"""
from datetime import date

from sqlalchemy import func, text\nfrom sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.models.market_universe import MarketUniverseMembership, MarketUniverseSnapshot


class MarketUniverseImportError(ValueError):
    """The constituent snapshot cannot be safely mapped or activated."""


class MarketUniverseService:
    NIFTY_500 = "NIFTY_500"
    EXPECTED_MEMBERS = 500

    def __init__(self, db: Session):
        self.db = db

    def import_nifty500(
        self, *, symbols: list[str], as_of_date: date, source: str
    ) -> MarketUniverseSnapshot:
        normalized = [symbol.strip().upper() for symbol in symbols]
        if len(normalized) != self.EXPECTED_MEMBERS or len(set(normalized)) != self.EXPECTED_MEMBERS:
            raise MarketUniverseImportError("Nifty 500 import requires exactly 500 unique symbols.")
        if not source or not source.strip():
            raise MarketUniverseImportError("A source description is required.")

        instruments = (
            self.db.query(Instrument)
            .filter(
                Instrument.is_active.is_(True),
                Instrument.exchange == "NSE",
                Instrument.segment == "NSE_EQ",
                Instrument.instrument_type == "EQUITY",
                func.upper(Instrument.trading_symbol).in_(normalized),
            )
            .all()
        )
        by_symbol: dict[str, list[Instrument]] = {}
        for instrument in instruments:
            by_symbol.setdefault(instrument.trading_symbol.upper(), []).append(instrument)

        missing = sorted(set(normalized) - set(by_symbol))
        ambiguous = sorted(symbol for symbol, matches in by_symbol.items() if len(matches) != 1)
        if missing or ambiguous or len(instruments) != self.EXPECTED_MEMBERS:
            details = []
            if missing:
                details.append(f"{len(missing)} symbols are not mapped to active NSE equity instruments")
            if ambiguous:
                details.append("ambiguous symbols: " + ", ".join(ambiguous[:10]))
            raise MarketUniverseImportError("Constituent snapshot rejected: " + "; ".join(details or ["invalid instrument mapping"]) + ".")

        try:
            if self.db.bind is not None and self.db.bind.dialect.name == "postgresql":\n                self.db.execute(text("SELECT pg_advisory_xact_lock(202611020045)"))\n            duplicate_date = (
                self.db.query(MarketUniverseSnapshot.id)
                .filter(
                    MarketUniverseSnapshot.universe_key == self.NIFTY_500,
                    MarketUniverseSnapshot.as_of_date == as_of_date,
                )
                .first()
            )
            if duplicate_date is not None:
                raise MarketUniverseImportError(
                    "A Nifty 500 snapshot for this effective date already exists; snapshots are immutable."
                )
            current = (
                self.db.query(MarketUniverseSnapshot)
                .filter(
                    MarketUniverseSnapshot.universe_key == self.NIFTY_500,
                    MarketUniverseSnapshot.is_active.is_(True),
                )
                .with_for_update()
                .all()
            )
            for snapshot in current:
                snapshot.is_active = False

            snapshot = MarketUniverseSnapshot(
                universe_key=self.NIFTY_500,
                as_of_date=as_of_date,
                source=source.strip(),
                member_count=self.EXPECTED_MEMBERS,
                is_active=True,
            )
            self.db.add(snapshot)
            self.db.flush()
            self.db.add_all([
                MarketUniverseMembership(
                    snapshot_id=snapshot.id,
                    instrument_id=instrument.id,
                    trading_symbol=instrument.trading_symbol,
                )
                for instrument in instruments
            ])
            self.db.commit()
            self.db.refresh(snapshot)
            return snapshot
        except Exception:
            self.db.rollback()
            raise

    def active_nifty500_instruments(self) -> list[Instrument]:
        snapshot = (
            self.db.query(MarketUniverseSnapshot)
            .filter(
                MarketUniverseSnapshot.universe_key == self.NIFTY_500,
                MarketUniverseSnapshot.is_active.is_(True),
            )
            .order_by(MarketUniverseSnapshot.created_at.desc())
            .first()
        )
        if snapshot is None:
            return []
        return (
            self.db.query(Instrument)
            .join(MarketUniverseMembership, MarketUniverseMembership.instrument_id == Instrument.id)
            .filter(MarketUniverseMembership.snapshot_id == snapshot.id, Instrument.is_active.is_(True))
            .order_by(Instrument.trading_symbol.asc())
            .all()
        )
