"""HTTP authorization regression tests for safety permissions, MFA, Origin and control routes."""
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
        json={"password": "correct-horse-battery-staple", "code": "123456", "purpose": "safety.admin.permissions"},
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
        json={"password": "correct-horse-battery-staple", "code": "123456", "purpose": "safety.admin.permissions"},
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



def test_safety_audit_read_requires_explicit_permission(client, db_session):
    _register_and_login(client, email="operator@example.com")
    response = client.get("/api/v1/admin/safety/audit")
    assert response.status_code == 403


def test_safety_audit_read_is_tenant_scoped_and_paginated(client, db_session):
    _register_and_login(client, email="operator@example.com")
    from app.repositories.user_repository import UserRepository
    from app.models.audit_log import AuditLog
    from app.models.live_account_safety import LiveAccountSafetyEvent, LiveAccountSafetyState
    from app.models.user import User

    users = UserRepository(db_session)
    operator = users.get_by_email("operator@example.com")
    operator.safety_permissions = ["safety.audit.read"]
    other = User(
        email="other@example.com",
        password_hash=hash_password("correct-horse-battery-staple"),
        full_name="Other",
    )
    db_session.add(other)
    db_session.flush()

    own_state = LiveAccountSafetyState(
        user_id=operator.id, broker="upstox", kill_switch_tripped=True,
        circuit_state="CLOSED", consecutive_broker_errors=0, version=2,
    )
    other_state = LiveAccountSafetyState(
        user_id=other.id, broker="upstox", kill_switch_tripped=True,
        circuit_state="CLOSED", consecutive_broker_errors=0, version=1,
    )
    db_session.add_all([own_state, other_state])
    db_session.flush()
    db_session.add_all([
        LiveAccountSafetyEvent(
            state_id=own_state.id, actor_user_id=operator.id,
            idempotency_key="own-event-0001", request_fingerprint="a" * 64,
            event_type="INITIALIZED", reason="own account initialized",
            error_code=None, consecutive_broker_errors=0, circuit_state="CLOSED",
            kill_switch_tripped=True, state_version=1,
        ),
        LiveAccountSafetyEvent(
            state_id=own_state.id, actor_user_id=operator.id,
            idempotency_key="own-event-0002", request_fingerprint="b" * 64,
            event_type="KILL_SWITCH_TRIPPED", reason="own account trip",
            error_code=None, consecutive_broker_errors=0, circuit_state="CLOSED",
            kill_switch_tripped=True, state_version=2,
        ),
        LiveAccountSafetyEvent(
            state_id=other_state.id, actor_user_id=other.id,
            idempotency_key="other-event-0001", request_fingerprint="c" * 64,
            event_type="KILL_SWITCH_TRIPPED", reason="other-account-secret",
            error_code=None, consecutive_broker_errors=0, circuit_state="CLOSED",
            kill_switch_tripped=True, state_version=1,
        ),
        AuditLog(
            user_id=operator.id, action="user.login", resource_type="session",
            resource_id="not-safety", event_metadata={},
        ),
    ])
    db_session.commit()

    first = client.get("/api/v1/admin/safety/audit?limit=1&offset=0")
    assert first.status_code == 200
    body = first.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert body["next_offset"] == 1
    assert body["items"][0]["action"] in {"INITIALIZED", "KILL_SWITCH_TRIPPED"}
    assert body["items"][0]["resource_type"] == "live_account_safety_state"

    second = client.get("/api/v1/admin/safety/audit?limit=1&offset=1")
    assert second.status_code == 200
    assert len(second.json()["items"]) == 1
    assert second.json()["next_offset"] is None

    serialized = first.text + second.text
    assert "other-account-secret" not in serialized
    assert "user.login" not in serialized
    assert "idempotency_key" not in serialized
    assert "request_fingerprint" not in serialized

def test_safety_audit_read_rejects_invalid_pagination(client, db_session):
    _register_and_login(client, email="operator@example.com")
    from app.repositories.user_repository import UserRepository

    user = UserRepository(db_session).get_by_email("operator@example.com")
    user.safety_permissions = ["safety.audit.read"]
    db_session.commit()
    assert client.get("/api/v1/admin/safety/audit?limit=0").status_code == 422
    assert client.get("/api/v1/admin/safety/audit?limit=101").status_code == 422
    assert client.get("/api/v1/admin/safety/audit?offset=-1").status_code == 422


def test_safety_status_requires_explicit_permission(client):
    _register_and_login(client, email="operator@example.com")
    response = client.get("/api/v1/safety/status")
    assert response.status_code == 403


def test_safety_status_and_trip_are_scoped_to_authenticated_user(client, db_session):
    _register_and_login(client, email="operator@example.com")
    from app.repositories.user_repository import UserRepository

    user = UserRepository(db_session).get_by_email("operator@example.com")
    user.safety_permissions = ["safety.status.read", "safety.kill_switch.trip"]
    db_session.commit()
    origin = settings.CORS_ORIGINS[0]

    before = client.get("/api/v1/safety/status")
    assert before.status_code == 200
    assert before.json()["state_exists"] is False
    assert before.json()["allowed"] is False
    assert before.json()["kill_switch_tripped"] is True

    trip = client.post(
        "/api/v1/safety/kill-switch/trip",
        json={"reason": "operator requested emergency stop"},
        headers={"Origin": origin, "Idempotency-Key": "operator-trip-0001"},
    )
    assert trip.status_code == 200
    assert trip.json()["state_exists"] is True
    assert trip.json()["kill_switch_tripped"] is True
    assert trip.json()["allowed"] is False

    state = client.get("/api/v1/safety/status")
    assert state.status_code == 200
    assert state.json()["kill_switch_tripped"] is True
    assert state.json()["version"] == trip.json()["version"]


