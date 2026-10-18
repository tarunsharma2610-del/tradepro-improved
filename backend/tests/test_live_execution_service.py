from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.core.config import settings
from app.models.broker_connection import BrokerConnection
from app.models.execution import Execution
from app.models.order import Order
from app.models.position import Position
from app.models.broker_trade_record import BrokerTradeRecord
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.instrument_service import InstrumentService
from app.services.live_execution_service import (
    LiveExecutionBlocked,
    LiveExecutionService,
    LiveOrderIntent,
    LiveRiskDecision,
)


@pytest.fixture()
def live_context(db_session, make_user):
    user = make_user()
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id, name="Live preflight", virtual_capital=Decimal("100000")
    )
    InstrumentService(db_session).seed_defaults()
    instrument = InstrumentRepository(db_session).search("RELIANCE")[0]
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted="encrypted-token",
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_connected=True,
    )
    db_session.add(connection)
    db_session.commit()
    return user, portfolio, instrument, connection


def _enable_preflight(monkeypatch):
    monkeypatch.setattr(settings, "TRADING_MODE", "LIVE")
    monkeypatch.setattr(settings, "LIVE_ORDER_SUBMISSION_ENABLED", True)
    monkeypatch.setattr(settings, "AUTOMATED_ENTRIES_ENABLED", True)
    monkeypatch.setattr(
        BrokerCredentialsService, "get_access_token", lambda self, user_id, broker: "test-access-token"
    )


def _intent(portfolio, instrument, **overrides):
    values = {
        "portfolio_id": portfolio.id,
        "instrument_id": instrument.id,
        "side": "BUY",
        "order_type": "MARKET",
        "segment": "EQUITY_DELIVERY",
        "quantity": 2,
    }
    values.update(overrides)
    return LiveOrderIntent(**values)


def _approved_gate():
    return lambda _user_id, _portfolio, _instrument, _intent: LiveRiskDecision(allowed=True)


def test_default_off_interlock_blocks_before_credentials_or_risk_gate(
    db_session, live_context, monkeypatch
):
    user, portfolio, instrument, _connection = live_context
    monkeypatch.setattr(settings, "TRADING_MODE", "LIVE")
    monkeypatch.setattr(settings, "LIVE_ORDER_SUBMISSION_ENABLED", False)
    token_lookup = Mock(side_effect=AssertionError("credentials must not be read"))
    risk_gate = Mock(side_effect=AssertionError("risk gate must not run"))
    monkeypatch.setattr(BrokerCredentialsService, "get_access_token", token_lookup)

    with pytest.raises(LiveExecutionBlocked, match="LIVE_ORDER_SUBMISSION_ENABLED is off"):
        LiveExecutionService(db_session, risk_gate=risk_gate).preflight(
            user.id, _intent(portfolio, instrument), user_confirmed=True
        )

    token_lookup.assert_not_called()
    risk_gate.assert_not_called()
    assert db_session.query(Order).count() == 0


def test_non_live_trading_mode_blocks_even_when_interlock_is_on(
    db_session, live_context, monkeypatch
):
    user, portfolio, instrument, _connection = live_context
    monkeypatch.setattr(settings, "TRADING_MODE", "PAPER")
    monkeypatch.setattr(settings, "LIVE_ORDER_SUBMISSION_ENABLED", True)

    with pytest.raises(LiveExecutionBlocked, match="TRADING_MODE must be LIVE"):
        LiveExecutionService(db_session, risk_gate=_approved_gate()).preflight(
            user.id, _intent(portfolio, instrument), user_confirmed=True
        )
    assert db_session.query(Order).count() == 0


def test_missing_risk_gate_blocks_even_with_environment_interlocks(
    db_session, live_context, monkeypatch
):
    user, portfolio, instrument, _connection = live_context
    _enable_preflight(monkeypatch)

    with pytest.raises(LiveExecutionBlocked, match="No reviewed account-wide live risk gate"):
        LiveExecutionService(db_session).preflight(
            user.id, _intent(portfolio, instrument), user_confirmed=True
        )
    assert db_session.query(Order).count() == 0


def test_explicit_user_confirmation_is_required(db_session, live_context, monkeypatch):
    user, portfolio, instrument, _connection = live_context
    _enable_preflight(monkeypatch)

    with pytest.raises(LiveExecutionBlocked, match="Explicit user confirmation"):
        LiveExecutionService(db_session, risk_gate=_approved_gate()).preflight(
            user.id, _intent(portfolio, instrument)
        )
    assert db_session.query(Order).count() == 0


def test_preflight_returns_non_secret_plan_without_order_or_accounting_side_effects(
    db_session, live_context, monkeypatch
):
    user, portfolio, instrument, connection = live_context
    _enable_preflight(monkeypatch)
    before_cash = Decimal(str(portfolio.cash_balance))
    plan = LiveExecutionService(db_session, risk_gate=_approved_gate()).preflight(
        user.id,
        _intent(portfolio, instrument, order_type="LIMIT", limit_price="123.4500"),
        user_confirmed=True,
    )

    assert plan.user_id == user.id
    assert plan.portfolio_id == portfolio.id
    assert plan.broker_connection_id == connection.id
    assert plan.instrument_key == instrument.instrument_key
    assert plan.limit_price == Decimal("123.4500")
    assert not hasattr(plan, "access_token")
    assert db_session.query(Order).count() == 0
    assert db_session.query(Execution).count() == 0
    assert db_session.query(Position).count() == 0
    assert db_session.query(BrokerTradeRecord).count() == 0
    db_session.refresh(portfolio)
    assert Decimal(str(portfolio.cash_balance)) == before_cash


