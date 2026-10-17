from uuid import UUID

import pyotp
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_value, encrypt_value
from app.core.security import create_token, hash_password, verify_password
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
        """Raises AuthError on any failure. Deliberately uses the same
        generic message for 'no such user' and 'wrong password' so login
        can't be used to enumerate registered emails."""
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("Incorrect email or password.")

        if user.mfa_enabled:
            if not mfa_code:
                raise MfaRequiredError()
            if not self._verify_totp(user, mfa_code):
                raise AuthError("Incorrect MFA code.")

        return user

    def issue_tokens(self, user: User) -> tuple[str, str]:
        access_token = create_token(user.id, "access")
        refresh_token = create_token(user.id, "refresh")
        return access_token, refresh_token

    def refresh_access_token(self, user_id: UUID) -> str:
        return create_token(user_id, "access")

    # --- MFA ---
    def start_mfa_enrollment(self, user: User) -> tuple[str, str]:
        """Returns (secret, otpauth_uri). Secret is stored encrypted
        immediately but mfa_enabled stays False until verify_and_enable
        confirms the user's authenticator app actually has it."""
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
        return True

    def disable_mfa(self, user: User) -> None:
        user.mfa_enabled = False
        user.mfa_secret_encrypted = None
        self.users.save(user)

    @staticmethod
    def _verify_totp(user: User, code: str) -> bool:
        if not user.mfa_secret_encrypted:
            return False
        secret = decrypt_value(user.mfa_secret_encrypted)
        if not secret:
            return False
        return pyotp.totp.TOTP(secret).verify(code, valid_window=1)


class MfaRequiredError(Exception):
    """Raised instead of AuthError specifically so the API layer can
    return {"mfa_required": true} without issuing tokens, rather than a
    generic 401."""
