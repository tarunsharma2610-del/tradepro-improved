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


def test_unsupported_derivative_segments_are_rejected_at_api_boundaries(client, db_session):
    """Equity-only master data must never be priced/accounted as F&O."""
    from app.models.backtest import BacktestRun
    from app.models.order import Order
    from app.models.strategy import Strategy
    from app.repositories.instrument_repository import InstrumentRepository
    from app.services.instrument_service import InstrumentService

    _register_and_login(client, "unsupported-segment@example.com")
    portfolio_id = client.post(
        "/api/v1/portfolios", json={"name": "Equity only", "virtual_capital": "100000"}
    ).json()["id"]
    InstrumentService(db_session).seed_defaults()
    instrument_id = str(InstrumentRepository(db_session).search("RELIANCE")[0].id)

    order_response = client.post(
        f"/api/v1/portfolios/{portfolio_id}/orders",
        json={
            "instrument_id": instrument_id, "side": "BUY", "order_type": "MARKET",
            "segment": "FUTURES", "quantity": 1,
        },
    )
    strategy_response = client.post(
        f"/api/v1/portfolios/{portfolio_id}/strategies",
        json={
            "instrument_id": instrument_id, "name": "Invalid options strategy",
            "segment": "OPTIONS", "quantity": 1, "max_daily_loss": "1000",
        },
    )
    backtest_response = client.post(
        "/api/v1/backtests",
        json={
            "instrument_id": instrument_id, "name": "Invalid futures backtest",
            "segment": "FUTURES", "from_date": "2026-08-01", "to_date": "2026-08-15",
            "initial_capital": "100000", "quantity": 1,
        },
    )

    assert order_response.status_code == 400
    assert "Futures and options are not enabled" in order_response.json()["detail"]
    assert strategy_response.status_code == 400
    assert backtest_response.status_code == 400
    assert db_session.query(Order).filter(Order.portfolio_id == portfolio_id).count() == 0
    assert db_session.query(Strategy).filter(Strategy.portfolio_id == portfolio_id).count() == 0
    assert db_session.query(BacktestRun).count() == 0