def test_risk_gate_rejection_fails_closed(db_session, live_context, monkeypatch):
    user, portfolio, instrument, _connection = live_context
    _enable_preflight(monkeypatch)
    gate = lambda *_args: LiveRiskDecision(allowed=False, reason="account exposure limit reached")

    with pytest.raises(LiveExecutionBlocked, match="account exposure limit reached"):
        LiveExecutionService(db_session, risk_gate=gate).preflight(
            user.id, _intent(portfolio, instrument), user_confirmed=True
        )
    assert db_session.query(Order).count() == 0


def test_risk_gate_exception_fails_closed(db_session, live_context, monkeypatch):
    user, portfolio, instrument, _connection = live_context
    _enable_preflight(monkeypatch)
    gate = Mock(side_effect=RuntimeError("risk service unavailable"))

    with pytest.raises(LiveExecutionBlocked, match="risk gate failed"):
        LiveExecutionService(db_session, risk_gate=gate).preflight(
            user.id, _intent(portfolio, instrument), user_confirmed=True
        )
    gate.assert_called_once()
    assert db_session.query(Order).count() == 0


def test_foreign_portfolio_is_not_visible_to_user(db_session, live_context, make_user, monkeypatch):
    _owner, portfolio, instrument, _connection = live_context
    stranger = make_user(email="live-preflight-stranger@example.com")
    _enable_preflight(monkeypatch)

    with pytest.raises(LiveExecutionBlocked, match="Portfolio not found"):
        LiveExecutionService(db_session, risk_gate=_approved_gate()).preflight(
            stranger.id, _intent(portfolio, instrument), user_confirmed=True
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"side": "BUYISH"}, "Side must be BUY or SELL"),
        ({"quantity": True}, "positive integer"),
        ({"quantity": 0}, "positive integer"),
        ({"order_type": "STOP"}, "Order type"),
        ({"segment": "OPTIONS"}, "Only verified equity"),
        ({"segment": []}, "Only verified equity"),
        ({"execution_reason": []}, "Unsupported execution reason"),
        ({"order_type": "LIMIT"}, "LIMIT orders require"),
        ({"order_type": "LIMIT", "limit_price": "NaN"}, "valid positive amount"),
        ({"order_type": "MARKET", "limit_price": Decimal("10")}, "must not include"),
    ],
)
def test_invalid_live_intents_are_rejected_before_risk_gate(
    db_session, live_context, monkeypatch, overrides, message
):
    user, portfolio, instrument, _connection = live_context
    _enable_preflight(monkeypatch)
    gate = Mock(return_value=LiveRiskDecision(allowed=True))

    with pytest.raises(LiveExecutionBlocked, match=message):
        LiveExecutionService(db_session, risk_gate=gate).preflight(
            user.id, _intent(portfolio, instrument, **overrides), user_confirmed=True
        )
    gate.assert_not_called()
    assert db_session.query(Order).count() == 0


def test_unverified_connection_or_unusable_token_blocks(db_session, live_context, monkeypatch):
    user, portfolio, instrument, connection = live_context
    _enable_preflight(monkeypatch)
    connection.is_connected = False
    db_session.commit()

    with pytest.raises(LiveExecutionBlocked, match="No verified Upstox connection"):
        LiveExecutionService(db_session, risk_gate=_approved_gate()).preflight(
            user.id, _intent(portfolio, instrument), user_confirmed=True
        )

    connection.is_connected = True
    db_session.commit()
    monkeypatch.setattr(BrokerCredentialsService, "get_access_token", lambda *_args: None)
    with pytest.raises(LiveExecutionBlocked, match="missing, expired, or unusable"):
        LiveExecutionService(db_session, risk_gate=_approved_gate()).preflight(
            user.id, _intent(portfolio, instrument), user_confirmed=True
        )
    assert db_session.query(Order).count() == 0


def test_strategy_intent_requires_strategy_id_and_automation_enabled(
    db_session, live_context, monkeypatch
):
    user, portfolio, instrument, _connection = live_context
    _enable_preflight(monkeypatch)

    with pytest.raises(LiveExecutionBlocked, match="strategy_id"):
        LiveExecutionService(db_session, risk_gate=_approved_gate()).preflight(
            user.id,
            _intent(portfolio, instrument, execution_reason="STRATEGY"),
            user_confirmed=True,
        )

    monkeypatch.setattr(settings, "AUTOMATED_ENTRIES_ENABLED", False)
    with pytest.raises(LiveExecutionBlocked, match="Automated entries are disabled"):
        LiveExecutionService(db_session, risk_gate=_approved_gate()).preflight(
            user.id,
            _intent(
                portfolio,
                instrument,
                execution_reason="STRATEGY",
                strategy_id=instrument.id,
            ),
            user_confirmed=True,
        )
    assert db_session.query(Order).count() == 0
