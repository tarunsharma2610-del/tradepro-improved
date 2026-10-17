"""
Five indicators, each reduced to a bounded score in [-1, 1] so
strategy_engine.py can combine them with simple weighted averaging
regardless of each indicator's native scale. Positive = bullish, negative
= bearish, 0 = neutral/insufficient data.

Same five factors as an earlier project in this line (AlgoEdge) used —
kept deliberately consistent rather than inventing a new indicator set.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Candle:
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    timestamp: datetime | None = None


def _clip(value: Decimal, lo: Decimal = Decimal("-1"), hi: Decimal = Decimal("1")) -> Decimal:
    return max(lo, min(hi, value))


def rsi(candles: list[Candle], period: int = 14) -> Decimal | None:
    """Classic Wilder RSI. Score = (50 - RSI) / 50: oversold (low RSI) is
    bullish (+), overbought (high RSI) is bearish (-)."""
    closes = [c.close for c in candles]
    if len(closes) < period + 1:
        return None

    gains, losses = [], []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, Decimal("0")))
        losses.append(max(-change, Decimal("0")))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        rsi_value = Decimal("100")
    else:
        rs = avg_gain / avg_loss
        rsi_value = Decimal("100") - (Decimal("100") / (1 + rs))

    return _clip((Decimal("50") - rsi_value) / Decimal("50"))


def sma_crossover(candles: list[Candle], fast_period: int = 10, slow_period: int = 30) -> Decimal | None:
    """Fast SMA above slow SMA is bullish. Score scales the relative gap,
    clipped so a large gap doesn't dominate the composite score."""
    closes = [c.close for c in candles]
    if len(closes) < slow_period:
        return None

    fast = sum(closes[-fast_period:]) / fast_period
    slow = sum(closes[-slow_period:]) / slow_period
    if slow == 0:
        return None

    relative_gap = (fast - slow) / slow
    return _clip(relative_gap * Decimal("20"))


def _ema_series(values: list[Decimal], period: int) -> list[Decimal]:
    k = Decimal(2) / (period + 1)
    ema = [values[0]]
    for v in values[1:]:
        ema.append(v * k + ema[-1] * (1 - k))
    return ema


def macd(candles: list[Candle], fast: int = 12, slow: int = 26, signal: int = 9) -> Decimal | None:
    """MACD line above its signal line is bullish. Score scales the
    histogram (macd - signal) relative to price, clipped."""
    closes = [c.close for c in candles]
    if len(closes) < slow + signal:
        return None

    ema_fast = _ema_series(closes, fast)
    ema_slow = _ema_series(closes, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = _ema_series(macd_line, signal)

    histogram = macd_line[-1] - signal_line[-1]
    last_close = closes[-1]
    if last_close == 0:
        return None

    return _clip((histogram / last_close) * Decimal("100"))


def momentum(candles: list[Candle], period: int = 10) -> Decimal | None:
    """Rate of change over `period` candles. Score scales the % change."""
    closes = [c.close for c in candles]
    if len(closes) < period + 1:
        return None

    then, now = closes[-period - 1], closes[-1]
    if then == 0:
        return None

    roc = (now - then) / then
    return _clip(roc * Decimal("10"))


def volume_spike(candles: list[Candle], lookback: int = 20, direction_period: int = 5) -> Decimal | None:
    """Volume alone isn't directional — this scores it as *confirmation*
    of the recent price direction: a volume spike accompanying a recent
    up-move is bullish, accompanying a down-move is bearish. A volume
    spike with no clear recent direction scores near zero."""
    if len(candles) < max(lookback, direction_period) + 1:
        return None

    volumes = [c.volume for c in candles]
    avg_volume = sum(volumes[-lookback - 1 : -1]) / lookback  # excludes the current candle
    if avg_volume == 0:
        return None

    current_volume = Decimal(volumes[-1])
    spike_ratio = current_volume / Decimal(avg_volume)
    spike_magnitude = _clip(spike_ratio - 1, Decimal("0"), Decimal("1"))  # 0 if not above average

    closes = [c.close for c in candles]
    then, now = closes[-direction_period - 1], closes[-1]
    direction = Decimal("1") if now > then else Decimal("-1") if now < then else Decimal("0")

    return _clip(direction * spike_magnitude)
