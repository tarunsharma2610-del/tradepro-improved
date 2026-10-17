from decimal import Decimal

from app.services.indicators import Candle, macd, momentum, rsi, sma_crossover, volume_spike


def _candles(closes: list[float], volumes: list[int] | None = None) -> list[Candle]:
    volumes = volumes or [1000] * len(closes)
    return [
        Candle(open=Decimal(str(c)), high=Decimal(str(c)), low=Decimal(str(c)), close=Decimal(str(c)), volume=v)
        for c, v in zip(closes, volumes)
    ]


def _rising(n: int, start: float = 100.0, step: float = 1.0) -> list[float]:
    return [start + i * step for i in range(n)]


def _falling(n: int, start: float = 100.0, step: float = 1.0) -> list[float]:
    return [start - i * step for i in range(n)]


# --- RSI ---

def test_rsi_none_with_insufficient_data():
    assert rsi(_candles(_rising(5)), period=14) is None


def test_rsi_strongly_negative_after_a_sustained_uptrend():
    # All gains, no losses -> RSI near 100 -> overbought -> bearish score
    result = rsi(_candles(_rising(30)), period=14)
    assert result is not None
    assert result < Decimal("-0.9")


def test_rsi_strongly_positive_after_a_sustained_downtrend():
    result = rsi(_candles(_falling(30)), period=14)
    assert result is not None
    assert result > Decimal("0.9")


# --- SMA crossover ---

def test_sma_crossover_positive_in_an_uptrend():
    result = sma_crossover(_candles(_rising(35)), fast_period=10, slow_period=30)
    assert result is not None
    assert result > 0


def test_sma_crossover_negative_in_a_downtrend():
    result = sma_crossover(_candles(_falling(35)), fast_period=10, slow_period=30)
    assert result is not None
    assert result < 0


def test_sma_crossover_none_with_insufficient_data():
    assert sma_crossover(_candles(_rising(10)), fast_period=10, slow_period=30) is None


# --- MACD ---

def test_macd_positive_in_a_sustained_uptrend():
    result = macd(_candles(_rising(50)), fast=12, slow=26, signal=9)
    assert result is not None
    assert result > 0


def test_macd_negative_in_a_sustained_downtrend():
    result = macd(_candles(_falling(50)), fast=12, slow=26, signal=9)
    assert result is not None
    assert result < 0


# --- Momentum ---

def test_momentum_positive_when_price_rose_over_the_period():
    result = momentum(_candles(_rising(15)), period=10)
    assert result is not None
    assert result > 0


def test_momentum_negative_when_price_fell_over_the_period():
    result = momentum(_candles(_falling(15)), period=10)
    assert result is not None
    assert result < 0


def test_momentum_scores_are_clipped_to_valid_range():
    # A huge move shouldn't blow past the [-1, 1] contract.
    result = momentum(_candles([100.0] + [1000.0] * 10), period=10)
    assert result is not None
    assert Decimal("-1") <= result <= Decimal("1")


# --- Volume spike ---

def test_volume_spike_positive_when_confirming_an_uptrend():
    closes = [100.0] * 20 + [101, 102, 103, 104, 105]  # up-move in the last 5
    volumes = [1000] * 20 + [1000, 1000, 1000, 1000, 5000]  # spike on the last candle
    result = volume_spike(_candles(closes, volumes), lookback=20, direction_period=5)
    assert result is not None
    assert result > 0


def test_volume_spike_negative_when_confirming_a_downtrend():
    closes = [100.0] * 20 + [99, 98, 97, 96, 95]
    volumes = [1000] * 20 + [1000, 1000, 1000, 1000, 5000]
    result = volume_spike(_candles(closes, volumes), lookback=20, direction_period=5)
    assert result is not None
    assert result < 0


def test_volume_spike_near_zero_without_above_average_volume():
    closes = [100.0] * 20 + [101, 102, 103, 104, 105]
    volumes = [1000] * 25  # flat volume, no spike
    result = volume_spike(_candles(closes, volumes), lookback=20, direction_period=5)
    assert result == Decimal("0")


def test_all_indicators_return_none_rather_than_guess_with_too_few_candles():
    tiny = _candles([100.0, 101.0, 102.0])
    assert rsi(tiny) is None
    assert sma_crossover(tiny) is None
    assert macd(tiny) is None
    assert momentum(tiny) is None
    assert volume_spike(tiny) is None
