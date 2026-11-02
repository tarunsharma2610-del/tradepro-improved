import pytest
from uuid import UUID

from app.services.auth_service import AuthError, AuthService, MfaRequiredError


def test_register_and_login(db_session):
    service = AuthService(db_session)
    service.register(email="new@example.com", password="correct-horse-battery-staple", full_name="New User")

    user = service.authenticate(email="new@example.com", password="correct-horse-battery-staple", mfa_code=None)
    assert user.email == "new@example.com"


def test_duplicate_registration_rejected(db_session):
    service = AuthService(db_session)
    service.register(email="dupe@example.com", password="correct-horse-battery-staple", full_name="A")
    with pytest.raises(AuthError):
        service.register(email="dupe@example.com", password="another-password-1234", full_name="B")


def test_wrong_password_and_unknown_email_give_the_same_error(db_session):
    service = AuthService(db_session)
    service.register(email="real@example.com", password="correct-horse-battery-staple", full_name="Real")

    with pytest.raises(AuthError) as wrong_pw:
        service.authenticate(email="real@example.com", password="totally-wrong-password", mfa_code=None)

    with pytest.raises(AuthError) as no_user:
        service.authenticate(email="ghost@example.com", password="anything-at-all-123", mfa_code=None)

    # Same message both times — login can't be used to enumerate registered emails.
    assert str(wrong_pw.value) == str(no_user.value)


def test_mfa_enroll_then_login_requires_code(db_session, make_user):
    user = make_user()
    service = AuthService(db_session)

    secret, uri = service.start_mfa_enrollment(user)
    assert user.email in uri or "otpauth://" in uri

    import pyotp

    valid_code = pyotp.TOTP(secret).now()
    assert service.verify_and_enable_mfa(user, valid_code) is True

    with pytest.raises(MfaRequiredError):
        service.authenticate(email=user.email, password="correct-horse-battery-staple", mfa_code=None)

    # Correct code succeeds
    fresh_code = pyotp.TOTP(secret).now()
    authenticated = service.authenticate(
        email=user.email, password="correct-horse-battery-staple", mfa_code=fresh_code
    )
    assert authenticated.id == user.id


def test_disabling_mfa_requires_password_and_current_totp(db_session, make_user):
    user = make_user()
    service = AuthService(db_session)
    secret, _ = service.start_mfa_enrollment(user)

    import pyotp

    assert service.verify_and_enable_mfa(user, pyotp.TOTP(secret).now()) is True
    current_code = pyotp.TOTP(secret).now()
    wrong_code = str((int(current_code) + 123456) % 1_000_000).zfill(6)
    with pytest.raises(AuthError):
        service.disable_mfa(user, password="incorrect-password", mfa_code=current_code)
    with pytest.raises(AuthError):
        service.disable_mfa(user, password="correct-horse-battery-staple", mfa_code=None)
    with pytest.raises(AuthError):
        service.disable_mfa(user, password="correct-horse-battery-staple", mfa_code=wrong_code)

    service.disable_mfa(
        user,
        password="correct-horse-battery-staple",
        mfa_code=pyotp.TOTP(secret).now(),
    )
    assert user.mfa_enabled is False
    assert user.mfa_secret_encrypted is None


def test_disabling_unenabled_mfa_still_requires_password(db_session, make_user):
    user = make_user()
    service = AuthService(db_session)
    with pytest.raises(AuthError):
        service.disable_mfa(user, password="incorrect-password", mfa_code=None)
    service.disable_mfa(user, password="correct-horse-battery-staple", mfa_code=None)
    assert user.mfa_enabled is False


@pytest.mark.parametrize("reserved_claim", ["sub", "type", "iat", "exp"])
def test_token_extra_claims_cannot_override_security_claims(reserved_claim):
    from uuid import uuid4

    from app.core.security import create_token

    with pytest.raises(ValueError, match="cannot override reserved claims"):
        create_token(uuid4(), "access", extra_claims={reserved_claim: "attacker-controlled"})


def test_token_allows_non_reserved_extra_claims():
    from uuid import uuid4

    import jwt

    from app.core.config import settings
    from app.core.security import create_token

    user_id = uuid4()
    token = create_token(user_id, "access", extra_claims={"scope": "read-only"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert payload["scope"] == "read-only"


def test_refresh_token_rotation_rejects_replay(db_session, make_user):
    from uuid import UUID

    from app.core.security import decode_token
    from app.models.auth_session import AuthSession

    user = make_user()
    service = AuthService(db_session)
    access_token, refresh_token = service.issue_tokens(user)
    old_payload = decode_token(refresh_token)
    assert old_payload and old_payload["type"] == "refresh"

    new_access, new_refresh = service.rotate_refresh_session(
        user_id=user.id,
        session_id=UUID(old_payload["sid"]),
        presented_jti=old_payload["jti"],
    )
    new_payload = decode_token(new_refresh)
    assert new_payload and new_payload["jti"] != old_payload["jti"]
    assert decode_token(new_access)["sid"] == old_payload["sid"]

    with pytest.raises(AuthError, match="Invalid or revoked refresh session"):
        service.rotate_refresh_session(
            user_id=user.id,
            session_id=UUID(old_payload["sid"]),
            presented_jti=old_payload["jti"],
        )

    session = db_session.get(AuthSession, UUID(old_payload["sid"]))
    assert session is not None
    assert session.revoked_at is None


def test_revoking_session_invalidates_its_access_token(db_session, make_user):
    from fastapi import HTTPException

    from app.core.deps import get_current_user
    from app.core.security import decode_token

    user = make_user()
    service = AuthService(db_session)
    access_token, refresh_token = service.issue_tokens(user)
    payload = decode_token(access_token)
    assert payload and payload["sid"]

    assert get_current_user(db_session, access_token=access_token, authorization=None).id == user.id
    service.revoke_session(UUID(payload["sid"]), user.id)

    with pytest.raises(HTTPException) as exc:
        get_current_user(db_session, access_token=access_token, authorization=None)
    assert exc.value.status_code == 401


def test_mfa_security_change_revokes_existing_sessions(db_session, make_user):
    from app.core.security import decode_token
    from app.models.auth_session import AuthSession

    user = make_user()
    service = AuthService(db_session)
    _, _ = service.issue_tokens(user)
    session = db_session.query(AuthSession).filter_by(user_id=user.id).one()
    assert session.revoked_at is None

    secret, _ = service.start_mfa_enrollment(user)
    import pyotp
    assert service.verify_and_enable_mfa(user, pyotp.TOTP(secret).now()) is True
    db_session.refresh(session)
    assert session.revoked_at is not None
