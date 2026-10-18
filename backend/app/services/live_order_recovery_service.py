"""Durable live-order intent identity and read-only recovery by broker tag.

This module intentionally has no place_order call. Once an intent is persisted,
a timeout or missing broker response is ambiguous: recovery may look up the
stable tag, but a no-match/error is never permission to submit again.
"""
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.brokers.base import BrokerAdapter
from app.brokers.registry import get_broker_adapter
from app.brokers.upstox.response_parsing import parse_order_history
from app.models.broker_order import BrokerOrder
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.repositories.broker_connection_repository import BrokerConnectionRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.live_execution_service import (
    LiveExecutionBlocked,
    LiveExecutionService,
    LiveOrderIntent,
    LiveOrderPreflight,
)


@dataclass(frozen=True)
class LiveOrderRecoveryResult:
    state: str
    order_id: UUID
    broker_order_ids: tuple[str, ...] = ()
    detail: str | None = None


def make_broker_tag(portfolio_id: UUID, idempotency_key: str) -> str:
    """Create a stable opaque Upstox-compatible tag (<= 40 chars)."""
    key = _validate_idempotency_key(idempotency_key)
    digest = hashlib.sha256(f"tradepro:v1:{portfolio_id}:{key}".encode("utf-8")).hexdigest()
    return f"tp{digest[:38]}"


