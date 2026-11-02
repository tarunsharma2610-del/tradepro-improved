from uuid import UUID

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


def _register_and_login(client, email):
    client.post("/api/v1/auth/register", json={"email": email, "password": "correct-horse-battery-staple", "full_name": "U"})
    client.post("/api/v1/auth/login", json={"email": email, "password": "correct-horse-battery-staple"})


def test_user_cannot_read_or_trade_another_users_portfolio(client, db_session):
    _register_and_login(client, "owner@example.com")
    created = client.post("/api/v1/portfolios", json={"name": "Main", "virtual_capital": "100000"})
    assert created.status_code == 201
    portfolio_id = created.json()["id"]

    # Switch to a different logged-in user in the SAME client (fresh login overwrites the cookie).
    _register_and_login(client, "intruder@example.com")

    assert client.get(f"/api/v1/portfolios/{portfolio_id}").status_code == 404
    assert client.get(f"/api/v1/portfolios/{portfolio_id}/positions").status_code == 404
    assert client.get(f"/api/v1/portfolios/{portfolio_id}/orders").status_code == 404

    from app.services.instrument_service import InstrumentService
    from app.repositories.instrument_repository import InstrumentRepository

    InstrumentService(db_session).seed_defaults()
    instrument_id = str(InstrumentRepository(db_session).search("TCS")[0].id)

    order_attempt = client.post(
        f"/api/v1/portfolios/{portfolio_id}/orders",
        json={"instrument_id": instrument_id, "side": "BUY", "order_type": "MARKET", "segment": "EQUITY_DELIVERY", "quantity": 1},
    )
    assert order_attempt.status_code == 400  # OrderValidationError -> 400, portfolio not found for this user

    # And the owner's list of portfolios never shows up under the intruder's account.
    assert client.get("/api/v1/portfolios").json() == []


def test_owner_can_fully_use_their_own_portfolio(client):
    _register_and_login(client, "owner2@example.com")
    created = client.post("/api/v1/portfolios", json={"name": "Main", "virtual_capital": "50000"})
    assert created.status_code == 201
    portfolio_id = created.json()["id"]

    assert client.get(f"/api/v1/portfolios/{portfolio_id}").status_code == 200
    assert client.get(f"/api/v1/portfolios/{portfolio_id}/positions").json() == []
    assert client.get(f"/api/v1/portfolios/{portfolio_id}/orders").json() == []
    assert len(client.get("/api/v1/portfolios").json()) == 1


def test_user_cannot_read_or_control_another_users_strategy(client, db_session):
    from app.services.instrument_service import InstrumentService
    from app.repositories.instrument_repository import InstrumentRepository

    _register_and_login(client, "strat-owner@example.com")
    portfolio_id = client.post("/api/v1/portfolios", json={"name": "Main", "virtual_capital": "100000"}).json()["id"]

    InstrumentService(db_session).seed_defaults()
    instrument_id = InstrumentRepository(db_session).search("INFY")[0].id

    created = client.post(
        f"/api/v1/portfolios/{portfolio_id}/strategies",
        json={
            "instrument_id": str(instrument_id), "name": "My strategy", "segment": "EQUITY_INTRADAY",
            "quantity": 1, "max_daily_loss": "2000",
        },
    )
    assert created.status_code == 201
    strategy_id = created.json()["id"]

    _register_and_login(client, "strat-intruder@example.com")

    assert client.get(f"/api/v1/portfolios/{portfolio_id}/strategies/{strategy_id}").status_code == 404
    assert client.post(f"/api/v1/portfolios/{portfolio_id}/strategies/{strategy_id}/activate").status_code == 404
    assert client.post(f"/api/v1/portfolios/{portfolio_id}/strategies/{strategy_id}/evaluate").status_code == 404
    assert client.delete(f"/api/v1/portfolios/{portfolio_id}/strategies/{strategy_id}").status_code == 404
    # And listing under the intruder's own (different, portfolio-less-access) view finds nothing.
    assert client.get(f"/api/v1/portfolios/{portfolio_id}/strategies").status_code == 404


