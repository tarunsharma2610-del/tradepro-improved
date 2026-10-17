from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.instrument import Instrument


class InstrumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, instrument_id: UUID) -> Instrument | None:
        return self.db.get(Instrument, instrument_id)

    def get_by_key(self, instrument_key: str) -> Instrument | None:
        return self.db.query(Instrument).filter(Instrument.instrument_key == instrument_key).first()

    def search(self, query: str, limit: int = 20) -> list[Instrument]:
        like = f"%{query.upper()}%"
        return (
            self.db.query(Instrument)
            .filter(Instrument.is_active.is_(True))
            .filter(
                (Instrument.trading_symbol.ilike(like)) | (Instrument.name.ilike(like))
            )
            .order_by(Instrument.trading_symbol)
            .limit(limit)
            .all()
        )

    def upsert(self, **fields) -> Instrument:
        existing = self.get_by_key(fields["instrument_key"])
        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)
            instrument = existing
        else:
            instrument = Instrument(**fields)
        self.db.add(instrument)
        self.db.commit()
        self.db.refresh(instrument)
        return instrument

    def upsert_many(
        self,
        records: list[dict],
        *,
        snapshot_keys: set[str] | None = None,
        reconcile_segments: set[str] | None = None,
        expired_before: date | None = None,
    ) -> int:
        """Upsert a full batch and optionally reconcile a validated full snapshot in one transaction."""
        if not records:
            return 0

        # Keep IN clauses below common SQLite parameter limits.
        keys = [record["instrument_key"] for record in records]
        existing_by_key = {}
        for start in range(0, len(keys), 500):
            chunk = keys[start : start + 500]
            existing = (
                self.db.query(Instrument)
                .filter(Instrument.instrument_key.in_(chunk))
                .all()
            )
            existing_by_key.update({item.instrument_key: item for item in existing})

        for record in records:
            key = record["instrument_key"]
            existing = existing_by_key.get(key)
            if existing is None:
                self.db.add(Instrument(**record))
            else:
                for field, value in record.items():
                    setattr(existing, field, value)

        if snapshot_keys is not None and reconcile_segments:
            # Only called after the service validates a complete BOD snapshot.
            # Unknown types still count as present keys, avoiding false delisting.
            active = (
                self.db.query(Instrument)
                .filter(Instrument.is_active.is_(True), Instrument.segment.in_(reconcile_segments))
                .all()
            )
            for instrument in active:
                if instrument.instrument_key not in snapshot_keys:
                    instrument.is_active = False

        if expired_before is not None:
            expired = (
                self.db.query(Instrument)
                .filter(
                    Instrument.is_active.is_(True),
                    Instrument.instrument_type.in_({"FUTURES", "OPTIONS"}),
                    Instrument.expiry.is_not(None),
                    Instrument.expiry < expired_before,
                )
                .all()
            )
            for instrument in expired:
                instrument.is_active = False

        self.db.commit()
        return len(records)

    def count(self) -> int:
        return self.db.query(Instrument).count()