class LiveOrderRecoveryService:
    """Persist an intent before a future submission and recover it read-only."""

    BROKER_NAME = "upstox"

    def __init__(
        self,
        db: Session,
        preflight_service: LiveExecutionService | None = None,
    ):
        self.db = db
        self.preflight = preflight_service or LiveExecutionService(db)
        self.connections = BrokerConnectionRepository(db)
        self.credentials = BrokerCredentialsService(db)

    def prepare_intent(
        self,
        user_id: UUID,
        intent: LiveOrderIntent,
        *,
        idempotency_key: str,
        user_confirmed: bool = False,
    ) -> Order:
        """Persist one stable intent; identical retries return the same row."""
        key = _validate_idempotency_key(idempotency_key)
        portfolio = (
            self.db.query(Portfolio)
            .filter(
                Portfolio.id == intent.portfolio_id,
                Portfolio.user_id == user_id,
            )
            .first()
        )
        if portfolio is None:
            raise LiveExecutionBlocked("Portfolio not found.")

        tag = make_broker_tag(portfolio.id, key)
        existing = (
            self.db.query(Order)
            .filter(Order.portfolio_id == portfolio.id, Order.idempotency_key == key)
            .first()
        )
        if existing is not None:
            self._ensure_same_intent(existing, intent, tag)
            return existing

        # For a new intent, all current live preflight gates must pass.
        plan = self.preflight.preflight(
            user_id, intent, user_confirmed=user_confirmed
        )
        if plan.portfolio_id != portfolio.id or plan.broker_name != self.BROKER_NAME:
            raise LiveExecutionBlocked("Preflight plan does not match the requested portfolio/broker.")

        order = Order(
            portfolio_id=portfolio.id,
            broker_connection_id=plan.broker_connection_id,
            instrument_id=plan.instrument_id,
            side=plan.side,
            order_type=plan.order_type,
            segment=plan.segment,
            quantity=plan.quantity,
            limit_price=plan.limit_price,
            status="PENDING_SUBMISSION",
            trading_mode="LIVE",
            execution_reason=intent.execution_reason,
            strategy_id=intent.strategy_id,
            idempotency_key=key,
            broker_tag=tag,
            placed_at=datetime.now(timezone.utc),
        )
        self.db.add(order)
        try:
            self.db.commit()
        except IntegrityError:
            # Handles concurrent retries racing on the DB uniqueness constraint.
            self.db.rollback()
            existing = (
                self.db.query(Order)
                .filter(Order.portfolio_id == portfolio.id, Order.idempotency_key == key)
                .first()
            )
            if existing is None:
                raise LiveExecutionBlocked(
                    "Intent identity collided with another persisted record; inspect before retrying."
                ) from None
            self._ensure_same_intent(existing, intent, tag)
            return existing
        self.db.refresh(order)
        return order

    def persist_preflighted_intent(
        self,
        user_id: UUID,
        intent: LiveOrderIntent,
        plan: LiveOrderPreflight,
        *,
        idempotency_key: str,
    ) -> Order:
        """Persist a plan produced by the safety-aware async coordinator.

        This method does no preflight and no network I/O itself. Callers must
        obtain the plan from LivePreflightCoordinator immediately beforehand.
        It rechecks owner, broker connection identity and all intent fields
        before committing the durable idempotent intent.
        """
        key = _validate_idempotency_key(idempotency_key)
        if not isinstance(plan, LiveOrderPreflight):
            raise LiveExecutionBlocked("A validated live preflight plan is required.")
        if (
            plan.user_id != user_id
            or plan.portfolio_id != intent.portfolio_id
            or plan.instrument_id != intent.instrument_id
            or plan.broker_name != self.BROKER_NAME
            or plan.side != intent.side
            or plan.order_type != intent.order_type
            or plan.segment != intent.segment
            or plan.quantity != intent.quantity
            or plan.limit_price != intent.limit_price
        ):
            raise LiveExecutionBlocked("Preflight plan does not match the requested user and intent.")

        portfolio = (
            self.db.query(Portfolio)
            .filter(Portfolio.id == intent.portfolio_id, Portfolio.user_id == user_id)
            .first()
        )
        if portfolio is None or not portfolio.is_active:
            raise LiveExecutionBlocked("An active portfolio owned by this user is required.")
        instrument = self.db.get(Instrument, plan.instrument_id)
        if (
            instrument is None
            or not instrument.is_active
            or instrument.instrument_key != plan.instrument_key
        ):
            raise LiveExecutionBlocked("Instrument changed after preflight; intent persistence blocked.")

        connection = self.connections.get_for_user(user_id, self.BROKER_NAME)
        if (
            connection is None
            or not connection.is_connected
            or connection.id != plan.broker_connection_id
        ):
            raise LiveExecutionBlocked("Broker connection changed after preflight; intent persistence blocked.")

        tag = make_broker_tag(portfolio.id, key)
        existing = (
            self.db.query(Order)
            .filter(Order.portfolio_id == portfolio.id, Order.idempotency_key == key)
            .first()
        )
        if existing is not None:
            self._ensure_same_intent(existing, intent, tag)
            return existing

        order = Order(
            portfolio_id=portfolio.id,
            broker_connection_id=plan.broker_connection_id,
            instrument_id=plan.instrument_id,
            side=plan.side,
            order_type=plan.order_type,
            segment=plan.segment,
            quantity=plan.quantity,
            limit_price=plan.limit_price,
            status="PENDING_SUBMISSION",
            trading_mode="LIVE",
            execution_reason=intent.execution_reason,
            strategy_id=intent.strategy_id,
            idempotency_key=key,
            broker_tag=tag,
            placed_at=datetime.now(timezone.utc),
        )
        self.db.add(order)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = (
                self.db.query(Order)
                .filter(Order.portfolio_id == portfolio.id, Order.idempotency_key == key)
                .first()
            )
            if existing is None:
                raise LiveExecutionBlocked(
                    "Intent identity collided with another persisted record; inspect before retrying."
                ) from None
            self._ensure_same_intent(existing, intent, tag)
            return existing
        self.db.refresh(order)
        return order

    def claim_submission_attempt(self, user_id: UUID, order_id: UUID) -> Order:
        """Atomically claim the one permitted initial submission attempt.

        This is only a durable local claim. It deliberately performs no broker
        I/O. A future submitter must commit this claim before network I/O and
        treat a crash after the claim as ambiguous, requiring read-only recovery.
        """
        order = self._get_owned_order(user_id, order_id)
        if order.trading_mode != "LIVE" or not order.broker_tag:
            raise LiveExecutionBlocked("Only a tagged LIVE intent can be claimed.")
        changed = (
            self.db.query(Order)
            .filter(
                Order.id == order.id,
                Order.trading_mode == "LIVE",
                Order.broker_tag.isnot(None),
                Order.status == "PENDING_SUBMISSION",
            )
            .update(
                {Order.status: "SUBMISSION_CLAIMED"},
                synchronize_session=False,
            )
        )
        self.db.commit()
        self.db.expire_all()
        current = self._get_owned_order(user_id, order_id)
        if changed != 1 or current.status != "SUBMISSION_CLAIMED":
            raise LiveExecutionBlocked(
                "Submission claim was already taken or order state changed; reconcile before any broker write."
            )
        return current

    def mark_submission_unknown(self, user_id: UUID, order_id: UUID) -> Order:
        """Durably mark the point immediately before a future broker POST.

        This method performs no network I/O. A future submitter must commit
        this state before issuing the request, so a crash/timeout triggers
        read-only recovery instead of a blind second POST.
        """
        order = self._get_owned_order(user_id, order_id)
        if order.trading_mode != "LIVE" or not order.broker_tag:
            raise LiveExecutionBlocked("Only a tagged LIVE intent can enter submission recovery.")
        if order.status not in {"PENDING_SUBMISSION", "SUBMISSION_CLAIMED", "SUBMISSION_UNKNOWN"}:
            raise LiveExecutionBlocked("Order is not in a submission-recovery eligible state.")

        # Compare-and-set the state in SQL. A stale ORM object must never
        # overwrite a terminal/reconciled state written by another worker.
        changed = (
            self.db.query(Order)
            .filter(
                Order.id == order.id,
                Order.trading_mode == "LIVE",
                Order.broker_tag.isnot(None),
                Order.status.in_({"PENDING_SUBMISSION", "SUBMISSION_CLAIMED", "SUBMISSION_UNKNOWN"}),
            )
            .update(
                {Order.status: "SUBMISSION_UNKNOWN"},
                synchronize_session=False,
            )
        )
        self.db.commit()
        self.db.expire_all()
        current = self._get_owned_order(user_id, order_id)
        if changed == 0 and current.status != "SUBMISSION_UNKNOWN":
            raise LiveExecutionBlocked(
                "Order state changed concurrently; recovery requires reconciliation."
            )
        if current.trading_mode != "LIVE" or not current.broker_tag:
            raise LiveExecutionBlocked("Order no longer qualifies for submission recovery.")
        if current.status != "SUBMISSION_UNKNOWN":
            raise LiveExecutionBlocked("Submission recovery state was not durably recorded.")
        return current

    async def recover_by_tag(
        self,
        user_id: UUID,
        order_id: UUID,
        *,
        adapter: BrokerAdapter | Any | None = None,
    ) -> LiveOrderRecoveryResult:
        """Read order history by stable tag; never resubmit or infer a fill."""
        order = self._get_owned_order(user_id, order_id)
        if order.trading_mode != "LIVE" or not order.broker_tag:
            raise LiveExecutionBlocked("Only tagged LIVE orders can be recovered.")
        if order.status not in {"PENDING_SUBMISSION", "SUBMISSION_CLAIMED", "SUBMISSION_UNKNOWN"}:
            raise LiveExecutionBlocked("Order is not in a submission-recovery eligible state.")

        # The exact account used at intent creation is part of order identity.
        # Never recover a legacy/unbound intent against whichever account happens
        # to be connected now: that could bind an unrelated broker order.
        if order.broker_connection_id is None:
            return LiveOrderRecoveryResult(
                state="UNKNOWN_REQUIRES_REVIEW",
                order_id=order.id,
                detail="Original broker connection is not recorded; reconcile the account manually and do not resubmit.",
            )
        connection = self.connections.get_for_user(user_id, self.BROKER_NAME)
        if (
            connection is None
            or not connection.is_connected
            or connection.id != order.broker_connection_id
        ):
            return LiveOrderRecoveryResult(
                state="UNKNOWN_REQUIRES_REVIEW",
                order_id=order.id,
                detail="Original broker connection is unavailable or changed; do not bind IDs or resubmit.",
            )

        existing_children = (
            self.db.query(BrokerOrder)
            .filter(BrokerOrder.order_id == order.id)
            .order_by(BrokerOrder.broker_order_id.asc())
            .all()
        )
        if existing_children:
            if any(
                row.broker_connection_id != order.broker_connection_id
                or row.broker_tag != order.broker_tag
                or row.broker_name != self.BROKER_NAME
                for row in existing_children
            ):
                return LiveOrderRecoveryResult(
                    state="MISMATCH_REQUIRES_REVIEW",
                    order_id=order.id,
                    detail="Existing broker-order mapping does not match the intent's bound connection/tag.",
                )
            return LiveOrderRecoveryResult(
                state="RECOVERED",
                order_id=order.id,
                broker_order_ids=tuple(row.broker_order_id for row in existing_children),
                detail="Existing durable broker-order mapping reused for the original connection; no broker call made.",
            )

        portfolio = self.db.get(Portfolio, order.portfolio_id)
        instrument = self.db.get(Instrument, order.instrument_id)
        if portfolio is None or instrument is None or portfolio.user_id != user_id:
            raise LiveExecutionBlocked("Order ownership or instrument could not be verified.")
        try:
            token = self.credentials.get_access_token(user_id, self.BROKER_NAME)
        except Exception:
            token = None
        if not isinstance(token, str) or not token.strip():
            return LiveOrderRecoveryResult(
                state="UNKNOWN_REQUIRES_REVIEW",
                order_id=order.id,
                detail="Upstox token unavailable; do not resubmit this intent.",
            )

        broker = adapter or get_broker_adapter(self.BROKER_NAME)
        try:
            response = await broker.get_order_history(token, tag=order.broker_tag)
        except Exception:
            return LiveOrderRecoveryResult(
                state="UNKNOWN_REQUIRES_REVIEW",
                order_id=order.id,
                detail="Order-history lookup failed; acceptance remains unknown, do not resubmit.",
            )
        if not response.ok:
            return LiveOrderRecoveryResult(
                state="UNKNOWN_REQUIRES_REVIEW",
                order_id=order.id,
                detail="Order-history lookup returned an error; do not resubmit.",
            )

        try:
            history = parse_order_history(response.data)
        except (TypeError, ValueError):
            return LiveOrderRecoveryResult(
                state="INVALID_BROKER_RESPONSE",
                order_id=order.id,
                detail="Order-history response failed validation; no broker mapping was written.",
            )
        if not history:
            return LiveOrderRecoveryResult(
                state="NO_MATCH_REQUIRES_REVIEW",
                order_id=order.id,
                detail="No order found by tag. Absence is not proof of rejection; do not resubmit automatically.",
            )

        grouped: dict[str, list[Any]] = {}
        for row in history:
            if row.tag != order.broker_tag:
                return LiveOrderRecoveryResult(
                    state="MISMATCH_REQUIRES_REVIEW",
                    order_id=order.id,
                    detail="Broker history contained a missing or mismatched tag; no mapping was written.",
                )
            if row.instrument_token != instrument.instrument_key or row.transaction_type != order.side:
                return LiveOrderRecoveryResult(
                    state="MISMATCH_REQUIRES_REVIEW",
                    order_id=order.id,
                    detail="Broker history instrument/side does not match the persisted intent.",
                )
            grouped.setdefault(row.order_id, []).append(row)

        child_specs: list[tuple[str, int]] = []
        for child_id, rows in grouped.items():
            quantities = {row.quantity for row in rows}
            if len(quantities) != 1:
                return LiveOrderRecoveryResult(
                    state="MISMATCH_REQUIRES_REVIEW",
                    order_id=order.id,
                    detail="Broker history changed requested quantity for a child order.",
                )
            child_specs.append((child_id, next(iter(quantities))))

        if sum(quantity for _child_id, quantity in child_specs) != order.quantity:
            return LiveOrderRecoveryResult(
                state="MISMATCH_REQUIRES_REVIEW",
                order_id=order.id,
                detail="Recovered child quantities do not equal the persisted intent quantity.",
            )

        # Persist identities only. Do not infer order status, fills, positions,
        # cash, or P&L from order history.
        now = datetime.now(timezone.utc)
        for child_id, quantity in child_specs:
            self.db.add(
                BrokerOrder(
                    broker_connection_id=connection.id,
                    order_id=order.id,
                    broker_name=self.BROKER_NAME,
                    broker_order_id=child_id,
                    broker_tag=order.broker_tag,
                    status="UNKNOWN",
                    requested_quantity=quantity,
                    filled_quantity=0,
                    status_checked_at=now,
                )
            )
        if len(child_specs) == 1:
            order.broker_order_id = child_specs[0][0]
            self.db.add(order)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            persisted = (
                self.db.query(BrokerOrder)
                .filter(
                    BrokerOrder.order_id == order.id,
                    BrokerOrder.broker_connection_id == connection.id,
                )
                .order_by(BrokerOrder.broker_order_id.asc())
                .all()
            )
            persisted_ids = tuple(row.broker_order_id for row in persisted)
            expected_ids = tuple(sorted(child_id for child_id, _quantity in child_specs))
            if persisted_ids == expected_ids:
                return LiveOrderRecoveryResult(
                    state="RECOVERED",
                    order_id=order.id,
                    broker_order_ids=persisted_ids,
                    detail="Concurrent recovery already persisted the same broker-order mapping.",
                )
            return LiveOrderRecoveryResult(
                state="UNKNOWN_REQUIRES_REVIEW",
                order_id=order.id,
                detail="Concurrent mapping conflict; manual reconciliation required.",
            )

        return LiveOrderRecoveryResult(
            state="RECOVERED",
            order_id=order.id,
            broker_order_ids=tuple(sorted(child_id for child_id, _quantity in child_specs)),
            detail="Broker IDs recovered by stable tag. Status and fills remain unconfirmed.",
        )

    def _get_owned_order(self, user_id: UUID, order_id: UUID) -> Order:
        order = (
            self.db.query(Order)
            .join(Portfolio, Portfolio.id == Order.portfolio_id)
            .filter(Order.id == order_id, Portfolio.user_id == user_id)
            .first()
        )
        if order is None:
            raise LiveExecutionBlocked("Order not found.")
        return order

    @staticmethod
    def _ensure_same_intent(order: Order, intent: LiveOrderIntent, tag: str) -> None:
        matches = (
            order.trading_mode == "LIVE"
            and order.broker_tag == tag
            and order.instrument_id == intent.instrument_id
            and order.side == intent.side
            and order.order_type == intent.order_type
            and order.segment == intent.segment
            and order.quantity == intent.quantity
            and (
                Decimal(str(order.limit_price)) if order.limit_price is not None else None
            ) == (
                Decimal(str(intent.limit_price)) if intent.limit_price is not None else None
            )
            and order.execution_reason == intent.execution_reason
            and order.strategy_id == intent.strategy_id
        )
        if not matches:
            raise LiveExecutionBlocked(
                "Idempotency key was already used for a different intent; use a new key only for a genuinely new order."
            )


def _validate_idempotency_key(value: str) -> str:
    if not isinstance(value, str):
        raise LiveExecutionBlocked("idempotency_key must be a non-empty string.")
    key = value.strip()
    if not key or len(key) > 100:
        raise LiveExecutionBlocked("idempotency_key must contain 1 to 100 non-whitespace characters.")
    return key
