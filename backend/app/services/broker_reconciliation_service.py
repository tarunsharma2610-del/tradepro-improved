"""Read-only broker status polling for explicitly LIVE orders.

This service intentionally does not create broker orders, map broker statuses
onto local FILLED/CANCELLED states, or mutate positions/cash. Those transitions
need a separately reviewed fill/reconciliation lifecycle and verified payloads.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.brokers.registry import get_broker_adapter
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.services.broker_credentials_service import BrokerCredentialsService


@dataclass
class BrokerStatusCheck:
    order_id: str
    ok: bool
    broker_status: str | None = None
    error: str | None = None


class BrokerReconciliationService:
    def __init__(self, db: Session):
        self.db = db
        self.credentials = BrokerCredentialsService(db)

    async def check_order_status(self, user_id: UUID, local_order_id: UUID) -> BrokerStatusCheck:
        row = (
            self.db.query(Order, Portfolio.user_id)
            .join(Portfolio, Portfolio.id == Order.portfolio_id)
            .filter(Order.id == local_order_id, Portfolio.user_id == user_id)
            .first()
        )
        if row is None:
            raise ValueError("Order not found.")
        order, owner_id = row
        if owner_id != user_id:
            raise ValueError("Order not found.")
        if order.trading_mode != "LIVE":
            raise ValueError("Broker reconciliation is only allowed for LIVE orders.")
        if not order.broker_order_id:
            raise ValueError("Order has no broker_order_id; status cannot be queried safely.")

        access_token = self.credentials.get_access_token(user_id, "upstox")
        if not access_token:
            raise ValueError("No usable Upstox session; reconnect before checking broker status.")

        result = await get_broker_adapter("upstox").get_order_status(access_token, order.broker_order_id)
        checked_at = datetime.now(timezone.utc)
        order.broker_status_checked_at = checked_at

        if not result.ok:
            order.broker_status_error = (result.error or "Broker status request failed.")[:500]
            self.db.add(order)
            self.db.commit()
            return BrokerStatusCheck(str(order.id), False, order.broker_status, order.broker_status_error)

        payload: Any = result.data
        if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
            payload = payload["data"]
        if not isinstance(payload, dict) or not isinstance(payload.get("status"), str) or not payload["status"].strip():
            order.broker_status_error = "Broker response did not contain a recognizable status field."
            self.db.add(order)
            self.db.commit()
            return BrokerStatusCheck(str(order.id), False, order.broker_status, order.broker_status_error)

        returned_order_id = payload.get("order_id")
        if returned_order_id is None or not str(returned_order_id).strip():
            order.broker_status_error = "Broker response did not include the requested broker order_id."
            self.db.add(order)
            self.db.commit()
            return BrokerStatusCheck(str(order.id), False, order.broker_status, order.broker_status_error)
        if str(returned_order_id) != order.broker_order_id:
            order.broker_status_error = "Broker response order_id did not match the requested broker order."
            self.db.add(order)
            self.db.commit()
            return BrokerStatusCheck(str(order.id), False, order.broker_status, order.broker_status_error)

        order.broker_status = payload["status"].strip()[:40]
        order.broker_status_error = None
        self.db.add(order)
        self.db.commit()
        return BrokerStatusCheck(str(order.id), True, order.broker_status, None)
