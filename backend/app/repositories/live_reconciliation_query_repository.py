"""Owner-scoped read queries for reconciliation run summaries and issues."""
import uuid

from sqlalchemy.orm import Session

from app.models.live_order_records import LiveReconciliationIssue, LiveReconciliationRun


class LiveReconciliationQueryRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _validate_limit(limit: int) -> None:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer between 1 and 100")

    def list_runs(
        self,
        *,
        user_id: uuid.UUID,
        broker_connection_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[LiveReconciliationRun]:
        self._validate_limit(limit)
        query = self.db.query(LiveReconciliationRun).filter(LiveReconciliationRun.user_id == user_id)
        if broker_connection_id is not None:
            query = query.filter(LiveReconciliationRun.broker_connection_id == broker_connection_id)
        if status is not None:
            query = query.filter(LiveReconciliationRun.status == status)
        return query.order_by(LiveReconciliationRun.started_at.desc(), LiveReconciliationRun.id.desc()).limit(limit).all()

    def list_issues(
        self,
        *,
        user_id: uuid.UUID,
        broker_connection_id: uuid.UUID | None = None,
        status: str | None = None,
        issue_type: str | None = None,
        limit: int = 50,
    ) -> list[LiveReconciliationIssue]:
        self._validate_limit(limit)
        query = self.db.query(LiveReconciliationIssue).filter(LiveReconciliationIssue.user_id == user_id)
        if broker_connection_id is not None:
            query = query.filter(LiveReconciliationIssue.broker_connection_id == broker_connection_id)
        if status is not None:
            query = query.filter(LiveReconciliationIssue.status == status)
        if issue_type is not None:
            query = query.filter(LiveReconciliationIssue.issue_type == issue_type)
        return query.order_by(LiveReconciliationIssue.last_seen_at.desc(), LiveReconciliationIssue.id.desc()).limit(limit).all()
