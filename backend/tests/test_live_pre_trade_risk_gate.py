from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.core.config import settings
from app.models.broker_connection import BrokerConnection
from app.models.order import Order
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.instrument_service import InstrumentService
from app.services.live_execution_service import LiveOrderIntent
from app.services.live_pre_trade_risk_gate import (
    AccountWideLiveRiskGate,
    BrokerFundsSnapshot,
    BrokerMarginSnapshot,
    BrokerPositionSnapshot,
    LiveQuoteSnapshot,
)


@pytest.fixture()
def risk_context(db_session, make_user, monkeypatch):
    user = make_user()
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id, name="Risk gate", virtual_capital=Decimal("100000")
    )
    InstrumentService(db_session).seed_defaults()
    instrument = InstrumentRepository(db_session).search("RELIANCE")[0]
    db_session.add(BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted="encrypted-token",
        access_token_expires_at=datetime(2026, 10, 19, 18, 0, tzinfo=timezone.utc),
        is_connected=True,
    ))
    db_session.commit()
    now = datetime(2026, 10, 19, 5, 0, tzinfo=timezone.utc)  # Monday, 10:30 IST
    monkeypatch.setattr(settings, "LIVE_MAX_ORDER_VALUE_INR", Decimal("10000"))
    monkeypatch.setattr(settings, "LIVE_MAX_GROSS_EXPOSURE_INR", Decimal("50000"))
    monkeypatch.setattr(settings, "LIVE_MAX_DAILY_LOSS_INR", Decimal("1000"))
    monkeypatch.setattr(settings, "LIVE_MAX_ORDERS_PER_UTC_DAY", 10)
    monkeypatch.setattr(settings, "LIVE_MAX_MARKET_DATA_AGE_SECONDS", 5)
    return user, portfolio, instrument, now


def _intent(portfolio, instrument, **overrides):
    values = dict(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        side="BUY",
        order_type="MARKET",
        segment="EQUITY_DELIVERY",
        quantity=2,
    )
    values.update(overrides)
    return LiveOrderIntent(**values)


def _gate(db_session, user, instrument, now, *, quote=None, positions=(), funds=None, margin=None):
    quote = quote or LiveQuoteSnapshot(Decimal("100"), now)
    funds = funds or BrokerFundsSnapshot(Decimal("100000"), now)
    margin = margin or BrokerMarginSnapshot(Decimal("200"), now)
    return AccountWideLiveRiskGate(
        db_session,
        quote_provider=lambda _uid, requested: quote,
        positions_provider=lambda _uid: positions,
        funds_provider=lambda _uid: funds,
        margin_provider=lambda _uid, _instrument, _intent, _value: margin,
        clock=lambda: now,
    )


def test_account_wide_gate_allows_only_with_fresh_broker_snapshots(
    db_session, risk_context
):
    user, portfolio, instrument, now = risk_context
    gate = _gate(db_session, user, instrument, now)

    result = gate(user.id, portfolio, instrument, _intent(portfolio, instrument))

    assert result.allowed is True
    assert "passed" in result.reason.lower()


def test_missing_broker_positions_provider_fails_closed(db_session, risk_context):
    user, portfolio, instrument, now = risk_context
    gate = AccountWideLiveRiskGate(
        db_session,
        quote_provider=lambda *_: LiveQuoteSnapshot(Decimal("100"), now),
        positions_provider=None,
        funds_provider=lambda *_: BrokerFundsSnapshot(Decimal("100000"), now),
        margin_provider=lambda *_: BrokerMarginSnapshot(Decimal("200"), now),
        clock=lambda: now,
    )

    result = gate(user.id, portfolio, instrument, _intent(portfolio, instrument))

    assert not result.allowed
    assert "providers are all required" in result.reason


def test_market_closed_blocks_before_external_snapshot_calls(db_session, risk_context):
    user, portfolio, instrument, now = risk_context
    closed = datetime(2026, 10, 19, 11, 0, tzinfo=timezone.utc)  # 16:30 IST
    called = []
    gate = AccountWideLiveRiskGate(
        db_session,
        quote_provider=lambda *_: called.append("quote"),
        positions_provider=lambda *_: called.append("positions"),
        funds_provider=lambda *_: called.append("funds"),
        margin_provider=lambda *_: called.append("margin"),
        clock=lambda: closed,
    )

    result = gate(user.id, portfolio, instrument, _intent(portfolio, instrument))

    assert not result.allowed
    assert "market session is closed" in result.reason
    assert called == []


