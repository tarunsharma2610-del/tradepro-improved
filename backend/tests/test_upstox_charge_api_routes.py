from datetime import date
import json
import uuid
from decimal import Decimal

from fastapi.testclient import TestClient

from app.core.deps import get_current_user, get_db
from app.models.broker_connection import BrokerConnection
from app.models.broker_api_reconciliation_record import BrokerApiReconciliationRecord
from app.main import app
from app.services.upstox_charge_api_orchestration_service import ChargeApiEnvelope


def _overrides(db_session, user):
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: user


def _clear_overrides():
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def test_brokerage_estimate_route_is_authenticated_and_estimate_only(
    db_session, make_user, monkeypatch
):
    from app.api.v1 import upstox_charges

    user = make_user()
    _overrides(db_session, user)
    monkeypatch.setattr(upstox_charges, "_connected_token", lambda db, user_id: "server-side-token")

    class FakeService:
        async def get_brokerage_estimate(self, token, **kwargs):
            assert token == "server-side-token"
            assert kwargs["trade_date"] == date(2026, 10, 27)
            return ChargeApiEnvelope(
                broker="upstox",
                endpoint="/v2/charges/brokerage",
                evidence_kind="ESTIMATE_ONLY",
                usable=True,
                per_fill_actual=False,
                trade_date=date(2026, 10, 27),
                scope={"exchange": "NSE", "segment": "EQ", "product": "I", "transaction_type": "BUY"},
                payload={"data": {"charges": {"ipft": None}}},
                status_code=200,
            )

    monkeypatch.setattr(upstox_charges, "UpstoxChargeApiOrchestrationService", FakeService)
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/upstox/charges/brokerage-estimate",
            params={
                "instrument_token": "NSE_EQ|TEST",
                "quantity": 1,
                "product": "I",
                "transaction_type": "BUY",
                "price": "100",
                "trade_date": "2026-10-27",
                "exchange": "NSE",
                "segment": "EQ",
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["evidence_kind"] == "ESTIMATE_ONLY"
        assert body["per_fill_actual"] is False
        assert body["payload"]["data"]["charges"]["ipft"] is None
    finally:
        _clear_overrides()


def test_aggregate_route_never_labels_response_as_per_fill_actual(db_session, make_user, monkeypatch):
    from app.api.v1 import upstox_charges

    user = make_user()
    connection = BrokerConnection(
        id=uuid.uuid4(),
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="test-encrypted-key",
        api_secret_encrypted="test-encrypted-secret",
        redirect_uri="http://localhost/callback",
        is_connected=True,
        access_token_encrypted="test-encrypted-token",
    )
    db_session.add(connection)
    db_session.commit()
    _overrides(db_session, user)
    monkeypatch.setattr(upstox_charges, "_connected_token", lambda db, user_id: "server-side-token")

    class FakeService:
        async def get_aggregate_trade_charges(self, token, **kwargs):
            assert token == "server-side-token"
            return ChargeApiEnvelope(
                broker="upstox",
                endpoint="/v2/trade/profit-loss/charges",
                evidence_kind="AGGREGATE_RECONCILIATION_ONLY",
                usable=True,
                per_fill_actual=False,
                trade_date=None,
                scope={"segment": "FO", "financial_year": "2627"},
                payload={"data": {"total_charges": 20.15, "access_token": "must-not-persist"}},
                status_code=200,
            )

    monkeypatch.setattr(upstox_charges, "UpstoxChargeApiOrchestrationService", FakeService)
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/upstox/charges/aggregate",
            params={"segment": "FO", "financial_year": "2627"},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["evidence_kind"] == "AGGREGATE_RECONCILIATION_ONLY"
        assert body["per_fill_actual"] is False
        assert body["trade_date"] is None
        assert body["payload"]["data"]["total_charges"] == 20.15
        record_id = body["reconciliation_record_id"]
        assert record_id
        record = db_session.query(BrokerApiReconciliationRecord).filter_by(id=uuid.UUID(record_id)).one()
        assert record.user_id == user.id
        assert record.broker_connection_id == connection.id
        assert record.evidence_kind == "AGGREGATE_RECONCILIATION_ONLY"
        assert record.per_fill_actual is False
        assert record.response_sha256
        assert "must-not-persist" not in record.response_json
        assert "access_token" not in record.response_json
        assert json.loads(record.response_json)["payload"]["data"]["total_charges"] == 20.15

        # Same owner, connection, scope and response are idempotent.
        second = client.get(
            "/api/v1/upstox/charges/aggregate",
            params={"segment": "FO", "financial_year": "2627"},
        )
        assert second.status_code == 200, second.text
        assert second.json()["reconciliation_record_id"] == record_id
        assert db_session.query(BrokerApiReconciliationRecord).count() == 1
    finally:
        _clear_overrides()


def test_estimate_route_rejects_invalid_quantity_before_api_call(db_session, make_user):
    user = make_user()
    _overrides(db_session, user)
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/upstox/charges/brokerage-estimate",
            params={
                "instrument_token": "NSE_EQ|TEST",
                "quantity": 0,
                "product": "I",
                "transaction_type": "BUY",
                "price": "100",
                "trade_date": "2026-10-27",
                "exchange": "NSE",
                "segment": "EQ",
            },
        )
        assert response.status_code == 422
    finally:
        _clear_overrides()


