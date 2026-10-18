"""Authenticated live-account safety controls.

These endpoints operate only on the persistent safety latch. They do not submit
broker orders and do not enable live trading.
"""
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import (
    get_current_user,
    get_db,
    require_recent_safety_mfa,
    require_same_origin_for_cookie_mutation,
    require_safety_permission,
)
from app.models.live_account_safety import LiveAccountSafetyState
from app.models.user import User
from app.schemas.live_safety import (
    SafetyControlRequest,
    SafetyResetRequest,
    SafetyStatusOut,
)
from app.services.live_account_safety_service import (
    DEFAULT_BROKER,
    LiveAccountSafetyService,
)
from app.services.live_execution_service import LiveExecutionBlocked

router = APIRouter(prefix="/safety", tags=["safety"])


def _status(db: Session, user: User, broker: str = DEFAULT_BROKER) -> SafetyStatusOut:
    decision = LiveAccountSafetyService(db).check_allowed(user.id, broker)
    try:
        state = (
            db.query(LiveAccountSafetyState)
            .filter(
                LiveAccountSafetyState.user_id == user.id,
                LiveAccountSafetyState.broker == broker,
            )
            .one_or_none()
        )
    except Exception:
        db.rollback()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Safety state unavailable; trading remains blocked") from None

    if state is None:
        return SafetyStatusOut(
            state_exists=False,
            broker=broker,
            allowed=False,
            decision_reason=decision.reason,
            kill_switch_tripped=True,
            circuit_state="UNKNOWN",
            consecutive_broker_errors=0,
            version=None,
        )
    return SafetyStatusOut(
        state_exists=True,
        broker=state.broker,
        allowed=decision.allowed,
        decision_reason=decision.reason,
        kill_switch_tripped=state.kill_switch_tripped,
        kill_switch_reason=state.kill_switch_reason,
        kill_switch_tripped_at=state.kill_switch_tripped_at,
        circuit_state=state.circuit_state,
        circuit_reason=state.circuit_reason,
        consecutive_broker_errors=state.consecutive_broker_errors,
        last_broker_error_at=state.last_broker_error_at,
        last_broker_error_code=state.last_broker_error_code,
        last_health_check_at=state.last_health_check_at,
        version=state.version,
    )


@router.get("/status", response_model=SafetyStatusOut)
def read_safety_status(
    db: Session = Depends(get_db),
    user: User = Depends(require_safety_permission("safety.status.read")),
):
    """Read only the authenticated user's own Upstox safety latch."""
    return _status(db, user)


@router.post("/kill-switch/trip", response_model=SafetyStatusOut)
def trip_kill_switch(
    payload: SafetyControlRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=8, max_length=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_safety_permission("safety.kill_switch.trip")),
    _origin: None = Depends(require_same_origin_for_cookie_mutation),
):
    """Trip the account-wide latch. This operation can only make trading less permissive."""
    service = LiveAccountSafetyService(db)
    try:
        service.initialize(
            user.id,
            broker=DEFAULT_BROKER,
            actor_user_id=user.id,
            idempotency_key=f"api-initialize:{user.id}",
        )
        service.trip_kill_switch(
            user.id,
            payload.reason,
            broker=DEFAULT_BROKER,
            actor_user_id=user.id,
            idempotency_key=idempotency_key,
        )
    except LiveExecutionBlocked as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return _status(db, user)


@router.post("/kill-switch/reset", response_model=SafetyStatusOut)
def reset_kill_switch(
    payload: SafetyResetRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=8, max_length=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_safety_permission("safety.reset")),
    _recent_mfa: User = Depends(require_recent_safety_mfa),
    _origin: None = Depends(require_same_origin_for_cookie_mutation),
):
    """Reset only after fresh MFA and a recent explicit passing safety health check."""
    try:
        LiveAccountSafetyService(db).manual_reset(
            user.id,
            payload.reason,
            broker=DEFAULT_BROKER,
            actor_user_id=user.id,
            idempotency_key=idempotency_key,
            expected_version=payload.expected_version,
        )
    except LiveExecutionBlocked as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return _status(db, user)
