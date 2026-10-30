"""Durable intake of fresh market observations into PAPER trailing-stop claims.

This service evaluates the existing shared trailing-stop rule and persists a
claim only when the observed price crosses the stop. It deliberately does not
execute orders. The caller owns the transaction and must hand a committed
claim to the separately reviewed PAPER execution stage.
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.services.market_scanner import MarketScanObservation
from app.services.paper_stop_event_claim_service import PaperStopEventClaimService
from app.services.position_math import check_trailing_stop


class PaperStopObservationRejected(ValueError):
    """The quote is not safe to use for stop evaluation."""


class PaperStopEventIntakeService:
    """Evaluate fresh scanner observations and durably claim triggered stops."""

    def __init__(self, db: Session, *, max_quote_age_seconds: int = 15):
        if isinstance(max_quote_age_seconds, bool) or not isinstance(max_quote_age_seconds, int) or not 1 <= max_quote_age_seconds <= 60:
            raise ValueError("Quote age limit must be between 1 and 60 seconds.")
        self.db = db
        self.max_quote_age_seconds = max_quote_age_seconds

    def evaluate_and_claim(
        self,
        observation: MarketScanObservation,
        *,
        now: datetime | None = None,
    ) -> list[PaperStopEvent]:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise PaperStopObservationRejected("Evaluation time must be timezone-aware.")
        if not isinstance(observation, MarketScanObservation):
            raise PaperStopObservationRejected("A validated market scanner observation is required.")
        if not isinstance(observation.user_id, str) or not observation.user_id:
            raise PaperStopObservationRejected("Observation user is missing.")
        if not observation.instrument_key or not observation.epoch or observation.version <= 0:
            raise PaperStopObservationRejected("Observation identity is invalid.")
        if not observation.ltp or not Decimal(str(observation.ltp)).is_finite() or observation.ltp <= 0:
            raise PaperStopObservationRejected("Observation price must be finite and positive.")

        try:
            owner_id = UUID(observation.user_id)
            received_at = datetime.fromisoformat(observation.received_at)
        except (ValueError, TypeError) as exc:
            raise PaperStopObservationRejected("Observation owner or receive timestamp is invalid.") from exc
        if received_at.tzinfo is None:
            raise PaperStopObservationRejected("Observation receive timestamp must be timezone-aware.")
        age = (current - received_at.astimezone(timezone.utc)).total_seconds()
        if age < -5 or age > self.max_quote_age_seconds:
            raise PaperStopObservationRejected("Observation is stale or timestamped in the future.")

        instrument = (
            self.db.query(Instrument)
            .filter(Instrument.instrument_key == observation.instrument_key)
            .first()
        )
        if instrument is None:
            return []

        strategies = (
            self.db.query(Strategy)
            .join(Portfolio, Portfolio.id == Strategy.portfolio_id)
            .filter(
                Portfolio.user_id == owner_id,
                Portfolio.is_active.is_(True),
                Strategy.instrument_id == instrument.id,
                Strategy.is_active.is_(True),
            )
            .order_by(Strategy.id.asc())
            .all()
        )
        if not strategies:
            return []

        created: list[PaperStopEvent] = []
        for candidate in strategies:
            # Preserve the repository-wide lock order used by order execution:
            # portfolio, strategy, then position.
            portfolio = (
                self.db.query(Portfolio)
                .filter(
                    Portfolio.id == candidate.portfolio_id,
                    Portfolio.user_id == owner_id,
                    Portfolio.is_active.is_(True),
                )
                .with_for_update()
                .first()
            )
            if portfolio is None:
                continue
            strategy = (
                self.db.query(Strategy)
                .filter(
                    Strategy.id == candidate.id,
                    Strategy.portfolio_id == portfolio.id,
                    Strategy.instrument_id == instrument.id,
                    Strategy.is_active.is_(True),
                )
                .with_for_update()
                .first()
            )
            if strategy is None:
                continue
            position = (
                self.db.query(Position)
                .filter(
                    Position.portfolio_id == portfolio.id,
                    Position.instrument_id == instrument.id,
                )
                .with_for_update()
                .first()
            )
            if position is None or position.quantity == 0:
                continue

            watermark = (
                Decimal(str(strategy.current_watermark))
                if strategy.current_watermark is not None else None
            )
            new_watermark, stop_hit = check_trailing_stop(
                watermark=watermark,
                position_quantity=position.quantity,
                current_price=Decimal(str(observation.ltp)),
                stop_pct=Decimal(str(strategy.trailing_stop_pct)),
            )
            strategy.current_watermark = new_watermark
            self.db.add(strategy)
            if not stop_hit:
                continue

            # The claim service revalidates user/portfolio/strategy/position
            # ownership and enforces the unique quote identity under locks.
            event = PaperStopEventClaimService(self.db).claim_trailing_stop(
                user_id=owner_id,
                portfolio_id=portfolio.id,
                strategy_id=strategy.id,
                instrument_id=instrument.id,
                quote_epoch=observation.epoch,
                quote_version=observation.version,
                trigger_price=Decimal(str(observation.ltp)),
                now=current,
            )
            if event is not None:
                created.append(event)

        return created
