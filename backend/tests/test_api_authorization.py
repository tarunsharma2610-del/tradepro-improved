"""
Everything in test_auth.py and test_broker_credentials.py exercises the
service layer directly. This file goes one level up and drives the actual
HTTP routes, because the auth *dependency wiring* (cookies, the admin
guard on /settings/platform, ownership checks) only gets tested for real
at that layer — see the constitution's rule: "never trust IDs supplied by
the frontend without checking ownership."
"""

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
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
    assert "123456:ABC-token" not in r.text  # masked, never echoed in full

    r = client.get("/api/v1/settings/platform")
    assert r.status_code == 200
    assert any(s["key"] == "telegram_bot_token" for s in r.json())


def test_health_endpoint_is_unauthenticated_and_unversioned(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
