"""
Deliberately aggregate-only. An admin gets counts (how many users, how
many active strategies) to gauge platform health, not a way to browse any
specific user's portfolio or trades -- that would cut against the same
multi-tenancy principle the rest of this app enforces ("never trust an id
without checking ownership") in spirit, even though an admin technically
has the database access to bypass it. Nothing here queries by another
user's identity.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import (
    SAFETY_PERMISSIONS,
    get_current_user,
    get_db,
    require_admin,
    require_recent_safety_mfa,
    require_same_origin_for_cookie_mutation,
    require_safety_permission,
)
from app.models.audit_log import AuditLog
from app.models.backtest import BacktestRun
from app.models.news_item import NewsItem
from app.models.portfolio import Portfolio
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.admin import (
    PlatformStatsOut,
    SafetyAuditEntry,
    SafetyAuditPage,
    SafetyPermissionChange,
    SafetyPermissionChangeOut,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=PlatformStatsOut)
def platform_stats(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return PlatformStatsOut(
        total_users=db.query(func.count(User.id)).scalar(),
        total_portfolios=db.query(func.count(Portfolio.id)).scalar(),
        total_active_strategies=db.query(func.count(Strategy.id)).filter(Strategy.is_active.is_(True)).scalar(),
        total_strategies=db.query(func.count(Strategy.id)).scalar(),
        total_news_items=db.query(func.count(NewsItem.id)).scalar(),
        total_backtest_runs=db.query(func.count(BacktestRun.id)).scalar(),
    )



@router.put("/users/{user_id}/safety-permissions", response_model=SafetyPermissionChangeOut)
def change_safety_permission(
    user_id: UUID,
    payload: SafetyPermissionChange,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    _recent_mfa: User = Depends(require_recent_safety_mfa),
    _origin: None = Depends(require_same_origin_for_cookie_mutation),
):
    """Explicitly grant/revoke one safety scope with fresh admin MFA.

    The actor and target are recorded in the same DB transaction as the grant.
    A platform-admin flag alone is insufficient: the actor must also pass the
    recent-MFA step-up dependency. Self-grants are forbidden.
    """
    if payload.permission not in SAFETY_PERMISSIONS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown safety permission")
    if payload.action == "grant" and admin.id == user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Self-granting safety permissions is forbidden")

    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    grants = set(target.safety_permissions or [])
    if payload.action == "grant":
        grants.add(payload.permission)
    else:
        grants.discard(payload.permission)
    target.safety_permissions = sorted(grants)

    db.add(AuditLog(
        user_id=admin.id,
        action=f"safety.permission.{payload.action}",
        resource_type="user",
        resource_id=str(target.id),
        ip_address=(request.client.host if request.client else None),
        event_metadata={
            "permission": payload.permission,
            "target_user_id": str(target.id),
            "actor_user_id": str(admin.id),
        },
    ))
    db.commit()
    db.refresh(target)
    return SafetyPermissionChangeOut(
        user_id=target.id,
        safety_permissions=target.safety_permissions or [],
    )



@router.get("/safety/audit", response_model=SafetyAuditPage)
def read_own_safety_audit(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=100000),
    db: Session = Depends(get_db),
    user: User = Depends(require_safety_permission("safety.audit.read")),
):
    """Return only safety audit events attributed to the authenticated user.

    No user ID is accepted from the caller. Filtering happens in SQL before
    pagination, so a permission grant cannot be used to enumerate another
    tenant's audit trail.
    """
    scoped = db.query(AuditLog).filter(
        AuditLog.user_id == user.id,
        AuditLog.action.like("safety.%"),
    )
    total = scoped.count()
    rows = (
        scoped.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return SafetyAuditPage(
        items=[
            SafetyAuditEntry(
                id=row.id,
                created_at=row.created_at,
                action=row.action,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                event_metadata=row.event_metadata or {},
            )
            for row in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
        next_offset=(offset + len(rows)) if offset + len(rows) < total else None,
    )
