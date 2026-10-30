"""Strict parser for Upstox V3 historical/intraday candle responses.

The provider's documented candle row is
[timestamp, open, high, low, close, volume, open_interest]. V3 examples
return newest-first rows; this parser normalizes them to chronological order
for the strategy and backtest indicator engines. It accepts only successful,
schema-valid responses and never manufactures missing market data.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import math
from typing import Any

from app.services.indicators import Candle


def _decimal(value: object) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("Boolean is not a valid market price.")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid numeric candle field.") from exc
    if not result.is_finite():
        raise ValueError("Non-finite numeric candle field.")
    return result


def parse_candles(response_data: Any) -> list[Candle] | None:
    """Parse documented Upstox V3 candle rows into oldest-first Candle objects.

    Returns None for provider errors or malformed/incomplete rows. The
    official response examples include an offset-aware ISO timestamp and
    seven fields per row; field order and ordering are verified against the
    provider's documented response contract.
    """
    if not isinstance(response_data, dict) or response_data.get("status") != "success":
        return None
    data = response_data.get("data")
    if not isinstance(data, dict):
        return None
    raw_candles = data.get("candles")
    if not isinstance(raw_candles, list) or not raw_candles:
        return None

    candles: list[Candle] = []
    timestamps: set[datetime] = set()
    try:
        for row in raw_candles:
            if not isinstance(row, (list, tuple)) or len(row) != 7:
                return None
            timestamp_raw = row[0]
            if not isinstance(timestamp_raw, str):
                return None
            timestamp = datetime.fromisoformat(timestamp_raw)
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                return None
            timestamp_utc = timestamp.astimezone(timezone.utc)
            if timestamp_utc in timestamps:
                return None
            timestamps.add(timestamp_utc)

            open_price, high, low, close = (_decimal(value) for value in row[1:5])
            volume_value = _decimal(row[5])
            _decimal(row[6])  # Validate the documented open-interest field too.
            if min(open_price, high, low, close) <= 0:
                return None
            if low > min(open_price, close) or high < max(open_price, close) or low > high:
                return None
            if volume_value < 0 or volume_value != volume_value.to_integral_value():
                return None
            volume = int(volume_value)
            candles.append(
                Candle(
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    timestamp=timestamp,
                )
            )
    except (ValueError, TypeError, InvalidOperation, OverflowError):
        return None

    return sorted(candles, key=lambda candle: candle.timestamp.astimezone(timezone.utc))
