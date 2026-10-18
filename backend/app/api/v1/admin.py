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

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import (\n    SAFETY_PERMISSIONS,\n    get_db,\n    require_admin,\n    require_recent_safety_mfa,\n    require_same_origin_for_cookie_mutation,\n)
from app.models.audit_log import AuditLog
from app.models.backtest import BacktestRun
from app.models.news_item import NewsItem
from app.models.portfolio import Portfolio
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.admin import PlatformStatsOut, SafetyPermissionChange, SafetyPermissionChangeOut

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