def test_aggregate_route_rejects_connection_owned_by_another_user(db_session, make_user, monkeypatch):
    from app.api.v1 import upstox_charges

    owner = make_user(email="owner@example.com")
    other_user = make_user(email="other-owner@example.com")
    connection = BrokerConnection(
        id=uuid.uuid4(),
        user_id=owner.id,
        broker="upstox",
        api_key_encrypted="test-encrypted-key",
        api_secret_encrypted="test-encrypted-secret",
        redirect_uri="http://localhost/callback",
        is_connected=True,
        access_token_encrypted="test-encrypted-token",
    )
    db_session.add(connection)
    db_session.commit()
    _overrides(db_session, other_user)
    monkeypatch.setattr(upstox_charges, "_connected_token", lambda db, user_id: "server-side-token")

    class UnexpectedService:
        async def get_aggregate_trade_charges(self, token, **kwargs):
            raise AssertionError("API must not be called for another user's connection")

    monkeypatch.setattr(upstox_charges, "UpstoxChargeApiOrchestrationService", UnexpectedService)
    try:
        response = TestClient(app).get(
            "/api/v1/upstox/charges/aggregate",
            params={"segment": "FO", "financial_year": "2627"},
        )
        assert response.status_code == 404
        assert db_session.query(BrokerApiReconciliationRecord).count() == 0
    finally:
        _clear_overrides()


def test_aggregate_snapshot_rejects_mutation(db_session, make_user):
    from datetime import datetime, timezone

    user = make_user()
    connection = BrokerConnection(
        id=uuid.uuid4(),
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="test-encrypted-key",
        api_secret_encrypted="test-encrypted-secret",
        redirect_uri="http://localhost/callback",
        is_connected=True,
        access_token_encrypted="test-encrypted-token",
    )
    db_session.add(connection)
    db_session.commit()
    record = BrokerApiReconciliationRecord(
        user_id=user.id,
        broker_connection_id=connection.id,
        broker="upstox",
        endpoint="/v2/trade/profit-loss/charges",
        api_version="v2",
        request_scope_json='{"segment":"FO"}',
        fetched_at=datetime.now(timezone.utc),
        fetch_status="SUCCESS",
        http_status_code=200,
        error_code=None,
        evidence_kind="AGGREGATE_RECONCILIATION_ONLY",
        per_fill_actual=False,
        response_sha256="a" * 64,
        response_json='{"payload":{"total_charges":20.15}}',
        idempotency_key="b" * 64,
    )
    db_session.add(record)
    db_session.commit()
    record.fetch_status = "CHANGED"
    try:
        db_session.commit()
    except ValueError as exc:
        assert "immutable" in str(exc)
    else:
        raise AssertionError("Aggregate evidence mutation must be rejected")
    db_session.rollback()
    assert db_session.query(BrokerApiReconciliationRecord).filter_by(id=record.id).one().fetch_status == "SUCCESS"
