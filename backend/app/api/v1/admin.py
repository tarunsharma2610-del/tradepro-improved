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
    """Return immutable safety-state events for the authenticated user's own account.

    The tenant owner predicate is applied in SQL before count/pagination. This
    endpoint never accepts a caller-selected user or state ID and deliberately
    does not expose idempotency keys, request fingerprints, or another tenant's
    state/event history.
    """
    from app.models.live_account_safety import LiveAccountSafetyEvent, LiveAccountSafetyState

    scoped = (
        db.query(LiveAccountSafetyEvent, LiveAccountSafetyState)
        .join(
            LiveAccountSafetyState,
            LiveAccountSafetyEvent.state_id == LiveAccountSafetyState.id,
        )
        .filter(LiveAccountSafetyState.user_id == user.id)
    )
    total = scoped.count()
    rows = (
        scoped.order_by(
            LiveAccountSafetyEvent.created_at.desc(),
            LiveAccountSafetyEvent.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return SafetyAuditPage(
        items=[
            SafetyAuditEntry(
                id=event.id,
                created_at=event.created_at,
                action=event.event_type,
                resource_type="live_account_safety_state",
                resource_id=str(state.id),
                event_metadata={
                    "broker": state.broker,
                    "reason": event.reason,
                    "error_code": event.error_code,
                    "circuit_state": event.circuit_state,
                    "kill_switch_tripped": event.kill_switch_tripped,
                    "consecutive_broker_errors": event.consecutive_broker_errors,
                    "state_version": event.state_version,
                    "actor_user_id": str(event.actor_user_id) if event.actor_user_id else None,
                },
            )
            for event, state in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
        next_offset=(offset + len(rows)) if offset + len(rows) < total else None,
    )