def test_user_cannot_read_or_delete_another_users_backtest(client, db_session):
    from app.services.instrument_service import InstrumentService
    from app.repositories.instrument_repository import InstrumentRepository

    _register_and_login(client, "bt-owner@example.com")
    InstrumentService(db_session).seed_defaults()
    instrument_id = InstrumentRepository(db_session).search("SBIN")[0].id

    created = client.post(
        "/api/v1/backtests",
        json={
            "instrument_id": str(instrument_id), "name": "My backtest", "segment": "EQUITY_INTRADAY",
            "from_date": "2026-08-01", "to_date": "2026-08-15", "initial_capital": "100000", "quantity": 5,
        },
    )
    assert created.status_code == 201  # completes synchronously — FAILED status (no broker) is still a 201 response
    backtest_id = created.json()["id"]
    assert created.json()["status"] == "FAILED"  # no broker connected in this test — expected, not a bug

    _register_and_login(client, "bt-intruder@example.com")

    assert client.get(f"/api/v1/backtests/{backtest_id}").status_code == 404
    assert client.get(f"/api/v1/backtests/{backtest_id}/trades").status_code == 404
    assert client.delete(f"/api/v1/backtests/{backtest_id}").status_code == 404
    assert client.get("/api/v1/backtests").json() == []


def test_owner_can_cancel_pending_limit_order_but_another_user_cannot(client, db_session):
    from app.services.instrument_service import InstrumentService
    from app.repositories.instrument_repository import InstrumentRepository

    _register_and_login(client, "limit-owner@example.com")
    portfolio_id = client.post(
        "/api/v1/portfolios", json={"name": "Limit test", "virtual_capital": "100000"}
    ).json()["id"]
    InstrumentService(db_session).seed_defaults()
    instrument_id = str(InstrumentRepository(db_session).search("RELIANCE")[0].id)

    placed = client.post(
        f"/api/v1/portfolios/{portfolio_id}/orders",
        json={
            "instrument_id": instrument_id,
            "side": "BUY",
            "order_type": "LIMIT",
            "segment": "EQUITY_DELIVERY",
            "quantity": 1,
            "limit_price": "2400",
        },
    )
    assert placed.status_code == 201
    order_id = placed.json()["id"]
    assert placed.json()["status"] == "PENDING"

    _register_and_login(client, "limit-intruder@example.com")
    assert client.delete(f"/api/v1/portfolios/{portfolio_id}/orders/{order_id}").status_code == 404

    _register_and_login(client, "limit-owner@example.com")
    cancelled = client.delete(f"/api/v1/portfolios/{portfolio_id}/orders/{order_id}")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"


def test_live_portfolio_cannot_activate_or_evaluate_paper_strategy(client, db_session):
    from app.models.portfolio import Portfolio

    _register_and_login(client, "live-mode-owner@example.com")
    portfolio_id = client.post(
        "/api/v1/portfolios",
        json={"name": "Live account", "virtual_capital": "100000"},
    ).json()["id"]

    from app.services.instrument_service import InstrumentService
    from app.repositories.instrument_repository import InstrumentRepository

    InstrumentService(db_session).seed_defaults()
    instrument_id = InstrumentRepository(db_session).search("INFY")[0].id
    created = client.post(
        f"/api/v1/portfolios/{portfolio_id}/strategies",
        json={
            "instrument_id": str(instrument_id),
            "name": "Must remain inactive",
            "segment": "EQUITY_INTRADAY",
            "quantity": 1,
            "max_daily_loss": "2000",
        },
    )
    assert created.status_code == 201
    strategy_id = created.json()["id"]

    portfolio = db_session.query(Portfolio).filter(Portfolio.id == UUID(portfolio_id)).one()
    portfolio.trading_mode = "LIVE"
    portfolio.balance_source = "UNAVAILABLE"
    portfolio.virtual_capital = 0
    portfolio.cash_balance = 0
    db_session.commit()

    activation = client.post(
        f"/api/v1/portfolios/{portfolio_id}/strategies/{strategy_id}/activate"
    )
    assert activation.status_code == 409
    assert "PAPER-only" in activation.json()["detail"]

    evaluation = client.post(
        f"/api/v1/portfolios/{portfolio_id}/strategies/{strategy_id}/evaluate"
    )
    assert evaluation.status_code == 200
    assert evaluation.json()["signal"] == "HOLD"
    assert "PAPER-only" in evaluation.json()["reason"]


