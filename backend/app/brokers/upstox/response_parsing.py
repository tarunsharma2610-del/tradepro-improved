"""Pure validation helpers for official Upstox order response payloads.

These functions do not make network requests or mutate database state. They
normalize broker responses for a future, separately reviewed live lifecycle.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class FundsAndMarginV3:
    """Validated funds snapshot; cash and pledged margin remain separate."""

    available_to_trade_total: Decimal
    cash_available_to_trade_total: Decimal
    pledge_available_to_trade_total: Decimal
    realized_loss: Decimal
    unrealized_loss: Decimal
    unsettled_profit_today: Decimal
    unsettled_profit_previous_days: Decimal


@dataclass(frozen=True)
class BrokerOrderDetails:
    order_id: str
    status: str
    quantity: int
    filled_quantity: int
    average_price: Decimal
    tag: str | None = None
    instrument_token: str | None = None
    transaction_type: str | None = None


@dataclass(frozen=True)
class BrokerOrderHistoryEntry:
    order_id: str
    status: str
    quantity: int
    filled_quantity: int | None = None
    average_price: Decimal | None = None
    tag: str | None = None
    instrument_token: str | None = None
    transaction_type: str | None = None


@dataclass(frozen=True)
class BrokerTrade:
    order_id: str
    trade_id: str
    quantity: int
    price: Decimal
    side: str
    instrument_token: str | None = None
    exchange_timestamp: str | None = None


def parse_funds_and_margin_v3(payload: Any) -> FundsAndMarginV3:
    """Validate Funds & Margin V3 while keeping cash separate from pledge margin.

    `available_to_trade_total` includes cash and pledged collateral; callers
    must not treat it as a pure cash balance.
    """
    data = _success_data(payload, dict, "funds-and-margin-v3")
    available = _required_object(data.get("available_to_trade"), "data.available_to_trade")
    cash = _required_object(
        available.get("cash_available_to_trade"),
        "data.available_to_trade.cash_available_to_trade",
    )
    pledge = _required_object(
        available.get("pledge_available_to_trade"),
        "data.available_to_trade.pledge_available_to_trade",
    )
    cash_margin_used = _required_object(
        cash.get("margin_used"),
        "data.available_to_trade.cash_available_to_trade.margin_used",
    )
    losses = _required_object(
        cash_margin_used.get("loss"),
        "data.available_to_trade.cash_available_to_trade.margin_used.loss",
    )
    unavailable = _required_object(data.get("unavailable_to_trade"), "data.unavailable_to_trade")
    cash_unavailable = _required_object(
        unavailable.get("cash_unavailable_to_trade"),
        "data.unavailable_to_trade.cash_unavailable_to_trade",
    )
    unsettled = _required_object(
        cash_unavailable.get("unsettled_profit"),
        "data.unavailable_to_trade.cash_unavailable_to_trade.unsettled_profit",
    )

    return FundsAndMarginV3(
        available_to_trade_total=_decimal(
            available.get("total"), "data.available_to_trade.total", allow_zero=True
        ),
        cash_available_to_trade_total=_decimal(
            cash.get("total"), "data.available_to_trade.cash_available_to_trade.total", allow_zero=True
        ),
        pledge_available_to_trade_total=_decimal(
            pledge.get("total"), "data.available_to_trade.pledge_available_to_trade.total", allow_zero=True
        ),
        realized_loss=_decimal(
            losses.get("realised"),
            "data.available_to_trade.cash_available_to_trade.margin_used.loss.realised",
            allow_zero=True,
        ),
        unrealized_loss=_decimal(
            losses.get("unrealised"),
            "data.available_to_trade.cash_available_to_trade.margin_used.loss.unrealised",
            allow_zero=True,
        ),
        unsettled_profit_today=_signed_decimal(
            unsettled.get("todays_profit"),
            "data.unavailable_to_trade.cash_unavailable_to_trade.unsettled_profit.todays_profit",
        ),
        unsettled_profit_previous_days=_signed_decimal(
            unsettled.get("previous_days"),
            "data.unavailable_to_trade.cash_unavailable_to_trade.unsettled_profit.previous_days",
        ),
    )


def parse_place_order_response(payload: Any) -> tuple[str, ...]:
    """Validate Place Order V3 and return all broker child order IDs."""
    data = _success_data(payload, dict, "place-order")
    raw_ids = data.get("order_ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        raise ValueError("Place Order V3 response must contain a non-empty data.order_ids list.")

    order_ids = tuple(_required_text(value, "data.order_ids[]") for value in raw_ids)
    if len(set(order_ids)) != len(order_ids):
        raise ValueError("Place Order V3 response contains duplicate broker order IDs.")
    return order_ids


def parse_order_details(payload: Any, expected_order_id: str) -> BrokerOrderDetails:
    """Validate Order Details identity and the quantity/price fields used for reconciliation."""
    expected = _required_text(expected_order_id, "expected_order_id")
    data = _success_data(payload, dict, "order-details")
    order_id = _required_text(data.get("order_id"), "data.order_id")
    if order_id != expected:
        raise ValueError("Order Details response order_id does not match the requested broker order.")

    status = _required_text(data.get("status"), "data.status")
    quantity = _required_int(data.get("quantity"), "data.quantity", minimum=1)
    filled_quantity = _required_int(data.get("filled_quantity"), "data.filled_quantity", minimum=0)
    if filled_quantity > quantity:
        raise ValueError("data.filled_quantity cannot exceed data.quantity.")
    average_price = _decimal(data.get("average_price"), "data.average_price", allow_zero=True)

    return BrokerOrderDetails(
        order_id=order_id,
        status=status,
        quantity=quantity,
        filled_quantity=filled_quantity,
        average_price=average_price,
        tag=_optional_text(data.get("tag"), "data.tag"),
        instrument_token=_optional_text(data.get("instrument_token"), "data.instrument_token"),
        transaction_type=_optional_side(data.get("transaction_type"), "data.transaction_type"),
    )


def parse_order_history(payload: Any, expected_order_id: str | None = None) -> tuple[BrokerOrderHistoryEntry, ...]:
    """Validate Order History rows; an empty data list is a valid no-match result."""
    expected = _required_text(expected_order_id, "expected_order_id") if expected_order_id is not None else None
    rows = _success_data(payload, list, "order-history")
    result: list[BrokerOrderHistoryEntry] = []
    for index, row in enumerate(rows):
        prefix = f"data[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{prefix} must be an object.")
        order_id = _required_text(row.get("order_id"), f"{prefix}.order_id")
        if expected is not None and order_id != expected:
            raise ValueError("Order History response order_id does not match the requested broker order.")
        status = _required_text(row.get("status"), f"{prefix}.status")
        quantity = _required_int(row.get("quantity"), f"{prefix}.quantity", minimum=1)
        filled_raw = row.get("filled_quantity")
        filled = (
            _required_int(filled_raw, f"{prefix}.filled_quantity", minimum=0)
            if filled_raw is not None else None
        )
        if filled is not None and filled > quantity:
            raise ValueError(f"{prefix}.filled_quantity cannot exceed quantity.")
        average_raw = row.get("average_price")
        average = _decimal(average_raw, f"{prefix}.average_price", allow_zero=True) if average_raw is not None else None

        result.append(
            BrokerOrderHistoryEntry(
                order_id=order_id,
                status=status,
                quantity=quantity,
                filled_quantity=filled,
                average_price=average,
                tag=_optional_text(row.get("tag"), f"{prefix}.tag"),
                instrument_token=_optional_text(row.get("instrument_token"), f"{prefix}.instrument_token"),
                transaction_type=_optional_side(row.get("transaction_type"), f"{prefix}.transaction_type"),
            )
        )
    return tuple(result)


def parse_order_trades(payload: Any, expected_order_id: str) -> tuple[BrokerTrade, ...]:
    """Validate per-order trade rows and reject duplicate/mismatched trade identities."""
    expected = _required_text(expected_order_id, "expected_order_id")
    rows = _success_data(payload, list, "order-trades")
    result: list[BrokerTrade] = []
    seen_trade_ids: set[str] = set()

    for index, row in enumerate(rows):
        prefix = f"data[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"{prefix} must be an object.")
        order_id = _required_text(row.get("order_id"), f"{prefix}.order_id")
        if order_id != expected:
            raise ValueError("Order Trades response order_id does not match the requested broker order.")
        trade_id = _required_text(row.get("trade_id"), f"{prefix}.trade_id")
        if trade_id in seen_trade_ids:
            raise ValueError("Order Trades response contains duplicate trade IDs.")
        seen_trade_ids.add(trade_id)
        quantity = _required_int(row.get("quantity"), f"{prefix}.quantity", minimum=1)
        price = _decimal(row.get("average_price"), f"{prefix}.average_price", allow_zero=False)
        side = _required_side(row.get("transaction_type"), f"{prefix}.transaction_type")

        result.append(
            BrokerTrade(
                order_id=order_id,
                trade_id=trade_id,
                quantity=quantity,
                price=price,
                side=side,
                instrument_token=_optional_text(row.get("instrument_token"), f"{prefix}.instrument_token"),
                exchange_timestamp=_optional_text(row.get("exchange_timestamp"), f"{prefix}.exchange_timestamp"),
            )
        )
    return tuple(result)


def _success_data(payload: Any, expected_type: type, endpoint: str) -> Any:
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise ValueError(f"Upstox {endpoint} response is not marked successful.")
    data = payload.get("data")
    if not isinstance(data, expected_type):
        raise ValueError(f"Upstox {endpoint} response has an invalid data payload.")
    return data


def _required_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object.")
    return value


def _signed_decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field} must be a valid numeric amount.")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a valid numeric amount.") from None
    if not number.is_finite():
        raise ValueError(f"{field} must be a finite numeric amount.")
    return number


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string.")
    return value.strip()


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field)


def _required_int(value: Any, field: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{field} must be an integer greater than or equal to {minimum}.")
    return value


def _decimal(value: Any, field: str, *, allow_zero: bool) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field} must be a valid numeric price.")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a valid numeric price.") from None
    if not number.is_finite() or number < 0 or (not allow_zero and number == 0):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{field} must be a finite {qualifier} price.")
    return number


def _required_side(value: Any, field: str) -> str:
    side = _required_text(value, field).upper()
    if side not in {"BUY", "SELL"}:
        raise ValueError(f"{field} must be BUY or SELL.")
    return side


def _optional_side(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _required_side(value, field)
