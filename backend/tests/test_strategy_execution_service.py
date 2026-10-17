from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.brokers.base import BrokerCallResult
from app.core.encryption import encrypt_value
from app.models.execution import Execution
from app.models.order import Order
from app.models.strategy import Strategy
from app.models.strategy_position import StrategyPosition
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
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1), is_connected=True,
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


def _candles_response(prices: list[float]):
    """`prices` given oldest-to-newest, the way a human writes a trend.
    Upstox's real (documented) convention is newest-first, and
    _parse_candles un-reverses that — so this builds the mocked raw array
    in newest-first order too, exactly mirroring what a real response
    would look like, rather than pre-flipping it for convenience."""
    newest_first = list(reversed(prices))
    candles = [[f"2026-08-{i + 1:02d}T10:00:00", p, p, p, p, 10000, 0] for i, p in enumerate(newest_first)]
    return BrokerCallResult(ok=True, data={"data": {"candles": candles}})


def _mock_broker(candles_result: BrokerCallResult, quote_price: str):
    fake_adapter = type(
        "FakeAdapter", (),
        {
            "get_historical_data": AsyncMock(return_value=candles_result),
            "get_quote": AsyncMock(return_value=BrokerCallResult(ok=True, data={"data": {"NSE_EQ|INE002A01018": {"last_price": quote_price}}})),
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


@pytest.mark.parametrize(
    "realized_pnl,should_block",
    [(Decimal("-9999.99"), False), (Decimal("-10000.00"), True), (Decimal("-12000.00"), True)],
)
def test_portfolio_daily_loss_limit_blocks_all_strategy_entries(
    db_session, portfolio, instrument, monkeypatch, realized_pnl, should_block
):
    """Losses from a manual/non-strategy fill count toward the portfolio cap."""
    from app.core.config import settings
    from app.services.risk_engine import check_can_enter

    _, p = portfolio
    strategy = _make_strategy(db_session, p.id, instrument.id)
    monkeypatch.setattr(settings, "PORTFOLIO_DAILY_LOSS_LIMIT_PCT", Decimal("2.0"))

    order = Order(
        portfolio_id=p.id, instrument_id=instrument.id, side="SELL",
        order_type="MARKET", segment="EQUITY_DELIVERY", quantity=1,
        status="FILLED", trading_mode="PAPER", execution_reason="MANUAL",
        strategy_id=None, placed_at=datetime.now(timezone.utc), filled_at=datetime.now(timezone.utc),
    )
    db_session.add(order)
    db_session.flush()
    db_session.add(Execution(
        order_id=order.id, portfolio_id=p.id, instrument_id=instrument.id,
        side="SELL", quantity=1, price=Decimal("100"), gross_value=Decimal("100"),
        brokerage=Decimal("0"), stt=Decimal("0"), exchange_charges=Decimal("0"),
        sebi_charges=Decimal("0"), stamp_duty=Decimal("0"), gst=Decimal("0"),
        total_charges=Decimal("0"), realized_pnl=realized_pnl, executed_at=datetime.now(timezone.utc),
    ))
    db_session.commit()

    result = check_can_enter(db_session, strategy)
    assert result.allowed is (not should_block)
    if should_block:
        assert result.reason is not None
        assert "portfolio daily loss limit" in result.reason.lower()


@pytest.mark.asyncio
async def test_strategy_does_not_exit_a_manual_position_in_the_same_instrument(db_session, portfolio, instrument):
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)

    from app.services.execution_service import ExecutionService, PlaceOrderRequest
    from app.services.transaction_costs import Segment as OrderSegment, Side as OrderSide
    from app.models.position import Position

    with patch(
        "app.services.execution_service.get_broker_adapter",
        return_value=type("FakeAdapter", (), {
            "get_quote": AsyncMock(return_value=BrokerCallResult(
                ok=True, data={"data": {instrument.instrument_key: {"last_price": "100.00"}}}
            ))
        })(),
    ):
        manual = await ExecutionService(db_session).place_order(
            user.id,
            PlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=OrderSide.BUY,
                order_type="MARKET", segment=OrderSegment.EQUITY_DELIVERY, quantity=5,
            ),
        )
    assert manual.status == "FILLED"

    strategy = _make_strategy(db_session, p.id, instrument.id)
    falling_prices = [110.0 - i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(falling_prices), "90.00"):
        result = await StrategyExecutionService(db_session).evaluate(strategy)

    assert result.signal == Signal.HOLD.value
    position = db_session.query(Position).filter_by(portfolio_id=p.id, instrument_id=instrument.id).one()
    assert position.quantity == 5
    assert db_session.query(Order).filter(Order.strategy_id == strategy.id, Order.status == "FILLED").count() == 0


