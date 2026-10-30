"""
This is the one place manual order placement happens in Phase 2 — and per
the architecture rule, it's built so Phase 3's strategy engine calls the
same place_order() rather than a parallel implementation (it'll pass
execution_reason="STRATEGY" and a strategy_id instead of the Phase 2
defaults, nothing else changes).

MARKET orders fill immediately against a real LTP fetched from the user's
connected broker — if there's no connected broker or the quote call
fails, the order is REJECTED with a clear reason. It never falls back to
a made-up price. PAPER LIMIT orders are stored as PENDING and checked by
the worker during market hours; fills use the same accounting engine.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.brokers.registry import get_broker_adapter
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.repositories.position_repository import PositionRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.position_math import apply_fill
from app.services.portfolio_risk_service import check_portfolio_order
from app.services.transaction_costs import Segment, Side, calculate_costs
from app.services.paper_trade_charge_estimator import estimate_paper_trade_costs
from app.core.config import settings
from app.services.execution_charge_totals import recompute_execution_total_charges


class OrderValidationError(Exception):
    """Raised for a malformed request (unknown portfolio/instrument) —
    the API layer turns this into a 404/400. Distinct from a business-rule
    REJECTED order, which is a normal, successfully-processed outcome."""


@dataclass
class PlaceOrderRequest:
    portfolio_id: UUID
    instrument_id: UUID
    side: Side
    order_type: str  # MARKET, LIMIT
    segment: Segment
    quantity: int
    limit_price: Decimal | None = None
    execution_reason: str = "MANUAL"  # "STRATEGY" when called from strategy_execution_service
    strategy_id: UUID | None = None


class ExecutionService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolios = PortfolioRepository(db)
        self.orders = OrderRepository(db)
        self.positions = PositionRepository(db)
        self.instruments = InstrumentRepository(db)
        self.broker_credentials = BrokerCredentialsService(db)

    async def place_order(self, user_id: UUID, req: PlaceOrderRequest) -> Order:
        # Validate at the service boundary as well as the HTTP schema: strategy
        # automation and future internal callers do not pass through Pydantic.
        if req.quantity <= 0:
            raise OrderValidationError("Quantity must be greater than zero.")
        if req.order_type not in {"MARKET", "LIMIT"}:
            raise OrderValidationError("Order type must be MARKET or LIMIT.")
        if req.order_type == "LIMIT":
            if req.limit_price is None or req.limit_price <= 0:
                raise OrderValidationError("LIMIT orders require a positive limit price.")
        elif req.limit_price is not None:
            raise OrderValidationError("MARKET orders must not include a limit price.")

        portfolio = self.portfolios.get_for_user_for_update(user_id, req.portfolio_id)
        if portfolio is None:
            raise OrderValidationError("Portfolio not found.")

        instrument = self.instruments.get_by_id(req.instrument_id)
        if instrument is None:
            raise OrderValidationError("Instrument not found.")

        now = datetime.now(timezone.utc)
        order = Order(
            portfolio_id=portfolio.id,
            instrument_id=instrument.id,
            side=req.side.value,
            order_type=req.order_type,
            segment=req.segment.value,
            quantity=req.quantity,
            limit_price=req.limit_price,
            status="PENDING",
            trading_mode="PAPER",
            execution_reason=req.execution_reason,
            strategy_id=req.strategy_id,
            placed_at=now,
        )

        if req.order_type == "LIMIT":
            risk_reason = check_portfolio_order(
                self.db, portfolio, instrument, side=req.side.value, quantity=req.quantity,
                estimated_price=Decimal(str(req.limit_price)),
                reducing_position=self._is_reducing_position(portfolio.id, instrument.id, req.side, req.quantity),
            )
            if risk_reason:
                return self._reject(order, risk_reason)
            # The worker rechecks relevant limits before filling the order.
            return self.orders.create(order)

        access_token = self.broker_credentials.get_access_token(user_id, "upstox")
        if access_token is None:
            return self._reject(order, "No connected broker with a live session — connect Upstox in Settings first.")

        ltp, quote_error = await self._get_ltp(portfolio.user_id, instrument.instrument_key, access_token, req.side, req.quantity)
        if ltp is None:
            return self._reject(order, quote_error or "No fresh market price is available.")

        risk_reason = check_portfolio_order(
            self.db, portfolio, instrument, side=req.side.value, quantity=req.quantity,
            estimated_price=ltp,
            reducing_position=self._is_reducing_position(portfolio.id, instrument.id, req.side, req.quantity),
        )
        if risk_reason:
            return self._reject(order, risk_reason)

        estimate = await self._estimate_paper_costs(
            access_token, instrument.instrument_key, req.segment, req.side, req.quantity, ltp
        )
        costs = estimate.costs
        charge_source = f"PAPER_{estimate.source}"

        if req.side == Side.BUY:
            required_cash = costs.gross_value + costs.total_charges
            if Decimal(str(portfolio.cash_balance)) < required_cash:
                return self._reject(order, f"Insufficient virtual capital: need {required_cash}, have {portfolio.cash_balance}.")

        if req.side == Side.SELL and req.segment == Segment.EQUITY_DELIVERY:
            position = self.positions.get_or_create(portfolio.id, instrument.id)
            if position.quantity < req.quantity:
                return self._reject(
                    order,
                    f"Insufficient holdings for a delivery sell: hold {position.quantity}, tried to sell {req.quantity}.",
                )

        return self._fill(order, portfolio, instrument, req, ltp, costs, charge_source=charge_source)

    def cancel_order(self, user_id: UUID, portfolio_id: UUID, order_id: UUID) -> Order:
        """Cancel a user's pending paper order; filled/rejected orders are immutable."""
        portfolio = self.portfolios.get_for_user_for_update(user_id, portfolio_id)
        if portfolio is None:
            raise OrderValidationError("Portfolio not found.")

        order = (
            self.db.query(Order)
            .filter(Order.id == order_id, Order.portfolio_id == portfolio.id)
            .with_for_update()
            .first()
        )
        if order is None:
            raise OrderValidationError("Order not found.")
        if order.trading_mode != "PAPER":
            raise OrderValidationError("Only paper orders can be cancelled through this endpoint.")
        if order.status != "PENDING":
            raise OrderValidationError(f"Only pending orders can be cancelled; current status is {order.status}.")

        order.status = "CANCELLED"
        return self.orders.save(order)

    async def match_pending_limit_orders(self, limit: int = 100) -> int:
        """Fill crossed PAPER LIMIT orders using current broker quotes.

        Uses the same cost, position and cash accounting as market orders.
        The conditional row lock/status predicate prevents two PostgreSQL
        workers from matching the same pending order concurrently.
        """
        pending_ids = [
            row[0]
            for row in (
                self.db.query(Order.id)
                .filter(
                    Order.status == "PENDING",
                    Order.order_type == "LIMIT",
                    Order.trading_mode == "PAPER",
                )
                .order_by(Order.placed_at.asc())
                .limit(max(1, min(limit, 500)))
                .all()
            )
        ]
        filled_count = 0

        for order_id in pending_ids:
            order = (
                self.db.query(Order)
                .filter(
                    Order.id == order_id,
                    Order.status == "PENDING",
                    Order.order_type == "LIMIT",
                    Order.trading_mode == "PAPER",
                )
                .with_for_update(skip_locked=True)
                .first()
            )
            if order is None:
                continue

            portfolio = (
                self.db.query(Portfolio)
                .filter(Portfolio.id == order.portfolio_id)
                .with_for_update()
                .first()
            )
            if portfolio is None:
                self.db.rollback()
                continue

            access_token = self.broker_credentials.get_access_token(portfolio.user_id, "upstox")
            if access_token is None:
                self.db.rollback()
                continue

            ltp, quote_error = await self._get_ltp(
                portfolio.user_id, order.instrument.instrument_key, access_token
            )
            if ltp is None:
                self.db.rollback()
                continue

            side = Side(order.side)
            limit_price = Decimal(str(order.limit_price))
            crossed = (side == Side.BUY and ltp <= limit_price) or (side == Side.SELL and ltp >= limit_price)
            if not crossed:
                self.db.rollback()
                continue

            # A limit order can receive price improvement, never a worse
            # fill than its limit: BUY fills at min(LTP, limit), SELL at max.
            fill_price = min(ltp, limit_price) if side == Side.BUY else max(ltp, limit_price)
            segment = Segment(order.segment)
            risk_reason = check_portfolio_order(
                self.db, portfolio, order.instrument, side=side.value, quantity=order.quantity,
                estimated_price=fill_price,
                reducing_position=self._is_reducing_position(portfolio.id, order.instrument_id, side, order.quantity),
                check_order_count=False,
                exclude_order_id=order.id,
            )
            if risk_reason:
                self._reject(order, risk_reason)
                continue

            estimate = await self._estimate_paper_costs(
                access_token, order.instrument.instrument_key, segment, side, order.quantity, fill_price
            )
            costs = estimate.costs
            charge_source = f"PAPER_{estimate.source}"

            if side == Side.BUY:
                required_cash = costs.gross_value + costs.total_charges
                if Decimal(str(portfolio.cash_balance)) < required_cash:
                    self._reject(order, f"Insufficient virtual capital at limit fill: need {required_cash}, have {portfolio.cash_balance}.")
                    continue

            if side == Side.SELL and segment == Segment.EQUITY_DELIVERY:
                position = (
                    self.db.query(Position)
                    .filter(Position.portfolio_id == portfolio.id, Position.instrument_id == order.instrument_id)
                    .first()
                )
                held_quantity = position.quantity if position is not None else 0
                if held_quantity < order.quantity:
                    self._reject(
                        order,
                        f"Insufficient holdings for a delivery limit sell: hold {held_quantity}, tried to sell {order.quantity}.",
                    )
                    continue

            req = PlaceOrderRequest(
                portfolio_id=order.portfolio_id,
                instrument_id=order.instrument_id,
                side=side,
                order_type="LIMIT",
                segment=segment,
                quantity=order.quantity,
                limit_price=limit_price,
                execution_reason=order.execution_reason,
                strategy_id=order.strategy_id,
            )
            self._fill(order, portfolio, order.instrument, req, fill_price, costs, charge_source=charge_source)
            filled_count += 1

        return filled_count

    async def _estimate_paper_costs(
        self, access_token: str, instrument_key: str, segment: Segment, side: Side,
        quantity: int, price: Decimal,
    ):
        """Use Upstox's pre-trade calculator when enabled; retain local rates as fallback."""
        if not settings.UPSTOX_CHARGE_ESTIMATES_ENABLED:
            from app.services.paper_trade_charge_estimator import PaperTradeChargeEstimate
            return PaperTradeChargeEstimate(
                calculate_costs(segment, side, quantity, price),
                "HARDCODED_FALLBACK",
                "api_estimates_disabled",
            )
        return await estimate_paper_trade_costs(
            access_token,
            instrument_token=instrument_key,
            quantity=quantity,
            segment=segment,
            side=side,
            price=price,
            trade_date=datetime.now(timezone.utc).date(),
        )

    async def _get_ltp(
        self,
        user_id: UUID,
        instrument_key: str,
        access_token: str,
        side: Side = Side.BUY,
        quantity: int = 1,
    ) -> tuple[Decimal | None, str | None]:
        """Price a paper market order from a fresh exchange snapshot's executable depth.

        The current WebSocket subscription is LTPC-only, so it is suitable for
        monitoring/valuation but does not provide enough depth to simulate a
        market fill. Use Full Market Quotes V3 for the executable bid/ask book.
        """
        quote_result = await get_broker_adapter("upstox").get_full_quote(access_token, [instrument_key])
        if not quote_result.ok:
            return None, f"Could not fetch a timestamped market-depth snapshot: {quote_result.error}"
        price = _extract_fresh_market_depth_price(
            quote_result.data, instrument_key, side=side, quantity=quantity
        )
        if price is None:
            return None, "Broker market-depth snapshot was missing, stale, invalid, or lacked enough executable quantity."
        return price, None

    def _is_reducing_position(self, portfolio_id: UUID, instrument_id: UUID, side: Side, quantity: int) -> bool:
        position = (
            self.db.query(Position)
            .filter(Position.portfolio_id == portfolio_id, Position.instrument_id == instrument_id)
            .first()
        )
        if position is None or position.quantity == 0:
            return False
        if side == Side.SELL:
            return position.quantity > 0 and quantity <= position.quantity
        return position.quantity < 0 and quantity <= abs(position.quantity)

    def _reject(self, order: Order, reason: str) -> Order:
        order.status = "REJECTED"
        order.rejection_reason = reason
        return self.orders.create(order)

    def _fill(self, order: Order, portfolio: Portfolio, instrument: Instrument, req: PlaceOrderRequest, ltp: Decimal, costs, *, charge_source: str = "PAPER_ESTIMATE") -> Order:
        now = datetime.now(timezone.utc)
        order.status = "FILLED"
        order.filled_at = now
        order = self.orders.create(order)

        position = self.positions.get_or_create(portfolio.id, instrument.id)
        update = apply_fill(
            position_quantity=position.quantity,
            position_avg_price=Decimal(str(position.avg_price)),
            side=req.side,
            fill_quantity=req.quantity,
            fill_price=ltp,
        )
        position.quantity = update.new_quantity
        position.avg_price = update.new_avg_price
        position.realized_pnl = Decimal(str(position.realized_pnl)) + update.realized_pnl
        self.positions.save(position)

        portfolio.cash_balance = Decimal(str(portfolio.cash_balance)) + costs.net_cash_impact
        self.portfolios.save(portfolio)

        execution = Execution(
            order_id=order.id,
            portfolio_id=portfolio.id,
            instrument_id=instrument.id,
            side=req.side.value,
            quantity=req.quantity,
            price=ltp,
            gross_value=costs.gross_value,
            brokerage=costs.brokerage,
            stt=costs.stt,
            exchange_charges=costs.exchange_charges,
            sebi_charges=costs.sebi_charges,
            stamp_duty=costs.stamp_duty,
            gst=costs.gst,
            demat_transaction_charges=None,
            demat_charge_status=(
                "UNKNOWN"
                if req.segment == Segment.EQUITY_DELIVERY and req.side == Side.SELL
                else "NOT_APPLICABLE"
            ),
            total_charges=costs.total_charges,
            charge_source=charge_source,
            realized_pnl=update.realized_pnl,
            executed_at=now,
        )
        # One shared component-based total calculation keeps the optional DP/demat
        # field null when not sourced, and includes it only when explicitly present.
        recompute_execution_total_charges(execution)
        self.db.add(execution)
        self.db.commit()

        return order


