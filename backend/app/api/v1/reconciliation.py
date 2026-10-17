"""Read-only, authenticated visibility for reconciliation run summaries and issues."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.repositories.live_reconciliation_query_repository import LiveReconciliationQueryRepository
from app.schemas.reconciliation import ReconciliationIssueOut, ReconciliationRunOut

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


@router.get("/runs", response_model=list[ReconciliationRunOut])
def list_reconciliation_runs(
    broker_connection_id: UUID | None = None,
    status: Literal["RUNNING", "COMPLETED", "COMPLETED_WITH_CONFLICTS", "FAILED", "LEASE_LOST"] | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List only the authenticated user's safe run summaries."""
    return LiveReconciliationQueryRepository(db).list_runs(
        user_id=user.id,
        broker_connection_id=broker_connection_id,
        status=status,
        limit=limit,
    )


@router.get("/issues", response_model=list[ReconciliationIssueOut])
def list_reconciliation_issues(
    broker_connection_id: UUID | None = None,
    status: Literal["OPEN", "RESOLVED"] | None = None,
    issue_type: str | None = Query(default=None, min_length=1, max_length=50),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List only the authenticated user's sanitized manual-review issues."""
    return LiveReconciliationQueryRepository(db).list_issues(
        user_id=user.id,
        broker_connection_id=broker_connection_id,
        status=status,
        issue_type=issue_type.upper() if issue_type else None,
        limit=limit,
    )
