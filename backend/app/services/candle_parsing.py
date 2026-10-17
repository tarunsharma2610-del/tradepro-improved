"""
Upstox candle response parsing, shared by strategy_execution_service.py
(live) and backtest_service.py (historical) — both need the exact same
parsing, so it lives here once rather than being copied.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.services.indicators import Candle


def parse_candles(response_data: Any) -> list[Candle] | None:
    """BEST-EFFORT: Upstox's documented candle array shape is
    [timestamp, open, high, low, close, volume, open_interest], oldest
    first — this wasn't independently verified against a live response
    (only the endpoint URL shape was, in app/brokers/upstox/adapter.py).
    Confirm field order against a real account before trusting this for
    anything beyond a first live test."""
    if not isinstance(response_data, dict):
        return None
    raw_candles = response_data.get("data", {}).get("candles")
    if not isinstance(raw_candles, list) or not raw_candles:
        return None

    try:
        candles = [
            Candle(
                open=Decimal(str(c[1])),
                high=Decimal(str(c[2])),
                low=Decimal(str(c[3])),
                close=Decimal(str(c[4])),
                volume=int(c[5]),
                timestamp=_parse_timestamp(c[0]),
            )
            for c in raw_candles
        ]
    except (IndexError, TypeError, ValueError):
        return None

    return list(reversed(candles))  # Upstox returns newest-first; indicators expect oldest-first


def _parse_timestamp(raw: object) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None
