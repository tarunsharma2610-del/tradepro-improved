"""Fail-closed, account-wide live pre-trade risk gate.

The gate deliberately receives quote, broker-funds, and margin providers as
dependencies. Missing, stale, malformed, or failed external data blocks an
order; it never substitutes paper cash or a fabricated quote. This is a
reviewable risk foundation, not authorization to submit live orders.
"""
from dataclasses import dataclass
from datetime import datetime, time, timezone
from decimal import Decimal, InvalidOperation
from typing import Callable
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.services.live_execution_service import (
    LiveExecutionBlocked,
    LiveOrderIntent,
    LiveRiskDecision,
)

IST = ZoneInfo("Asia/Kolkata")
PENDING_LIVE_STATES = ("PENDING_SUBMISSION", "SUBMITTING", "SUBMISSION_UNKNOWN", "PENDING", "PARTIALLY_FILLED")


@dataclass(frozen=True)
class LiveQuoteSnapshot:
    price: Decimal
    observed_at: datetime


@dataclass(frozen=True)
class BrokerPositionSnapshot:
    instrument_key: str
    quantity: int
    market_price: Decimal
    observed_at: datetime


@dataclass(frozen=True)
class BrokerFundsSnapshot:
    cash_available: Decimal
    observed_at: datetime


@dataclass(frozen=True)
class BrokerMarginSnapshot:
    required_margin: Decimal
    observed_at: datetime


QuoteProvider = Callable[[UUID, Instrument], LiveQuoteSnapshot]
PositionsProvider = Callable[[UUID], tuple[BrokerPositionSnapshot, ...]]
FundsProvider = Callable[[UUID], BrokerFundsSnapshot]
MarginProvider = Callable[[UUID, Instrument, LiveOrderIntent, Decimal], BrokerMarginSnapshot]
Clock = Callable[[], datetime]