def test_user_can_create_separate_paper_and_live_portfolios_with_immutable_modes(client):
    _register_and_login(client, "dual-mode-owner@example.com")

    paper = client.post(
        "/api/v1/portfolios",
        json={"name": "Paper account", "virtual_capital": "100000", "trading_mode": "PAPER"},
    )
    live = client.post(
        "/api/v1/portfolios",
        json={"name": "Live account", "trading_mode": "LIVE"},
    )

    assert paper.status_code == 201
    assert live.status_code == 201
    assert paper.json()["trading_mode"] == "PAPER"
    assert live.json()["trading_mode"] == "LIVE"
    assert paper.json()["id"] != live.json()["id"]
    assert paper.json()["cash_balance"] == "100000.00"
    assert live.json()["cash_balance"] == "0.00"
    assert live.json()["virtual_capital"] == "0.00"
    assert live.json()["balance_source"] == "UNAVAILABLE"

    # The risk-settings endpoint cannot mutate a portfolio's execution mode.
    attempted_paper_switch = client.patch(
        f"/api/v1/portfolios/{paper.json()['id']}/risk-settings",
        json={"trading_mode": "LIVE"},
    )
    attempted_live_switch = client.patch(
        f"/api/v1/portfolios/{live.json()['id']}/risk-settings",
        json={"trading_mode": "PAPER"},
    )
    assert attempted_paper_switch.status_code == 200
    assert attempted_live_switch.status_code == 200
    assert attempted_paper_switch.json()["trading_mode"] == "PAPER"
    assert attempted_live_switch.json()["trading_mode"] == "LIVE"

    listed = client.get("/api/v1/portfolios")
    assert listed.status_code == 200
    modes = {item["id"]: item["trading_mode"] for item in listed.json()}
    assert modes[paper.json()["id"]] == "PAPER"
    assert modes[live.json()["id"]] == "LIVE"


def test_portfolio_creation_rejects_unknown_trading_mode(client):
    _register_and_login(client, "invalid-mode-owner@example.com")
    response = client.post(
        "/api/v1/portfolios",
        json={"name": "Invalid account", "virtual_capital": "100000", "trading_mode": "REAL"},
    )
    assert response.status_code == 422


def test_paper_positions_are_returned_and_live_positions_fail_closed_until_broker_allocation(client, db_session):
    from app.repositories.instrument_repository import InstrumentRepository
    from app.repositories.position_repository import PositionRepository
    from app.services.instrument_service import InstrumentService

    _register_and_login(client, "position-isolation@example.com")
    paper = client.post(
        "/api/v1/portfolios",
        json={"name": "Paper", "virtual_capital": "100000", "trading_mode": "PAPER"},
    )
    live = client.post(
        "/api/v1/portfolios",
        json={"name": "Live", "trading_mode": "LIVE"},
    )
    assert paper.status_code == live.status_code == 201

    InstrumentService(db_session).seed_defaults()
    instrument_id = InstrumentRepository(db_session).search("TCS")[0].id
    positions = PositionRepository(db_session)

    paper_position = positions.get_or_create(UUID(paper.json()["id"]), instrument_id)
    paper_position.quantity = 5
    paper_position.avg_price = 3500
    positions.save(paper_position)

    paper_rows = client.get(f"/api/v1/portfolios/{paper.json()['id']}/positions")
    live_rows = client.get(f"/api/v1/portfolios/{live.json()['id']}/positions")
    assert paper_rows.status_code == 200
    assert len(paper_rows.json()) == 1
    assert paper_rows.json()[0]["quantity"] == 5
    assert live_rows.status_code == 503
    assert "verified broker sync and portfolio allocation" in live_rows.json()["detail"]