def test_stale_quote_blocks(db_session, risk_context):
    user, portfolio, instrument, now = risk_context
    stale = LiveQuoteSnapshot(Decimal("100"), now - timedelta(seconds=6))
    gate = _gate(db_session, user, instrument, now, quote=stale)

    result = gate(user.id, portfolio, instrument, _intent(portfolio, instrument))

    assert not result.allowed
    assert "stale" in result.reason.lower()


def test_account_wide_broker_exposure_limit_blocks(db_session, risk_context):
    user, portfolio, instrument, now = risk_context
    position = BrokerPositionSnapshot(
        instrument_key="NSE_EQ|OTHER",
        quantity=600,
        market_price=Decimal("100"),
        observed_at=now,
    )
    gate = _gate(db_session, user, instrument, now, positions=(position,))

    result = gate(user.id, portfolio, instrument, _intent(portfolio, instrument))

    assert not result.allowed
    assert "gross exposure" in result.reason.lower()


def test_stale_broker_position_snapshot_blocks(db_session, risk_context):
    user, portfolio, instrument, now = risk_context
    position = BrokerPositionSnapshot(
        instrument_key="NSE_EQ|OTHER",
        quantity=1,
        market_price=Decimal("100"),
        observed_at=now - timedelta(seconds=20),
    )
    gate = _gate(db_session, user, instrument, now, positions=(position,))

    result = gate(user.id, portfolio, instrument, _intent(portfolio, instrument))

    assert not result.allowed
    assert "stale" in result.reason.lower()


def test_order_value_cap_blocks(db_session, risk_context):
    user, portfolio, instrument, now = risk_context
    gate = _gate(db_session, user, instrument, now)

    result = gate(
        user.id, portfolio, instrument,
        _intent(portfolio, instrument, quantity=101),
    )

    assert not result.allowed
    assert "order-value limit" in result.reason.lower()


def test_broker_margin_greater_than_available_cash_blocks(db_session, risk_context):
    user, portfolio, instrument, now = risk_context
    gate = _gate(
        db_session, user, instrument, now,
        funds=BrokerFundsSnapshot(Decimal("100"), now),
        margin=BrokerMarginSnapshot(Decimal("200"), now),
    )

    result = gate(user.id, portfolio, instrument, _intent(portfolio, instrument))

    assert not result.allowed
    assert "below estimated required margin" in result.reason.lower()


def test_invalid_broker_margin_snapshot_fails_closed(db_session, risk_context):
    user, portfolio, instrument, now = risk_context
    gate = _gate(
        db_session, user, instrument, now,
        margin=BrokerMarginSnapshot(Decimal("-1"), now),
    )

    result = gate(user.id, portfolio, instrument, _intent(portfolio, instrument))

    assert not result.allowed
    assert "required margin is invalid" in result.reason.lower()


def test_account_wide_live_order_frequency_limit_blocks(db_session, risk_context):
    user, portfolio, instrument, now = risk_context
    for index in range(10):
        db_session.add(Order(
            portfolio_id=portfolio.id,
            instrument_id=instrument.id,
            side="BUY",
            order_type="LIMIT",
            segment="EQUITY_DELIVERY",
            quantity=1,
            limit_price=Decimal("100"),
            status="CANCELLED",
            trading_mode="LIVE",
            execution_reason="MANUAL",
            idempotency_key=f"risk-frequency-{index}",
            placed_at=now - timedelta(minutes=index),
        ))
    db_session.commit()
    gate = _gate(db_session, user, instrument, now)

    result = gate(user.id, portfolio, instrument, _intent(portfolio, instrument))

    assert not result.allowed
    assert "frequency limit" in result.reason.lower()


def test_provider_exception_fails_closed_without_propagating(db_session, risk_context):
    user, portfolio, instrument, now = risk_context
    gate = AccountWideLiveRiskGate(
        db_session,
        quote_provider=lambda *_: (_ for _ in ()).throw(RuntimeError("provider down")),
        positions_provider=lambda *_: (),
        funds_provider=lambda *_: BrokerFundsSnapshot(Decimal("100000"), now),
        margin_provider=lambda *_: BrokerMarginSnapshot(Decimal("200"), now),
        clock=lambda: now,
    )

    result = gate(user.id, portfolio, instrument, _intent(portfolio, instrument))

    assert not result.allowed
    assert "quote lookup failed" in result.reason.lower()