class AccountWideLiveRiskGate:
    """Callable risk gate suitable for injection into LiveExecutionService.

    Current positions are valued using fresh broker quotes; pending live orders
    are conservatively added to exposure. A pending order with an unknown
    broker outcome remains exposure and blocks if its price cannot be valued.
    """

    def __init__(
        self,
        db: Session,
        *,
        quote_provider: QuoteProvider | None,
        positions_provider: PositionsProvider | None,
        funds_provider: FundsProvider | None,
        margin_provider: MarginProvider | None,
        clock: Clock | None = None,
    ):
        self.db = db
        self.quote_provider = quote_provider
        self.positions_provider = positions_provider
        self.funds_provider = funds_provider
        self.margin_provider = margin_provider
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def __call__(
        self,
        user_id: UUID,
        portfolio: Portfolio,
        instrument: Instrument,
        intent: LiveOrderIntent,
    ) -> LiveRiskDecision:
        try:
            return self.evaluate(user_id, portfolio, instrument, intent)
        except LiveExecutionBlocked as exc:
            return LiveRiskDecision(allowed=False, reason=str(exc))
        except Exception:
            # Database/provider surprises are not permission to trade.
            return LiveRiskDecision(allowed=False, reason="Live risk data unavailable; order blocked.")

    def evaluate(
        self,
        user_id: UUID,
        portfolio: Portfolio,
        instrument: Instrument,
        intent: LiveOrderIntent,
    ) -> LiveRiskDecision:
        now = self.clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise LiveExecutionBlocked("Risk-gate clock must return a timezone-aware timestamp.")
        now_ist = now.astimezone(IST)
        if now_ist.weekday() >= 5 or not (time(9, 15) <= now_ist.time().replace(tzinfo=None) < time(15, 30)):
            raise LiveExecutionBlocked("Indian equity market session is closed; live order blocked.")

        if not all((self.quote_provider, self.positions_provider, self.funds_provider, self.margin_provider)):
            raise LiveExecutionBlocked("Fresh quote, broker positions, funds, and margin providers are all required.")

        quote = self._fresh_quote(user_id, instrument, now)
        proposed_value = quote.price * Decimal(intent.quantity)
        if intent.order_type == "LIMIT" and intent.limit_price is not None:
            proposed_value = Decimal(str(intent.limit_price)) * Decimal(intent.quantity)
            # Market price remains a required fresh check even for limit orders.

        max_order_value = Decimal(str(settings.LIVE_MAX_ORDER_VALUE_INR))
        max_gross_exposure = Decimal(str(settings.LIVE_MAX_GROSS_EXPOSURE_INR))
        if max_order_value <= 0 or max_gross_exposure <= 0:
            raise LiveExecutionBlocked("Configured live order-value/exposure caps must be positive.")
        if proposed_value > max_order_value:
            raise LiveExecutionBlocked("Proposed order exceeds the configured live order-value limit.")

        portfolios = self.db.query(Portfolio.id).filter(Portfolio.user_id == user_id).all()
        portfolio_ids = [row[0] for row in portfolios]
        if not portfolio_ids:
            raise LiveExecutionBlocked("No owned portfolios are available for account-wide risk checks.")

        # Account-wide exposure comes from the connected broker's actual
        # positions, never the app's paper Position table (which is virtual).
        try:
            broker_positions = self.positions_provider(user_id) if self.positions_provider else None
        except Exception as exc:
            raise LiveExecutionBlocked("Broker position lookup failed; order blocked.") from exc
        if not isinstance(broker_positions, (tuple, list)):
            raise LiveExecutionBlocked("Broker positions snapshot is missing or invalid.")
        exposure = Decimal("0")
        for broker_position in broker_positions:
            if not isinstance(broker_position, BrokerPositionSnapshot):
                raise LiveExecutionBlocked("Broker position row is invalid.")
            if not isinstance(broker_position.instrument_key, str) or not broker_position.instrument_key.strip():
                raise LiveExecutionBlocked("Broker position instrument identity is invalid.")
            if type(broker_position.quantity) is not int:
                raise LiveExecutionBlocked("Broker position quantity is invalid.")
            if not isinstance(broker_position.market_price, Decimal) or not broker_position.market_price.is_finite() or broker_position.market_price <= 0:
                raise LiveExecutionBlocked("Broker position mark price is invalid.")
            self._fresh_timestamp(broker_position.observed_at, now, "Broker position")
            exposure += abs(Decimal(broker_position.quantity)) * broker_position.market_price

        # Existing unresolved orders are included, so a retry or timeout cannot
        # create risk budget by disappearing from local status.
        pending = (
            self.db.query(Order)
            .filter(
                Order.portfolio_id.in_(portfolio_ids),
                Order.trading_mode == "LIVE",
                Order.status.in_(PENDING_LIVE_STATES),
            )
            .all()
        )
        for order in pending:
            pending_instrument = self.db.get(Instrument, order.instrument_id)
            if pending_instrument is None or not pending_instrument.is_active:
                raise LiveExecutionBlocked("A pending live order cannot be safely valued.")
            if order.limit_price is not None:
                mark = Decimal(str(order.limit_price))
            else:
                mark = self._fresh_quote(user_id, pending_instrument, now).price
            exposure += Decimal(order.quantity) * mark

        if exposure + proposed_value > max_gross_exposure:
            raise LiveExecutionBlocked("Account-wide gross exposure limit would be exceeded.")

        frequency_limit = int(settings.LIVE_MAX_ORDERS_PER_UTC_DAY)
        if frequency_limit <= 0:
            raise LiveExecutionBlocked("Live order-frequency limit is invalid or disabled.")
        day_start = now.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = (
            self.db.query(func.count(Order.id))
            .filter(
                Order.portfolio_id.in_(portfolio_ids),
                Order.trading_mode == "LIVE",
                Order.placed_at >= day_start,
            )
            .scalar()
        ) or 0
        if today_count >= frequency_limit:
            raise LiveExecutionBlocked("Account-wide live order-frequency limit reached.")

        daily_loss_limit = Decimal(str(settings.LIVE_MAX_DAILY_LOSS_INR))
        if daily_loss_limit <= 0:
            raise LiveExecutionBlocked("Live daily-loss limit is invalid or disabled.")
        realized_pnl = (
            self.db.query(func.coalesce(func.sum(Execution.realized_pnl), 0))
            .filter(
                Execution.portfolio_id.in_(portfolio_ids),
                Execution.executed_at >= day_start,
                Execution.broker_connection_id.isnot(None),
            )
            .scalar()
        )
        realized_pnl = Decimal(str(realized_pnl or 0))
        if realized_pnl < 0 and abs(realized_pnl) >= daily_loss_limit:
            raise LiveExecutionBlocked("Account-wide daily realized-loss limit reached.")

        funds = self.funds_provider(user_id)
        if not isinstance(funds, BrokerFundsSnapshot):
            raise LiveExecutionBlocked("Broker funds snapshot is invalid.")
        self._fresh_timestamp(funds.observed_at, now, "Broker funds")
        if not funds.cash_available.is_finite() or funds.cash_available < 0:
            raise LiveExecutionBlocked("Broker cash availability is invalid.")

        margin = self.margin_provider(user_id, instrument, intent, proposed_value)
        if not isinstance(margin, BrokerMarginSnapshot):
            raise LiveExecutionBlocked("Broker margin estimate is invalid.")
        self._fresh_timestamp(margin.observed_at, now, "Broker margin")
        if not margin.required_margin.is_finite() or margin.required_margin < 0:
            raise LiveExecutionBlocked("Broker required margin is invalid.")
        if margin.required_margin > funds.cash_available:
            raise LiveExecutionBlocked("Broker cash available is below estimated required margin.")

        return LiveRiskDecision(allowed=True, reason="Account-wide live pre-trade checks passed.")

    def _fresh_quote(self, user_id: UUID, instrument: Instrument, now: datetime) -> LiveQuoteSnapshot:
        try:
            quote = self.quote_provider(user_id, instrument) if self.quote_provider else None
        except Exception as exc:
            raise LiveExecutionBlocked("Broker quote lookup failed; order blocked.") from exc
        if not isinstance(quote, LiveQuoteSnapshot):
            raise LiveExecutionBlocked("Broker quote snapshot is missing or invalid.")
        if not quote.price.is_finite() or quote.price <= 0:
            raise LiveExecutionBlocked("Broker quote price is invalid.")
        self._fresh_timestamp(quote.observed_at, now, "Broker quote")
        return quote

    @staticmethod
    def _fresh_timestamp(observed_at: datetime, now: datetime, label: str) -> None:
        if not isinstance(observed_at, datetime) or observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise LiveExecutionBlocked(f"{label} timestamp must be timezone-aware.")
        age = (now - observed_at).total_seconds()
        if age < -2 or age > int(settings.LIVE_MAX_MARKET_DATA_AGE_SECONDS):
            raise LiveExecutionBlocked(f"{label} data is stale or from the future.")
