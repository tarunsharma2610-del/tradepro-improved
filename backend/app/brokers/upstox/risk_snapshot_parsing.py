"""Strict parsing for read-only Upstox market-risk snapshots.

No parser in this module authorizes an order. Unknown or malformed response
shapes raise ValueError so callers can fail closed instead of guessing.
"""
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class FullMarketQuote:
    instrument_key: str
    last_price: Decimal
    observed_at: datetime


@dataclass(frozen=True)
class OpenBrokerPosition:
    instrument_key: str
    quantity: int


@dataclass(frozen=True)
class MarketHoliday:
    market_date: date
    holiday_type: str
    closed_exchanges: tuple[str, ...]
    open_exchanges: tuple[tuple[str, datetime, datetime], ...]


@dataclass(frozen=True)
class ExchangeTiming:
    exchange: str
    market_date: date
    opens_at: datetime
    closes_at: datetime


def parse_full_market_quote(payload: Any, expected_instrument_key: str) -> FullMarketQuote:
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise ValueError("Full Market Quote response is not marked successful.")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("Full Market Quote data must be an object.")
    matches = [
        row for row in data.values()
        if isinstance(row, dict) and row.get("instrument_token") == expected_instrument_key
    ]
    if len(matches) != 1:
        raise ValueError("Full Market Quote must contain exactly one matching instrument token.")
    row = matches[0]
    price = _positive_decimal(row.get("last_price"), "data.last_price")
    timestamp = row.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("data.timestamp must be an ISO-8601 timestamp.")
    try:
        observed_at = datetime.fromisoformat(timestamp)
    except ValueError:
        raise ValueError("data.timestamp must be an ISO-8601 timestamp.") from None
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("data.timestamp must include a timezone offset.")
    return FullMarketQuote(expected_instrument_key, price, observed_at.astimezone(timezone.utc))


def parse_open_positions(payload: Any) -> tuple[OpenBrokerPosition, ...]:
    rows = _success_list(payload, "positions")
    result: list[OpenBrokerPosition] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"data[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{prefix} must be an object.")
        key = _required_text(row.get("instrument_token"), f"{prefix}.instrument_token")
        quantity = row.get("quantity")
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError(f"{prefix}.quantity must be an integer.")
        if key in seen:
            raise ValueError(f"Duplicate broker position instrument {key}.")
        seen.add(key)
        if quantity:
            result.append(OpenBrokerPosition(key, quantity))
    return tuple(result)


def parse_market_holidays(payload: Any) -> tuple[MarketHoliday, ...]:
    rows = _success_list(payload, "market holidays")
    result: list[MarketHoliday] = []
    seen: set[date] = set()
    for index, row in enumerate(rows):
        prefix = f"data[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{prefix} must be an object.")
        try:
            market_date = date.fromisoformat(_required_text(row.get("date"), f"{prefix}.date"))
        except ValueError:
            raise ValueError(f"{prefix}.date must be YYYY-MM-DD.") from None
        if market_date in seen:
            raise ValueError(f"Duplicate market calendar date {market_date}.")
        seen.add(market_date)
        holiday_type = _required_text(row.get("holiday_type"), f"{prefix}.holiday_type")
        closed = row.get("closed_exchanges", [])
        opened = row.get("open_exchanges", [])
        if not isinstance(closed, list) or any(not isinstance(v, str) or not v.strip() for v in closed):
            raise ValueError(f"{prefix}.closed_exchanges must be a list of exchange names.")
        if not isinstance(opened, list):
            raise ValueError(f"{prefix}.open_exchanges must be a list.")
        open_rows: list[tuple[str, datetime, datetime]] = []
        for sub_index, entry in enumerate(opened):
            ep = f"{prefix}.open_exchanges[{sub_index}]"
            if not isinstance(entry, dict):
                raise ValueError(f"{ep} must be an object.")
            exchange = _required_text(entry.get("exchange"), f"{ep}.exchange")
            start = _epoch_ms(entry.get("start_time"), f"{ep}.start_time")
            end = _epoch_ms(entry.get("end_time"), f"{ep}.end_time")
            if end <= start:
                raise ValueError(f"{ep} end_time must follow start_time.")
            open_rows.append((exchange, start, end))
        result.append(MarketHoliday(market_date, holiday_type, tuple(closed), tuple(open_rows)))
    return tuple(result)


def parse_market_timings(payload: Any, expected_date: date, expected_exchange: str = "NSE") -> ExchangeTiming:
    rows = _success_list(payload, "market timings")
    matches = [row for row in rows if isinstance(row, dict) and row.get("exchange") == expected_exchange]
    if len(matches) != 1:
        raise ValueError(f"Market Timings must contain exactly one {expected_exchange} row.")
    row = matches[0]
    opens_at = _epoch_ms(row.get("start_time"), "data.start_time")
    closes_at = _epoch_ms(row.get("end_time"), "data.end_time")
    if opens_at.date() != expected_date or closes_at.date() != expected_date or closes_at <= opens_at:
        raise ValueError("Market timing timestamps do not describe the requested date/session.")
    return ExchangeTiming(expected_exchange, expected_date, opens_at, closes_at)


def _success_list(payload: Any, endpoint: str) -> list[Any]:
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise ValueError(f"Upstox {endpoint} response is not marked successful.")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError(f"Upstox {endpoint} data must be a list.")
    return rows


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text.")
    return value.strip()


def _positive_decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field} must be a positive finite number.")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a positive finite number.") from None
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError(f"{field} must be a positive finite number.")
    return parsed


def _epoch_ms(value: Any, field: str) -> datetime:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{field} must be a positive epoch-millisecond timestamp.")
    try:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        raise ValueError(f"{field} is outside the supported timestamp range.") from None
