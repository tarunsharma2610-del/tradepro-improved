from contextlib import ExitStack
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.brokers.base import BrokerCallResult
from app.core.encryption import encrypt_value
from app.models.backtest import BacktestRun
from app.services.backtest_service import BacktestService
from app.services.instrument_service import InstrumentService


@pytest.fixture()
def instrument(db_session):
    InstrumentService(db_session).seed_defaults()
    from app.repositories.instrument_repository import InstrumentRepository

    return InstrumentRepository(db_session).search("TCS")[0]


def _connect_fake_broker(db_session, user_id):
    from app.models.broker_connection import BrokerConnection

    conn = BrokerConnection(
        user_id=user_id, broker="upstox",
        api_key_encrypted=encrypt_value("k"), api_secret_encrypted=encrypt_value("s"),
        redirect_uri="https://example.com/cb", access_token_encrypted=encrypt_value("tok"),
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1), is_connected=True,
    )
    db_session.add(conn)
    db_session.commit()


def _make_run(db_session, user_id, instrument_id, **overrides) -> BacktestRun:
    defaults = dict(
        user_id=user_id, instrument_id=instrument_id, name="Test backtest", segment="EQUITY_INTRADAY",
        from_date=date(2026, 8, 1), to_date=date(2026, 8, 15), initial_capital=Decimal("100000"), quantity=5,
        rsi_weight=Decimal("0"), sma_crossover_weight=Decimal("0"), macd_weight=Decimal("0"),
        volume_spike_weight=Decimal("0"), momentum_weight=Decimal("1"),
        entry_score_threshold=Decimal("0.3"), exit_score_threshold=Decimal("-0.3"),
        trailing_stop_pct=Decimal("50"), slippage_bps=Decimal("5"), status="PENDING",
    )
    defaults.update(overrides)
    run = BacktestRun(**defaults)
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def _candles_response(prices: list[float]):
    """Build documented newest-first V3 rows with valid offset-aware timestamps."""
    newest_first = list(reversed(prices))
    latest = datetime(2026, 8, 15, 15, 15, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    candles = [
        [
            (latest - timedelta(minutes=5 * i)).isoformat(),
            p, p, p, p, 10000, 0,
        ]
        for i, p in enumerate(newest_first)
    ]
    return BrokerCallResult(ok=True, data={"status": "success", "data": {"candles": candles}})


def _mock_historical_data(candles_result: BrokerCallResult):
    fake_adapter = type("FakeAdapter", (), {"get_historical_data": AsyncMock(return_value=candles_result)})()
    stack = ExitStack()
    stack.enter_context(patch("app.services.backtest_service.get_broker_adapter", return_value=fake_adapter))
    return stack


@pytest.mark.asyncio
async def test_no_connected_broker_fails_cleanly(db_session, make_user, instrument):
    user = make_user()
    run = _make_run(db_session, user.id, instrument.id)

    result = await BacktestService(db_session).run(user.id, run, instrument)

    assert result.status == "FAILED"
    assert "broker" in result.error_message.lower()


@pytest.mark.asyncio
async def test_insufficient_candle_history_fails_with_a_clear_reason(db_session, make_user, instrument):
    user = make_user()
    _connect_fake_broker(db_session, user.id)
    run = _make_run(db_session, user.id, instrument.id)

    with _mock_historical_data(_candles_response([100.0, 101.0, 102.0])):
        result = await BacktestService(db_session).run(user.id, run, instrument)

    assert result.status == "FAILED"
    assert "candles" in result.error_message.lower()


@pytest.mark.asyncio
async def test_full_round_trip_backtest_persists_run_and_trades(db_session, make_user, instrument):
    user = make_user()
    _connect_fake_broker(db_session, user.id)
    run = _make_run(db_session, user.id, instrument.id)

    prices = [100.0] * 40 + [100 + i * 0.5 for i in range(1, 21)] + [110 - i * 0.5 for i in range(1, 21)]
    with _mock_historical_data(_candles_response(prices)):
        result = await BacktestService(db_session).run(user.id, run, instrument)

    assert result.status == "COMPLETED"
    assert result.final_capital is not None
    assert result.net_pnl == result.final_capital - result.initial_capital
    assert result.total_trades >= 1
    assert result.completed_at is not None

    from app.repositories.backtest_repository import BacktestRepository

    trades = BacktestRepository(db_session).list_trades(run.id)
    assert len(trades) >= 2  # at least one entry + one exit
    assert any(t.side == "BUY" for t in trades)
    assert any(t.side == "SELL" for t in trades)
    # Every persisted trade carries its own full cost breakdown, not a collapsed total.
    assert all(t.total_charges == t.brokerage + t.stt + t.exchange_charges + t.sebi_charges + t.stamp_duty + t.gst for t in trades)


@pytest.mark.asyncio
async def test_flat_prices_complete_with_zero_trades_not_an_error(db_session, make_user, instrument):
    user = make_user()
    _connect_fake_broker(db_session, user.id)
    run = _make_run(db_session, user.id, instrument.id)

    with _mock_historical_data(_candles_response([100.0] * 80)):
        result = await BacktestService(db_session).run(user.id, run, instrument)

    assert result.status == "COMPLETED"
    assert result.total_trades == 0
    assert result.net_pnl == Decimal("0.00")