def _extract_fresh_market_depth_price(
    quote_data: Any,
    instrument_key: str,
    *,
    side: Side,
    quantity: int,
    now: datetime | None = None,
    max_snapshot_age_seconds: int = 15,
) -> Decimal | None:
    """Return a depth-weighted paper fill price from a fresh Upstox V3 snapshot.

    Snapshot timestamp, not last_trade_time, determines feed freshness:
    an illiquid instrument can have an older last trade while its current
    bid/ask book remains fresh. BUY consumes asks; SELL consumes bids.
    """
    if quantity <= 0 or not isinstance(quote_data, dict):
        return None
    payload = quote_data.get("data", quote_data)
    if not isinstance(payload, dict):
        return None
    current = now or datetime.now(timezone.utc)
    for quote in payload.values():
        if not isinstance(quote, dict) or quote.get("instrument_token") != instrument_key:
            continue
        try:
            snapshot_raw = quote.get("timestamp")
            if not isinstance(snapshot_raw, str):
                return None
            snapshot_time = datetime.fromisoformat(snapshot_raw.replace("Z", "+00:00"))
            if snapshot_time.tzinfo is None:
                return None
            snapshot_age = (current - snapshot_time.astimezone(timezone.utc)).total_seconds()
            if snapshot_age < -60 or snapshot_age > max_snapshot_age_seconds:
                return None
            depth = quote.get("depth")
            if not isinstance(depth, dict):
                return None
            levels = depth.get("sell" if side == Side.BUY else "buy")
            if not isinstance(levels, list):
                return None
            remaining = quantity
            gross_value = Decimal("0")
            for level in levels:
                if not isinstance(level, dict):
                    continue
                try:
                    price = Decimal(str(level.get("price")))
                    available = int(level.get("quantity"))
                except (InvalidOperation, TypeError, ValueError, OverflowError):
                    continue
                if not price.is_finite() or price <= 0 or available <= 0:
                    continue
                taken = min(remaining, available)
                gross_value += price * taken
                remaining -= taken
                if remaining == 0:
                    return gross_value / Decimal(quantity)
            return None
        except (TypeError, ValueError, OverflowError):
            return None
    return None


def _extract_ltp(quote_data: Any, instrument_key: str) -> Decimal | None:
    """Return only the requested instrument's quote; never guess from another key.

    A missing requested key is a failed quote, not permission to use a
    different instrument's price for paper accounting.
    """
    if not isinstance(quote_data, dict):
        return None
    payload = quote_data.get("data", quote_data)
    if not isinstance(payload, dict):
        return None

    def parse_price(value: Any) -> Decimal | None:
        try:
            price = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None
        return price if price.is_finite() and price > 0 else None

    direct = payload.get(instrument_key)
    if isinstance(direct, dict) and "last_price" in direct:
        return parse_price(direct["last_price"])

    return None
