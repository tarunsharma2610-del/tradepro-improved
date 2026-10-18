"""Atomic promotion of staged broker trades into isolated live accounting.

This module is deliberately not registered with an API route, worker, or order
submission path. Each trade requires an explicit fee breakdown and provenance.
It updates LivePosition + Execution in one DB transaction and never mutates the
paper Position or Portfolio.cash_balance.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import UUID

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
from app.services.live_execution_service import LiveExecutionBlocked
from app.services.position_math import apply_fill
from app.services.transaction_costs import Side

CENT = Decimal("0.01")
ALLOWED_CHARGE_SOURCES = {"BROKER_REPORTED", "APPROVED_ESTIMATE"}


@dataclass(frozen=True)
class LiveChargeBreakdown:
    """Caller-supplied charge values with auditable source provenance.

    APPROVED_ESTIMATE is allowed only when the caller explicitly labels it as
    such and supplies the estimator/version reference; it is never represented
    as broker-confirmed. No charge calculator is silently invoked here.
    """

    brokerage: Decimal
    stt: Decimal
    exchange_charges: Decimal
    sebi_charges: Decimal
    stamp_duty: Decimal
    gst: Decimal
    source: str
    reference: str
    dp_charges: Decimal = Decimal("0")


@dataclass(frozen=True)
class LiveFillAccountingResult:
    broker_connection_id: UUID
    broker_trade_id: str
    execution_id: UUID | None
    duplicate: bool
    live_position_quantity: int
    live_position_avg_price: Decimal
    realized_pnl: Decimal


class LiveFillAccountingService:
    """Promote one previously ingested broker trade, idempotently and atomically."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _money(value: object, label: str) -> Decimal:
        try:
            result = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise LiveExecutionBlocked(f"{label} must be a valid monetary amount.") from None
        if not result.is_finite() or result < 0:
            raise LiveExecutionBlocked(f"{label} must be finite and non-negative.")
        return result.quantize(CENT, rounding=ROUND_HALF_UP)

    @classmethod
    def _validate_charges(cls, charges: LiveChargeBreakdown) -> tuple[dict[str, Decimal], Decimal]:
        if not isinstance(charges, LiveChargeBreakdown):
            raise LiveExecutionBlocked("An explicit validated live charge breakdown is required.")
        source = charges.source.strip().upper() if isinstance(charges.source, str) else ""
        reference = charges.reference.strip() if isinstance(charges.reference, str) else ""
        if source not in ALLOWED_CHARGE_SOURCES:
            raise LiveExecutionBlocked("Charge source must be BROKER_REPORTED or APPROVED_ESTIMATE.")
        if not reference:
            raise LiveExecutionBlocked("Charge provenance reference is required.")
        if len(reference) > 200:
            raise LiveExecutionBlocked("Charge provenance reference must not exceed 200 characters.")
        names = ("brokerage", "stt", "exchange_charges", "sebi_charges", "stamp_duty", "gst", "dp_charges")
        values = {name: cls._money(getattr(charges, name), name) for name in names}
        total = sum(values.values(), Decimal("0.00")).quantize(CENT, rounding=ROUND_HALF_UP)
        return values | {"charge_source": source, "charge_reference": reference}, total

    def account_trade(
        self,
        user_id: UUID,
        broker_trade_record_id: UUID,
        charges: LiveChargeBreakdown,
    ) -> LiveFillAccountingResult:
        """Atomically record one staged fill and apply it to LivePosition.

        The caller must pass a fee breakdown from a reviewed source. This method
        does not query the broker and does not infer or calculate fees.
        """
        try:
            validated_charges, total_charges = self._validate_charges(charges)
            record = (
                self.db.query(BrokerTradeRecord)
                .filter(BrokerTradeRecord.id == broker_trade_record_id)
                .with_for_update()
                .first()
            )
            if record is None:
                raise LiveExecutionBlocked("Staged broker trade record was not found.")

            child = (
                self.db.query(BrokerOrder)
                .filter(BrokerOrder.id == record.broker_order_ref_id)
                .with_for_update()
                .first()
            )
            if child is None or child.broker_connection_id != record.broker_connection_id:
                raise LiveExecutionBlocked("Staged trade's broker-order/connection mapping is invalid.")

            connection = (
                self.db.query(BrokerConnection)
                .filter(
                    BrokerConnection.id == record.broker_connection_id,
                    BrokerConnection.user_id == user_id,
                    BrokerConnection.broker == child.broker_name,
                )
                .first()
            )
            if connection is None:
                raise LiveExecutionBlocked("Staged trade is not owned by this user's broker connection.")

            order = (
                self.db.query(Order)
                .filter(Order.id == child.order_id)
                .with_for_update(of=Order)
                .first()
            )
            if order is None or order.trading_mode != "LIVE":
                raise LiveExecutionBlocked("Staged trade must map to a valid LIVE order.")
            owner = self.db.query(Portfolio.user_id).filter(Portfolio.id == order.portfolio_id).scalar()
            if owner != user_id:
                raise LiveExecutionBlocked("Live order is not owned by this user.")
            instrument = self.db.get(Instrument, order.instrument_id)
            if instrument is None or not instrument.is_active:
                raise LiveExecutionBlocked("Live order instrument is missing or inactive.")
            if record.side not in {"BUY", "SELL"} or record.side != order.side:
                raise LiveExecutionBlocked("Staged trade side conflicts with its parent order.")
            if record.instrument_token != instrument.instrument_key:
                raise LiveExecutionBlocked("Staged trade instrument token conflicts with its parent order.")
            if record.quantity <= 0 or record.price is None:
                raise LiveExecutionBlocked("Staged trade quantity or price is invalid.")
            try:
                price = Decimal(str(record.price))
            except (InvalidOperation, TypeError, ValueError):
                raise LiveExecutionBlocked("Trade price must be a valid monetary amount.") from None
            if not price.is_finite() or price <= 0:
                raise LiveExecutionBlocked("Trade price must be finite and positive.")
            # Keep the broker's supported four-decimal precision; only gross
            # turnover and fee components are rounded to paise.
            price = price.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            if price <= 0:
                raise LiveExecutionBlocked("Trade price is below the supported four-decimal precision.")
            gross_value = (price * Decimal(record.quantity)).quantize(CENT, rounding=ROUND_HALF_UP)

            # A trade record is eligible for accounting only after the child
            # order has been reconciled against the broker's official status
            # and the full durable trade list. Staged trades alone are not
            # sufficient evidence of the broker-confirmed cumulative fill.
            if (
                child.status_checked_at is None
                or child.status not in {"PARTIALLY_FILLED", "FILLED", "CANCELLED_PARTIALLY_FILLED"}
            ):
                raise LiveExecutionBlocked(
                    "Broker child order has not been successfully reconciled with confirmed fills."
                )
            if (
                type(child.filled_quantity) is not int
                or child.filled_quantity <= 0
                or child.requested_quantity is None
                or child.requested_quantity <= 0
                or child.filled_quantity > child.requested_quantity
            ):
                raise LiveExecutionBlocked("Broker child-order confirmed fill quantity is invalid.")
            staged_quantity = (
                self.db.query(BrokerTradeRecord.quantity)
                .filter(
                    BrokerTradeRecord.broker_connection_id == record.broker_connection_id,
                    BrokerTradeRecord.broker_order_ref_id == child.id,
                )
                .all()
            )
            durable_trade_quantity = sum(int(row[0]) for row in staged_quantity)
            if durable_trade_quantity != child.filled_quantity:
                raise LiveExecutionBlocked(
                    "Staged trade quantity does not match the broker child order's confirmed fill quantity."
                )

            existing = (
                self.db.query(Execution)
                .filter(
                    Execution.broker_connection_id == record.broker_connection_id,
                    Execution.broker_trade_id == record.broker_trade_id,
                )
                .first()
            )
            accounted_quantity = (
                self.db.query(Execution.quantity)
                .filter(
                    Execution.broker_connection_id == record.broker_connection_id,
                    Execution.broker_order_ref_id == child.id,
                )
                .all()
            )
            cumulative_accounted_quantity = sum(int(row[0]) for row in accounted_quantity)
            if cumulative_accounted_quantity > child.filled_quantity:
                raise LiveExecutionBlocked(
                    "Already-accounted fill quantity exceeds the broker-confirmed child-order fill quantity."
                )
            if existing is None and cumulative_accounted_quantity + record.quantity > child.filled_quantity:
                raise LiveExecutionBlocked(
                    "Promoting this trade would exceed the broker-confirmed child-order fill quantity."
                )
            if existing is not None:
                if (
                    existing.broker_order_ref_id != child.id
                    or existing.order_id != order.id
                    or existing.quantity != record.quantity
                    or Decimal(str(existing.price)) != Decimal(str(record.price))
                ):
                    raise LiveExecutionBlocked("Conflicting execution already exists for this broker trade ID.")
                # Do not silently treat a different charge source or amount as
                # a replay. Final contract-note charges need a separate,
                # append-only, idempotent adjustment workflow; mutating the
                # original execution would hide the estimate-to-actual change.
                persisted_charge_values = {
                    "brokerage": existing.brokerage,
                    "stt": existing.stt,
                    "exchange_charges": existing.exchange_charges,
                    "sebi_charges": existing.sebi_charges,
                    "stamp_duty": existing.stamp_duty,
                    "gst": existing.gst,
                    "dp_charges": existing.dp_charges,
                    "charge_source": existing.charge_source,
                    "charge_reference": existing.charge_reference,
                }
                if any(
                    Decimal(str(persisted_charge_values[name])) != Decimal(str(validated_charges[name]))
                    for name in (
                        "brokerage", "stt", "exchange_charges", "sebi_charges",
                        "stamp_duty", "gst", "dp_charges",
                    )
                ) or (
                    persisted_charge_values["charge_source"] != validated_charges["charge_source"]
                    or persisted_charge_values["charge_reference"] != validated_charges["charge_reference"]
                ):
                    raise LiveExecutionBlocked(
                        "Execution already has different charge provenance; final-charge adjustments require "
                        "a separate idempotent adjustment workflow."
                    )
                position = (
                    self.db.query(LivePosition)
                    .filter(
                        LivePosition.broker_connection_id == record.broker_connection_id,
                        LivePosition.instrument_id == instrument.id,
                    )
                    .first()
                )
                return LiveFillAccountingResult(
                    broker_connection_id=record.broker_connection_id,
                    broker_trade_id=record.broker_trade_id,
                    execution_id=existing.id,
                    duplicate=True,
                    live_position_quantity=position.quantity if position else 0,
                    live_position_avg_price=Decimal(str(position.avg_price if position else 0)),
                    realized_pnl=Decimal(str(existing.realized_pnl)),
                )

            position = (
                self.db.query(LivePosition)
                .filter(
                    LivePosition.broker_connection_id == record.broker_connection_id,
                    LivePosition.instrument_id == instrument.id,
                )
                .with_for_update(of=LivePosition)
                .first()
            )
            if position is None:
                position = LivePosition(
                    broker_connection_id=record.broker_connection_id,
                    instrument_id=instrument.id,
                    quantity=0,
                    avg_price=Decimal("0"),
                    realized_pnl=Decimal("0"),
                )
                self.db.add(position)
                self.db.flush()

            update = apply_fill(
                position_quantity=position.quantity,
                position_avg_price=Decimal(str(position.avg_price)),
                side=Side(record.side),
                fill_quantity=record.quantity,
                fill_price=price,
            )
            position.quantity = update.new_quantity
            position.avg_price = update.new_avg_price
            position.realized_pnl = (
                Decimal(str(position.realized_pnl)) + update.realized_pnl
            ).quantize(CENT, rounding=ROUND_HALF_UP)

            execution = Execution(
                order_id=order.id,
                portfolio_id=order.portfolio_id,
                instrument_id=instrument.id,
                side=record.side,
                quantity=record.quantity,
                price=price,
                gross_value=gross_value,
                brokerage=validated_charges["brokerage"],
                stt=validated_charges["stt"],
                exchange_charges=validated_charges["exchange_charges"],
                sebi_charges=validated_charges["sebi_charges"],
                stamp_duty=validated_charges["stamp_duty"],
                gst=validated_charges["gst"],
                dp_charges=validated_charges["dp_charges"],
                total_charges=total_charges,
                charge_source=validated_charges["charge_source"],
                charge_reference=validated_charges["charge_reference"],
                realized_pnl=update.realized_pnl,
                broker_order_ref_id=child.id,
                broker_name=child.broker_name,
                broker_connection_id=record.broker_connection_id,
                broker_trade_id=record.broker_trade_id,
                executed_at=self._trade_timestamp(record.exchange_timestamp),
            )
            self.db.add(execution)
            self.db.flush()
            self.db.commit()
            self.db.refresh(execution)
            self.db.refresh(position)
            return LiveFillAccountingResult(
                broker_connection_id=record.broker_connection_id,
                broker_trade_id=record.broker_trade_id,
                execution_id=execution.id,
                duplicate=False,
                live_position_quantity=position.quantity,
                live_position_avg_price=Decimal(str(position.avg_price)),
                realized_pnl=update.realized_pnl,
            )
        except IntegrityError:
            self.db.rollback()
            # The unique (connection, trade ID) execution constraint is the
            # final arbiter under concurrent replay. Return duplicate only if
            # the committed execution matches this exact staged trade.
            record = self.db.get(BrokerTradeRecord, broker_trade_record_id)
            if record is None:
                raise
            existing = (
                self.db.query(Execution)
                .filter(
                    Execution.broker_connection_id == record.broker_connection_id,
                    Execution.broker_trade_id == record.broker_trade_id,
                )
                .first()
            )
            if existing is None:
                raise
            if (
                existing.broker_order_ref_id != record.broker_order_ref_id
                or existing.quantity != record.quantity
                or Decimal(str(existing.price)) != Decimal(str(record.price))
            ):
                raise LiveExecutionBlocked("Conflicting execution already exists for this broker trade ID.")
            position = (
                self.db.query(LivePosition)
                .filter(
                    LivePosition.broker_connection_id == record.broker_connection_id,
                    LivePosition.instrument_id == existing.instrument_id,
                )
                .first()
            )
            return LiveFillAccountingResult(
                broker_connection_id=record.broker_connection_id,
                broker_trade_id=record.broker_trade_id,
                execution_id=existing.id,
                duplicate=True,
                live_position_quantity=position.quantity if position else 0,
                live_position_avg_price=Decimal(str(position.avg_price if position else 0)),
                realized_pnl=Decimal(str(existing.realized_pnl)),
            )
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _trade_timestamp(value: str | None):
        from datetime import datetime, timezone

        if not value:
            return datetime.now(timezone.utc)
        # Upstox trade timestamp formats are not yet verified. Preserve the
        # original string in BrokerTradeRecord and only parse strict ISO-8601
        # values here; unknown formats use ingestion time as an explicit
        # fallback rather than guessing a timezone.
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return datetime.now(timezone.utc)
        return parsed.astimezone(timezone.utc)
