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

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings

from app.brokers.registry import get_broker_adapter
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.models.strategy_position import StrategyPosition
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.position_math import apply_fill
from app.services.instrument_validation import validate_instrument_segment
from app.services.transaction_costs import Segment, Side, calculate_costs


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
    idempotency_key: str | None = None


class ExecutionService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolios = PortfolioRepository(db)
        self.orders = OrderRepository(db)
        self.instruments = InstrumentRepository(db)
        self.broker_credentials = BrokerCredentialsService(db)

    async def place_order(self, user_id: UUID, req: PlaceOrderRequest) -> Order:
        # Fail closed: this service implements PAPER accounting only. Until a separately
        # reviewed live execution lifecycle exists, refuse LIVE or unknown modes here.
        if settings.TRADING_MODE.strip().upper() != "PAPER":
            raise OrderValidationError(
                "Live trading is not implemented in this build. Set TRADING_MODE=PAPER; "
                "no broker order was submitted."
            )

        # Validate at the service boundary as well as the HTTP schema: strategy
        # automation and future internal callers do not pass through Pydantic.
        if req.execution_reason == "STRATEGY" and req.strategy_id is None:
            raise OrderValidationError("Strategy orders require a strategy_id.")
        if req.quantity <= 0:
            raise OrderValidationError("Quantity must be greater than zero.")
        if req.order_type not in {"MARKET", "LIMIT"}:
            raise OrderValidationError("Order type must be MARKET or LIMIT.")
        if req.order_type == "LIMIT":
            if req.limit_price is None or req.limit_price <= 0:
                raise OrderValidationError("LIMIT orders require a positive limit price.")
        elif req.limit_price is not None:
            raise OrderValidationError("MARKET orders must not include a limit price.")

        portfolio = self.portfolios.get_for_user(user_id, req.portfolio_id)
        if portfolio is None:
            raise OrderValidationError("Portfolio not found.")

        if req.idempotency_key:
            existing = (
                self.db.query(Order)
                .filter(Order.portfolio_id == portfolio.id, Order.idempotency_key == req.idempotency_key)
                .first()
            )
            if existing is not None:
                self._ensure_same_idempotent_request(existing, req)
                return existing

        instrument = self.instruments.get_by_id(req.instrument_id)
        if instrument is None:
            raise OrderValidationError("Instrument not found.")

        try:
            validate_instrument_segment(instrument, req.segment)
        except ValueError as exc:
            raise OrderValidationError(str(exc)) from exc

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
            idempotency_key=req.idempotency_key,
            placed_at=now,
        )

        if req.order_type == "LIMIT":
            # The limit is the worst price accepted by the paper matcher, so it
            # is a conservative estimate of this order's notional value.
            limit_reason = self._order_value_limit_reason(portfolio, req.quantity, req.limit_price)
            if limit_reason:
                return self._reject(order, limit_reason)
            # The worker fills this later if the market quote crosses the limit.
            saved, _created = self._persist_order(order)
            return saved

        access_token = self.broker_credentials.get_access_token(user_id, "upstox")
        if access_token is None:
            return self._reject(order, "No connected broker with a live session — connect Upstox in Settings first.")

        quote_result = await get_broker_adapter("upstox").get_quote(access_token, [instrument.instrument_key])
        if not quote_result.ok:
            return self._reject(order, f"Could not fetch a live price: {quote_result.error}")

        ltp = _extract_ltp(quote_result.data, instrument.instrument_key)
        if ltp is None:
            return self._reject(order, "Broker response didn't contain a readable last traded price.")

        costs = calculate_costs(req.segment, req.side, req.quantity, ltp)

        if req.side == Side.BUY:
            required_cash = costs.gross_value + costs.total_charges
            if Decimal(str(portfolio.cash_balance)) < required_cash:
                return self._reject(order, f"Insufficient virtual capital: need {required_cash}, have {portfolio.cash_balance}.")

        value_limit_reason = self._order_value_limit_reason(portfolio, req.quantity, ltp)
        if value_limit_reason:
            return self._reject(order, value_limit_reason)

        return self._fill(order, portfolio, instrument, req, ltp, costs)

    def cancel_order(self, user_id: UUID, portfolio_id: UUID, order_id: UUID) -> Order:
        """Cancel a user's pending paper order; filled/rejected orders are immutable."""
        portfolio = self.portfolios.get_for_user(user_id, portfolio_id)
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

            portfolio = self.db.get(Portfolio, order.portfolio_id)
            if portfolio is None:
                self.db.rollback()
                continue

            access_token = self.broker_credentials.get_access_token(portfolio.user_id, "upstox")
            if access_token is None:
                self.db.rollback()
                continue

            quote_result = await get_broker_adapter("upstox").get_quote(
                access_token, [order.instrument.instrument_key]
            )
            if not quote_result.ok:
                self.db.rollback()
                continue

            ltp = _extract_ltp(quote_result.data, order.instrument.instrument_key)
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
            costs = calculate_costs(segment, side, order.quantity, fill_price)

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
            self._fill(order, portfolio, order.instrument, req, fill_price, costs)
            filled_count += 1

        return filled_count

    def _reject(self, order: Order, reason: str) -> Order:
        order.status = "REJECTED"
        order.rejection_reason = reason
        saved, _created = self._persist_order(order)
        return saved

    def _fill(self, order: Order, portfolio: Portfolio, instrument: Instrument, req: PlaceOrderRequest, ltp: Decimal, costs) -> Order:
        """Apply one paper fill atomically, protecting cash and allocated shares."""
        now = datetime.now(timezone.utc)
        try:
            locked_portfolio = (
                self.db.query(Portfolio)
                .filter(Portfolio.id == portfolio.id)
                .with_for_update()
                .populate_existing()
                .first()
            )
            if locked_portfolio is None:
                raise OrderValidationError("Portfolio not found.")

            strategy_position = None
            strategy_position_is_new = False
            if req.execution_reason == "STRATEGY":
                strategy = (
                    self.db.query(Strategy)
                    .filter(
                        Strategy.id == req.strategy_id,
                        Strategy.portfolio_id == locked_portfolio.id,
                        Strategy.instrument_id == instrument.id,
                    )
                    .with_for_update()
                    .first()
                )
                if strategy is None:
                    raise OrderValidationError("Strategy not found for this portfolio and instrument.")
                strategy_position = (
                    self.db.query(StrategyPosition)
                    .filter(StrategyPosition.strategy_id == req.strategy_id)
                    .with_for_update()
                    .populate_existing()
                    .first()
                )
                if strategy_position is None:
                    strategy_position = StrategyPosition(
                        strategy_id=req.strategy_id,
                        portfolio_id=locked_portfolio.id,
                        instrument_id=instrument.id,
                        quantity=0,
                        avg_price=0,
                        realized_pnl=0,
                    )
                    strategy_position_is_new = True

                if req.side == Side.BUY and strategy_position.quantity != 0:
                    return self._reject(order, "Strategy already owns an open position; duplicate entry rejected.")
                if req.side == Side.SELL and (
                    strategy_position.quantity <= 0 or req.quantity > strategy_position.quantity
                ):
                    return self._reject(
                        order,
                        f"Strategy does not own enough shares to exit: owns {strategy_position.quantity}, tried to sell {req.quantity}.",
                    )

            if req.side == Side.BUY:
                required_cash = costs.gross_value + costs.total_charges
                if Decimal(str(locked_portfolio.cash_balance)) < required_cash:
                    return self._reject(
                        order,
                        f"Insufficient virtual capital: need {required_cash}, have {locked_portfolio.cash_balance}.",
                    )

            position = (
                self.db.query(Position)
                .filter(
                    Position.portfolio_id == locked_portfolio.id,
                    Position.instrument_id == instrument.id,
                )
                .with_for_update()
                .populate_existing()
                .first()
            )
            held_quantity = position.quantity if position is not None else 0

            if req.side == Side.SELL and req.execution_reason != "STRATEGY":
                allocated = (
                    self.db.query(func.coalesce(func.sum(StrategyPosition.quantity), 0))
                    .filter(
                        StrategyPosition.portfolio_id == locked_portfolio.id,
                        StrategyPosition.instrument_id == instrument.id,
                        StrategyPosition.quantity > 0,
                    )
                    .scalar()
                )
                available = max(held_quantity - int(allocated or 0), 0)
                if req.segment == Segment.EQUITY_DELIVERY and available < req.quantity:
                    return self._reject(
                        order,
                        f"Insufficient unallocated delivery holdings: available {available}, tried to sell {req.quantity}.",
                    )
                if held_quantity > 0 and available < req.quantity:
                    return self._reject(
                        order,
                        f"Shares reserved by strategy positions: available to sell {available}, tried to sell {req.quantity}.",
                    )

            if position is None:
                position = Position(
                    portfolio_id=locked_portfolio.id,
                    instrument_id=instrument.id,
                    quantity=0,
                    avg_price=0,
                    realized_pnl=0,
                )
                self.db.add(position)

            order.status = "FILLED"
            order.filled_at = now
            self.db.add(order)
            try:
                # Flush only the order row first; related accounting remains uncommitted.
                self.db.flush()
            except IntegrityError:
                self.db.rollback()
                if not order.idempotency_key:
                    raise
                existing = (
                    self.db.query(Order)
                    .filter(
                        Order.portfolio_id == order.portfolio_id,
                        Order.idempotency_key == order.idempotency_key,
                    )
                    .first()
                )
                if existing is None:
                    raise
                self._ensure_same_order_payload(existing, order)
                return existing

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

            strategy_realized_pnl = None
            if strategy_position is not None:
                strategy_update = apply_fill(
                    position_quantity=strategy_position.quantity,
                    position_avg_price=Decimal(str(strategy_position.avg_price)),
                    side=req.side,
                    fill_quantity=req.quantity,
                    fill_price=ltp,
                )
                strategy_position.quantity = strategy_update.new_quantity
                strategy_position.avg_price = strategy_update.new_avg_price
                strategy_position.realized_pnl = Decimal(str(strategy_position.realized_pnl)) + strategy_update.realized_pnl
                strategy_realized_pnl = strategy_update.realized_pnl
                self.db.add(strategy_position)

            locked_portfolio.cash_balance = (
                Decimal(str(locked_portfolio.cash_balance)) + costs.net_cash_impact
            )

            execution = Execution(
                order_id=order.id,
                portfolio_id=locked_portfolio.id,
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
                total_charges=costs.total_charges,
                realized_pnl=update.realized_pnl,
                strategy_realized_pnl=strategy_realized_pnl,
                executed_at=now,
            )
            self.db.add_all([position, locked_portfolio, execution])
            self.db.commit()
            self.db.refresh(order)
            return order
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _order_value_limit_reason(portfolio: Portfolio, quantity: int, price: Decimal | None) -> str | None:
        limit_pct = Decimal(str(settings.MAX_ORDER_VALUE_PCT_OF_VIRTUAL_CAPITAL))
        if limit_pct <= 0 or price is None:
            return None
        estimated_value = Decimal(quantity) * Decimal(str(price))
        maximum_value = Decimal(str(portfolio.virtual_capital)) * limit_pct / Decimal("100")
        if estimated_value > maximum_value:
            return (
                f"Maximum order value exceeded: estimated ₹{estimated_value} is above "
                f"₹{maximum_value} ({limit_pct}% of starting virtual capital)."
            )
        return None

    def _persist_order(self, order: Order) -> tuple[Order, bool]:
        """Persist once; the database uniqueness constraint arbitrates concurrent retries."""
        try:
            return self.orders.create(order), True
        except IntegrityError:
            self.db.rollback()
            if not order.idempotency_key:
                raise
            existing = (
                self.db.query(Order)
                .filter(
                    Order.portfolio_id == order.portfolio_id,
                    Order.idempotency_key == order.idempotency_key,
                )
                .first()
            )
            if existing is None:
                raise
            self._ensure_same_order_payload(existing, order)
            return existing, False

    @staticmethod
    def _ensure_same_idempotent_request(existing: Order, req: PlaceOrderRequest) -> None:
        if (
            existing.instrument_id != req.instrument_id
            or existing.side != req.side.value
            or existing.order_type != req.order_type
            or existing.segment != req.segment.value
            or existing.quantity != req.quantity
            or (None if existing.limit_price is None else Decimal(str(existing.limit_price))) != req.limit_price
        ):
            raise OrderValidationError(
                "Idempotency key was already used for a different order request. Use a new key."
            )

    @staticmethod
    def _ensure_same_order_payload(existing: Order, candidate: Order) -> None:
        existing_price = None if existing.limit_price is None else Decimal(str(existing.limit_price))
        candidate_price = None if candidate.limit_price is None else Decimal(str(candidate.limit_price))
        if (
            existing.instrument_id != candidate.instrument_id
            or existing.side != candidate.side
            or existing.order_type != candidate.order_type
            or existing.segment != candidate.segment
            or existing.quantity != candidate.quantity
            or existing_price != candidate_price
        ):
            raise OrderValidationError(
                "Idempotency key was already used for a different order request. Use a new key."
            )


def _extract_ltp(quote_data: Any, instrument_key: str) -> Decimal | None:
    """Defensive on purpose: the exact key Upstox nests quotes under in the
    response wasn't independently confirmed against a live account, only
    against a documented curl example — see app/brokers/upstox/adapter.py.
    This tries the documented shape first, then falls back to scanning for
    any entry that looks like a quote, and gives up (returns None) rather
    than guessing a number if neither works."""
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

    for value in payload.values():
        if isinstance(value, dict) and "last_price" in value:
            parsed = parse_price(value["last_price"])
            if parsed is not None:
                return parsed

    return None
