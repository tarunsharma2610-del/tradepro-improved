import pytest

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
