from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.repositories.portfolio_repository import PortfolioRepository


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_non_admin_gets_403(client):
    client.post("/api/v1/auth/register", json={"email": "u@example.com", "password": "correct-horse-battery-staple", "full_name": "U"})
    client.post("/api/v1/auth/login", json={"email": "u@example.com", "password": "correct-horse-battery-staple"})
    assert client.get("/api/v1/admin/stats").status_code == 403


def test_admin_gets_real_aggregate_counts(client, db_session, make_user):
    # make_user creates the row directly (with the same known test password
    # every fixture uses) -- login through the real endpoint against it,
    # no need to also call /register.
    admin = make_user(email="admin@example.com", is_admin=True)
    PortfolioRepository(db_session).create(user_id=admin.id, name="P1", virtual_capital=Decimal("1000"))
    PortfolioRepository(db_session).create(user_id=admin.id, name="P2", virtual_capital=Decimal("1000"))

    client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "correct-horse-battery-staple"})

    r = client.get("/api/v1/admin/stats")
    assert r.status_code == 200
    assert r.json()["total_portfolios"] == 2
    assert r.json()["total_users"] == 1


def test_market_data_metrics_requires_admin(client):
    assert client.get("/api/v1/admin/market-data-metrics").status_code == 401

    client.post(
        "/api/v1/auth/register",
        json={"email": "metrics-user@example.com", "password": "correct-horse-battery-staple", "full_name": "U"},
    )
    client.post(
        "/api/v1/auth/login",
        json={"email": "metrics-user@example.com", "password": "correct-horse-battery-staple"},
    )
    assert client.get("/api/v1/admin/market-data-metrics").status_code == 403


def test_market_data_metrics_admin_route_returns_only_fixed_aggregate_counters(client, make_user, monkeypatch):
    from app.services.market_data_metrics import _ALLOWED_COUNTERS

    class FakeRedis:
        async def hgetall(self, key):
            return {name: 0 for name in _ALLOWED_COUNTERS}

        async def scard(self, key):
            return 2

        async def aclose(self):
            return None

    monkeypatch.setattr("app.api.v1.admin.from_url", lambda *args, **kwargs: FakeRedis())
    make_user(email="metrics-admin@example.com", is_admin=True)
    client.post(
        "/api/v1/auth/login",
        json={"email": "metrics-admin@example.com", "password": "correct-horse-battery-staple"},
    )

    response = client.get("/api/v1/admin/market-data-metrics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "fleet_aggregated"
    assert payload["source"] == "redis_atomic_counters"
    assert payload["worker_count"] == 2
    assert payload["trading_mode"] == "PAPER"
    assert set(payload["counters"]) == {
        "market_quote_dispatch_accepted_unique_total",
        "market_quote_dispatch_coalesced_total",
        "market_quote_dispatch_dropped_unique_total",
        "market_quote_dispatch_rejected_total",
        "market_quote_dispatch_handler_failures_total",
        "market_quote_dispatch_exhausted_total",
        "market_quote_dispatch_processed_total",
    }
    assert all(isinstance(value, int) and value >= 0 for value in payload["counters"].values())
    assert "metrics-admin@example.com" not in response.text
