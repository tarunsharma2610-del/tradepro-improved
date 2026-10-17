"""Durable, deduplicated manual-review issues for read-only reconciliation."""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.broker_connection import BrokerConnection
from app.models.live_order_records import (
    LiveOrderIntent,
    LiveReconciliationIssue,
    LiveReconciliationRun,
)
from app.repositories.live_order_repository import _validate_safe_json


_ALLOWED_ISSUE_TYPES = {
    "INVALID_TRADE_RECORD",
    "TRADE_PERSISTENCE_CONFLICT",
    "INVALID_ORDER_RECORD",
    "UNMATCHED_ORDER",
    "ORDER_MATCH_REQUIRES_REVIEW",
    "MATCHED_INTENT_NOT_FOUND",
    "ORDER_STATUS_TRANSITION_CONFLICT",
    "FILL_LINK_CONFLICT",
}


class LiveReconciliationIssueRepository:
    """Stores only whitelisted issue categories and small sanitized details."""

    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        *,
        user_id: uuid.UUID,
        broker_connection_id: uuid.UUID,
        issue_type: str,
        safe_details: dict[str, Any],
        run_id: uuid.UUID | None = None,
        intent_id: uuid.UUID | None = None,
        broker_order_id: str | None = None,
        broker_trade_id: str | None = None,
        now: datetime | None = None,
    ) -> tuple[LiveReconciliationIssue, bool]:
        kind = issue_type.strip().upper() if isinstance(issue_type, str) else ""
        if kind not in _ALLOWED_ISSUE_TYPES:
            raise ValueError("unsupported reconciliation issue type")
        if not isinstance(safe_details, dict):
            raise ValueError("safe_details must be an object")
        _validate_safe_json(safe_details, field_name="safe_details")
        encoded_details = json.dumps(safe_details, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if len(encoded_details) > 2048:
            raise ValueError("safe_details exceeds the 2048-character limit")

        def optional_id(value: str | None, field: str) -> str | None:
            if value is None:
                return None
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > 128:
                raise ValueError(f"{field} must contain 1-128 characters")
            return value.strip()

        order_id = optional_id(broker_order_id, "broker_order_id")
        trade_id = optional_id(broker_trade_id, "broker_trade_id")
        connection = self.db.query(BrokerConnection).filter(
            BrokerConnection.id == broker_connection_id,
            BrokerConnection.user_id == user_id,
        ).first()
        if connection is None:
            raise ValueError("broker connection not found for authenticated user")
        if run_id is not None:
            run = self.db.query(LiveReconciliationRun).filter(
                LiveReconciliationRun.id == run_id,
                LiveReconciliationRun.user_id == user_id,
                LiveReconciliationRun.broker_connection_id == broker_connection_id,
            ).first()
            if run is None:
                raise ValueError("reconciliation run does not belong to this user and connection")
        if intent_id is not None:
            intent = self.db.query(LiveOrderIntent).filter(
                LiveOrderIntent.id == intent_id,
                LiveOrderIntent.user_id == user_id,
                LiveOrderIntent.broker_connection_id == broker_connection_id,
            ).first()
            if intent is None:
                raise ValueError("intent does not belong to this user and connection")

        fingerprint_payload = {
            "issue_type": kind,
            "broker_order_id": order_id,
            "broker_trade_id": trade_id,
            "intent_id": str(intent_id) if intent_id else None,
            "safe_details": safe_details,
        }
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")

        existing = self.db.query(LiveReconciliationIssue).filter(
            LiveReconciliationIssue.broker_connection_id == broker_connection_id,
            LiveReconciliationIssue.fingerprint == fingerprint,
        ).first()
        if existing is not None:
            existing.run_id = run_id
            existing.status = "OPEN"
            existing.last_seen_at = now
            existing.occurrence_count += 1
            existing.resolved_at = None
            self.db.commit()
            self.db.refresh(existing)
            return existing, False

        issue = LiveReconciliationIssue(
            user_id=user_id,
            broker_connection_id=broker_connection_id,
            run_id=run_id,
            intent_id=intent_id,
            issue_type=kind,
            fingerprint=fingerprint,
            broker_order_id=order_id,
            broker_trade_id=trade_id,
            status="OPEN",
            safe_details=dict(safe_details),
            first_seen_at=now,
            last_seen_at=now,
            occurrence_count=1,
        )
        try:
            self.db.add(issue)
            self.db.commit()
            self.db.refresh(issue)
            return issue, True
        except IntegrityError:
            self.db.rollback()
            existing = self.db.query(LiveReconciliationIssue).filter(
                LiveReconciliationIssue.broker_connection_id == broker_connection_id,
                LiveReconciliationIssue.fingerprint == fingerprint,
            ).first()
            if existing is None:
                raise
            existing.run_id = run_id
            existing.status = "OPEN"
            existing.last_seen_at = now
            existing.occurrence_count += 1
            existing.resolved_at = None
            self.db.commit()
            self.db.refresh(existing)
            return existing, False
