"""Unregistered orchestration: reconcile all child orders, then promote staged fills.

No order-write API is called here. The coordinator requires successful official
status/trade reconciliation for every child before promoting any fill belonging
to the conceptual parent order. Multiple fills require distinct, timezone-aware
exchange timestamps so position accounting is applied in deterministic order.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.services.broker_child_order_reconciliation_service import (
    BrokerChildOrderReconciliationService,
)
from app.services.live_execution_service import LiveExecutionBlocked
from app.services.live_fill_promotion_service import LiveFillPromotionService


RECONCILED_CHILD_STATES = {
    "OPEN",
    "PENDING",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELLED",
    "CANCELLED_PARTIALLY_FILLED",
    "REJECTED",
}


@dataclass(frozen=True)
class ChildFillOutcome:
    broker_order_ref_id: UUID
    broker_order_id: str
    broker_status: str | None
    confirmed_filled_quantity: int
    staged_trade_count: int
    promoted_trade_count: int
    duplicate_trade_count: int
    error: str | None = None


@dataclass(frozen=True)
class LiveOrderFillReconciliationResult:
    local_order_id: UUID
    reconciliation_complete: bool
    promotion_complete: bool
    total_staged_trades: int
    total_promoted_trades: int
    total_duplicate_trades: int
    child_results: tuple[ChildFillOutcome, ...]
    blocked_reason: str | None = None


class LiveOrderFillReconciliationCoordinator:
    """Read-only broker reconciliation followed by staged-fill promotion."""

    def __init__(
        self,
        db: Session,
        *,
        child_reconciler: Any | None = None,
        promotion_service: Any | None = None,
    ):
        self.db = db
        self.child_reconciler = child_reconciler or BrokerChildOrderReconciliationService(db)
        self.promotion_service = promotion_service or LiveFillPromotionService(db)

    async def reconcile_and_promote(
        self, user_id: UUID, local_order_id: UUID
    ) -> LiveOrderFillReconciliationResult:
        row = (
            self.db.query(Order, Portfolio.user_id)
            .join(Portfolio, Portfolio.id == Order.portfolio_id)
            .filter(Order.id == local_order_id, Portfolio.user_id == user_id)
            .first()
        )
        if row is None:
            raise LiveExecutionBlocked("Order not found.")
        order, owner_id = row
        if owner_id != user_id or order.trading_mode != "LIVE":
            raise LiveExecutionBlocked("Fill reconciliation requires an owned LIVE order.")

        children = (
            self.db.query(BrokerOrder)
            .filter(
                BrokerOrder.order_id == order.id,
                BrokerOrder.broker_name == "upstox",
                BrokerOrder.broker_connection_id.isnot(None),
            )
            .order_by(BrokerOrder.created_at, BrokerOrder.id)
            .all()
        )
        if not children:
            raise LiveExecutionBlocked("No mapped Upstox child orders are available for reconciliation.")

        # Reconcile every child before promoting any fill for the parent. If a
        # sibling is unknown or mismatched, leave all staged fills unaccounted
        # so a retry can recover a consistent parent-order view.
        child_data: dict[UUID, dict[str, Any]] = {}
        reconciliation_errors: list[str] = []
        for child in children:
            entry = {
                "child": child,
                "status": None,
                "filled_quantity": 0,
                "staged_count": 0,
                "promoted_count": 0,
                "duplicate_count": 0,
                "error": None,
            }
            child_data[child.id] = entry
            try:
                result = await self.child_reconciler.reconcile(user_id, order.id, child.id)
                self.db.refresh(child)
                if (
                    result.broker_order_ref_id != child.id
                    or result.broker_order_id != child.broker_order_id
                    or result.status != child.status
                    or result.filled_quantity != child.filled_quantity
                ):
                    raise LiveExecutionBlocked(
                        "Child reconciliation result does not match the persisted broker child order."
                    )
                if child.status_checked_at is None or child.status not in RECONCILED_CHILD_STATES:
                    raise LiveExecutionBlocked(
                        "Broker child order lacks a successful recognized reconciliation state."
                    )
                entry["status"] = child.status
                entry["filled_quantity"] = int(child.filled_quantity)
            except Exception as exc:
                entry["error"] = str(exc)[:300] or "Child reconciliation failed."
                reconciliation_errors.append(
                    f"{child.broker_order_id}: {entry['error']}"
                )

        if reconciliation_errors:
            return self._result(
                order.id,
                child_data,
                reconciliation_complete=False,
                promotion_complete=False,
                blocked_reason="No fills were promoted because one or more child orders failed reconciliation: "
                + "; ".join(reconciliation_errors),
            )

        child_ids = list(child_data)
        records = (
            self.db.query(BrokerTradeRecord)
            .filter(BrokerTradeRecord.broker_order_ref_id.in_(child_ids))
            .order_by(BrokerTradeRecord.created_at, BrokerTradeRecord.id)
            .all()
        )
        records_by_child: dict[UUID, list[BrokerTradeRecord]] = {child_id: [] for child_id in child_ids}
        for record in records:
            entry = child_data.get(record.broker_order_ref_id)
            if entry is None or record.broker_connection_id != entry["child"].broker_connection_id:
                return self._result(
                    order.id,
                    child_data,
                    reconciliation_complete=True,
                    promotion_complete=False,
                    blocked_reason="A staged trade has an invalid child-order/connection mapping.",
                )
            records_by_child[record.broker_order_ref_id].append(record)
            entry["staged_count"] += 1

        for child_id, entry in child_data.items():
            durable_quantity = sum(record.quantity for record in records_by_child[child_id])
            if durable_quantity != entry["filled_quantity"]:
                return self._result(
                    order.id,
                    child_data,
                    reconciliation_complete=True,
                    promotion_complete=False,
                    blocked_reason=(
                        f"Staged trade quantity for child {entry['child'].broker_order_id} "
                        "does not match its broker-confirmed filled quantity."
                    ),
                )

        if len(records) > 1:
            timestamps: list[tuple[datetime, BrokerTradeRecord]] = []
            seen_timestamps: set[datetime] = set()
            for record in records:
                value = record.exchange_timestamp
                if not isinstance(value, str) or not value.strip():
                    return self._result(
                        order.id,
                        child_data,
                        reconciliation_complete=True,
                        promotion_complete=False,
                        blocked_reason=(
                            "Multiple fills require distinct timezone-aware exchange timestamps; "
                            "no fills were promoted."
                        ),
                    )
                try:
                    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    timestamp = None
                if timestamp is None or timestamp.tzinfo is None or timestamp.utcoffset() is None:
                    return self._result(
                        order.id,
                        child_data,
                        reconciliation_complete=True,
                        promotion_complete=False,
                        blocked_reason=(
                            "Multiple fills require distinct timezone-aware exchange timestamps; "
                            "no fills were promoted."
                        ),
                    )
                timestamp = timestamp.astimezone()
                if timestamp in seen_timestamps:
                    return self._result(
                        order.id,
                        child_data,
                        reconciliation_complete=True,
                        promotion_complete=False,
                        blocked_reason=(
                            "Multiple fills share an exchange timestamp; fill ordering is ambiguous and "
                            "promotion was blocked."
                        ),
                    )
                seen_timestamps.add(timestamp)
                timestamps.append((timestamp, record))
            records = [record for _, record in sorted(timestamps, key=lambda item: item[0])]

        promotion_error: str | None = None
        for record in records:
            try:
                result = await self.promotion_service.promote_trade(user_id, record.id)
                entry = child_data[record.broker_order_ref_id]
                if result.duplicate:
                    entry["duplicate_count"] += 1
                else:
                    entry["promoted_count"] += 1
            except Exception as exc:
                promotion_error = (
                    f"Promotion stopped at broker trade {record.broker_trade_id}: "
                    f"{str(exc)[:300] or 'charge/accounting promotion failed.'}"
                )
                break

        return self._result(
            order.id,
            child_data,
            reconciliation_complete=True,
            promotion_complete=promotion_error is None,
            blocked_reason=promotion_error,
        )

    @staticmethod
    def _result(
        local_order_id: UUID,
        child_data: dict[UUID, dict[str, Any]],
        *,
        reconciliation_complete: bool,
        promotion_complete: bool,
        blocked_reason: str | None,
    ) -> LiveOrderFillReconciliationResult:
        children = tuple(
            ChildFillOutcome(
                broker_order_ref_id=entry["child"].id,
                broker_order_id=entry["child"].broker_order_id,
                broker_status=entry["status"] or entry["child"].status,
                confirmed_filled_quantity=entry["filled_quantity"],
                staged_trade_count=entry["staged_count"],
                promoted_trade_count=entry["promoted_count"],
                duplicate_trade_count=entry["duplicate_count"],
                error=entry["error"],
            )
            for entry in child_data.values()
        )
        return LiveOrderFillReconciliationResult(
            local_order_id=local_order_id,
            reconciliation_complete=reconciliation_complete,
            promotion_complete=promotion_complete,
            total_staged_trades=sum(child.staged_trade_count for child in children),
            total_promoted_trades=sum(child.promoted_trade_count for child in children),
            total_duplicate_trades=sum(child.duplicate_trade_count for child in children),
            child_results=children,
            blocked_reason=blocked_reason,
        )
