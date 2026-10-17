from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User


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

    user = db.get(User, UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Guards every /settings/platform/* route. Regular users never reach
    these — not via hidden UI, via a hard 403 on the API itself."""
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user
