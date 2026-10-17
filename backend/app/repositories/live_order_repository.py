"""Repository safeguards for durable live-order intent creation.

This module persists intent/audit/outbox records only. It deliberately has no broker adapter
dependency and cannot submit, cancel, or reconcile broker orders.
"""
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.broker_connection import BrokerConnection
from app.models.live_order_records import BrokerFillIdentity, LiveOrderEvent, LiveOrderIntent, LiveOrderOutbox
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

    def record_broker_fill(
        self,
        *,
        user_id: uuid.UUID,
        broker_connection_id: uuid.UUID,
        broker_trade_id: str,
        broker_order_id: str,
        instrument_key: str,
        side: str,
        quantity: int,
        price: Any,
        executed_at: datetime,
        product: str,
        order_type: str,
        intent_id: uuid.UUID | None = None,
        safe_details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> tuple[BrokerFillIdentity, bool]:
        """Atomically persist one validated broker trade and audit event, idempotently.

        No broker I/O occurs here. The caller must normalize and match the trade first.
        Duplicate trade IDs with identical economic details are no-ops; a duplicate ID
        carrying different details is a conflict requiring manual reconciliation.
        """
        from decimal import Decimal, InvalidOperation

        def required(value: str, field: str, max_length: int = 128) -> str:
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > max_length:
                raise ValueError(f"{field} must contain 1-{max_length} characters")
            return value.strip()

        trade_id = required(broker_trade_id, "broker_trade_id")
        order_id = required(broker_order_id, "broker_order_id")
        instrument = required(instrument_key, "instrument_key")
        normalized_side = required(side, "side", 4).upper()
        if normalized_side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        normalized_product = required(product, "product", 16).upper()
        normalized_order_type = required(order_type, "order_type", 16).upper()
        if normalized_order_type not in {"MARKET", "LIMIT", "SL", "SL-M"}:
            raise ValueError("order_type is not supported")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        try:
            normalized_price = Decimal(str(price))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("price must be finite and positive") from exc
        if not normalized_price.is_finite() or normalized_price <= 0:
            raise ValueError("price must be finite and positive")
        if not isinstance(executed_at, datetime) or executed_at.tzinfo is None:
            raise ValueError("executed_at must be timezone-aware")
        if safe_details is not None:
            if not isinstance(safe_details, dict):
                raise ValueError("safe_details must be a JSON object")
            _validate_safe_json(safe_details, field_name="safe_details")

        connection = self.db.query(BrokerConnection).filter(
            BrokerConnection.id == broker_connection_id,
            BrokerConnection.user_id == user_id,
        ).first()
        if connection is None:
            raise ValueError("broker connection not found for authenticated user")
        if intent_id is not None:
            intent = self.db.query(LiveOrderIntent).filter(
                LiveOrderIntent.id == intent_id,
                LiveOrderIntent.user_id == user_id,
                LiveOrderIntent.broker_connection_id == broker_connection_id,
            ).first()
            if intent is None:
                raise ValueError("matched intent not found for authenticated user and broker connection")
            if intent.broker_order_id != order_id:
                raise LiveOrderVersionConflict("fill must match an intent already linked to this broker order ID")
            snapshot = intent.order_snapshot or {}
            expected_instrument = snapshot.get("instrument_key", snapshot.get("instrument_token"))
            expected_side = snapshot.get("side", snapshot.get("transaction_type"))
            expected_type = snapshot.get("order_type")
            expected_product = snapshot.get("product")
            expected_quantity = snapshot.get("quantity")
            if not all(value is not None for value in (
                expected_instrument, expected_side, expected_type, expected_product, expected_quantity
            )):
                raise ValueError("linked intent is missing required economic fields")
            if str(expected_instrument).strip() != instrument:
                raise LiveOrderVersionConflict("fill instrument differs from linked intent")
            if str(expected_side).strip().upper() != normalized_side:
                raise LiveOrderVersionConflict("fill side differs from linked intent")
            if str(expected_type).strip().upper() != normalized_order_type:
                raise LiveOrderVersionConflict("fill order type differs from linked intent")
            if str(expected_product).strip().upper() != normalized_product:
                raise LiveOrderVersionConflict("fill product differs from linked intent")
            try:
                requested_quantity = int(expected_quantity)
            except (TypeError, ValueError) as exc:
                raise ValueError("linked intent quantity is invalid") from exc
            if (
                isinstance(expected_quantity, bool)
                or requested_quantity <= 0
                or str(expected_quantity).strip() not in {str(requested_quantity), f"{requested_quantity}.0"}
            ):
                raise ValueError("linked intent quantity is invalid")
            if quantity > requested_quantity:
                raise LiveOrderVersionConflict("single fill quantity exceeds linked intent quantity")
            if normalized_order_type in {"LIMIT", "SL"}:
                raw_limit = snapshot.get("limit_price", snapshot.get("price"))
                try:
                    limit_price = Decimal(str(raw_limit))
                except (InvalidOperation, TypeError, ValueError) as exc:
                    raise ValueError("linked intent limit price is invalid") from exc
                if not limit_price.is_finite() or limit_price <= 0:
                    raise ValueError("linked intent limit price is invalid")
                if normalized_side == "BUY" and normalized_price > limit_price:
                    raise LiveOrderVersionConflict("buy fill price is worse than the linked limit price")
                if normalized_side == "SELL" and normalized_price < limit_price:
                    raise LiveOrderVersionConflict("sell fill price is worse than the linked limit price")

        stored_details = dict(safe_details or {})
        for key, value in (("normalized_product", normalized_product), ("normalized_order_type", normalized_order_type)):
            if key in stored_details and stored_details[key] != value:
                raise ValueError(f"safe_details {key} conflicts with normalized fill data")
            stored_details[key] = value

        def same_payload(existing: BrokerFillIdentity) -> bool:
            old_time = existing.executed_at
            new_time = executed_at
            if old_time.tzinfo is None:
                old_time = old_time.replace(tzinfo=timezone.utc)
            if new_time.tzinfo is None:
                new_time = new_time.replace(tzinfo=timezone.utc)
            return (
                existing.broker_order_id == order_id
                and (intent_id is None or existing.intent_id == intent_id)
                and existing.instrument_key == instrument
                and existing.side == normalized_side
                and existing.quantity == quantity
                and Decimal(str(existing.price)) == normalized_price
                and old_time.astimezone(timezone.utc) == new_time.astimezone(timezone.utc)
                and (existing.safe_details or {}) == stored_details
            )

        existing = self.db.query(BrokerFillIdentity).filter(
            BrokerFillIdentity.broker_connection_id == broker_connection_id,
            BrokerFillIdentity.broker_trade_id == trade_id,
        ).first()
        if existing is not None:
            if not same_payload(existing):
                raise LiveOrderVersionConflict("broker trade ID already exists with different fill details")
            return existing, False

        fill = BrokerFillIdentity(
            broker_connection_id=broker_connection_id,
            intent_id=intent_id,
            broker_order_id=order_id,
            broker_trade_id=trade_id,
            instrument_key=instrument,
            side=normalized_side,
            quantity=quantity,
            price=normalized_price,
            executed_at=executed_at,
            safe_details=stored_details,
        )
        if intent_id is not None:
            already_recorded = self.db.query(BrokerFillIdentity).filter(
                BrokerFillIdentity.intent_id == intent_id
            ).all()
            recorded_quantity = sum(item.quantity for item in already_recorded)
            snapshot_quantity = int(intent.order_snapshot["quantity"])
            if recorded_quantity + quantity > snapshot_quantity:
                raise LiveOrderVersionConflict("aggregate fill quantity would exceed linked intent quantity")
        self.db.add(fill)
        try:
            self.db.flush()
            if intent_id is not None:
                self.db.add(LiveOrderEvent(
                    intent_id=intent_id,
                    event_type="BROKER_FILL_RECORDED",
                    correlation_id=correlation_id,
                    actor_user_id=None,
                    safe_details={
                        "broker_trade_id": trade_id,
                        "broker_order_id": order_id,
                        "quantity": quantity,
                        "price": str(normalized_price),
                        "side": normalized_side,
                        "product": normalized_product,
                        "order_type": normalized_order_type,
                    },
                ))
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            winner = self.db.query(BrokerFillIdentity).filter(
                BrokerFillIdentity.broker_connection_id == broker_connection_id,
                BrokerFillIdentity.broker_trade_id == trade_id,
            ).first()
            if winner is not None and same_payload(winner):
                return winner, False
            raise LiveOrderVersionConflict("broker trade ID raced with a different fill payload") from exc
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(fill)
        return fill, True

    def link_existing_fill_to_intent(
        self,
        *,
        user_id: uuid.UUID,
        fill_id: uuid.UUID,
        intent_id: uuid.UUID,
        correlation_id: str | None = None,
    ) -> tuple[BrokerFillIdentity, bool]:
        """Safely link a previously unmatched fill after an intent is identified.

        Performs no broker I/O. All account/order/economic checks happen before a
        compare-and-set update, and the link plus audit event are committed atomically.
        """
        fill = self.db.query(BrokerFillIdentity).filter(
            BrokerFillIdentity.id == fill_id
        ).first()
        if fill is None:
            raise ValueError("broker fill not found")
        intent = self.db.query(LiveOrderIntent).filter(
            LiveOrderIntent.id == intent_id,
            LiveOrderIntent.user_id == user_id,
            LiveOrderIntent.broker_connection_id == fill.broker_connection_id,
        ).first()
        if intent is None:
            raise ValueError("intent not found for authenticated user and fill broker connection")
        if fill.intent_id is not None:
            if fill.intent_id == intent_id:
                return fill, False
            raise LiveOrderVersionConflict("broker fill is already linked to a different intent")
        if not intent.broker_order_id or intent.broker_order_id != fill.broker_order_id:
            raise LiveOrderVersionConflict("fill broker order ID does not match linked intent")
        snapshot = intent.order_snapshot or {}
        expected_instrument = snapshot.get("instrument_key", snapshot.get("instrument_token"))
        expected_side = snapshot.get("side", snapshot.get("transaction_type"))
        expected_type = snapshot.get("order_type")
        expected_product = snapshot.get("product")
        expected_quantity = snapshot.get("quantity")
        details = fill.safe_details or {}
        fill_product = details.get("normalized_product")
        fill_order_type = details.get("normalized_order_type")
        if not all(value is not None for value in (
            expected_instrument, expected_side, expected_type, expected_product,
            expected_quantity, fill_product, fill_order_type
        )):
            raise ValueError("fill or intent is missing required economic fields")
        if str(expected_instrument).strip() != fill.instrument_key:
            raise LiveOrderVersionConflict("fill instrument differs from intent")
        if str(expected_side).strip().upper() != fill.side:
            raise LiveOrderVersionConflict("fill side differs from intent")
        if str(expected_type).strip().upper() != str(fill_order_type).strip().upper():
            raise LiveOrderVersionConflict("fill order type differs from intent")
        if str(expected_product).strip().upper() != str(fill_product).strip().upper():
            raise LiveOrderVersionConflict("fill product differs from intent")
        try:
            requested_quantity = int(expected_quantity)
        except (TypeError, ValueError) as exc:
            raise ValueError("intent quantity is invalid") from exc
        if (
            isinstance(expected_quantity, bool)
            or requested_quantity <= 0
            or str(expected_quantity).strip() not in {str(requested_quantity), f"{requested_quantity}.0"}
        ):
            raise ValueError("intent quantity is invalid")
        if fill.quantity > requested_quantity:
            raise LiveOrderVersionConflict("fill quantity exceeds intent quantity")
        if str(fill_order_type).strip().upper() in {"LIMIT", "SL"}:
            from decimal import Decimal, InvalidOperation
            try:
                limit_price = Decimal(str(snapshot.get("limit_price", snapshot.get("price"))))
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise ValueError("intent limit price is invalid") from exc
            if not limit_price.is_finite() or limit_price <= 0:
                raise ValueError("intent limit price is invalid")
            fill_price = Decimal(str(fill.price))
            if fill.side == "BUY" and fill_price > limit_price:
                raise LiveOrderVersionConflict("buy fill price is worse than intent limit price")
            if fill.side == "SELL" and fill_price < limit_price:
                raise LiveOrderVersionConflict("sell fill price is worse than intent limit price")

        existing_fills = self.db.query(BrokerFillIdentity).filter(
            BrokerFillIdentity.intent_id == intent_id
        ).all()
        if sum(item.quantity for item in existing_fills) + fill.quantity > requested_quantity:
            raise LiveOrderVersionConflict("linking this fill would exceed aggregate intent quantity")
        try:
            result = self.db.execute(
                update(BrokerFillIdentity)
                .where(
                    BrokerFillIdentity.id == fill_id,
                    BrokerFillIdentity.broker_connection_id == intent.broker_connection_id,
                    BrokerFillIdentity.intent_id.is_(None),
                )
                .values(intent_id=intent_id)
            )
            if result.rowcount != 1:
                self.db.rollback()
                current = self.db.query(BrokerFillIdentity).filter(
                    BrokerFillIdentity.id == fill_id
                ).first()
                if current is not None and current.intent_id == intent_id:
                    return current, False
                raise LiveOrderVersionConflict("fill was linked concurrently; reload before retrying")
            self.db.add(LiveOrderEvent(
                intent_id=intent_id,
                event_type="BROKER_FILL_LINKED",
                correlation_id=correlation_id,
                actor_user_id=user_id,
                safe_details={
                    "broker_trade_id": fill.broker_trade_id,
                    "broker_order_id": fill.broker_order_id,
                    "quantity": fill.quantity,
                    "price": str(fill.price),
                    "side": fill.side,
                },
            ))
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise LiveOrderVersionConflict("fill link conflicted with a concurrent update") from exc
        except Exception:
            self.db.rollback()
            raise
        linked = self.db.query(BrokerFillIdentity).filter(
            BrokerFillIdentity.id == fill_id
        ).one()
        return linked, True

    def apply_reconciliation_transition(
        self,
        *,
        user_id: uuid.UUID,
        intent_id: uuid.UUID,
        expected_version: int,
        new_state: str,
        broker_order_id: str | None = None,
        safe_details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> tuple[LiveOrderIntent, bool]:
        return _apply_reconciliation_transition(
            self,
            user_id=user_id,
            intent_id=intent_id,
            expected_version=expected_version,
            new_state=new_state,
            broker_order_id=broker_order_id,
            safe_details=safe_details,
            correlation_id=correlation_id,
        )


class LiveOrderVersionConflict(RuntimeError):
    """The intent changed since the caller's expected version or a unique link conflicted."""


class InvalidLiveOrderTransition(ValueError):
    """A broker observation cannot safely move the intent between these states."""


_ALLOWED_RECONCILIATION_TRANSITIONS = {
    "CREATED": {"PENDING", "OPEN", "TRIGGER_PENDING", "PARTIALLY_FILLED", "PARTIALLY_FILLED_CANCELLED", "FILLED", "REJECTED", "CANCEL_PENDING", "CANCELLED", "UNKNOWN", "RECONCILIATION_REQUIRED"},
    "UNKNOWN": {"PENDING", "OPEN", "TRIGGER_PENDING", "PARTIALLY_FILLED", "PARTIALLY_FILLED_CANCELLED", "FILLED", "REJECTED", "CANCEL_PENDING", "CANCELLED", "RECONCILIATION_REQUIRED"},
    "PENDING": {"OPEN", "TRIGGER_PENDING", "PARTIALLY_FILLED", "PARTIALLY_FILLED_CANCELLED", "FILLED", "REJECTED", "CANCEL_PENDING", "CANCELLED", "UNKNOWN", "RECONCILIATION_REQUIRED"},
    "TRIGGER_PENDING": {"PENDING", "OPEN", "PARTIALLY_FILLED", "PARTIALLY_FILLED_CANCELLED", "FILLED", "REJECTED", "CANCEL_PENDING", "CANCELLED", "UNKNOWN", "RECONCILIATION_REQUIRED"},
    "OPEN": {"PARTIALLY_FILLED", "PARTIALLY_FILLED_CANCELLED", "FILLED", "REJECTED", "CANCEL_PENDING", "CANCELLED", "UNKNOWN", "RECONCILIATION_REQUIRED"},
    "PARTIALLY_FILLED": {"FILLED", "PARTIALLY_FILLED_CANCELLED", "CANCEL_PENDING", "CANCELLED", "UNKNOWN", "RECONCILIATION_REQUIRED"},
    "CANCEL_PENDING": {"OPEN", "PARTIALLY_FILLED", "PARTIALLY_FILLED_CANCELLED", "FILLED", "CANCELLED", "UNKNOWN", "RECONCILIATION_REQUIRED"},
    # A cancel can race with execution; broker trades may prove a cancelled order
    # partially or fully filled. Rejected/filled contradictions require quarantine.
    "CANCELLED": {"PARTIALLY_FILLED", "PARTIALLY_FILLED_CANCELLED", "FILLED", "RECONCILIATION_REQUIRED"},
    "PARTIALLY_FILLED_CANCELLED": {"FILLED", "RECONCILIATION_REQUIRED"},
    "FILLED": set(),
    "REJECTED": {"RECONCILIATION_REQUIRED"},
    "RECONCILIATION_REQUIRED": set(),
}


def _validate_transition_details(details: dict[str, Any] | None) -> None:
    if details is not None:
        if not isinstance(details, dict):
            raise ValueError("safe_details must be a JSON object")
        _validate_safe_json(details, field_name="safe_details")


def _apply_reconciliation_transition(
    self: LiveOrderRepository,
    *,
    user_id: uuid.UUID,
    intent_id: uuid.UUID,
    expected_version: int,
    new_state: str,
    broker_order_id: str | None = None,
    safe_details: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> tuple[LiveOrderIntent, bool]:
    """Atomically persist a validated broker observation and audit event.

    This repository-only operation does not fetch broker data or submit/cancel orders.
    Callers must only invoke it after matching the observation to this intent.
    Returns (intent, changed); repeated same-state observations at the current version
    are no-ops and do not create duplicate audit events.
    """
    state = new_state.strip().upper()
    if state not in _ALLOWED_RECONCILIATION_TRANSITIONS:
        raise InvalidLiveOrderTransition(f"unsupported reconciliation state: {state}")
    if expected_version < 1:
        raise ValueError("expected_version must be positive")
    if broker_order_id is not None:
        broker_order_id = broker_order_id.strip()
        if not broker_order_id or len(broker_order_id) > 128:
            raise ValueError("broker_order_id must contain 1-128 characters")
    _validate_transition_details(safe_details)

    intent = self.db.query(LiveOrderIntent).filter(
        LiveOrderIntent.id == intent_id,
        LiveOrderIntent.user_id == user_id,
    ).first()
    if intent is None:
        raise ValueError("live-order intent not found for authenticated user")
    if intent.version != expected_version:
        raise LiveOrderVersionConflict("live-order intent version changed; reload before applying observation")
    if intent.broker_order_id and broker_order_id and intent.broker_order_id != broker_order_id:
        raise LiveOrderVersionConflict("intent is already linked to a different broker order ID")

    observed_state = state
    fill_rows = self.db.query(BrokerFillIdentity.quantity).filter(
        BrokerFillIdentity.intent_id == intent_id
    ).all()
    persisted_fill_quantity = sum(int(row[0]) for row in fill_rows)
    try:
        requested_quantity = int((intent.order_snapshot or {}).get("quantity", 0))
    except (TypeError, ValueError):
        requested_quantity = 0
    from app.services.live_order_reconciliation import resolve_order_state_with_fill_evidence
    fill_resolution = resolve_order_state_with_fill_evidence(
        observed_state,
        requested_quantity=requested_quantity,
        persisted_fill_quantity=persisted_fill_quantity,
    )
    state = fill_resolution.state

    if intent.state == state and (broker_order_id is None or intent.broker_order_id == broker_order_id):
        return intent, False
    previous_state = intent.state
    if state != previous_state and state not in _ALLOWED_RECONCILIATION_TRANSITIONS.get(previous_state, set()):
        raise InvalidLiveOrderTransition(f"transition {previous_state} -> {state} is not allowed")

    values: dict[str, Any] = {
        "state": state,
        "version": LiveOrderIntent.version + 1,
        "last_reconciled_at": datetime.now(timezone.utc),
    }
    if broker_order_id is not None:
        values["broker_order_id"] = broker_order_id
    try:
        result = self.db.execute(
            update(LiveOrderIntent)
            .where(
                LiveOrderIntent.id == intent_id,
                LiveOrderIntent.user_id == user_id,
                LiveOrderIntent.version == expected_version,
                LiveOrderIntent.state == previous_state,
            )
            .values(**values)
        )
        if result.rowcount != 1:
            self.db.rollback()
            raise LiveOrderVersionConflict("live-order intent changed concurrently; reload before applying observation")

        details: dict[str, Any] = {
            "previous_state": previous_state,
            "new_state": state,
            "previous_version": expected_version,
            "new_version": expected_version + 1,
        }
        if broker_order_id is not None:
            details["broker_order_id"] = broker_order_id
        details["observed_broker_state"] = observed_state
        details["fill_evidence_resolution"] = fill_resolution.reason
        details["persisted_fill_quantity"] = persisted_fill_quantity
        if safe_details:
            details["broker_observation"] = safe_details
        _validate_safe_json(details, field_name="safe_details")
        self.db.add(
            LiveOrderEvent(
                intent_id=intent_id,
                event_type="BROKER_STATUS_RECONCILED",
                correlation_id=correlation_id,
                actor_user_id=None,
                safe_details=details,
            )
        )
        self.db.commit()
    except IntegrityError as exc:
        self.db.rollback()
        raise LiveOrderVersionConflict("broker order ID is already linked or reconciliation update conflicted") from exc
    except Exception:
        self.db.rollback()
        raise

    updated = self.db.query(LiveOrderIntent).filter(
        LiveOrderIntent.id == intent_id,
        LiveOrderIntent.user_id == user_id,
    ).one()
    return updated, True

