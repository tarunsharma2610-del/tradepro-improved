import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.broker_connection import BrokerConnection
from app.models.live_order_records import LiveReconciliationIssue, LiveReconciliationRun
from app.repositories.live_reconciliation_issue_repository import LiveReconciliationIssueRepository


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _register_login(client, email):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct-horse-battery-staple", "full_name": "Test"},
    )
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "correct-horse-battery-staple"})
    assert response.status_code == 200


def _connection(db_session, user, name):
    connection = BrokerConnection(
        user_id=user.id, broker="upstox", api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret", redirect_uri="https://example.invalid/callback",
        is_connected=False,
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)
    return connection


def test_reconciliation_lists_require_authentication(client):
    assert client.get("/api/v1/reconciliation/runs").status_code == 401
    assert client.get("/api/v1/reconciliation/issues").status_code == 401


def test_reconciliation_lists_are_owner_scoped_and_sanitized(client, db_session):
    from app.repositories.user_repository import UserRepository

    _register_login(client, "recon-owner@example.com")
    owner = UserRepository(db_session).get_by_email("recon-owner@example.com")
    owner_connection = _connection(db_session, owner, "owner")
    owner_run = LiveReconciliationRun(
        user_id=owner.id, broker_connection_id=owner_connection.id,
        status="COMPLETED", summary={"orders_seen": 1, "orders_matched": 1, "orders_unmatched": 0,
                                     "trades_seen": 1, "fills_inserted": 1, "duplicate_fills": 0, "conflicts": 0},
    )
    db_session.add(owner_run)
    db_session.commit()
    issue, _ = LiveReconciliationIssueRepository(db_session).record(
        user_id=owner.id, broker_connection_id=owner_connection.id,
        issue_type="UNMATCHED_ORDER", broker_order_id="owner-order",
        safe_details={"match_status": "NO_MATCH", "reason_code": "ORDER_NOT_SAFELY_MATCHED"},
    )

    _register_login(client, "recon-other@example.com")
    other = UserRepository(db_session).get_by_email("recon-other@example.com")
    other_connection = _connection(db_session, other, "other")
    db_session.add(LiveReconciliationRun(
        user_id=other.id, broker_connection_id=other_connection.id, status="FAILED",
        error_code="TOKEN_UNAVAILABLE", summary={"orders_seen": 0, "orders_matched": 0, "orders_unmatched": 0,
                                                  "trades_seen": 0, "fills_inserted": 0, "duplicate_fills": 0, "conflicts": 0},
    ))
    db_session.commit()
    LiveReconciliationIssueRepository(db_session).record(
        user_id=other.id, broker_connection_id=other_connection.id,
        issue_type="UNMATCHED_ORDER", broker_order_id="other-order",
        safe_details={"match_status": "NO_MATCH", "reason_code": "ORDER_NOT_SAFELY_MATCHED"},
    )

    _register_login(client, "recon-owner@example.com")
    runs = client.get("/api/v1/reconciliation/runs").json()
    issues = client.get("/api/v1/reconciliation/issues").json()
    assert len(runs) == 1
    assert runs[0]["broker_connection_id"] == str(owner_connection.id)
    assert len(issues) == 1
    assert issues[0]["id"] == str(issue.id)
    assert issues[0]["broker_order_id"] == "owner-order"
    assert "other-order" not in str(issues)
    assert "access_token" not in str(issues).lower()
    assert client.get(f"/api/v1/reconciliation/issues?broker_connection_id={other_connection.id}").json() == []


def test_reconciliation_filters_and_limits_are_validated(client, db_session):
    from app.repositories.user_repository import UserRepository
    _register_login(client, "recon-filter@example.com")
    user = UserRepository(db_session).get_by_email("recon-filter@example.com")
    connection = _connection(db_session, user, "filter")
    db_session.add(LiveReconciliationRun(
        user_id=user.id, broker_connection_id=connection.id, status="FAILED",
        error_code="TOKEN_UNAVAILABLE", summary={"orders_seen": 0, "orders_matched": 0, "orders_unmatched": 0,
                                                  "trades_seen": 0, "fills_inserted": 0, "duplicate_fills": 0, "conflicts": 0},
    ))
    db_session.commit()
    assert len(client.get("/api/v1/reconciliation/runs?status=FAILED").json()) == 1
    assert client.get("/api/v1/reconciliation/runs?status=NOT_A_STATUS").status_code == 422
    assert client.get("/api/v1/reconciliation/issues?limit=101").status_code == 422
