"""Atomic promotion of a broker-confirmed trade into live accounting.

The service is deliberately unregistered. It writes only broker-scoped
LivePosition and Execution rows; it never changes paper Position rows or
Portfolio.cash_balance. Actual broker-reported charges with an audit reference
are mandatory; estimated paper costs are rejected for live promotion.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.live_position import LivePosition
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.services.position_math import apply_fill
from app.services.transaction_costs import Side


CENT = Decimal("0.01")


@dataclass(frozen=True)
class LiveFillChargeBreakdown:
    brokerage: Decimal
    stt: Decimal
    exchange_charges: Decimal
    sebi_charges: Decimal
    stamp_duty: Decimal
    gst: Decimal
    total_charges: Decimal
    source: str
    reference: str


@dataclass(frozen=True)
class LiveFillAccountingResult:
    execution_id: UUID
    broker_trade_id: str
    inserted: bool
    live_position_quantity: int
    live_position_average_price: Decimal
    realized_pnl: Decimal


class LiveFillAccountingService:
    """Promote one staged broker trade exactly once, atomically."""

    def __init__(self, db: Session):
        self.db = db

    def promote_trade(
        self,
        user_id: UUID,
        broker_trade_record_id: UUID,
        charges: LiveFillChargeBreakdown,
    ) -> LiveFillAccountingResult:
        try:
            fee_values = self._validate_charges(charges)
            record = (
                self.db.query(BrokerTradeRecord)
                .filter(BrokerTradeRecord.id == broker_trade_record_id)
                .with_for_update()
                .first()
            )
            if record is None:
                raise ValueError("Broker trade intake record not found.")

            child = (
                self.db.query(BrokerOrder)
                .filter(BrokerOrder.id == record.broker_order_ref_id)
                .with_for_update()
                .first()
            )
            if child is None or child.broker_connection_id != record.broker_connection_id:
                raise ValueError("Broker trade is not bound to a valid child-order/connection mapping.")
            if record.quantity > child.filled_quantity or record.quantity > child.requested_quantity:
                raise ValueError("Broker trade quantity exceeds the broker-confirmed child-order fill quantity.")
            row = (
                self.db.query(Order, Portfolio.user_id)
                .join(Portfolio, Portfolio.id == Order.portfolio_id)
                .filter(Order.id == child.order_id, Portfolio.user_id == user_id)
                .with_for_update()
                .first()
            )
            if row is None:
                raise ValueError("Broker trade order not found.")
            order, owner_id = row
            if owner_id != user_id or order.trading_mode != "LIVE":
                raise ValueError("Live fill accounting is only allowed for an owned LIVE order.")
            if order.execution_reason != "MANUAL":
                raise ValueError("Only manual LIVE orders are supported by this accounting step.")
            connection = (
                self.db.query(BrokerConnection)
                .filter(
                    BrokerConnection.id == record.broker_connection_id,
                    BrokerConnection.user_id == user_id,
                    BrokerConnection.broker == child.broker_name,
                )
                .first()
            )
            if connection is None or child.broker_name != "upstox":
                raise ValueError("Broker trade connection is not owned by this user.")
            instrument: Instrument | None = self.db.get(Instrument, order.instrument_id)
            if instrument is None:
                raise ValueError("The order instrument no longer exists.")
            if record.instrument_token != instrument.instrument_key:
                raise ValueError("Broker trade instrument does not match the local order.")
            if record.side != order.side or record.side not in {"BUY", "SELL"}:
                raise ValueError("Broker trade side does not match the local order.")
            if type(record.quantity) is not int or record.quantity <= 0:
                raise ValueError("Broker trade quantity is invalid.")
            price = Decimal(str(record.price))
            if not price.is_finite() or price <= 0:
                raise ValueError("Broker trade price is invalid.")
            executed_at = self._parse_exchange_timestamp(record.exchange_timestamp)

            existing = (
                self.db.query(Execution)
                .filter(
                    Execution.broker_connection_id == connection.id,
                    Execution.broker_trade_id == record.broker_trade_id,
                )
                .first()
            )
            if existing is not None:
                if not self._same_execution(existing, record, order, fee_values, charges):
                    raise ValueError("Broker trade already has a conflicting accounted execution.")
                position = self._get_live_position(connection.id, instrument.id)
                if position is None:
                    raise ValueError("Accounted execution exists but its live position row is missing.")
                self.db.rollback()
                return self._result(existing, record, position, inserted=False)

            # A child order's filled_quantity is an aggregate cap, not a per-trade
            # cap. The child row is locked above so concurrent promotions for the
            # same child are serialized on PostgreSQL.
            accounted_quantity = (
                self.db.query(func.coalesce(func.sum(Execution.quantity), 0))
                .filter(
                    Execution.broker_order_ref_id == child.id,
                    Execution.broker_connection_id == connection.id,
                )
                .scalar()
            )
            if int(accounted_quantity or 0) + record.quantity > child.filled_quantity:
                raise ValueError(
                    "Cumulative accounted trade quantity exceeds the broker-confirmed child-order fill quantity."
                )

            portfolio = (
                self.db.query(Portfolio)
                .filter(Portfolio.id == order.portfolio_id, Portfolio.user_id == user_id)
                .with_for_update()
                .first()
            )
            if portfolio is None or not portfolio.is_active:
                raise ValueError("Order portfolio is missing or inactive.")

            position = self._get_live_position(connection.id, instrument.id, lock=True)
            if position is None:
                position = LivePosition(
                    broker_connection_id=connection.id,
                    instrument_id=instrument.id,
                    quantity=0,
                    avg_price=Decimal("0"),
                    realized_pnl=Decimal("0"),
                )
                self.db.add(position)
                self.db.flush()

            side = Side(record.side)
            update = apply_fill(
                position_quantity=position.quantity,
                position_avg_price=Decimal(str(position.avg_price)),
                side=side,
                fill_quantity=record.quantity,
                fill_price=price,
            )
            position.quantity = update.new_quantity
            position.avg_price = update.new_avg_price
            position.realized_pnl = Decimal(str(position.realized_pnl)) + update.realized_pnl

            gross_value = (price * Decimal(record.quantity)).quantize(CENT, rounding=ROUND_HALF_UP)
            execution = Execution(
                order_id=order.id,
                portfolio_id=portfolio.id,
                instrument_id=instrument.id,
                side=record.side,
                quantity=record.quantity,
                price=price,
                gross_value=gross_value,
                brokerage=fee_values["brokerage"],
                stt=fee_values["stt"],
                exchange_charges=fee_values["exchange_charges"],
                sebi_charges=fee_values["sebi_charges"],
                stamp_duty=fee_values["stamp_duty"],
                gst=fee_values["gst"],
                total_charges=fee_values["total_charges"],
                charge_source=charges.source,
                charge_reference=charges.reference.strip(),
                realized_pnl=update.realized_pnl,
                strategy_realized_pnl=None,
                broker_order_ref_id=child.id,
                broker_name=child.broker_name,
                broker_connection_id=connection.id,
                broker_trade_id=record.broker_trade_id,
                executed_at=executed_at,
            )
            self.db.add_all([position, execution])
            self.db.commit()
            self.db.refresh(execution)
            self.db.refresh(position)
            return self._result(execution, record, position, inserted=True)
        except IntegrityError:
            self.db.rollback()
            # A concurrent promotion may have won the unique trade-ID race.
            record = self.db.get(BrokerTradeRecord, broker_trade_record_id)
            if record is not None:
                existing = (
                    self.db.query(Execution)
                    .filter(
                        Execution.broker_connection_id == record.broker_connection_id,
                        Execution.broker_trade_id == record.broker_trade_id,
                    )
                    .first()
                )
                if existing is not None:
                    position = self._get_live_position(
                        record.broker_connection_id,
                        existing.instrument_id,
                    )
                    if position is not None and existing.charge_source == charges.source and existing.charge_reference == charges.reference.strip():
                        return self._result(existing, record, position, inserted=False)
            raise ValueError("Concurrent live fill promotion conflict; review required.") from None
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _validate_charges(charges: LiveFillChargeBreakdown) -> dict[str, Decimal]:
        if not isinstance(charges, LiveFillChargeBreakdown):
            raise ValueError("An explicit validated live-fill charge breakdown is required.")
        if charges.source != "BROKER_REPORTED":
            raise ValueError("Live fill promotion requires broker-reported charges, not estimates.")
        if not isinstance(charges.reference, str) or not charges.reference.strip():
            raise ValueError("Broker-reported charges require a non-empty audit reference.")
        names = (
            "brokerage", "stt", "exchange_charges", "sebi_charges",
            "stamp_duty", "gst", "total_charges",
        )
        values: dict[str, Decimal] = {}
        for name in names:
            raw = getattr(charges, name)
            try:
                amount = Decimal(str(raw))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError(f"Live-fill charge {name} is invalid.") from None
            if not amount.is_finite() or amount < 0:
                raise ValueError(f"Live-fill charge {name} must be finite and non-negative.")
            if amount != amount.quantize(CENT):
                raise ValueError(f"Live-fill charge {name} must be expressed to paise precision.")
            values[name] = amount
        component_sum = sum(values[name] for name in names[:-1])
        if values["total_charges"] != component_sum:
            raise ValueError("Live-fill total_charges must equal the sum of its six components.")
        return values

    @staticmethod
    def _parse_exchange_timestamp(value: str | None) -> datetime:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Broker trade exchange timestamp is required for live accounting.")
        try:
            parsed = datetime.fromisoformat(value.strip())
        except ValueError:
            raise ValueError("Broker trade exchange timestamp is not valid ISO-8601.") from None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("Broker trade exchange timestamp must include a timezone offset.")
        return parsed.astimezone(timezone.utc)

    def _get_live_position(self, connection_id: UUID, instrument_id: UUID, lock: bool = False) -> LivePosition | None:
        query = self.db.query(LivePosition).filter(
            LivePosition.broker_connection_id == connection_id,
            LivePosition.instrument_id == instrument_id,
        )
        if lock:
            query = query.with_for_update().populate_existing()
        return query.first()

    @staticmethod
    def _same_execution(
        execution: Execution,
        record: BrokerTradeRecord,
        order: Order,
        fees: dict[str, Decimal],
        charges: LiveFillChargeBreakdown,
    ) -> bool:
        return (
            execution.order_id == order.id
            and execution.broker_order_ref_id == record.broker_order_ref_id
            and execution.quantity == record.quantity
            and Decimal(str(execution.price)) == Decimal(str(record.price))
            and execution.side == record.side
            and execution.charge_source == charges.source
            and execution.charge_reference == charges.reference.strip()
            and Decimal(str(execution.brokerage)) == fees["brokerage"]
            and Decimal(str(execution.stt)) == fees["stt"]
            and Decimal(str(execution.exchange_charges)) == fees["exchange_charges"]
            and Decimal(str(execution.sebi_charges)) == fees["sebi_charges"]
            and Decimal(str(execution.stamp_duty)) == fees["stamp_duty"]
            and Decimal(str(execution.gst)) == fees["gst"]
            and Decimal(str(execution.total_charges)) == fees["total_charges"]
        )

    @staticmethod
    def _result(
        execution: Execution,
        record: BrokerTradeRecord,
        position: LivePosition,
        *,
        inserted: bool,
    ) -> LiveFillAccountingResult:
        return LiveFillAccountingResult(
            execution_id=execution.id,
            broker_trade_id=record.broker_trade_id,
            inserted=inserted,
            live_position_quantity=position.quantity,
            live_position_average_price=Decimal(str(position.avg_price)),
            realized_pnl=Decimal(str(execution.realized_pnl)),
        )
