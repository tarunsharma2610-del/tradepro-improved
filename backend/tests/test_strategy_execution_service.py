from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.brokers.base import BrokerCallResult
from app.core.encryption import encrypt_value
from app.models.strategy import Strategy
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.instrument_service import InstrumentService
from app.services.strategy_engine import Signal
from app.services.strategy_execution_service import StrategyExecutionService


@pytest.fixture()
def instrument(db_session):
    InstrumentService(db_session).seed_defaults()
    from app.repositories.instrument_repository import InstrumentRepository

    return InstrumentRepository(db_session).search("RELIANCE")[0]


@pytest.fixture()
def portfolio(db_session, make_user):
    user = make_user()
    p = PortfolioRepository(db_session).create(user_id=user.id, name="Auto", virtual_capital=Decimal("500000"))
    return user, p


def _connect_fake_broker(db_session, user_id):
    from app.models.broker_connection import BrokerConnection

    conn = BrokerConnection(
        user_id=user_id, broker="upstox",
        api_key_encrypted=encrypt_value("k"), api_secret_encrypted=encrypt_value("s"),
        redirect_uri="https://example.com/cb", access_token_encrypted=encrypt_value("tok"),
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        analytics_token_encrypted=encrypt_value("fake-analytics-token"),
        analytics_token_expires_at=datetime.now(timezone.utc) + timedelta(days=365), is_connected=True,
    )
    db_session.add(conn)
    db_session.commit()


def _make_strategy(db_session, portfolio_id, instrument_id, **overrides) -> Strategy:
    defaults = dict(
        portfolio_id=portfolio_id, instrument_id=instrument_id, name="Test strategy",
        segment="EQUITY_INTRADAY", quantity=1, is_active=True,
        rsi_weight=Decimal("0"), sma_crossover_weight=Decimal("0"), macd_weight=Decimal("0"),
        volume_spike_weight=Decimal("0"), momentum_weight=Decimal("1"),  # momentum-only: simplest to steer in tests
        entry_score_threshold=Decimal("0.3"), exit_score_threshold=Decimal("-0.3"),
        trailing_stop_pct=Decimal("2"), max_daily_loss=Decimal("5000"),
    )
    defaults.update(overrides)
    strategy = Strategy(**defaults)
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)
    return strategy


def _candles_response(prices: list[float], *, age_minutes: int = 0):
    """Build a newest-first response with controllable freshness."""
    newest_first = list(reversed(prices))
    now = datetime.now(timezone.utc) - timedelta(minutes=age_minutes)
    candles = [
        [(now - timedelta(minutes=5 * i)).isoformat(), p, p, p, p, 10000, 0]
        for i, p in enumerate(newest_first)
    ]
    return BrokerCallResult(ok=True, data={"status": "success", "data": {"candles": candles}})


def _mock_broker(candles_result: BrokerCallResult, quote_price: str):
    fake_adapter = type(
        "FakeAdapter", (),
        {
            "get_historical_data": AsyncMock(return_value=candles_result),
            "get_intraday_data": AsyncMock(return_value=candles_result),
            "get_full_quote": AsyncMock(return_value=BrokerCallResult(ok=True, data={"data": {"NSE_EQ:TEST": {"instrument_token": "NSE_EQ|INE002A01018", "last_price": quote_price, "last_trade_time": "1600000000000", "timestamp": datetime.now(timezone.utc).isoformat(), "depth": {"buy": [{"price": quote_price, "quantity": 100000, "orders": 10}], "sell": [{"price": quote_price, "quantity": 100000, "orders": 10}]}}}})),
        },
    )()
    stack = ExitStack()
    stack.enter_context(patch("app.services.strategy_execution_service.get_broker_adapter", return_value=fake_adapter))
    stack.enter_context(patch("app.services.execution_service.get_broker_adapter", return_value=fake_adapter))
    return stack


@pytest.mark.asyncio
async def test_no_connected_broker_holds_without_crashing(db_session, portfolio, instrument):
    _, p = portfolio
    strategy = _make_strategy(db_session, p.id, instrument.id)
    service = StrategyExecutionService(db_session)

    result = await service.evaluate(strategy)
    assert result.signal == Signal.HOLD.value
    assert "broker" in result.reason.lower()


@pytest.mark.asyncio
async def test_insufficient_candle_history_holds(db_session, portfolio, instrument):
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    strategy = _make_strategy(db_session, p.id, instrument.id)
    service = StrategyExecutionService(db_session)

    with _mock_broker(_candles_response([100.0, 101.0, 102.0]), "102.00"):
        result = await service.evaluate(strategy)

    assert result.signal == Signal.HOLD.value