def test_live_portfolio_order_submission_is_rejected_before_broker_access(client, db_session):
    from app.models.order import Order
    from app.repositories.instrument_repository import InstrumentRepository
    from app.services.instrument_service import InstrumentService

    _register_and_login(client, "live-order-denial@example.com")
    live = client.post(
        "/api/v1/portfolios",
        json={"name": "Live", "trading_mode": "LIVE"},
    )
    assert live.status_code == 201

    InstrumentService(db_session).seed_defaults()
    instrument_id = str(InstrumentRepository(db_session).search("TCS")[0].id)
    response = client.post(
        f"/api/v1/portfolios/{live.json()['id']}/orders",
        json={
            "instrument_id": instrument_id,
            "side": "BUY",
            "order_type": "MARKET",
            "segment": "EQUITY_DELIVERY",
            "quantity": 1,
        },
    )
    assert response.status_code == 400
    assert "PAPER-only" in response.json()["detail"]
    assert db_session.query(Order).filter(Order.portfolio_id == UUID(live.json()["id"])).count() == 0


def test_live_portfolio_rejects_simulated_starting_capital(client):
    _register_and_login(client, "live-capital-rejected@example.com")
    response = client.post(
        "/api/v1/portfolios",
        json={"name": "Live with fake funds", "virtual_capital": "500000", "trading_mode": "LIVE"},
    )
    assert response.status_code == 422


