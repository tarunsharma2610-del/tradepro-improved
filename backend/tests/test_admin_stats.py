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
