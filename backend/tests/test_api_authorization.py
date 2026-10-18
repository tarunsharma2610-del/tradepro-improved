"""
HTTP authorization regression tests plus focused tests for the safety
permission and cookie-Origin dependencies. Safety-control routes are not
registered by this foundation change.
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import (
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


def test_bearer_only_mutation_does_not_depend_on_cookie_origin():
    request = _request("POST", [], cookie=b"")
    require_same_origin_for_cookie_mutation(request)
