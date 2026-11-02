import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pyotp
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.encryption import decrypt_value, encrypt_value
from app.core.security import create_token, hash_password, verify_password
from app.models.auth_session import AuthSession
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, *, email: str, password: str, full_name: str) -> User:
        if self.users.get_by_email(email):
            raise AuthError("An account with this email already exists.")
        return self.users.create(email=email, password_hash=hash_password(password), full_name=full_name)

    def authenticate(self, *, email: str, password: str, mfa_code: str | None) -> User:
        """Use one generic message for missing user and wrong password."""
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("Incorrect email or password.")
        if user.mfa_enabled:
            if not mfa_code:
                raise MfaRequiredError()
            if not self._verify_totp(user, mfa_code):
                raise AuthError("Incorrect MFA code.")
        return user

    @staticmethod
    def _token_hash(jti: str) -> str:
        return hashlib.sha256(jti.encode("utf-8")).hexdigest()

    def issue_tokens(self, user: User) -> tuple[str, str]:
        """Create one persisted session and bind both JWTs to its session id."""
        now = datetime.now(timezone.utc)
        session_id = uuid4()
        jti = str(uuid4())
        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        self.db.add(
            AuthSession(
                id=session_id,
                user_id=user.id,
                refresh_token_hash=self._token_hash(jti),
                expires_at=expires_at,
            )
        )
        self.db.commit()
        access_token = create_token(user.id, "access", session_id=session_id)
        refresh_token = create_token(
            user.id, "refresh", session_id=session_id, token_id=jti
        )
        return access_token, refresh_token

    def rotate_refresh_session(
        self, *, user_id: UUID, session_id: UUID, presented_jti: str
    ) -> tuple[str, str]:
        """Atomically rotate a refresh credential; replay or stale sessions fail."""
        session = (
            self.db.query(AuthSession)
            .filter(AuthSession.id == session_id, AuthSession.user_id == user_id)
            .with_for_update()
            .one_or_none()
        )
        now = datetime.now(timezone.utc)
        if (
            session is None
            or session.revoked_at is not None
            or session.expires_at.replace(tzinfo=timezone.utc) <= now
            or not hmac.compare_digest(session.refresh_token_hash, self._token_hash(presented_jti))
        ):
            raise AuthError("Invalid or revoked refresh session.")

        next_jti = str(uuid4())
        session.refresh_token_hash = self._token_hash(next_jti)
        session.expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        session.last_used_at = now
        self.db.add(session)
        self.db.commit()

        access_token = create_token(user_id, "access", session_id=session_id)
        refresh_token = create_token(
            user_id, "refresh", session_id=session_id, token_id=next_jti
        )
        return access_token, refresh_token

    def revoke_session(self, session_id: UUID, user_id: UUID | None = None) -> None:
        query = self.db.query(AuthSession).filter(
            AuthSession.id == session_id, AuthSession.revoked_at.is_(None)
        )
        if user_id is not None:
            query = query.filter(AuthSession.user_id == user_id)
        session = query.one_or_none()
        if session is not None:
            session.revoked_at = datetime.now(timezone.utc)
            self.db.add(session)
            self.db.commit()

    def revoke_all_sessions(self, user_id: UUID) -> None:
        self.db.query(AuthSession).filter(
            AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None)
        ).update({AuthSession.revoked_at: datetime.now(timezone.utc)}, synchronize_session=False)
        self.db.commit()

    # --- MFA ---
    def start_mfa_enrollment(self, user: User) -> tuple[str, str]:
        secret = pyotp.random_base32()
        user.mfa_secret_encrypted = encrypt_value(secret)
        self.users.save(user)
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Trading Platform")
        return secret, uri

    def verify_and_enable_mfa(self, user: User, code: str) -> bool:
        if not self._verify_totp(user, code):
            return False
        user.mfa_enabled = True
        self.users.save(user)
        self.revoke_all_sessions(user.id)
        return True

    def disable_mfa(self, user: User, *, password: str, mfa_code: str | None) -> None:
        if not verify_password(password, user.password_hash):
            raise AuthError("Incorrect password.")
        if user.mfa_enabled and (not mfa_code or not self._verify_totp(user, mfa_code)):
            raise AuthError("Incorrect MFA code.")
        user.mfa_enabled = False
        user.mfa_secret_encrypted = None
        self.users.save(user)
        self.revoke_all_sessions(user.id)

    @staticmethod
    def _verify_totp(user: User, code: str) -> bool:
        if not user.mfa_secret_encrypted:
            return False
        secret = decrypt_value(user.mfa_secret_encrypted)
        if not secret:
            return False
        return pyotp.totp.TOTP(secret).verify(code, valid_window=1)


class MfaRequiredError(Exception):
    """Raised when MFA is required but a login request did not supply its code."""
