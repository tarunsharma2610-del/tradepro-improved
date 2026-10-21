"""Durable, credential-safe summaries for read-only reconciliation runs."""
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.broker_connection import BrokerConnection
from app.models.live_order_records import LiveReconciliationLease, LiveReconciliationRun


_SUMMARY_COUNTERS = {
    "orders_seen", "orders_matched", "orders_unmatched", "trades_seen",
    "fills_inserted", "duplicate_fills", "conflicts",
}
_RUN_STATES = {"RUNNING", "COMPLETED", "COMPLETED_WITH_CONFLICTS", "FAILED", "LEASE_LOST"}


class LiveReconciliationRunRepository:
    """Persists run lifecycle and count-only summaries; no broker I/O."""

    def __init__(self, db: Session):
        self.db = db

    def start(self, *, user_id: uuid.UUID, broker_connection_id: uuid.UUID) -> LiveReconciliationRun:
        connection = self.db.query(BrokerConnection).filter(
            BrokerConnection.id == broker_connection_id,
            BrokerConnection.user_id == user_id,
        ).first()
        if connection is None:
            raise ValueError("broker connection not found for authenticated user")
        run = LiveReconciliationRun(
            user_id=user_id,
            broker_connection_id=broker_connection_id,
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
            summary={key: 0 for key in sorted(_SUMMARY_COUNTERS)},
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def finish(
        self,
        *,
        run_id: uuid.UUID,
        user_id: uuid.UUID,
        broker_connection_id: uuid.UUID,
        status: str,
        summary: dict[str, Any],
        error_code: str | None = None,
        now: datetime | None = None,
    ) -> LiveReconciliationRun:
        normalized_status = status.strip().upper()
        if normalized_status not in _RUN_STATES - {"RUNNING"}:
            raise ValueError("invalid terminal reconciliation run status")
        if not isinstance(summary, dict) or set(summary) != _SUMMARY_COUNTERS:
            raise ValueError("summary must contain only the known reconciliation counters")
        for key, value in summary.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"summary counter {key} must be a non-negative integer")
        if error_code is not None:
            if not isinstance(error_code, str) or not error_code or len(error_code) > 100:
                raise ValueError("error_code must be a safe category")
            if not all(char.isupper() or char.isdigit() or char == "_" for char in error_code):
                raise ValueError("error_code must contain only uppercase letters, digits and underscores")
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        result = self.db.execute(
            update(LiveReconciliationRun)
            .where(
                LiveReconciliationRun.id == run_id,
                LiveReconciliationRun.user_id == user_id,
                LiveReconciliationRun.broker_connection_id == broker_connection_id,
                LiveReconciliationRun.status == "RUNNING",
            )
            .values(
                status=normalized_status,
                completed_at=now,
                error_code=error_code,
                summary=dict(summary),
            )
        )
        if result.rowcount != 1:
            self.db.rollback()
            raise RuntimeError("reconciliation run is missing, not owned, or already completed")
        self.db.commit()
        return self.db.query(LiveReconciliationRun).filter(
            LiveReconciliationRun.id == run_id,
            LiveReconciliationRun.user_id == user_id,
        ).one()

    def fail_orphaned_runs(
        self,
        *,
        user_id: uuid.UUID,
        broker_connection_id: uuid.UUID,
        stale_before: datetime,
        now: datetime | None = None,
    ) -> int:
        """Fail stale RUNNING summaries only when no unexpired lease owns the connection.

        Lock the lease row on databases that support row locks so a concurrent
        claimant cannot race the orphan check. This records recovery state only;
        it never retries broker calls or alters fill/accounting evidence.
        """
        now = now or datetime.now(timezone.utc)
        if stale_before.tzinfo is None or now.tzinfo is None:
            raise ValueError("stale_before and now must be timezone-aware")
        if stale_before > now:
            raise ValueError("stale_before cannot be later than now")

        lease = self.db.query(LiveReconciliationLease).filter(
            LiveReconciliationLease.user_id == user_id,
            LiveReconciliationLease.broker_connection_id == broker_connection_id,
        ).with_for_update().first()
        if lease is not None and lease.lease_token is not None and lease.claimed_until is not None and lease.claimed_until > now:
            self.db.rollback()
            return 0

        result = self.db.execute(
            update(LiveReconciliationRun)
            .where(
                LiveReconciliationRun.user_id == user_id,
                LiveReconciliationRun.broker_connection_id == broker_connection_id,
                LiveReconciliationRun.status == "RUNNING",
                LiveReconciliationRun.started_at < stale_before,
            )
            .values(
                status="FAILED",
                completed_at=now,
                error_code="WORKER_INTERRUPTED",
            )
        )
        count = int(result.rowcount or 0)
        self.db.commit()
        return count
