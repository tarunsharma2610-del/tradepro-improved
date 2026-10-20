"""Reconcile broker child-order status against durable broker trade intake.

Only BrokerOrder metadata is updated. This module does not transition the
conceptual local Order, create Execution rows, or change cash/positions/P&L.
"""
import hmac
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.brokers.base import BrokerAdapter, BrokerCallResult
from app.brokers.registry import get_broker_adapter
from app.brokers.upstox.response_parsing import parse_order_details
from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.repositories.broker_connection_repository import BrokerConnectionRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.broker_trade_ingestion_service import (
    BrokerTradeIngestionResult,
    BrokerTradeIngestionService,
)


@dataclass(frozen=True)
class BrokerChildReconciliationResult:
    local_order_id: UUID
    broker_order_ref_id: UUID
    broker_order_id: str
    status: str
    filled_quantity: int
    average_fill_price: Decimal | None
    trades_inserted: int
    duplicate_trades: int


class BrokerChildOrderReconciliationService:
    """Fetch official status and trade rows, then update only child-order metadata."""

    BROKER_NAME = "upstox"
    TERMINAL_STATES = {"FILLED", "CANCELLED", "CANCELLED_PARTIALLY_FILLED", "REJECTED"}

    def __init__(self, db: Session, adapter: BrokerAdapter | Any | None = None):
        self.db = db
        self.adapter = adapter
        self.connections = BrokerConnectionRepository(db)
        self.credentials = BrokerCredentialsService(db)
        self.ingestion = BrokerTradeIngestionService(db, adapter=adapter)

    async def reconcile(
        self,
        user_id: UUID,
        local_order_id: UUID,
        broker_order_ref_id: UUID,
    ) -> BrokerChildReconciliationResult:
        order, child, connection = self._owned_context(user_id, local_order_id, broker_order_ref_id)
        trade_result = await self.ingestion.fetch_and_ingest(
            user_id, local_order_id, child.broker_order_id
        )

        # Trade intake rechecks its own credential identity. Obtain a fresh
        # token for the independent official status read and bind it again
        # after async I/O before changing BrokerOrder metadata.
        token = self.credentials.get_access_token(user_id, self.BROKER_NAME)
        if not isinstance(token, str) or not token.strip():
            raise ValueError("No usable Upstox access token; child-order reconciliation blocked.")
        adapter = self.adapter or get_broker_adapter(self.BROKER_NAME)
        try:
            response = await adapter.get_order_status(token, child.broker_order_id)
        except Exception as exc:
            raise ValueError("Upstox child-order status lookup failed; status was not updated.") from exc
        if not isinstance(response, BrokerCallResult) or not response.ok:
            detail = response.error if isinstance(response, BrokerCallResult) else "invalid adapter result"
            raise ValueError(f"Upstox child-order status lookup failed: {detail or 'unknown error'}.")
        try:
            details = parse_order_details(response.data, child.broker_order_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Upstox child-order details failed validation: {exc}") from exc

        try:
            self.db.refresh(connection)
            current_token = self.credentials.get_access_token(user_id, self.BROKER_NAME)
        except Exception as exc:
            raise ValueError("Upstox connection could not be revalidated after status lookup.") from exc
        if (
            not connection.is_connected
            or connection.id != child.broker_connection_id
            or not isinstance(current_token, str)
            or not hmac.compare_digest(current_token, token)
        ):
            raise ValueError("Upstox connection or token changed during status lookup; reconciliation blocked.")

        # Trade intake locks the parent Order row. Re-acquire that same lock
        # after network I/O before reading staged trades so a concurrent intake
        # cannot commit between the trade-sum check and child-state update.
        locked_order_row = (
            self.db.query(Order, Portfolio.user_id)
            .join(Portfolio, Portfolio.id == Order.portfolio_id)
            .filter(Order.id == order.id, Portfolio.user_id == user_id)
            .with_for_update(of=Order)
            .populate_existing()
            .first()
        )
        if locked_order_row is None:
            raise ValueError("Order ownership changed during broker status lookup; child status was not updated.")
        locked_order, owner_id = locked_order_row
        if owner_id != user_id or locked_order.trading_mode != "LIVE":
            raise ValueError("Local order is no longer LIVE; child status was not updated.")
        if (
            locked_order.instrument_id != order.instrument_id
            or locked_order.side != order.side
            or locked_order.quantity != order.quantity
        ):
            raise ValueError("Local order economics changed during broker status lookup; reconciliation blocked.")
        order = locked_order

        # Lock/refresh the child row after the parent row, using the same lock
        # order as trade intake, and revalidate all mapping/economic fields.
        locked_child = (
            self.db.query(BrokerOrder)
            .filter(BrokerOrder.id == child.id, BrokerOrder.order_id == order.id)
            .with_for_update()
            .populate_existing()
            .first()
        )
        if (
            locked_child is None
            or locked_child.broker_connection_id != connection.id
            or locked_child.broker_order_id != details.order_id
        ):
            raise ValueError("Broker child-order mapping changed during reconciliation.")
        child = locked_child
        if details.quantity <= 0 or details.quantity != child.requested_quantity:
            raise ValueError("Broker order quantity conflicts with the persisted child-order mapping.")
        if details.instrument_token is not None and details.instrument_token != order.instrument.instrument_key:
            raise ValueError("Broker order instrument conflicts with the persisted local order.")
        if details.transaction_type is not None and details.transaction_type != order.side:
            raise ValueError("Broker order side conflicts with the persisted local order.")

        normalized_status = self._normalize_status(details.status, details.filled_quantity, details.quantity)
        records = (
            self.db.query(BrokerTradeRecord)
            .filter(
                BrokerTradeRecord.broker_connection_id == connection.id,
                BrokerTradeRecord.broker_order_ref_id == child.id,
            )
            .all()
        )
        recorded_quantity = sum(int(record.quantity) for record in records)
        if recorded_quantity != details.filled_quantity:
            raise ValueError(
                "Broker status filled_quantity does not match the durable broker trade records; child status was not updated."
            )

        average_fill_price: Decimal | None = None
        if recorded_quantity:
            gross = sum(Decimal(str(record.price)) * int(record.quantity) for record in records)
            average_fill_price = gross / Decimal(recorded_quantity)
            if details.average_price <= 0 or abs(average_fill_price - details.average_price) > Decimal("0.01"):
                raise ValueError(
                    "Broker average price conflicts with durable trade records; child status was not updated."
                )

        if child.status in self.TERMINAL_STATES and child.status != normalized_status:
            raise ValueError("Broker child-order terminal state conflict; manual review required.")
        if details.filled_quantity < int(child.filled_quantity or 0):
            raise ValueError("Broker reported a lower filled quantity than previously reconciled.")

        child.status = normalized_status
        child.filled_quantity = details.filled_quantity
        try:
            self.db.add(child)
            self.db.commit()
            self.db.refresh(child)
        except Exception:
            self.db.rollback()
            raise

        return BrokerChildReconciliationResult(
            local_order_id=order.id,
            broker_order_ref_id=child.id,
            broker_order_id=child.broker_order_id,
            status=child.status,
            filled_quantity=child.filled_quantity,
            average_fill_price=average_fill_price,
            trades_inserted=trade_result.inserted_count,
            duplicate_trades=trade_result.duplicate_count,
        )

    def _owned_context(
        self, user_id: UUID, local_order_id: UUID, broker_order_ref_id: UUID
    ) -> tuple[Order, BrokerOrder, BrokerConnection]:
        row = (
            self.db.query(Order, Portfolio.user_id)
            .join(Portfolio, Portfolio.id == Order.portfolio_id)
            .filter(Order.id == local_order_id, Portfolio.user_id == user_id)
            .first()
        )
        if row is None:
            raise ValueError("Order not found.")
        order, owner_id = row
        if owner_id != user_id or order.trading_mode != "LIVE":
            raise ValueError("Child-order reconciliation is only allowed for an owned LIVE order.")
        child = (
            self.db.query(BrokerOrder)
            .filter(BrokerOrder.id == broker_order_ref_id, BrokerOrder.order_id == order.id)
            .first()
        )
        if child is None or child.broker_name != self.BROKER_NAME or child.broker_connection_id is None:
            raise ValueError("Broker child order mapping is missing or invalid.")
        connection = self.connections.get_for_user(user_id, self.BROKER_NAME)
        if connection is None or not connection.is_connected or connection.id != child.broker_connection_id:
            raise ValueError("Broker child order is not bound to this user's verified Upstox connection.")
        return order, child, connection

    @classmethod
    def _normalize_status(cls, raw_status: str, filled: int, requested: int) -> str:
        normalized = " ".join(raw_status.strip().lower().replace("_", " ").split())
        if filled < 0 or filled > requested:
            raise ValueError("Broker filled quantity is outside the requested order quantity.")
        if normalized in {"complete", "completed", "filled"}:
            if filled != requested:
                raise ValueError("Broker reports complete while filled quantity is incomplete.")
            return "FILLED"
        if normalized in {"cancelled", "canceled"}:
            if filled == requested and requested > 0:
                raise ValueError("Broker reports cancelled after the full requested quantity was filled.")
            return "CANCELLED_PARTIALLY_FILLED" if filled else "CANCELLED"
        if normalized in {"rejected", "reject"}:
            if filled:
                raise ValueError("Broker reports rejected despite a non-zero filled quantity.")
            return "REJECTED"
        if normalized in {"partially filled", "partial"}:
            if filled <= 0 or filled >= requested:
                raise ValueError("Broker partial-fill status conflicts with filled quantity.")
            return "PARTIALLY_FILLED"
        if normalized in {
            "open", "pending", "trigger pending", "validation pending",
            "put order req received", "modify pending", "modify req received",
            "cancel pending", "open pending",
        }:
            if filled >= requested and requested > 0:
                raise ValueError("Broker reports an open order despite the full requested quantity being filled.")
            return "PARTIALLY_FILLED" if filled else (
                "OPEN" if normalized in {"open", "open pending"} else "PENDING"
            )
        raise ValueError("Unrecognized broker order status; child-order state was not updated.")
