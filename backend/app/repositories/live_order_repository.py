"""Repository safeguards for durable live-order intent creation.

This module persists intent/audit/outbox records only. It deliberately has no broker adapter
dependency and cannot submit, cancel, or reconcile broker orders.
"""
import hashlib
import json
import re
import uuid
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.broker_connection import BrokerConnection
from app.models.live_order_records import LiveOrderEvent, LiveOrderIntent, LiveOrderOutbox
from app.models.portfolio import Portfolio


_SENSITIVE_KEY_PARTS = (
    "accesstoken", "refreshtoken", "token", "secret", "password",
    "authorization", "apikey", "clientsecret", "privatekey", "cookie",
)


def _validate_safe_json(value: Any, *, field_name: str) -> None:
    """Reject credential-like keys and values that are not finite JSON.

    This is a defense-in-depth key-name check, not a substitute for callers
    explicitly redacting secrets before building snapshots or audit details.
    """
    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if not isinstance(key, str):
                    raise ValueError(f"{field_name} keys must be strings")
                normalized = re.sub(r"[^a-z0-9]", "", key.lower())
                if any(part in normalized for part in _SENSITIVE_KEY_PARTS):
                    raise ValueError(f"{field_name} must not contain credential-like field '{key}'")
                walk(child, f"{path}.{key}")
        elif isinstance(node, (list, tuple)):
            for index, child in enumerate(node):
                walk(child, f"{path}[{index}]")

    walk(value, field_name)
    try:
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must contain finite JSON-compatible values") from exc


def canonical_request_hash(
    *, user_id: uuid.UUID, portfolio_id: uuid.UUID, broker_connection_id: uuid.UUID,
    order_snapshot: dict[str, Any],
) -> str:
    """Hash canonical JSON plus ownership/account scope; reject non-JSON or non-finite values."""
    canonical = json.dumps(
        {
            "user_id": str(user_id),
            "portfolio_id": str(portfolio_id),
            "broker_connection_id": str(broker_connection_id),
            "order": order_snapshot,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class IdempotencyConflict(ValueError):
    """The same client key was reused for a different economic request."""


class LiveOrderRepository:
    """Persist live intent + outbox + initial audit event as one DB transaction."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_idempotency_key(
        self, user_id: uuid.UUID, broker_connection_id: uuid.UUID, client_idempotency_key: str
    ) -> LiveOrderIntent | None:
        return (
            self.db.query(LiveOrderIntent)
            .filter(
                LiveOrderIntent.user_id == user_id,
                LiveOrderIntent.broker_connection_id == broker_connection_id,
                LiveOrderIntent.client_idempotency_key == client_idempotency_key,
            )
            .first()
        )

    def create_or_get_intent(
        self,
        *,
        user_id: uuid.UUID,
        portfolio_id: uuid.UUID,
        broker_connection_id: uuid.UUID,
        client_idempotency_key: str,
        order_snapshot: dict[str, Any],
        correlation_id: str | None = None,
    ) -> tuple[LiveOrderIntent, bool]:
        """Return (intent, created). Same key/hash is idempotent; key/hash mismatch conflicts.

        Ownership is checked against both portfolio and broker connection. The intent, outbox,
        and first event are committed together. Unique constraints arbitrate concurrent requests.
        """
        key = client_idempotency_key.strip()
        if not key or len(key) > 128:
            raise ValueError("client_idempotency_key must contain 1-128 non-whitespace characters")
        if not isinstance(order_snapshot, dict) or not order_snapshot:
            raise ValueError("order_snapshot must be a non-empty normalized order object")
        _validate_safe_json(order_snapshot, field_name="order_snapshot")

        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id, Portfolio.user_id == user_id
        ).first()
        connection = self.db.query(BrokerConnection).filter(
            BrokerConnection.id == broker_connection_id, BrokerConnection.user_id == user_id
        ).first()
        if portfolio is None or connection is None:
            raise ValueError("portfolio and broker connection must belong to the authenticated user")

        request_hash = canonical_request_hash(
            user_id=user_id,
            portfolio_id=portfolio_id,
            broker_connection_id=broker_connection_id,
            order_snapshot=order_snapshot,
        )
        existing = self.get_by_idempotency_key(user_id, broker_connection_id, key)
        if existing is not None:
            if existing.request_hash != request_hash:
                raise IdempotencyConflict("idempotency key already exists with a different request payload")
            return existing, False

        intent = LiveOrderIntent(
            user_id=user_id,
            portfolio_id=portfolio_id,
            broker_connection_id=broker_connection_id,
            client_idempotency_key=key,
            request_hash=request_hash,
            order_snapshot=order_snapshot,
            state="CREATED",
        )
        try:
            self.db.add(intent)
            self.db.flush()
            self.db.add(LiveOrderOutbox(intent_id=intent.id, status="READY"))
            self.db.add(
                LiveOrderEvent(
                    intent_id=intent.id,
                    event_type="INTENT_CREATED",
                    correlation_id=correlation_id,
                    actor_user_id=user_id,
                    safe_details={"state": "CREATED", "outbox": "READY"},
                )
            )
            self.db.commit()
            self.db.refresh(intent)
            return intent, True
        except IntegrityError:
            # A concurrent request may have won the unique-key race. Roll back our entire
            # transaction before looking up that winner; no orphan outbox/event is retained.
            self.db.rollback()
            winner = self.get_by_idempotency_key(user_id, broker_connection_id, key)
            if winner is None:
                raise
            if winner.request_hash != request_hash:
                raise IdempotencyConflict(
                    "idempotency key already exists with a different request payload"
                )
            return winner, False

    def append_event(
        self,
        *,
        user_id: uuid.UUID,
        intent_id: uuid.UUID,
        event_type: str,
        safe_details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> LiveOrderEvent:
        """Append an audit event only for an intent owned by the authenticated user.

        Callers must pass redacted, non-secret details; access tokens and authorization headers
        must never be stored in event details.
        """
        if not event_type.strip() or len(event_type) > 50:
            raise ValueError("event_type must contain 1-50 characters")
        intent = self.db.query(LiveOrderIntent).filter(
            LiveOrderIntent.id == intent_id, LiveOrderIntent.user_id == user_id
        ).first()
        if intent is None:
            raise ValueError("live-order intent not found for authenticated user")
        if safe_details is not None:
            if not isinstance(safe_details, dict):
                raise ValueError("safe_details must be a JSON object")
            _validate_safe_json(safe_details, field_name="safe_details")
        event = LiveOrderEvent(
            intent_id=intent_id,
            event_type=event_type,
            correlation_id=correlation_id,
            actor_user_id=user_id,
            safe_details=safe_details,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
