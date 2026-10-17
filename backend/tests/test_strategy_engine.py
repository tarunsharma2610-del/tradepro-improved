from decimal import Decimal

from app.services.indicators import Candle
from app.services.strategy_engine import IndicatorWeights, Signal, compute_score, decide


def _flat_candles(n: int, price: float = 100.0) -> list[Candle]:
    return [Candle(Decimal(str(price)), Decimal(str(price)), Decimal(str(price)), Decimal(str(price)), 1000) for _ in range(n)]


def _rising_candles(n: int) -> list[Candle]:
    return [
        Candle(Decimal(str(100 + i)), Decimal(str(100 + i)), Decimal(str(100 + i)), Decimal(str(100 + i)), 1000)
        for i in range(n)
    ]


def test_compute_score_none_when_no_indicator_has_enough_data():
    result = compute_score(_flat_candles(3), IndicatorWeights())
    assert result.composite_score is None


def test_compute_score_ignores_zero_weighted_indicators():
    weights = IndicatorWeights(rsi=Decimal("1"), sma_crossover=Decimal("0"), macd=Decimal("0"), volume_spike=Decimal("0"), momentum=Decimal("0"))
    result = compute_score(_rising_candles(50), weights)
    assert result.composite_score is not None
    # With only RSI weighted, the composite should equal RSI's own score exactly.
    assert result.composite_score == result.components["rsi"]


def test_compute_score_is_a_weighted_average_bounded_by_component_range():
    result = compute_score(_rising_candles(50), IndicatorWeights())
    assert result.composite_score is not None
    assert Decimal("-1") <= result.composite_score <= Decimal("1")


def test_decide_holds_when_score_is_none():
    score = compute_score(_flat_candles(3), IndicatorWeights())
    assert decide(score, in_position=False, entry_threshold=Decimal("0.5"), exit_threshold=Decimal("-0.3")) == Signal.HOLD


def test_decide_enters_when_flat_and_score_beats_entry_threshold():
    score = compute_score(_rising_candles(60), IndicatorWeights())
    # A sustained uptrend produces mixed signals (bullish momentum/SMA/MACD, bearish overbought RSI) —
    # use a low bar so the test asserts the threshold *mechanism*, not a specific market view.
    result = decide(score, in_position=False, entry_threshold=Decimal("-1"), exit_threshold=Decimal("-2"))
    assert result == Signal.ENTER_LONG


def test_decide_holds_when_flat_and_score_below_entry_threshold():
    score = compute_score(_rising_candles(60), IndicatorWeights())
    result = decide(score, in_position=False, entry_threshold=Decimal("2"), exit_threshold=Decimal("-2"))
    assert result == Signal.HOLD


def test_decide_exits_when_in_position_and_score_falls_to_exit_threshold():
    score = compute_score(_rising_candles(60), IndicatorWeights())
    result = decide(score, in_position=True, entry_threshold=Decimal("2"), exit_threshold=Decimal("2"))
    assert result == Signal.EXIT


def test_decide_holds_when_in_position_and_score_still_above_exit_threshold():
    score = compute_score(_rising_candles(60), IndicatorWeights())
    result = decide(score, in_position=True, entry_threshold=Decimal("2"), exit_threshold=Decimal("-2"))
    assert result == Signal.HOLD