@pytest.mark.asyncio
async def test_strong_uptrend_triggers_entry_through_the_real_execution_engine(db_session, portfolio, instrument):
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    strategy = _make_strategy(db_session, p.id, instrument.id)
    service = StrategyExecutionService(db_session)

    rising_prices = [100.0 + i * 0.5 for i in range(20)]  # clear momentum, well past the entry threshold
    with _mock_broker(_candles_response(rising_prices), str(rising_prices[-1])):
        result = await service.evaluate(strategy)

    assert result.signal == Signal.ENTER_LONG.value
    assert result.order_id is not None

    from app.repositories.position_repository import PositionRepository

    position = PositionRepository(db_session).get_or_create(p.id, instrument.id)
    assert position.quantity == strategy.quantity  # the fixed size configured on the strategy

    db_session.refresh(strategy)
    assert strategy.current_watermark is not None
    assert strategy.last_evaluated_at is not None


@pytest.mark.asyncio
async def test_score_reversal_exits_an_open_position(db_session, portfolio, instrument):
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    strategy = _make_strategy(db_session, p.id, instrument.id)
    service = StrategyExecutionService(db_session)

    rising_prices = [100.0 + i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(rising_prices), str(rising_prices[-1])):
        entry = await service.evaluate(strategy)
    assert entry.signal == Signal.ENTER_LONG.value

    db_session.refresh(strategy)
    falling_prices = [110.0 - i * 0.5 for i in range(20)]  # sharp reversal — momentum score should flip negative
    with _mock_broker(_candles_response(falling_prices), str(falling_prices[-1])):
        exit_result = await service.evaluate(strategy)

    assert exit_result.signal == Signal.EXIT.value

    from app.repositories.position_repository import PositionRepository

    position = PositionRepository(db_session).get_or_create(p.id, instrument.id)
    assert position.quantity == 0

    db_session.refresh(strategy)
    assert strategy.current_watermark is None


@pytest.mark.asyncio
async def test_paused_strategy_does_not_enter(db_session, portfolio, instrument):
    from datetime import timezone as tz

    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    today = datetime.now(tz.utc).date()
    strategy = _make_strategy(db_session, p.id, instrument.id, paused_until=today)
    service = StrategyExecutionService(db_session)

    rising_prices = [100.0 + i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(rising_prices), str(rising_prices[-1])):
        result = await service.evaluate(strategy)

    assert result.signal == Signal.HOLD.value
    assert "paused" in result.reason.lower() or "risk engine" in result.reason.lower()

    from app.repositories.position_repository import PositionRepository

    position = PositionRepository(db_session).get_or_create(p.id, instrument.id)
    assert position.quantity == 0  # never entered



@pytest.mark.asyncio
async def test_emergency_kill_switch_blocks_new_entries_but_does_not_disable_evaluation(db_session, portfolio, instrument, monkeypatch):
    from app.core.config import settings

    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    strategy = _make_strategy(db_session, p.id, instrument.id)
    monkeypatch.setattr(settings, "AUTOMATED_ENTRIES_ENABLED", False)
    service = StrategyExecutionService(db_session)

    rising_prices = [100.0 + i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(rising_prices), str(rising_prices[-1])):
        result = await service.evaluate(strategy)

    assert result.signal == Signal.HOLD.value
    assert "kill switch" in result.reason.lower()

    from app.repositories.position_repository import PositionRepository
    position = PositionRepository(db_session).get_or_create(p.id, instrument.id)
    assert position.quantity == 0


@pytest.mark.asyncio
async def test_inactive_strategy_cannot_be_evaluated_even_via_manual_service_call(db_session, portfolio, instrument):
    _, p = portfolio
    strategy = _make_strategy(db_session, p.id, instrument.id, is_active=False)
    service = StrategyExecutionService(db_session)

    with patch("app.services.strategy_execution_service.get_broker_adapter") as adapter:
        result = await service.evaluate(strategy)

    assert result.signal == Signal.HOLD.value
    assert "inactive" in result.reason.lower()
    adapter.assert_not_called()

@pytest.mark.asyncio
async def test_emergency_kill_switch_keeps_strategy_exits_available(db_session, portfolio, instrument, monkeypatch):
    from app.core.config import settings
    from app.repositories.position_repository import PositionRepository

    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    strategy = _make_strategy(db_session, p.id, instrument.id)
    service = StrategyExecutionService(db_session)

    rising_prices = [100.0 + i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(rising_prices), str(rising_prices[-1])):
        entry = await service.evaluate(strategy)
    assert entry.signal == Signal.ENTER_LONG.value
    assert PositionRepository(db_session).get_or_create(p.id, instrument.id).quantity > 0

    # The emergency switch is entry-only: it must not trap an existing position.
    monkeypatch.setattr(settings, "AUTOMATED_ENTRIES_ENABLED", False)
    falling_prices = [110.0 - i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(falling_prices), str(falling_prices[-1])):
        exit_result = await service.evaluate(strategy)

    assert exit_result.signal == Signal.EXIT.value
    assert exit_result.order_id is not None
    assert PositionRepository(db_session).get_or_create(p.id, instrument.id).quantity == 0