def test_safety_trip_rejects_missing_idempotency_key(client, db_session):
    _register_and_login(client, email="operator@example.com")
    from app.repositories.user_repository import UserRepository

    user = UserRepository(db_session).get_by_email("operator@example.com")
    user.safety_permissions = ["safety.kill_switch.trip"]
    db_session.commit()
    response = client.post(
        "/api/v1/safety/kill-switch/trip",
        json={"reason": "operator requested emergency stop"},
        headers={"Origin": settings.CORS_ORIGINS[0]},
    )
    assert response.status_code == 422


def test_safety_reset_requires_permission_and_recent_mfa(client, db_session):
    _register_and_login(client, email="operator@example.com")
    from app.repositories.user_repository import UserRepository

    user = UserRepository(db_session).get_by_email("operator@example.com")
    user.safety_permissions = ["safety.reset"]
    db_session.commit()
    response = client.post(
        "/api/v1/safety/kill-switch/reset",
        json={"reason": "reviewed recovery", "expected_version": 1},
        headers={"Origin": settings.CORS_ORIGINS[0], "Idempotency-Key": "operator-reset-0001"},
    )
    assert response.status_code == 403


def test_safety_reset_with_recent_mfa_still_requires_fresh_health_check(client, db_session):
    _register_and_login(client, email="operator@example.com")
    from datetime import datetime, timezone
    from app.repositories.user_repository import UserRepository
    from app.services.live_account_safety_service import LiveAccountSafetyService

    user = UserRepository(db_session).get_by_email("operator@example.com")
    user.safety_permissions = ["safety.reset"]
    user.mfa_enabled = True
    db_session.commit()
    LiveAccountSafetyService(db_session).initialize(
        user.id, actor_user_id=user.id, idempotency_key="test-initialize-safety",
    )
    verified_at = int(datetime.now(timezone.utc).timestamp())
    step_up = create_token(
        user.id,
        "step_up",
        extra_claims={
            "scope": "safety.reset",
            "amr": ["pwd", "totp"],
            "mfa_verified_at": verified_at,
        },
    )
    response = client.post(
        "/api/v1/safety/kill-switch/reset",
        json={"reason": "reviewed recovery", "expected_version": 1},
        headers={
            "Origin": settings.CORS_ORIGINS[0],
            "Idempotency-Key": "operator-reset-0002",
            "X-Safety-Step-Up": step_up,
        },
    )
    assert response.status_code == 409
    assert "health check" in response.json()["detail"].lower()


def test_cookie_authenticated_safety_trip_rejects_missing_origin(client, db_session):
    _register_and_login(client, email="operator@example.com")
    from app.repositories.user_repository import UserRepository

    user = UserRepository(db_session).get_by_email("operator@example.com")
    user.safety_permissions = ["safety.kill_switch.trip"]
    db_session.commit()
    response = client.post(
        "/api/v1/safety/kill-switch/trip",
        json={"reason": "operator requested emergency stop"},
        headers={"Idempotency-Key": "operator-trip-0002"},
    )
    assert response.status_code == 403


def test_non_admin_cannot_request_permission_management_step_up(client, db_session, monkeypatch):
    _register_and_login(client, email="ordinary@example.com")
    from app.repositories.user_repository import UserRepository
    from app.services.auth_service import AuthService
    monkeypatch.setattr(AuthService, "_verify_totp", staticmethod(lambda user, code: code == "123456"))
    user = UserRepository(db_session).get_by_email("ordinary@example.com")
    user.mfa_enabled = True
    user.mfa_secret_encrypted = "test-encrypted-secret"
    db_session.commit()
    response = client.post(
        "/api/v1/auth/mfa/step-up",
        json={"password": "correct-horse-battery-staple", "code": "123456", "purpose": "safety.admin.permissions"},
        headers={"Origin": settings.CORS_ORIGINS[0]},
    )
    assert response.status_code == 403


def test_reset_step_up_token_cannot_authorize_permission_management(client, db_session):
    _register_and_login(client, email="admin@example.com")
    from app.repositories.user_repository import UserRepository
    from app.core.deps import require_recent_safety_mfa_scope
    user = UserRepository(db_session).get_by_email("admin@example.com")
    user.is_admin = True
    user.mfa_enabled = True
    db_session.commit()
    token = create_token(user.id, "step_up", extra_claims={
        "scope": "safety.reset",
        "amr": ["pwd", "totp"],
        "mfa_verified_at": int(datetime.now(timezone.utc).timestamp()),
    })
    dependency = require_recent_safety_mfa_scope("safety.admin.permissions")
    with pytest.raises(HTTPException) as exc:
        dependency(step_up_token=token, user=user)
    assert exc.value.status_code == 403


def test_permission_management_route_rejects_reset_scope_token(client, db_session):
    _register_and_login(client, email="admin@example.com")
    from app.repositories.user_repository import UserRepository
    users = UserRepository(db_session)
    admin = users.get_by_email("admin@example.com")
    admin.is_admin = True
    admin.mfa_enabled = True
    target = users.create(
        email="target@example.com",
        password_hash=hash_password("correct-horse-battery-staple"),
        full_name="Target",
    )
    db_session.commit()
    token = create_token(admin.id, "step_up", extra_claims={
        "scope": "safety.reset",
        "amr": ["pwd", "totp"],
        "mfa_verified_at": int(datetime.now(timezone.utc).timestamp()),
    })
    response = client.put(
        f"/api/v1/admin/users/{target.id}/safety-permissions",
        json={"permission": "safety.audit.read", "action": "grant"},
        headers={"Origin": settings.CORS_ORIGINS[0], "X-Safety-Step-Up": token},
    )
    assert response.status_code == 403
    db_session.refresh(target)
    assert target.safety_permissions == []
