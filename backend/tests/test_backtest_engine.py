from decimal import Decimal

from app.services.backtest_engine import (
    BacktestConfig,
    _apply_slippage,
    _max_drawdown_pct,
    run_backtest,
)
from app.services.indicators import Candle
from app.services.strategy_engine import IndicatorWeights
from app.services.transaction_costs import Segment, Side

# Isolate momentum only (weight=1, everything else 0) — same trick used in
# the live strategy tests, for predictable, steerable behavior.
MOMENTUM_ONLY = IndicatorWeights(rsi=Decimal("0"), sma_crossover=Decimal("0"), macd=Decimal("0"), volume_spike=Decimal("0"), momentum=Decimal("1"))


def _candles(closes: list[float]) -> list[Candle]:
    return [Candle(Decimal(str(c)), Decimal(str(c)), Decimal(str(c)), Decimal(str(c)), 1000) for c in closes]


def _base_config(**overrides) -> BacktestConfig:
    defaults = dict(
        initial_capital=Decimal("100000"), quantity=10, segment=Segment.EQUITY_INTRADAY, weights=MOMENTUM_ONLY,
        entry_threshold=Decimal("0.3"), exit_threshold=Decimal("-0.3"), trailing_stop_pct=Decimal("50"),  # loose stop — isolate score-driven exits in most tests
        slippage_bps=Decimal("5"),
    )
    defaults.update(overrides)
    return BacktestConfig(**defaults)


def test_insufficient_candles_returns_a_clear_error_not_a_crash():
    result = run_backtest(_candles([100.0] * 10), _base_config())
    assert result.error is not None
    assert result.final_capital == result.initial_capital
    assert result.trades == []


def test_uptrend_then_reversal_produces_a_full_round_trip():
    closes = [100.0] * 40 + [100 + i * 0.5 for i in range(1, 21)] + [110 - i * 0.5 for i in range(1, 21)]
    result = run_backtest(_candles(closes), _base_config())

    assert result.error is None
    sides = [t.side for t in result.trades]
    assert Side.BUY in sides
    assert Side.SELL in sides
    # The exit should have realized some (nonzero) P&L — it closed a position.
    assert any(t.realized_pnl != 0 for t in result.trades)


def test_flat_prices_never_trade():
    result = run_backtest(_candles([100.0] * 80), _base_config())
    assert result.trades == []
    assert result.final_capital == result.initial_capital


def test_buy_fills_worse_than_raw_price_sell_fills_worse_than_raw_price():
    assert _apply_slippage(Decimal("100"), Side.BUY, Decimal("10")) > Decimal("100")
    assert _apply_slippage(Decimal("100"), Side.SELL, Decimal("10")) < Decimal("100")


def test_zero_slippage_fills_at_exactly_the_candle_close():
    assert _apply_slippage(Decimal("100"), Side.BUY, Decimal("0")) == Decimal("100")


def test_entry_skipped_when_it_would_exceed_available_capital():
    closes = [100.0] * 40 + [100 + i * 0.5 for i in range(1, 21)]
    config = _base_config(initial_capital=Decimal("50"), quantity=1000)  # 1000 shares at ~100+ each, way over 50
    result = run_backtest(_candles(closes), config)

    assert result.trades == []
    assert result.final_capital == config.initial_capital


def test_net_pnl_is_final_minus_initial_capital():
    result = run_backtest(_candles([100.0] * 80), _base_config())
    assert result.net_pnl == result.final_capital - result.initial_capital == Decimal("0")


def test_win_and_loss_counts_only_reflect_closing_trades():
    closes = [100.0] * 40 + [100 + i * 0.5 for i in range(1, 21)] + [110 - i * 0.5 for i in range(1, 21)]
    result = run_backtest(_candles(closes), _base_config())

    closing = result.closing_trades
    assert len(closing) >= 1
    assert result.win_count + result.loss_count <= len(closing)  # breakeven trades (exactly 0 pnl) are neither


def test_max_drawdown_pct_on_a_simple_hand_built_curve():
    # Peak 100 -> trough 80 -> partial recovery to 90: drawdown is (100-80)/100 = 20%, not measured from the recovery.
    curve = [Decimal("100"), Decimal("110"), Decimal("80"), Decimal("90")]
    assert _max_drawdown_pct(curve) == Decimal("100") * (Decimal("110") - Decimal("80")) / Decimal("110")


def test_max_drawdown_pct_is_zero_for_a_monotonically_rising_curve():
    curve = [Decimal("100"), Decimal("105"), Decimal("110")]
    assert _max_drawdown_pct(curve) == Decimal("0")
