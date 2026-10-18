from collections.abc import Callable
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User


SAFETY_PERMISSIONS = frozenset({
    "safety.status.read",
    "safety.audit.read",
    "safety.kill_switch.trip",
    "safety.reset",
})


def _extract_token(access_token: str | None, authorization: str | None) -> str | None:
    """Cookie first (the browser frontend's normal path), Bearer header as a
    fallback (useful for scripts, tests, and any future non-browser client)."""
    if access_token:
        return access_token
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1]
    return None


def get_current_user(
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(default=None),
    authorization: str | None = Header(default=None),
) -> User:
    token = _extract_token(access_token, authorization)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    try:
        subject = UUID(payload.get("sub", ""))
    except (TypeError, ValueError, AttributeError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from None

    user = db.get(User, subject)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    return user


def require_safety_permission(permission: str) -> Callable:
    """Return a default-deny dependency for one explicit safety permission.

    Platform-admin status intentionally grants no safety permission. Grants are
    assigned explicitly in User.safety_permissions and are not client supplied.
    """
    if permission not in SAFETY_PERMISSIONS:
        raise ValueError(f"Unknown safety permission: {permission}")

    def _require_permission(user: User = Depends(get_current_user)) -> User:
        grants = user.safety_permissions or []
        if permission not in grants:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Safety permission required")
        return user

    return _require_permission


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Guards every /settings/platform/* route. Regular users never reach
    these — not via hidden UI, via a hard 403 on the API itself."""
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user
