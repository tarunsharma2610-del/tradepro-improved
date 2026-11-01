"""Strict normalization for Upstox short-term position snapshots."""
from decimal import Decimal, InvalidOperation
from typing import Any


def _decimal(value: Any, field: str, *, nullable: bool = False, places: str = "0.01") -> str | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or value is None:
        raise ValueError(f"Missing or invalid position field: {field}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid position field: {field}") from exc
    if not number.is_finite():
        raise ValueError(f"Non-finite position field: {field}")
    return format(number.quantize(Decimal(places)), "f")


def normalize_upstox_positions(payload: Any) -> list[dict[str, Any]]:
    """Validate the documented Get Positions envelope and preserve broker semantics.

    'realised' and 'unrealised' are broker-reported position/day figures, not
    lifetime portfolio P&L. No instrument mapping or synthetic positions are created.
    """
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise ValueError("Upstox positions response status is not success.")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError("Upstox positions response data must be a list.")
    normalized = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Invalid position row at index {index}.")
        instrument_key = row.get("instrument_token")
        symbol = row.get("trading_symbol") or row.get("tradingsymbol")
        exchange = row.get("exchange")
        product = row.get("product")
        quantity = row.get("quantity")
        if not all(isinstance(value, str) and value.strip() for value in (instrument_key, symbol, exchange, product)):
            raise ValueError(f"Missing instrument identity in position row {index}.")
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError(f"Invalid quantity in position row {index}.")
        average_price = row.get("average_price")
        normalized.append({
            "instrument_key": instrument_key,
            "trading_symbol": symbol,
            "exchange": exchange,
            "product": product,
            "quantity": quantity,
            "average_price": _decimal(average_price, f"data[{index}].average_price", nullable=quantity == 0, places="0.0001"),
            "last_price": _decimal(row.get("last_price"), f"data[{index}].last_price", places="0.0001"),
            "broker_reported_pnl": _decimal(row.get("pnl"), f"data[{index}].pnl"),
            "broker_reported_unrealised": _decimal(row.get("unrealised"), f"data[{index}].unrealised"),
            "broker_reported_realised": _decimal(row.get("realised"), f"data[{index}].realised"),
        })
    return normalized
