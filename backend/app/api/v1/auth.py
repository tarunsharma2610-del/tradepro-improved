from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.security import decode_token
from app.middleware.audit import write_audit_log
from app.middleware.rate_limit import login_rate_limit, register_rate_limit
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResult,
    MfaEnrollResponse,
    MfaVerifyRequest,
    MfaDisableRequest,
    RegisterRequest,
)
from app.schemas.user import UserOut
from app.services.auth_service import AuthError, AuthService, MfaRequiredError

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_KWARGS = dict(
    httponly=True,
    secure=settings.ENVIRONMENT != "development",
    samesite="lax",
    path="/",
)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest, request: Request, db: Session = Depends(get_db), _rl=Depends(register_rate_limit)
):
    service = AuthService(db)
    try:
        user = service.register(email=payload.email, password=payload.password, full_name=payload.full_name)
    except AuthError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    write_audit_log(db, action="user.register", user_id=user.id, request=request)
    return user


@router.post("/login", response_model=UserOut | LoginResult)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _rl=Depends(login_rate_limit),
):
    service = AuthService(db)
    try:
        user = service.authenticate(email=payload.email, password=payload.password, mfa_code=payload.mfa_code)
    except MfaRequiredError:
        return LoginResult(mfa_required=True)
    except AuthError as exc:
        write_audit_log(db, action="user.login_failed", request=request, metadata={"email": payload.email})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc))

    access_token, refresh_token = service.issue_tokens(user)
    response.set_cookie(
        "access_token", access_token, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, **COOKIE_KWARGS
    )
    response.set_cookie(
        "refresh_token", refresh_token, max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, **COOKIE_KWARGS
    )
    write_audit_log(db, action="user.login", user_id=user.id, request=request)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    # Revoke the server-side session before clearing the browser credentials.
    service = AuthService(db)
    for cookie_name in ("access_token", "refresh_token"):
        token = request.cookies.get(cookie_name)
        payload = decode_token(token) if token else None
        if payload and payload.get("sid") and payload.get("sub"):
            try:
                service.revoke_session(UUID(payload["sid"]), UUID(payload["sub"]))
            except (ValueError, TypeError):
                pass
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    payload = decode_token(refresh_token) if refresh_token else None
    if (
        not payload
        or payload.get("type") != "refresh"
        or not payload.get("sid")
        or not payload.get("jti")
        or not payload.get("sub")
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    try:
        access_token, rotated_refresh_token = AuthService(db).rotate_refresh_session(
            user_id=UUID(payload["sub"]),
            session_id=UUID(payload["sid"]),
            presented_jti=str(payload["jti"]),
        )
    except (ValueError, TypeError, AuthError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or revoked refresh session")
    response.set_cookie(
        "access_token", access_token, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, **COOKIE_KWARGS
    )
    response.set_cookie(
        "refresh_token", rotated_refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, **COOKIE_KWARGS
    )


@router.post("/mfa/enroll", response_model=MfaEnrollResponse)
def mfa_enroll(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = AuthService(db)
    try:
        secret, uri = service.start_mfa_enrollment(user)
    except AuthError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return MfaEnrollResponse(otpauth_uri=uri, secret=secret)


@router.post("/mfa/verify", status_code=status.HTTP_204_NO_CONTENT)
def mfa_verify(
    payload: MfaVerifyRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = AuthService(db)
    if not service.verify_and_enable_mfa(user, payload.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect code")
    write_audit_log(db, action="user.mfa_enabled", user_id=user.id, request=request)
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


@router.post("/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
def mfa_disable(
    payload: MfaDisableRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = AuthService(db)
    try:
        service.disable_mfa(user, password=payload.password, mfa_code=payload.mfa_code)
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc))
    write_audit_log(db, action="user.mfa_disabled", user_id=user.id, request=request)
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
