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
        json={"name": "Live account", "virtual_capital": "250000", "trading_mode": "LIVE"},
    )

    assert paper.status_code == 201
    assert live.status_code == 201
    assert paper.json()["trading_mode"] == "PAPER"
    assert live.json()["trading_mode"] == "LIVE"
    assert paper.json()["id"] != live.json()["id"]
    assert paper.json()["cash_balance"] == "100000.00"
    assert live.json()["cash_balance"] == "250000.00"

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


def test_paper_and_live_positions_are_isolated_by_portfolio(client, db_session):
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
        json={"name": "Live", "virtual_capital": "250000", "trading_mode": "LIVE"},
    )
    assert paper.status_code == live.status_code == 201

    InstrumentService(db_session).seed_defaults()
    instrument_id = InstrumentRepository(db_session).search("TCS")[0].id
    positions = PositionRepository(db_session)

    paper_position = positions.get_or_create(UUID(paper.json()["id"]), instrument_id)
    paper_position.quantity = 5
    paper_position.avg_price = 3500
    positions.save(paper_position)

    live_position = positions.get_or_create(UUID(live.json()["id"]), instrument_id)
    live_position.quantity = 9
    live_position.avg_price = 3600
    positions.save(live_position)

    paper_rows = client.get(f"/api/v1/portfolios/{paper.json()['id']}/positions")
    live_rows = client.get(f"/api/v1/portfolios/{live.json()['id']}/positions")
    assert paper_rows.status_code == live_rows.status_code == 200
    assert len(paper_rows.json()) == len(live_rows.json()) == 1
    assert paper_rows.json()[0]["quantity"] == 5
    assert live_rows.json()[0]["quantity"] == 9


def test_live_portfolio_order_submission_is_rejected_before_broker_access(client, db_session):
    from app.models.order import Order
    from app.repositories.instrument_repository import InstrumentRepository
    from app.services.instrument_service import InstrumentService

    _register_and_login(client, "live-order-denial@example.com")
    live = client.post(
        "/api/v1/portfolios",
        json={"name": "Live", "virtual_capital": "100000", "trading_mode": "LIVE"},
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