@pytest.mark.asyncio
async def test_strategy_pnl_uses_its_own_entry_basis_not_portfolio_average(db_session, portfolio, instrument):
    from app.services.analytics_service import strategy_analytics
    from app.services.execution_service import ExecutionService, PlaceOrderRequest
    from app.services.transaction_costs import Segment as OrderSegment, Side as OrderSide

    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    with patch(
        "app.services.execution_service.get_broker_adapter",
        return_value=type("FakeAdapter", (), {
            "get_quote": AsyncMock(return_value=BrokerCallResult(
                ok=True, data={"data": {instrument.instrument_key: {"last_price": "100.00"}}}
            ))
        })(),
    ):
        await ExecutionService(db_session).place_order(
            user.id,
            PlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=OrderSide.BUY,
                order_type="MARKET", segment=OrderSegment.EQUITY_DELIVERY, quantity=10,
            ),
        )

    strategy = _make_strategy(db_session, p.id, instrument.id)
    rising_prices = [100.0 + i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(rising_prices), "120.00"):
        entry = await StrategyExecutionService(db_session).evaluate(strategy)
    assert entry.signal == Signal.ENTER_LONG.value

    allocation = db_session.query(StrategyPosition).filter_by(strategy_id=strategy.id).one()
    assert allocation.quantity == 1
    assert allocation.avg_price == Decimal("120.0000")

    falling_prices = [110.0 - i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(falling_prices), "130.00"):
        exit_result = await StrategyExecutionService(db_session).evaluate(strategy)
    assert exit_result.signal == Signal.EXIT.value

    db_session.refresh(allocation)
    assert allocation.quantity == 0
    assert allocation.realized_pnl == Decimal("10.00")
    analytics = strategy_analytics(db_session, p.id)
    assert analytics[0].total_realized_pnl == Decimal("10.00")


@pytest.mark.asyncio
async def test_strategy_cannot_open_a_second_position_when_one_is_already_allocated(db_session, portfolio, instrument):
    from app.services.execution_service import ExecutionService, PlaceOrderRequest
    from app.services.transaction_costs import Segment as OrderSegment, Side as OrderSide

    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    strategy = _make_strategy(db_session, p.id, instrument.id)
    rising_prices = [100.0 + i * 0.5 for i in range(20)]
    with _mock_broker(_candles_response(rising_prices), "110.00"):
        first = await StrategyExecutionService(db_session).evaluate(strategy)
    assert first.signal == Signal.ENTER_LONG.value

    with patch(
        "app.services.execution_service.get_broker_adapter",
        return_value=type("FakeAdapter", (), {
            "get_quote": AsyncMock(return_value=BrokerCallResult(
                ok=True, data={"data": {instrument.instrument_key: {"last_price": "111.00"}}}
            ))
        })(),
    ):
        second = await ExecutionService(db_session).place_order(
            user.id,
            PlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=OrderSide.BUY,
                order_type="MARKET", segment=OrderSegment.EQUITY_INTRADAY, quantity=1,
                execution_reason="STRATEGY", strategy_id=strategy.id,
            ),
        )
    assert second.status == "REJECTED"
    assert "already owns an open position" in second.rejection_reason.lower()


@pytest.mark.asyncio
async def test_repeated_entry_signal_on_same_candle_reuses_one_idempotency_key(db_session, portfolio, instrument):
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    strategy = _make_strategy(db_session, p.id, instrument.id)
    rising_prices = [100.0 + i * 0.5 for i in range(20)]

    # This quote exceeds the existing paper order-notional cap, so the first
    # attempt is rejected and does not create a StrategyPosition. Re-evaluation
    # on the same candle must return that same rejected order, not submit again.
    with _mock_broker(_candles_response(rising_prices), "30000.00"):
        first = await StrategyExecutionService(db_session).evaluate(strategy)
        second = await StrategyExecutionService(db_session).evaluate(strategy)

    assert first.signal == Signal.ENTER_LONG.value
    assert second.signal == Signal.ENTER_LONG.value
    assert first.order_id == second.order_id
    orders = db_session.query(Order).filter(Order.strategy_id == strategy.id).all()
    assert len(orders) == 1
    assert orders[0].status == "REJECTED"
    assert orders[0].idempotency_key == f"strategy:{strategy.id}:BUY:2026-08-01T10:00:00"