@pytest.mark.asyncio
async def test_stale_candles_fail_closed_without_opening_a_position(db_session, portfolio, instrument):
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    strategy = _make_strategy(db_session, p.id, instrument.id)
    service = StrategyExecutionService(db_session)

    rising_prices = [100.0 + i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(rising_prices, age_minutes=30), str(rising_prices[-1])):
        result = await service.evaluate(strategy)

    assert result.signal == Signal.HOLD.value
    assert "stale" in result.reason.lower()
    from app.repositories.position_repository import PositionRepository
    assert PositionRepository(db_session).get_or_create(p.id, instrument.id).quantity == 0


@pytest.mark.asyncio
async def test_worker_scanner_ltp_drives_trailing_stop_without_changing_candle_indicators(db_session, portfolio, instrument):
    from datetime import datetime, timezone
    from app.services.market_scanner import MarketScanner

    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    strategy = _make_strategy(db_session, p.id, instrument.id)
    rising_prices = [100.0 + i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(rising_prices), str(rising_prices[-1])):
        entry = await StrategyExecutionService(db_session).evaluate(strategy)
    assert entry.signal == Signal.ENTER_LONG.value

    scanner = MarketScanner(max_age_seconds=15)
    received_at = datetime.now(timezone.utc)
    observation = scanner.process_quote(user.id, {
        "user_id": str(user.id), "instrument_key": instrument.instrument_key,
        "epoch": "worker-test-epoch", "version": 1, "ltp": 100.0,
        "exchange_timestamp_ms": int(received_at.timestamp() * 1000),
        "received_at": received_at.isoformat(),
    })
    assert observation is not None

    db_session.refresh(strategy)
    with _mock_broker(_candles_response(rising_prices), str(rising_prices[-1])):
        result = await StrategyExecutionService(db_session, scanner=scanner).evaluate(strategy)
    assert result.signal == Signal.EXIT.value
    from app.repositories.position_repository import PositionRepository
    assert PositionRepository(db_session).get_or_create(p.id, instrument.id).quantity == 0


@pytest.mark.asyncio
async def test_other_users_scanner_observation_cannot_trigger_strategy_trailing_stop(db_session, portfolio, instrument):
    from datetime import datetime, timezone
    from app.services.market_scanner import MarketScanner

    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    strategy = _make_strategy(db_session, p.id, instrument.id)
    rising_prices = [100.0 + i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(rising_prices), str(rising_prices[-1])):
        entry = await StrategyExecutionService(db_session).evaluate(strategy)
    assert entry.signal == Signal.ENTER_LONG.value

    scanner = MarketScanner(max_age_seconds=15)
    received_at = datetime.now(timezone.utc)
    observation = scanner.process_quote("different-user", {
        "user_id": "different-user", "instrument_key": instrument.instrument_key,
        "epoch": "other-user-epoch", "version": 1, "ltp": 1.0,
        "exchange_timestamp_ms": int(received_at.timestamp() * 1000),
        "received_at": received_at.isoformat(),
    })
    assert observation is not None
    assert scanner.latest(user.id, instrument.instrument_key) is None

    db_session.refresh(strategy)
    with _mock_broker(_candles_response(rising_prices), str(rising_prices[-1])):
        result = await StrategyExecutionService(db_session, scanner=scanner).evaluate(strategy)
    assert result.signal == Signal.HOLD.value


@pytest.mark.asyncio
async def test_expired_scanner_observation_cannot_trigger_trailing_stop(db_session, portfolio, instrument, monkeypatch):
    from datetime import datetime, timezone
    from app.services import market_scanner as scanner_module
    from app.services.market_scanner import MarketScanner
    from app.repositories.position_repository import PositionRepository

    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    strategy = _make_strategy(db_session, p.id, instrument.id)
    rising_prices = [100.0 + i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(rising_prices), str(rising_prices[-1])):
        entry = await StrategyExecutionService(db_session).evaluate(strategy)
    assert entry.signal == Signal.ENTER_LONG.value

    scanner = MarketScanner(max_age_seconds=15)
    received_at = datetime.now(timezone.utc)
    monkeypatch.setattr(scanner_module.time, "monotonic", lambda: 100.0)
    observation = scanner.process_quote(user.id, {
        "user_id": str(user.id), "instrument_key": instrument.instrument_key,
        "epoch": "expired-worker-test", "version": 1, "ltp": 1.0,
        "exchange_timestamp_ms": int(received_at.timestamp() * 1000),
        "received_at": received_at.isoformat(),
    })
    assert observation is not None

    # Expire the quote before evaluation. The candle indicators still say HOLD;
    # the stale low LTP must not trigger a trailing-stop exit.
    monkeypatch.setattr(scanner_module.time, "monotonic", lambda: 115.1)
    db_session.refresh(strategy)
    with _mock_broker(_candles_response(rising_prices), str(rising_prices[-1])):
        result = await StrategyExecutionService(db_session, scanner=scanner).evaluate(strategy)

    assert result.signal == Signal.HOLD.value
    assert PositionRepository(db_session).get_or_create(p.id, instrument.id).quantity == strategy.quantity
