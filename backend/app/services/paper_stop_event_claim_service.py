"""Transactional PAPER stop-event claims.

Claims are storage/state coordination only. This module never places orders
and never calls a broker. A caller must commit the surrounding transaction
before treating a returned claim as durable.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy


class PaperStopClaimRejected(ValueError):
    """The stop event cannot safely be claimed for the supplied ownership."""


class PaperStopEventClaimService:
    def __init__(self, db: Session):
        self.db = db

    def claim_trailing_stop(
        self,
        *,
        user_id: UUID,
        portfolio_id: UUID,
        strategy_id: UUID,
        instrument_id: UUID,
        quote_epoch: str,
        quote_version: int,
        trigger_price: Decimal,
        lease_seconds: int = 30,
        now: datetime | None = None,
    ) -> PaperStopEvent | None:
        """Claim one quote for one unambiguously owned open PAPER position.

        Returns None for an already-claimed quote identity. Raises
        PaperStopClaimRejected for invalid ownership or ambiguous strategy
        ownership. Caller owns commit/rollback.
        """
        if not quote_epoch or len(quote_epoch) > 128:
            raise PaperStopClaimRejected("Invalid quote epoch.")
        if isinstance(quote_version, bool) or not isinstance(quote_version, int) or quote_version <= 0:
            raise PaperStopClaimRejected("Quote version must be a positive integer.")
        price = Decimal(str(trigger_price))
        if not price.is_finite() or price <= 0:
            raise PaperStopClaimRejected("Trigger price must be finite and positive.")
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int) or not 1 <= lease_seconds <= 300:
            raise PaperStopClaimRejected("Claim lease must be between 1 and 300 seconds.")

        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise PaperStopClaimRejected("Claim time must be timezone-aware.")

        # Match the shared execution service's lock order: portfolio first,
        # then strategy, then the portfolio/instrument position.
        portfolio = (
            self.db.query(Portfolio)
            .filter(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id,
                Portfolio.is_active.is_(True),
            )
            .with_for_update()
            .first()
        )
        if portfolio is None:
            raise PaperStopClaimRejected("Active user-owned portfolio not found.")

        strategy = (
            self.db.query(Strategy)
            .filter(
                Strategy.id == strategy_id,
                Strategy.portfolio_id == portfolio.id,
                Strategy.instrument_id == instrument_id,
                Strategy.is_active.is_(True),
            )
            .with_for_update(of=Strategy)
            .first()
        )
        if strategy is None:
            raise PaperStopClaimRejected("Active strategy ownership does not match portfolio and instrument.")

        instrument = self.db.query(Instrument).filter(Instrument.id == instrument_id).first()
        if instrument is None:
            raise PaperStopClaimRejected("Instrument not found.")

        # Position is portfolio+instrument scoped, not strategy scoped.
        # Until allocations exist, multiple active strategies are ambiguous.
        competing = (
            self.db.query(Strategy.id)
            .filter(
                Strategy.portfolio_id == portfolio.id,
                Strategy.instrument_id == instrument_id,
                Strategy.is_active.is_(True),
                Strategy.id != strategy.id,
            )
            .with_for_update()
            .first()
        )
        if competing is not None:
            raise PaperStopClaimRejected(
                "Multiple active strategies share this portfolio/instrument position; ownership is ambiguous."
            )

        position = (
            self.db.query(Position)
            .filter(
                Position.portfolio_id == portfolio.id,
                Position.instrument_id == instrument_id,
            )
            .with_for_update()
            .first()
        )
        if position is None or position.quantity == 0:
            raise PaperStopClaimRejected("No open portfolio position exists for this strategy instrument.")

        event = PaperStopEvent(
            user_id=user_id,
            portfolio_id=portfolio.id,
            strategy_id=strategy.id,
            instrument_id=instrument.id,
            event_type="TRAILING_STOP",
            quote_epoch=quote_epoch,
            quote_version=quote_version,
            trigger_price=price,
            state="CLAIMED",
            claim_token=uuid4(),
            claimed_until=current + timedelta(seconds=lease_seconds),
            attempt_count=1,
        )
        try:
            # Savepoint allows duplicate-key rejection without poisoning the
            # caller's outer transaction.
            with self.db.begin_nested():
                self.db.add(event)
                self.db.flush()
        except IntegrityError:
            return None
        return event
