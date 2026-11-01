"""Atomic execution of durable PAPER trailing-stop events.

This service is the only bridge between a claimed stop event and the shared
PAPER ExecutionService. It validates ownership and the lease, performs the
existing PAPER fill without committing, transitions the event, and commits
both together. It never submits broker orders.
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.models.order import Order
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.services.execution_service import (
    ExecutionService,
    OrderValidationError,
    PlaceOrderRequest,
)
from app.services.paper_stop_event_lifecycle import PaperStopEventLifecycle
from app.services.transaction_costs import Segment, Side


class PaperStopEventExecutionRejected(ValueError):
    """A stop event is not authorized or cannot safely be executed."""


class PaperStopEventExecutionService:
    """Execute one claimed stop event in a single caller-owned transaction."""

    def __init__(self, db: Session):
        self.db = db
        self.execution = ExecutionService(db)
        self.lifecycle = PaperStopEventLifecycle(db)

    @staticmethod
    def _utc_datetime(value: datetime) -> datetime:
        """Normalize DB datetimes to UTC; SQLite may drop timezone metadata.

        DateTime(timezone=True) is timezone-aware on PostgreSQL, while SQLite
        returns naive values for the same column. Persisted naive values are
        interpreted as UTC because all lifecycle timestamps are written in UTC.
        """
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _existing_completed_order(self, event: PaperStopEvent, claim_token: UUID) -> Order:
        if event.claim_token != claim_token:
            raise PaperStopEventExecutionRejected("Claim token does not own this stop event.")
        order = (
            self.db.query(Order)
            .filter(Order.paper_stop_event_id == event.id)
            .first()
        )
        if (
            order is None
            or order.portfolio_id != event.portfolio_id
            or order.strategy_id != event.strategy_id
            or order.instrument_id != event.instrument_id
            or order.execution_reason != "STRATEGY"
            or order.trading_mode != "PAPER"
            or order.order_type != "MARKET"
            or order.status != "FILLED"
        ):
            raise PaperStopEventExecutionRejected(
                "Completed stop event has no matching filled PAPER order."
            )
        return order

    async def execute_claimed(
        self,
        *,
        user_id: UUID,
        event_id: UUID,
        claim_token: UUID,
        now: datetime | None = None,
    ) -> Order:
        """Execute a valid claim; duplicate completed deliveries return its order.

        Lock order is portfolio -> strategy -> event -> position. Locking the
        event before reading the position lets a completed redelivery return
        its original order even though the successful first fill flattened the
        position. The event's token and lease are revalidated after locks are
        acquired. The PAPER order, fill ledger, cash/position changes, and
        COMPLETED transition share one database commit.
        """
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise PaperStopEventExecutionRejected("Execution time must be timezone-aware.")
        if not isinstance(claim_token, UUID):
            raise PaperStopEventExecutionRejected("A valid claim token is required.")

        # Initial unlocked read discovers the lock keys only. Immutable
        # ownership fields are rechecked after all rows are locked.
        snapshot = self.db.query(PaperStopEvent).filter(PaperStopEvent.id == event_id).first()
        if snapshot is None:
            raise PaperStopEventExecutionRejected("Stop event not found.")

        try:
            portfolio = (
                self.db.query(Portfolio)
                .filter(
                    Portfolio.id == snapshot.portfolio_id,
                    Portfolio.user_id == user_id,
                    Portfolio.is_active.is_(True),
                )
                .with_for_update()
                .first()
            )
            if portfolio is None:
                raise PaperStopEventExecutionRejected("Active user-owned portfolio not found.")

            strategy = (
                self.db.query(Strategy)
                .filter(
                    Strategy.id == snapshot.strategy_id,
                    Strategy.portfolio_id == portfolio.id,
                    Strategy.instrument_id == snapshot.instrument_id,
                )
                .with_for_update(of=Strategy)
                .first()
            )
            if strategy is None or not strategy.is_active:
                raise PaperStopEventExecutionRejected("Active strategy ownership does not match stop event.")

            instrument = (
                self.db.query(Instrument)
                .filter(Instrument.id == snapshot.instrument_id)
                .first()
            )
            if instrument is None:
                raise PaperStopEventExecutionRejected("Stop-event instrument no longer exists.")

            # Lock and validate the event before the position. A completed
            # duplicate delivery must return its original order even though
            # the first fill has already flattened the position.
            event = (
                self.db.query(PaperStopEvent)
                .filter(PaperStopEvent.id == event_id)
                .with_for_update()
                # The initial unlocked snapshot above may already be present
                # in this Session's identity map. Force PostgreSQL's locked
                # row values to replace that potentially stale CLAIMED state
                # after another worker commits COMPLETED while we wait.
                .populate_existing()
                .first()
            )
            if (
                event is None
                or event.user_id != user_id
                or event.portfolio_id != portfolio.id
                or event.strategy_id != strategy.id
                or event.instrument_id != instrument.id
            ):
                raise PaperStopEventExecutionRejected("Stop-event ownership changed; execution denied.")

            if event.state == "COMPLETED":
                return self._existing_completed_order(event, claim_token)
            if event.state != "CLAIMED" or event.claim_token != claim_token:
                raise PaperStopEventExecutionRejected("Stop event is not owned by this active claim.")
            if (
                event.claimed_until is None
                or self._utc_datetime(event.claimed_until) <= self._utc_datetime(current)
            ):
                raise PaperStopEventExecutionRejected("Stop-event claim lease has expired.")

            position = (
                self.db.query(Position)
                .filter(
                    Position.portfolio_id == portfolio.id,
                    Position.instrument_id == instrument.id,
                )
                .with_for_update(of=Position)
                .first()
            )
            if position is None or position.quantity == 0:
                raise PaperStopEventExecutionRejected("Stop event has no open position to close.")

            executing = self.lifecycle.begin_execution(
                event_id=event.id,
                claim_token=claim_token,
                now=current,
            )
            if executing is None:
                raise PaperStopEventExecutionRejected("Stop-event claim could not enter EXECUTING state.")

            side = Side.SELL if position.quantity > 0 else Side.BUY
            request = PlaceOrderRequest(
                portfolio_id=portfolio.id,
                instrument_id=instrument.id,
                side=side,
                order_type="MARKET",
                segment=Segment(strategy.segment),
                quantity=abs(position.quantity),
                execution_reason="STRATEGY",
                strategy_id=strategy.id,
            )
            order = await self.execution.place_order(
                user_id,
                request,
                commit=False,
                paper_stop_event_id=event.id,
            )

            if order.status == "FILLED":
                strategy.current_watermark = None
                self.db.add(strategy)
                completed = self.lifecycle.complete(
                    event_id=event.id,
                    claim_token=claim_token,
                    now=datetime.now(timezone.utc),
                )
                if completed is None:
                    raise PaperStopEventExecutionRejected(
                        "Stop-event lease/token changed before atomic completion."
                    )
            elif order.status == "REJECTED":
                # A rejected order is durably bound to this event's unique key.
                # Do not retry it as a second order; require a fresh quote event.
                failed = self.lifecycle.fail(
                    event_id=event.id,
                    claim_token=claim_token,
                    error_code="PAPER_ORDER_REJECTED",
                    now=datetime.now(timezone.utc),
                )
                if failed is None:
                    raise PaperStopEventExecutionRejected(
                        "Stop-event lease/token changed before failure recording."
                    )
            else:
                raise PaperStopEventExecutionRejected(
                    f"Unexpected PAPER MARKET order state: {order.status}."
                )

            # Exactly one commit owns order, execution, position, cash,
            # strategy watermark and event terminal state.
            self.db.commit()
            self.db.refresh(order)
            return order
        except Exception:
            self.db.rollback()
            raise