def test_live_portfolio_balance_is_unavailable_until_broker_sync(client):
    _register_and_login(client, "live-balance-unavailable@example.com")
    response = client.post(
        "/api/v1/portfolios",
        json={"name": "Unsynced live account", "trading_mode": "LIVE"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["balance_source"] == "UNAVAILABLE"
    assert data["cash_balance"] == "0.00"
    assert data["virtual_capital"] == "0.00"



def test_broker_allocation_requires_owned_live_portfolio_and_verified_unexpired_connection(client, db_session):
    from datetime import datetime, timedelta, timezone
    from app.models.broker_connection import BrokerConnection
    from app.models.user import User

    _register_and_login(client, "allocation-api-owner@example.com")
    live = client.post("/api/v1/portfolios", json={"name": "LIVE", "trading_mode": "LIVE"})
    paper = client.post(
        "/api/v1/portfolios",
        json={"name": "PAPER", "trading_mode": "PAPER", "virtual_capital": "100000"},
    )
    assert live.status_code == paper.status_code == 201

    connection = BrokerConnection(
        user_id=db_session.query(User).filter_by(email="allocation-api-owner@example.com").one().id,
        broker="upstox",
        api_key_encrypted="encrypted-api-key",
        api_secret_encrypted="encrypted-api-secret",
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted="encrypted-access-token",
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_connected=True,
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)

    payload = {"broker_connection_id": str(connection.id)}
    allocated = client.post(f"/api/v1/portfolios/{live.json()['id']}/broker-allocation", json=payload)
    assert allocated.status_code == 201
    assert allocated.json()["broker"] == "upstox"
    assert allocated.json()["trading_mode"] == "LIVE"
    assert "access_token" not in allocated.text
    assert client.get(f"/api/v1/portfolios/{live.json()['id']}/broker-allocation").status_code == 200

    duplicate = client.post(f"/api/v1/portfolios/{live.json()['id']}/broker-allocation", json=payload)
    assert duplicate.status_code == 409
    assert client.post(f"/api/v1/portfolios/{paper.json()['id']}/broker-allocation", json=payload).status_code == 409


def test_broker_allocation_rejects_unverified_or_expired_connection(client, db_session):
    from datetime import datetime, timedelta, timezone
    from app.models.broker_connection import BrokerConnection
    from app.models.user import User

    _register_and_login(client, "allocation-unverified@example.com")
    live = client.post("/api/v1/portfolios", json={"name": "LIVE", "trading_mode": "LIVE"})
    owner = db_session.query(User).filter_by(email="allocation-unverified@example.com").one()
    connection = BrokerConnection(
        user_id=owner.id,
        broker="upstox",
        api_key_encrypted="encrypted-api-key",
        api_secret_encrypted="encrypted-api-secret",
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted="encrypted-access-token",
        access_token_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        is_connected=True,
    )
    db_session.add(connection)
    db_session.commit()
    response = client.post(
        f"/api/v1/portfolios/{live.json()['id']}/broker-allocation",
        json={"broker_connection_id": str(connection.id)},
    )
    assert response.status_code == 409


def test_latest_broker_positions_never_exposes_snapshot_from_replaced_account(client, db_session):
    from datetime import datetime, timedelta, timezone
    from app.models.broker_connection import BrokerConnection
    from app.models.broker_position_snapshot import BrokerPositionSnapshot
    from app.models.user import User

    _register_and_login(client, "positions-reallocation@example.com")
    live = client.post("/api/v1/portfolios", json={"name": "LIVE", "trading_mode": "LIVE"})
    assert live.status_code == 201
    portfolio_id = UUID(live.json()["id"])
    owner = db_session.query(User).filter_by(email="positions-reallocation@example.com").one()

    def make_connection(broker="upstox"):
        connection = BrokerConnection(
            user_id=owner.id,
            broker=broker,
            api_key_encrypted="encrypted-api-key",
            api_secret_encrypted="encrypted-api-secret",
            redirect_uri="https://example.invalid/callback",
            access_token_encrypted="encrypted-access-token",
            access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_connected=True,
        )
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)
        return connection

    first = make_connection()
    second = make_connection("zerodha")
    first_allocation = client.post(
        f"/api/v1/portfolios/{portfolio_id}/broker-allocation",
        json={"broker_connection_id": str(first.id)},
    )
    assert first_allocation.status_code == 201

    snapshot = BrokerPositionSnapshot(
        broker_connection_id=first.id,
        portfolio_id=portfolio_id,
        user_id=owner.id,
        positions=[{"instrument_key": "NSE_EQ|INE062A01020", "quantity": 1}],
        raw_response={"status": "success", "data": []},
    )
    db_session.add(snapshot)
    from decimal import Decimal
    from app.models.broker_holding_snapshot import BrokerHoldingSnapshot
    holding_snapshot = BrokerHoldingSnapshot(
        broker_connection_id=first.id,
        portfolio_id=portfolio_id,
        user_id=owner.id,
        holdings=[{"isin": "INE528G01035", "quantity": 36, "t1_quantity": 3}],
        raw_response={"status": "success", "data": []},
    )
    db_session.add(holding_snapshot)
    from app.models.broker_funds_snapshot import BrokerFundsSnapshot
    funds_snapshot = BrokerFundsSnapshot(
        broker_connection_id=first.id,
        portfolio_id=portfolio_id,
        user_id=owner.id,
        total_available_to_trade=Decimal("1000.00"),
        cash_available_to_trade=Decimal("900.00"),
        pledge_available_to_trade=Decimal("100.00"),
        unsettled_profit_today=Decimal("0.00"),
        unsettled_profit_previous_days=Decimal("0.00"),
        raw_response={"status": "success", "data": {}},
    )
    db_session.add(funds_snapshot)
    db_session.commit()

    latest_before = client.get(f"/api/v1/portfolios/{portfolio_id}/broker-positions/latest")
    assert latest_before.status_code == 200
    assert latest_before.json()["broker_connection_id"] == str(first.id)
    funds_before = client.get(f"/api/v1/portfolios/{portfolio_id}/broker-funds/latest")
    assert funds_before.status_code == 200
    assert funds_before.json()["broker_connection_id"] == str(first.id)
    holdings_before = client.get(f"/api/v1/portfolios/{portfolio_id}/broker-holdings/latest")
    assert holdings_before.status_code == 200
    assert holdings_before.json()["broker_connection_id"] == str(first.id)

    removed = client.delete(f"/api/v1/portfolios/{portfolio_id}/broker-allocation")
    assert removed.status_code == 204
    second_allocation = client.post(
        f"/api/v1/portfolios/{portfolio_id}/broker-allocation",
        json={"broker_connection_id": str(second.id)},
    )
    assert second_allocation.status_code == 201

    latest_after = client.get(f"/api/v1/portfolios/{portfolio_id}/broker-positions/latest")
    assert latest_after.status_code == 404
    funds_after = client.get(f"/api/v1/portfolios/{portfolio_id}/broker-funds/latest")
    assert funds_after.status_code == 404
    holdings_after = client.get(f"/api/v1/portfolios/{portfolio_id}/broker-holdings/latest")
    assert holdings_after.status_code == 404


def test_live_unrealized_pnl_endpoint_is_owner_scoped_and_requires_live_allocation(client):
    _register_and_login(client, "live-pnl-owner@example.com")
    live = client.post(
        "/api/v1/portfolios",
        json={"name": "Live P&L", "trading_mode": "LIVE"},
    )
    assert live.status_code == 201
    portfolio_id = live.json()["id"]

    # No broker allocation means there is no authoritative account snapshot to value.
    unavailable = client.get(f"/api/v1/portfolios/{portfolio_id}/live-unrealized-pnl")
    assert unavailable.status_code == 404

    _register_and_login(client, "live-pnl-intruder@example.com")
    hidden = client.get(f"/api/v1/portfolios/{portfolio_id}/live-unrealized-pnl")
    assert hidden.status_code == 404


def test_live_unrealized_pnl_endpoint_rejects_paper_portfolios(client):
    _register_and_login(client, "paper-pnl-owner@example.com")
    paper = client.post(
        "/api/v1/portfolios",
        json={"name": "Paper P&L", "trading_mode": "PAPER", "virtual_capital": "100000"},
    )
    assert paper.status_code == 201

    response = client.get(
        f"/api/v1/portfolios/{paper.json()['id']}/live-unrealized-pnl"
    )
    assert response.status_code == 409


def test_live_unrealized_pnl_returns_503_when_redis_is_unavailable(client, db_session, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from app.models.broker_connection import BrokerConnection
    from app.models.broker_position_snapshot import BrokerPositionSnapshot
    from app.models.user import User
    import app.api.v1.portfolios as portfolios_api

    _register_and_login(client, "live-pnl-redis-owner@example.com")
    live = client.post(
        "/api/v1/portfolios",
        json={"name": "LIVE Redis outage", "trading_mode": "LIVE"},
    )
    assert live.status_code == 201
    portfolio_id = UUID(live.json()["id"])
    owner = db_session.query(User).filter_by(email="live-pnl-redis-owner@example.com").one()
    connection = BrokerConnection(
        user_id=owner.id,
        broker="upstox",
        api_key_encrypted="encrypted-api-key",
        api_secret_encrypted="encrypted-api-secret",
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted="encrypted-access-token",
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_connected=True,
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)
    allocated = client.post(
        f"/api/v1/portfolios/{portfolio_id}/broker-allocation",
        json={"broker_connection_id": str(connection.id)},
    )
    assert allocated.status_code == 201
    db_session.add(BrokerPositionSnapshot(
        broker_connection_id=connection.id,
        portfolio_id=portfolio_id,
        user_id=owner.id,
        positions=[{
            "instrument_key": "NSE_EQ|INE062A01020",
            "quantity": 1,
            "average_price": "100.00",
        }],
        raw_response={"status": "success", "data": []},
    ))
    db_session.commit()

    class UnavailableRedis:
        async def ping(self):
            raise OSError("Redis is unavailable")

        async def aclose(self):
            return None

    monkeypatch.setattr(
        portfolios_api,
        "from_url",
        lambda *args, **kwargs: UnavailableRedis(),
    )
    response = client.get(f"/api/v1/portfolios/{portfolio_id}/live-unrealized-pnl")
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


def test_live_unrealized_pnl_rejects_stale_broker_position_snapshot(client, db_session, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from app.models.broker_connection import BrokerConnection
    from app.models.broker_position_snapshot import BrokerPositionSnapshot
    from app.models.user import User
    import app.api.v1.portfolios as portfolios_api

    _register_and_login(client, "live-pnl-stale-owner@example.com")
    live = client.post(
        "/api/v1/portfolios",
        json={"name": "LIVE stale snapshot", "trading_mode": "LIVE"},
    )
    assert live.status_code == 201
    portfolio_id = UUID(live.json()["id"])
    owner = db_session.query(User).filter_by(email="live-pnl-stale-owner@example.com").one()
    connection = BrokerConnection(
        user_id=owner.id,
        broker="upstox",
        api_key_encrypted="encrypted-api-key",
        api_secret_encrypted="encrypted-api-secret",
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted="encrypted-access-token",
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_connected=True,
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)
    allocated = client.post(
        f"/api/v1/portfolios/{portfolio_id}/broker-allocation",
        json={"broker_connection_id": str(connection.id)},
    )
    assert allocated.status_code == 201
    db_session.add(BrokerPositionSnapshot(
        broker_connection_id=connection.id,
        portfolio_id=portfolio_id,
        user_id=owner.id,
        positions=[{
            "instrument_key": "NSE_EQ|INE062A01020",
            "quantity": 1,
            "average_price": "100.00",
        }],
        raw_response={"status": "success", "data": []},
        created_at=datetime.now(timezone.utc) - timedelta(seconds=121),
    ))
    db_session.commit()

    def redis_must_not_be_opened(*args, **kwargs):
        raise AssertionError("stale broker snapshots must be rejected before Redis reads")

    monkeypatch.setattr(portfolios_api, "from_url", redis_must_not_be_opened)
    response = client.get(f"/api/v1/portfolios/{portfolio_id}/live-unrealized-pnl")
    assert response.status_code == 503
    assert "snapshot is stale" in response.json()["detail"]


def test_live_unrealized_pnl_api_uses_real_user_scoped_redis_snapshot(client, db_session):
    import asyncio
    import time
    from datetime import datetime, timedelta, timezone
    from redis.asyncio import from_url
    from app.core.config import settings
    from app.models.broker_connection import BrokerConnection
    from app.models.broker_position_snapshot import BrokerPositionSnapshot
    from app.models.user import User
    from app.services.redis_market_quote_publisher import RedisMarketQuotePublisher
    from app.services.upstox_market_data_streamer import MarketTick

    _register_and_login(client, "live-pnl-redis-integration@example.com")
    live = client.post(
        "/api/v1/portfolios",
        json={"name": "LIVE Redis integration", "trading_mode": "LIVE"},
    )
    assert live.status_code == 201
    portfolio_id = UUID(live.json()["id"])
    owner = db_session.query(User).filter_by(
        email="live-pnl-redis-integration@example.com"
    ).one()
    connection = BrokerConnection(
        user_id=owner.id,
        broker="upstox",
        api_key_encrypted="encrypted-api-key",
        api_secret_encrypted="encrypted-api-secret",
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted="encrypted-access-token",
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_connected=True,
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)
    allocated = client.post(
        f"/api/v1/portfolios/{portfolio_id}/broker-allocation",
        json={"broker_connection_id": str(connection.id)},
    )
    assert allocated.status_code == 201

    instrument_key = "NSE_EQ|INE062A01020"
    snapshot_time = datetime.now(timezone.utc)
    db_session.add(BrokerPositionSnapshot(
        broker_connection_id=connection.id,
        portfolio_id=portfolio_id,
        user_id=owner.id,
        positions=[{
            "instrument_key": instrument_key,
            "quantity": 2,
            "average_price": "100.00",
        }],
        raw_response={"status": "success", "data": []},
        created_at=snapshot_time,
    ))
    db_session.commit()

    async def publish_real_quote():
        redis_client = from_url(settings.REDIS_URL, decode_responses=True)
        publisher = RedisMarketQuotePublisher(redis_client, owner.id, ttl_seconds=15)
        tick = MarketTick(
            instrument_key=instrument_key,
            ltp=120.0,
            exchange_timestamp_ms=int(snapshot_time.timestamp() * 1000),
            received_at=snapshot_time,
            received_monotonic=time.monotonic(),
        )
        try:
            assert await publisher.publish(tick) is True
        finally:
            await redis_client.aclose()

    asyncio.run(publish_real_quote())
    response = client.get(f"/api/v1/portfolios/{portfolio_id}/live-unrealized-pnl")
    assert response.status_code == 200
    payload = response.json()
    assert payload["complete"] is True
    assert payload["unavailable_position_count"] == 0
    assert payload["total_unrealized_pnl"] == "40.00"
    assert payload["rows"][0]["instrument_key"] == instrument_key
    assert payload["rows"][0]["status"] == "AVAILABLE"

    async def remove_test_quote():
        redis_client = from_url(settings.REDIS_URL, decode_responses=True)
        publisher = RedisMarketQuotePublisher(redis_client, owner.id)
        try:
            key = publisher.snapshot_key(instrument_key)
            await redis_client.delete(key, f"{key}:version")
        finally:
            await redis_client.aclose()

    asyncio.run(remove_test_quote())


def test_user_cannot_access_another_users_broker_evidence_or_reconciliation(client, db_session):
    from decimal import Decimal
    from uuid import uuid4

    from app.models.broker_charge_evidence import BrokerChargeEvidence
    from app.models.broker_charge_source_component import BrokerChargeSourceComponent
    from app.models.broker_connection import BrokerConnection
    from app.models.live_order_records import LiveReconciliationIssue, LiveReconciliationRun
    from app.models.user import User

    _register_and_login(client, "resource-owner@example.com")
    owner = db_session.query(User).filter_by(email="resource-owner@example.com").one()
    connection = BrokerConnection(
        user_id=owner.id,
        broker="upstox",
        api_key_encrypted="test-encrypted-api-key",
        api_secret_encrypted="test-encrypted-api-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=False,
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)

    evidence_id = uuid4()
    evidence = BrokerChargeEvidence(
        id=evidence_id,
        broker_connection_id=connection.id,
        source_kind="CONTRACT_NOTE",
        broker_report_reference="owner-only-report",
        source_filename="contract-note.pdf",
        storage_key="opaque-test-storage-key",
        source_sha256="a" * 64,
        byte_size=128,
        received_by_user_id=owner.id,
        status="RECEIVED",
    )
    component = BrokerChargeSourceComponent(
        evidence_id=evidence_id,
        source_sha256="a" * 64,
        component_name="brokerage",
        revision=1,
        source_amount=Decimal("1.00"),
        currency="INR",
        extraction_method="MANUAL_TRANSCRIPTION",
        parser_version="manual-transcription-v1",
        source_locator="page 1, row 1",
        extracted_by_user_id=owner.id,
        status="PENDING_REVIEW",
    )
    run = LiveReconciliationRun(
        user_id=owner.id,
        broker_connection_id=connection.id,
        status="COMPLETED",
        summary={"orders_seen": 1},
    )
    db_session.add(run)
    db_session.flush()
    issue = LiveReconciliationIssue(
        user_id=owner.id,
        broker_connection_id=connection.id,
        run_id=run.id,
        issue_type="UNMATCHED_BROKER_ORDER",
        fingerprint="b" * 64,
        safe_details={"reason": "manual review required"},
        status="OPEN",
        occurrence_count=1,
    )
    db_session.add_all([evidence, component, run, issue])
    db_session.commit()

    _register_and_login(client, "resource-intruder@example.com")

    # Uploading against another user's broker connection and accessing its
    # stored document/source components must all fail without disclosing ownership.
    upload = client.post(
        f"/api/v1/broker-charge-evidence/connections/{connection.id}/contract-notes",
        data={"broker_report_reference": "intruder-upload-attempt"},
        files={"file": ("contract-note.pdf", b"not a real contract note", "application/pdf")},
    )
    assert upload.status_code == 404
    assert client.get(f"/api/v1/broker-charge-evidence/{evidence_id}/document").status_code == 404
    assert client.post(
        f"/api/v1/broker-charge-evidence/{evidence_id}/components",
        json={
            "component_name": "brokerage",
            "source_amount": "1.00",
            "currency": "INR",
            "source_locator": "page 1, row 1",
        },
    ).status_code == 404
    assert client.post(
        f"/api/v1/broker-charge-evidence/{evidence_id}/components/{component.id}/review",
        json={
            "confirm_source_matches": True,
            "eligible_fill_record_ids": [str(uuid4())],
            "allocation_basis": "EXPLICIT_REVIEWED",
        },
    ).status_code == 404
    assert client.post(
        f"/api/v1/broker-charge-evidence/{evidence_id}/components/{component.id}/reject",
        json={"confirm_source_matches": True, "review_note": "not authorized"},
    ).status_code == 404

    # Reconciliation queries must not disclose another user's runs or issues,
    # even when the caller supplies that user's broker_connection_id.
    runs = client.get(
        "/api/v1/reconciliation/runs",
        params={"broker_connection_id": str(connection.id)},
    )
    issues = client.get(
        "/api/v1/reconciliation/issues",
        params={"broker_connection_id": str(connection.id)},
    )
    assert runs.status_code == 200
    assert runs.json() == []
    assert issues.status_code == 200
    assert issues.json() == []

    # Broker settings expose only the authenticated user's own connections.
    connections = client.get("/api/v1/settings/broker")
    assert connections.status_code == 200
    assert connections.json() == []
