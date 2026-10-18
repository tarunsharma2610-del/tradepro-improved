from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.broker_connection import BrokerConnection
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.live_charge_adjustment import LiveChargeAdjustment
from app.models.order import Order
from app.models.user import User
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.instrument_service import InstrumentService
from app.repositories.instrument_repository import InstrumentRepository


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _register_and_login(client, email):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "correct-horse-battery-staple",
            "full_name": "Analytics User",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    assert login.status_code == 200


def test_live_analytics_is_read_only_separate_and_owner_scoped(client, db_session):
    _register_and_login(client, "live-analytics-owner@example.com")
    created = client.post(
        "/api/v1/portfolios",
        json={"name": "P&L isolation", "virtual_capital": "100000"},
    )
    assert created.status_code == 201
    portfolio_id = created.json()["id"]
    owner = db_session.query(User).filter_by(email="live-analytics-owner@example.com").one()
    InstrumentService(db_session).seed_defaults()
    instrument = InstrumentRepository(db_session).search("RELIANCE")[0]
    now = datetime.now(timezone.utc)
    connection = BrokerConnection(
        user_id=owner.id,
        broker="upstox",
        api_key_encrypted="test-key",
        api_secret_encrypted="test-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=True,
    )
    portfolio = PortfolioRepository(db_session).get_for_user(owner.id, __import__("uuid").UUID(portfolio_id))
    live_order = Order(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        side="SELL",
        order_type="MARKET",
        segment="EQUITY_DELIVERY",
        quantity=2,
        status="FILLED",
        trading_mode="LIVE",
        execution_reason="MANUAL",
        broker_order_id="api-live-analytics-child",
        placed_at=now,
        filled_at=now,
    )
    db_session.add_all([connection, live_order])
    db_session.flush()
    execution = Execution(
        order_id=live_order.id,
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        side="SELL",
        quantity=2,
        price=Decimal("100"),
        gross_value=Decimal("200"),
        brokerage=Decimal("4"),
        stt=Decimal("2"),
        exchange_charges=Decimal("1"),
        sebi_charges=Decimal("1"),
        stamp_duty=Decimal("1"),
        gst=Decimal("1"),
        dp_charges=Decimal("0"),
        total_charges=Decimal("10"),
        charge_source="APPROVED_ESTIMATE",
        charge_reference="estimator-v1",
        realized_pnl=Decimal("80"),
        broker_name="upstox",
        broker_connection_id=connection.id,
        broker_trade_id="api-live-analytics-trade",
        executed_at=now,
    )
    db_session.add(execution)
    db_session.flush()
    db_session.add(LiveChargeAdjustment(
        execution_id=execution.id,
        broker_connection_id=connection.id,
        broker_trade_id="api-live-analytics-trade",
        adjustment_number=1,
        source="BROKER_REPORTED",
        source_reference="contract-note:api-live-analytics",
        brokerage=Decimal("6"),
        stt=Decimal("3"),
        exchange_charges=Decimal("2"),
        sebi_charges=Decimal("1"),
        stamp_duty=Decimal("1"),
        gst=Decimal("2"),
        dp_charges=Decimal("0"),
        previous_effective_total=Decimal("10"),
        new_effective_total=Decimal("15"),
        charge_delta=Decimal("5"),
        net_realized_pnl_delta=Decimal("-5"),
    ))
    db_session.commit()

    live = client.get(f"/api/v1/portfolios/{portfolio_id}/live-analytics")
    assert live.status_code == 200
    payload = live.json()
    assert Decimal(str(payload["total_gross_realized_pnl"])) == Decimal("80.00")
    assert Decimal(str(payload["total_net_realized_pnl"])) == Decimal("65.00")
    assert Decimal(str(payload["total_effective_costs"])) == Decimal("15.00")
    assert payload["total_fills"] == 1
    assert "broker account balances remain authoritative" in payload["accounting_note"]

    # The normal analytics endpoint remains a PAPER-only cash/performance view.
    paper = client.get(f"/api/v1/portfolios/{portfolio_id}/analytics")
    assert paper.status_code == 200
    assert paper.json()["total_trades"] == 0
    assert paper.json()["equity_curve"] == []

    _register_and_login(client, "live-analytics-intruder@example.com")
    denied = client.get(f"/api/v1/portfolios/{portfolio_id}/live-analytics")
    assert denied.status_code == 404


def test_live_analytics_requires_authentication(client):
    response = client.get("/api/v1/portfolios/00000000-0000-0000-0000-000000000000/live-analytics")
    assert response.status_code == 401
