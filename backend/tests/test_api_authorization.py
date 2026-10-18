"""HTTP authorization regression tests for safety permissions, MFA and Origin controls.

The admin permission-provisioning route is covered here. Safety status, audit,
kill-switch and reset routes are not yet registered.
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_token, hash_password
from app.core.deps import (
    require_recent_safety_mfa,
    require_same_origin_for_cookie_mutation,
    require_safety_permission,
)
from app.main import app


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _register_and_login(client, email="user@example.com"):
    client.post(
        "/api/v1/auth/register", json={"email": email, "password": "correct-horse-battery-staple", "full_name": "U"}
    )
    client.post("/api/v1/auth/login", json={"email": email, "password": "correct-horse-battery-staple"})
    return client


def test_unauthenticated_requests_are_rejected(client):
    assert client.get("/api/v1/users/me").status_code == 401
    assert client.get("/api/v1/settings/broker").status_code == 401
    assert client.get("/api/v1/settings/platform").status_code == 401


def test_authenticated_user_can_reach_their_own_settings(client):
    _register_and_login(client)
    r = client.get("/api/v1/users/me")
    assert r.status_code == 200
    assert r.json()["email"] == "user@example.com"


def test_non_admin_gets_403_on_admin_only_platform_settings(client):
    _register_and_login(client)
    r = client.get("/api/v1/settings/platform")
    assert r.status_code == 403


def test_admin_can_reach_platform_settings(client, db_session):
    _register_and_login(client, email="admin@example.com")
    from app.repositories.user_repository import UserRepository

    user = UserRepository(db_session).get_by_email("admin@example.com")
    user.is_admin = True
    db_session.add(user)
    db_session.commit()

    r = client.put(
        "/api/v1/settings/platform",
        json={"key": "telegram_bot_token", "value": "123456:ABC-token", "description": "prod bot"},
    )
    assert r.status_code == 200
    assert "123456:ABC-token" not in r.text

    r = client.get("/api/v1/settings/platform")
    assert r.status_code == 200
    assert any(s["key"] == "telegram_bot_token" for s in r.json())


def test_health_endpoint_is_unauthenticated_and_unversioned(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_malformed_signed_jwt_subject_is_normalized_to_401(client):
    token = jwt.encode(
        {
            "sub": "not-a-uuid",
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_admin_flag_does_not_grant_safety_reset_permission():
    dependency = require_safety_permission("safety.reset")
    admin_without_grant = SimpleNamespace(is_admin=True, safety_permissions=[])
    with pytest.raises(HTTPException) as exc:
        dependency(admin_without_grant)
    assert exc.value.status_code == 403


def test_explicit_safety_permission_is_accepted():
    dependency = require_safety_permission("safety.audit.read")
    operator = SimpleNamespace(is_admin=False, safety_permissions=["safety.audit.read"])
    assert dependency(operator) is operator


def test_unknown_safety_permission_fails_at_definition_time():
    with pytest.raises(ValueError):
        require_safety_permission("safety.live_trade")


def _request(method: str, headers: list[tuple[bytes, bytes]], cookie: bytes = b"access_token=signed") -> Request:
    return Request({
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": "/api/v1/safety/reset",
        "raw_path": b"/api/v1/safety/reset",
        "query_string": b"",
        "headers": [(b"cookie", cookie), *headers],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    })


def test_cookie_mutation_requires_allowed_origin():
    request = _request("POST", [])
    with pytest.raises(HTTPException) as exc:
        require_same_origin_for_cookie_mutation(request)
    assert exc.value.status_code == 403


def test_cookie_mutation_rejects_untrusted_origin():
    request = _request("POST", [(b"origin", b"https://attacker.example")])
    with pytest.raises(HTTPException) as exc:
        require_same_origin_for_cookie_mutation(request)
    assert exc.value.status_code == 403


def test_cookie_mutation_accepts_configured_origin():
    origin = settings.CORS_ORIGINS[0].encode()
    request = _request("POST", [(b"origin", origin)])
    require_same_origin_for_cookie_mutation(request)


def test_step_up_http_requires_enabled_mfa_and_fresh_password_totp(client, db_session, monkeypatch):
    _register_and_login(client)
    from app.repositories.user_repository import UserRepository
    from app.services.auth_service import AuthService

    user = UserRepository(db_session).get_by_email("user@example.com")
    user.mfa_enabled = True
    user.mfa_secret_encrypted = "test-encrypted-secret"
    db_session.commit()
    monkeypatch.setattr(AuthService, "_verify_totp", staticmethod(lambda user, code: code == "123456"))

    response = client.post(
        "/api/v1/auth/mfa/step-up",
        json={"password": "correct-horse-battery-staple", "code": "123456"},
        headers={"Origin": settings.CORS_ORIGINS[0]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["expires_in"] == 300
    token = body["step_up_token"]
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["type"] == "step_up"
    assert payload["scope"] == "safety.reset"
    assert payload["sub"] == str(user.id)
    assert "totp" in payload["amr"]

    bad_password = client.post(
        "/api/v1/auth/mfa/step-up",
        json={"password": "wrong-password", "code": "123456"},
        headers={"Origin": settings.CORS_ORIGINS[0]},
    )
    assert bad_password.status_code == 401


def test_step_up_http_denies_accounts_without_mfa(client, db_session):
    _register_and_login(client)
    response = client.post(
        "/api/v1/auth/mfa/step-up",
        json={"password": "correct-horse-battery-staple", "code": "123456"},
        headers={"Origin": settings.CORS_ORIGINS[0]},
    )
    assert response.status_code == 403


def test_admin_cannot_grant_safety_permission_without_recent_mfa(client, db_session):
    _register_and_login(client, email="admin@example.com")
    from app.repositories.user_repository import UserRepository

    user = UserRepository(db_session).get_by_email("admin@example.com")
    user.is_admin = True
    db_session.commit()
    target = UserRepository(db_session).create(
        email="target@example.com",
        password_hash=hash_password("correct-horse-battery-staple"),
        full_name="Target",
    )
    response = client.put(
        f"/api/v1/admin/users/{target.id}/safety-permissions",
        json={"permission": "safety.audit.read", "action": "grant"},
        headers={"Origin": settings.CORS_ORIGINS[0]},
    )
    assert response.status_code == 403
    db_session.refresh(target)
    assert target.safety_permissions == []


def test_admin_cannot_self_grant_safety_permission_even_with_recent_mfa(client, db_session, monkeypatch):
    _register_and_login(client, email="admin@example.com")
    from app.repositories.user_repository import UserRepository
    from app.services.auth_service import AuthService
    user = UserRepository(db_session).get_by_email("admin@example.com")
    user.is_admin = True
    user.mfa_enabled = True
    user.mfa_secret_encrypted = "test-encrypted-secret"
    db_session.commit()
    monkeypatch.setattr(AuthService, "_verify_totp", staticmethod(lambda user, code: code == "123456"))
    step_up = client.post(
        "/api/v1/auth/mfa/step-up",
        json={"password": "correct-horse-battery-staple", "code": "123456"},
        headers={"Origin": settings.CORS_ORIGINS[0]},
    )
    assert step_up.status_code == 200
    response = client.put(
        f"/api/v1/admin/users/{user.id}/safety-permissions",
        json={"permission": "safety.reset", "action": "grant"},
        headers={"Origin": settings.CORS_ORIGINS[0], "X-Safety-Step-Up": step_up.json()["step_up_token"]},
    )
    assert response.status_code == 403


def test_mfa_admin_can_grant_and_revoke_scoped_permission_with_audit(client, db_session, monkeypatch):
    _register_and_login(client, email="admin@example.com")
    from app.repositories.user_repository import UserRepository
    from app.services.auth_service import AuthService
    from app.models.audit_log import AuditLog

    users = UserRepository(db_session)
    admin = users.get_by_email("admin@example.com")
    admin.is_admin = True
    admin.mfa_enabled = True
    admin.mfa_secret_encrypted = "test-encrypted-secret"
    db_session.commit()
    target = users.create(
        email="target@example.com",
        password_hash=__import__("app.core.security", fromlist=["hash_password"]).hash_password("correct-horse-battery-staple"),
        full_name="Target",
    )
    monkeypatch.setattr(AuthService, "_verify_totp", staticmethod(lambda user, code: code == "123456"))
    step_up = client.post(
        "/api/v1/auth/mfa/step-up",
        json={"password": "correct-horse-battery-staple", "code": "123456"},
        headers={"Origin": settings.CORS_ORIGINS[0]},
    )
    assert step_up.status_code == 200
    headers = {
        "Origin": settings.CORS_ORIGINS[0],
        "X-Safety-Step-Up": step_up.json()["step_up_token"],
    }
    granted = client.put(
        f"/api/v1/admin/users/{target.id}/safety-permissions",
        json={"permission": "safety.audit.read", "action": "grant"},
        headers=headers,
    )
    assert granted.status_code == 200
    assert granted.json()["safety_permissions"] == ["safety.audit.read"]
    revoked = client.put(
        f"/api/v1/admin/users/{target.id}/safety-permissions",
        json={"permission": "safety.audit.read", "action": "revoke"},
        headers=headers,
    )
    assert revoked.status_code == 200
    assert revoked.json()["safety_permissions"] == []
    events = db_session.query(AuditLog).filter(AuditLog.action.in_([
        "safety.permission.grant", "safety.permission.revoke"
    ])).all()
    assert len(events) == 2
    assert all(event.user_id == admin.id and event.resource_id == str(target.id) for event in events)


def test_recent_mfa_step_up_rejects_missing_or_wrong_scope_token(make_user):
    user = make_user()
    with pytest.raises(HTTPException) as exc:
        require_recent_safety_mfa(step_up_token=None, user=user)
    assert exc.value.status_code == 403

    wrong_scope = create_token(user.id, "step_up", extra_claims={
        "scope": "other", "amr": ["pwd", "totp"],
        "mfa_verified_at": int(datetime.now(timezone.utc).timestamp()),
    })
    with pytest.raises(HTTPException) as exc:
        require_recent_safety_mfa(step_up_token=wrong_scope, user=user)
    assert exc.value.status_code == 403


def test_recent_mfa_step_up_is_user_bound_and_accepts_fresh_token(make_user):
    user = make_user()
    user.mfa_enabled = True
    token = create_token(user.id, "step_up", extra_claims={
        "scope": "safety.reset", "amr": ["pwd", "totp"],
        "mfa_verified_at": int(datetime.now(timezone.utc).timestamp()),
    })
    assert require_recent_safety_mfa(step_up_token=token, user=user) is user
    another_user = make_user(email="another@example.com")
    with pytest.raises(HTTPException) as exc:
        require_recent_safety_mfa(step_up_token=token, user=another_user)
    assert exc.value.status_code == 403


def test_recent_mfa_step_up_rejects_token_if_mfa_was_disabled(make_user):
    user = make_user()
    token = create_token(user.id, "step_up", extra_claims={
        "scope": "safety.reset", "amr": ["pwd", "totp"],
        "mfa_verified_at": int(datetime.now(timezone.utc).timestamp()),
    })
    with pytest.raises(HTTPException) as exc:
        require_recent_safety_mfa(step_up_token=token, user=user)
    assert exc.value.status_code == 403


def test_recent_mfa_step_up_rejects_stale_verification(make_user):
    user = make_user()
    old = int((datetime.now(timezone.utc) - timedelta(minutes=6)).timestamp())
    token = create_token(user.id, "step_up", extra_claims={
        "scope": "safety.reset", "amr": ["pwd", "totp"], "mfa_verified_at": old,
    })
    with pytest.raises(HTTPException) as exc:
        require_recent_safety_mfa(step_up_token=token, user=user)
    assert exc.value.status_code == 403


def test_bearer_only_mutation_does_not_depend_on_cookie_origin():
    request = _request("POST", [], cookie=b"")
    require_same_origin_for_cookie_mutation(request)
