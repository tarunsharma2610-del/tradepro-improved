"""
Pure combination logic, deliberately separate from indicators.py (each
indicator's own math) and from strategy_execution_service.py (fetching
data and acting on the signal). This is the one place "how do five scores
become one decision" lives.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.services.indicators import Candle, macd, momentum, rsi, sma_crossover, volume_spike


class Signal(str, Enum):
    ENTER_LONG = "ENTER_LONG"
    EXIT = "EXIT"
    HOLD = "HOLD"


@dataclass
class IndicatorWeights:
    rsi: Decimal = Decimal("1")
    sma_crossover: Decimal = Decimal("1")
    macd: Decimal = Decimal("1")
    volume_spike: Decimal = Decimal("1")
    momentum: Decimal = Decimal("1")


@dataclass
class ScoreResult:
    composite_score: Decimal | None  # None if not enough data for any indicator yet
    components: dict[str, Decimal | None]


def compute_score(candles: list[Candle], weights: IndicatorWeights) -> ScoreResult:
    components = {
        "rsi": rsi(candles),
        "sma_crossover": sma_crossover(candles),
        "macd": macd(candles),
        "volume_spike": volume_spike(candles),
        "momentum": momentum(candles),
    }

    weight_map = {
        "rsi": weights.rsi,
        "sma_crossover": weights.sma_crossover,
        "macd": weights.macd,
        "volume_spike": weights.volume_spike,
        "momentum": weights.momentum,
    }

    available = {k: v for k, v in components.items() if v is not None and weight_map[k] != 0}
    if not available:
        return ScoreResult(composite_score=None, components=components)

    weighted_sum = sum(available[k] * weight_map[k] for k in available)
    total_weight = sum(abs(weight_map[k]) for k in available)
    composite = weighted_sum / total_weight if total_weight != 0 else Decimal("0")

    return ScoreResult(composite_score=composite, components=components)


def decide(
    score: ScoreResult, *, in_position: bool, entry_threshold: Decimal, exit_threshold: Decimal
) -> Signal:
    """entry_threshold and exit_threshold are both compared against the
    same composite score, but mean different things: entering needs
    conviction (score >= entry_threshold), staying in only requires not
    having deteriorated past exit_threshold (which should be set lower
    than entry_threshold, or every entry would instantly re-exit)."""
    if score.composite_score is None:
        return Signal.HOLD

    if in_position:
        return Signal.EXIT if score.composite_score <= exit_threshold else Signal.HOLD

    return Signal.ENTER_LONG if score.composite_score >= entry_threshold else Signal.HOLD
