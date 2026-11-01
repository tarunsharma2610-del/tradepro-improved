"""Strict normalization for read-only broker funds snapshots."""
from decimal import Decimal, InvalidOperation
from typing import Any


def _amount(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"Missing or invalid funds field: {field}")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid funds field: {field}") from exc
    if not amount.is_finite():
        raise ValueError(f"Non-finite funds field: {field}")
    return amount.quantize(Decimal("0.01"))


def normalize_upstox_funds_v3(payload: Any) -> dict[str, Decimal]:
    """Validate the documented V3 envelope and extract semantically distinct amounts.

    Deliberately does not infer withdrawable cash, account equity, or portfolio
    cash balance from available-to-trade margin.
    """
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise ValueError("Upstox funds response status is not success.")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("Upstox funds response data is missing.")
    available = data.get("available_to_trade")
    unavailable = data.get("unavailable_to_trade")
    if not isinstance(available, dict) or not isinstance(unavailable, dict):
        raise ValueError("Upstox funds response sections are missing.")
    cash = available.get("cash_available_to_trade")
    pledge = available.get("pledge_available_to_trade")
    cash_unavailable = unavailable.get("cash_unavailable_to_trade")
    if not all(isinstance(section, dict) for section in (cash, pledge, cash_unavailable)):
        raise ValueError("Upstox funds response breakdown is incomplete.")
    unsettled = cash_unavailable.get("unsettled_profit")
    if not isinstance(unsettled, dict):
        raise ValueError("Upstox unsettled-profit breakdown is missing.")
    return {
        "total_available_to_trade": _amount(available.get("total"), "available_to_trade.total"),
        "cash_available_to_trade": _amount(cash.get("total"), "cash_available_to_trade.total"),
        "pledge_available_to_trade": _amount(pledge.get("total"), "pledge_available_to_trade.total"),
        "unsettled_profit_today": _amount(unsettled.get("todays_profit"), "unsettled_profit.todays_profit"),
        "unsettled_profit_previous_days": _amount(unsettled.get("previous_days"), "unsettled_profit.previous_days"),
    }
