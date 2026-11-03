"""Strict normalization for Upstox long-term equity holdings snapshots."""
from decimal import Decimal, InvalidOperation
from typing import Any


def _decimal(value: Any, field: str, *, nullable: bool = False, places: str = "0.01") -> str | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or value is None:
        raise ValueError(f"Missing or invalid holding field: {field}")
    try:
        number = Decimal(str(value))
        if not number.is_finite():
            raise ValueError(f"Non-finite holding field: {field}")
        if number == 0:
            number = abs(number)
        return format(number.quantize(Decimal(places)), "f")
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid holding field: {field}") from exc


def _quantity(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Invalid holding quantity: {field}")
    return value


def normalize_upstox_holdings(payload: Any) -> list[dict[str, Any]]:
    """Validate Get Holdings response; keep settlement/collateral quantities distinct.

    This function does not add collateral or T+1 quantities to settled quantity,
    infer unknown instruments, or treat broker P&L as a lifetime ledger.
    """
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise ValueError("Upstox holdings response status is not success.")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError("Upstox holdings response data must be a list.")

    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Invalid holding row at index {index}.")
        isin = row.get("isin")
        instrument_key = row.get("instrument_token")
        symbol = row.get("trading_symbol") or row.get("tradingsymbol")
        exchange = row.get("exchange")
        if not all(isinstance(value, str) and value.strip() for value in (isin, instrument_key, symbol, exchange)):
            raise ValueError(f"Missing holding identity in row {index}.")

        quantity = _quantity(row.get("quantity"), f"data[{index}].quantity")
        normalized.append({
            "isin": isin.strip(),
            "instrument_key": instrument_key.strip(),
            "trading_symbol": symbol.strip(),
            "company_name": row.get("company_name") if isinstance(row.get("company_name"), str) else None,
            "exchange": exchange.strip(),
            "product": row.get("product") if isinstance(row.get("product"), str) else None,
            "quantity": quantity,
            "average_price": _decimal(row.get("average_price"), f"data[{index}].average_price", nullable=quantity == 0, places="0.0001"),
            "last_price": _decimal(row.get("last_price"), f"data[{index}].last_price", places="0.0001"),
            "close_price": _decimal(row.get("close_price"), f"data[{index}].close_price", nullable=True, places="0.0001"),
            "broker_reported_pnl": _decimal(row.get("pnl"), f"data[{index}].pnl", nullable=True),
            "day_change": _decimal(row.get("day_change"), f"data[{index}].day_change", nullable=True),
            "day_change_percentage": _decimal(row.get("day_change_percentage"), f"data[{index}].day_change_percentage", nullable=True, places="0.0001"),
            "haircut": _decimal(row.get("haircut"), f"data[{index}].haircut", nullable=True, places="0.0001"),
            "cnc_used_quantity": _quantity(row.get("cnc_used_quantity", 0), f"data[{index}].cnc_used_quantity"),
            "collateral_quantity": _quantity(row.get("collateral_quantity", 0), f"data[{index}].collateral_quantity"),
            "collateral_update_quantity": _quantity(row.get("collateral_update_quantity", 0), f"data[{index}].collateral_update_quantity"),
            "t1_quantity": _quantity(row.get("t1_quantity", 0), f"data[{index}].t1_quantity"),
            "collateral_type": row.get("collateral_type") if isinstance(row.get("collateral_type"), str) else None,
        })
    return normalized
