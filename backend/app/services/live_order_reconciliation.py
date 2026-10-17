"""Pure normalization helpers for broker order observations.

This module deliberately performs no network calls and has no database dependency.
Unknown or inconsistent broker data is escalated, never guessed into a terminal state.
"""
from dataclasses import dataclass
from typing import Any, Mapping


# Canonical application states. This is intentionally a conservative subset of
# Upstox's documented status strings; unrecognized statuses require review.
_STATUS_MAP = {
    "validation pending": "PENDING",
    "modify pending": "PENDING",
    "trigger pending": "TRIGGER_PENDING",
    "put order req received": "PENDING",
    "modify after market order req received": "PENDING",
    "after market order req received": "PENDING",
    "open pending": "PENDING",
    "open": "OPEN",
    "modified": "OPEN",
    "not modified": "OPEN",
    "not cancelled": "OPEN",
    "cancel pending": "CANCEL_PENDING",
    "cancelled after market order": "CANCELLED",
    "cancelled": "CANCELLED",
    "rejected": "REJECTED",
    "complete": "FILLED",
    "partially filled": "PARTIALLY_FILLED",
    "partial": "PARTIALLY_FILLED",
}


class BrokerOrderDataError(ValueError):
    """The broker response is malformed or internally inconsistent."""


@dataclass(frozen=True)
class NormalizedBrokerOrder:
    broker_order_id: str
    raw_status: str
    state: str
    instrument_key: str
    side: str
    order_type: str
    quantity: int
    filled_quantity: int
    average_price: float
    product: str | None
    tag: str | None
    needs_review: bool


def _required_text(record: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise BrokerOrderDataError(f"missing required field: {'/'.join(keys)}")


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise BrokerOrderDataError(f"{field} must be a non-negative integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise BrokerOrderDataError(f"{field} must be a non-negative integer") from exc
    if parsed < 0 or str(value).strip() not in {str(parsed), f"{parsed}.0"}:
        raise BrokerOrderDataError(f"{field} must be a non-negative integer")
    return parsed


def _nonnegative_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise BrokerOrderDataError(f"{field} must be a finite non-negative number")
    try:
        parsed = float(value or 0)
    except (TypeError, ValueError) as exc:
        raise BrokerOrderDataError(f"{field} must be a finite non-negative number") from exc
    import math
    if not math.isfinite(parsed) or parsed < 0:
        raise BrokerOrderDataError(f"{field} must be a finite non-negative number")
    return parsed


def normalize_upstox_order(record: Mapping[str, Any]) -> NormalizedBrokerOrder:
    """Normalize one order-book/history/detail record without guessing unknown states.

    Supports the field names documented by Upstox v2 order book, details and history.
    A successful normalization is not proof that the order belongs to a local intent;
    callers must separately verify account scope and all economic fields before linking.
    """
    if not isinstance(record, Mapping):
        raise BrokerOrderDataError("broker order record must be an object")

    broker_order_id = _required_text(record, "order_id")
    raw_status = _required_text(record, "status")
    instrument_key = _required_text(record, "instrument_token", "instrument_key")
    side = _required_text(record, "transaction_type").upper()
    order_type = _required_text(record, "order_type").upper()
    if side not in {"BUY", "SELL"}:
        raise BrokerOrderDataError("transaction_type must be BUY or SELL")
    if order_type not in {"MARKET", "LIMIT", "SL", "SL-M"}:
        raise BrokerOrderDataError("unsupported broker order_type")

    quantity = _nonnegative_int(record.get("quantity"), "quantity")
    filled = _nonnegative_int(record.get("filled_quantity", 0), "filled_quantity")
    average_price = _nonnegative_number(record.get("average_price", 0), "average_price")
    if quantity <= 0:
        raise BrokerOrderDataError("quantity must be greater than zero")
    if filled > quantity:
        raise BrokerOrderDataError("filled_quantity exceeds requested quantity")

    normalized_status = " ".join(raw_status.casefold().split())
    state = _STATUS_MAP.get(normalized_status)
    needs_review = state is None
    if state is None:
        state = "RECONCILIATION_REQUIRED"
    elif filled == quantity and filled > 0:
        # Fill quantity is strong evidence of execution, even if a stale status string
        # disagrees. A full-fill/status conflict is still flagged for review.
        if state != "FILLED":
            needs_review = True
        state = "FILLED"
    elif filled > 0 and state in {"OPEN", "PENDING", "TRIGGER_PENDING"}:
        state = "PARTIALLY_FILLED"
    elif state == "FILLED" and filled != quantity:
        needs_review = True
        state = "RECONCILIATION_REQUIRED"

    product_value = record.get("product")
    tag_value = record.get("tag")
    product = product_value.strip() if isinstance(product_value, str) and product_value.strip() else None
    tag = tag_value.strip() if isinstance(tag_value, str) and tag_value.strip() else None

    return NormalizedBrokerOrder(
        broker_order_id=broker_order_id,
        raw_status=raw_status,
        state=state,
        instrument_key=instrument_key,
        side=side,
        order_type=order_type,
        quantity=quantity,
        filled_quantity=filled,
        average_price=average_price,
        product=product,
        tag=tag,
        needs_review=needs_review,
    )
