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
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token")

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    from uuid import UUID

    service = AuthService(db)
    new_access_token = service.refresh_access_token(UUID(payload["sub"]))
    response.set_cookie(
        "access_token", new_access_token, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, **COOKIE_KWARGS
    )


@router.post("/mfa/enroll", response_model=MfaEnrollResponse)
def mfa_enroll(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = AuthService(db)
    secret, uri = service.start_mfa_enrollment(user)
    return MfaEnrollResponse(otpauth_uri=uri, secret=secret)


@router.post("/mfa/verify", status_code=status.HTTP_204_NO_CONTENT)
def mfa_verify(
    payload: MfaVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = AuthService(db)
    if not service.verify_and_enable_mfa(user, payload.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect code")
    write_audit_log(db, action="user.mfa_enabled", user_id=user.id, request=request)


@router.post("/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
def mfa_disable(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = AuthService(db)
    service.disable_mfa(user)
    write_audit_log(db, action="user.mfa_disabled", user_id=user.id, request=request)
