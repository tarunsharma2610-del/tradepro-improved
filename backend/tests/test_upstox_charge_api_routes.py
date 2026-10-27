from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.core.deps import get_current_user, get_db
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
                payload={"data": {"total_charges": 20.15}},
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
