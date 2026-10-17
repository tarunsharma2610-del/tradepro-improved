"""Pure normalization helpers for broker order and trade observations.

This module deliberately performs no network calls and has no database dependency.
Unknown or inconsistent broker data is escalated, never guessed into a terminal state.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
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
    price: float
    trigger_price: float
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
    price = _nonnegative_number(record.get("price", 0), "price")
    trigger_price = _nonnegative_number(record.get("trigger_price", 0), "trigger_price")
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
        price=price,
        trigger_price=trigger_price,
        product=product,
        tag=tag,
        needs_review=needs_review,
    )


@dataclass(frozen=True)
class ReconciliationIntentCandidate:
    """Minimal local intent fields required for safe matching.

    Candidates must be loaded for the broker connection authenticated by the caller.
    The connection ID is still checked here as a defense against cross-account linking.
    """
    intent_id: str
    broker_connection_id: str
    broker_order_id: str | None
    broker_tag: str | None
    order_snapshot: Mapping[str, Any]


@dataclass(frozen=True)
class IntentMatchResult:
    status: str
    intent_id: str | None
    reason: str


def _snapshot_value(snapshot: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in snapshot and snapshot[key] is not None:
            return snapshot[key]
    return None


def _decimal_equal(left: Any, right: Any) -> bool:
    from decimal import Decimal, InvalidOperation
    try:
        a, b = Decimal(str(left)), Decimal(str(right))
    except (InvalidOperation, TypeError, ValueError):
        return False
    return a.is_finite() and b.is_finite() and a == b


def _economic_mismatch(order: NormalizedBrokerOrder, snapshot: Mapping[str, Any]) -> str | None:
    """Return a mismatch reason; missing required snapshot fields are mismatches, not wildcards."""
    expected_instrument = _snapshot_value(snapshot, "instrument_key", "instrument_token")
    expected_side = _snapshot_value(snapshot, "side", "transaction_type")
    expected_type = _snapshot_value(snapshot, "order_type")
    expected_quantity = _snapshot_value(snapshot, "quantity")
    expected_product = _snapshot_value(snapshot, "product")
    if not all(value is not None for value in (
        expected_instrument, expected_side, expected_type, expected_quantity, expected_product
    )):
        return "local intent is missing a required economic field"
    if str(expected_instrument).strip() != order.instrument_key:
        return "instrument key differs"
    if str(expected_side).strip().upper() != order.side:
        return "transaction side differs"
    if str(expected_type).strip().upper() != order.order_type:
        return "order type differs"
    try:
        expected_qty = int(expected_quantity)
        if isinstance(expected_quantity, bool) or str(expected_quantity).strip() not in {
            str(expected_qty), f"{expected_qty}.0"
        }:
            return "local quantity is invalid"
    except (TypeError, ValueError):
        return "local quantity is invalid"
    if expected_qty != order.quantity:
        return "requested quantity differs"
    if str(expected_product).strip().upper() != (order.product or "").upper():
        return "product differs"

    if order.order_type in {"LIMIT", "SL"}:
        expected_price = _snapshot_value(snapshot, "limit_price", "price")
        if expected_price is None or not _decimal_equal(expected_price, order.price) or order.price <= 0:
            return "limit price differs or is missing"
    if order.order_type in {"SL", "SL-M"}:
        expected_trigger = _snapshot_value(snapshot, "trigger_price")
        if expected_trigger is None or not _decimal_equal(expected_trigger, order.trigger_price) or order.trigger_price <= 0:
            return "trigger price differs or is missing"
    return None


def match_broker_order_to_intent(
    order: NormalizedBrokerOrder,
    candidates: list[ReconciliationIntentCandidate] | tuple[ReconciliationIntentCandidate, ...],
    *,
    broker_connection_id: str,
) -> IntentMatchResult:
    """Match only within one authenticated broker connection; never guess on ambiguity.

    Existing broker-order ID is the strongest correlation. Otherwise, an exact non-empty
    broker tag may nominate one candidate, but a tag alone is insufficient: all required
    economic fields must also match. This pure helper persists nothing and performs no I/O.
    """
    scoped = [
        candidate for candidate in candidates
        if str(candidate.broker_connection_id) == str(broker_connection_id)
    ]

    by_order_id = [c for c in scoped if c.broker_order_id and c.broker_order_id == order.broker_order_id]
    if len(by_order_id) > 1:
        return IntentMatchResult("AMBIGUOUS", None, "multiple local intents already reference this broker order ID")
    nominated: list[ReconciliationIntentCandidate]
    if by_order_id:
        nominated = by_order_id
    else:
        if not order.tag:
            return IntentMatchResult("NO_MATCH", None, "no known broker order ID or non-empty correlation tag matched")
        nominated = [c for c in scoped if c.broker_tag and c.broker_tag == order.tag]
        if not nominated:
            return IntentMatchResult("NO_MATCH", None, "no local intent has this exact broker tag in the selected connection")
        if len(nominated) > 1:
            return IntentMatchResult("AMBIGUOUS", None, "multiple local intents share this broker tag")

    candidate = nominated[0]
    mismatch = _economic_mismatch(order, candidate.order_snapshot)
    if mismatch:
        return IntentMatchResult("ECONOMIC_MISMATCH", candidate.intent_id, mismatch)
    if order.needs_review or order.state == "RECONCILIATION_REQUIRED":
        return IntentMatchResult("NEEDS_REVIEW", candidate.intent_id, "broker observation is flagged for manual review")
    return IntentMatchResult("MATCHED", candidate.intent_id, "unique correlation and all required economic fields match")



@dataclass(frozen=True)
class NormalizedBrokerFill:
    """Validated single executed trade from Upstox order-trades response."""
    broker_trade_id: str
    broker_order_id: str
    instrument_key: str
    side: str
    quantity: int
    price: Decimal
    executed_at: datetime
    product: str | None
    exchange: str | None
    order_type: str | None
    trading_symbol: str | None
    exchange_order_id: str | None
    order_ref_id: str | None


def _parse_upstox_trade_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise BrokerOrderDataError("trade timestamp is missing")
    raw = value.strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
        for fmt in ("%d-%b-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            raise BrokerOrderDataError("trade timestamp format is unsupported")
    if parsed.tzinfo is None:
        # Upstox's documented exchange_timestamp is exchange-local time (India).
        from zoneinfo import ZoneInfo
        parsed = parsed.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
    return parsed.astimezone(timezone.utc)


def normalize_upstox_trade(record: Mapping[str, Any]) -> NormalizedBrokerFill:
    """Validate one Upstox GET /order/trades record; no network or persistence.

    Uses exchange_timestamp as execution time, trade_id as the stable fill identity,
    and average_price as the execution price documented by Upstox.
    """
    if not isinstance(record, Mapping):
        raise BrokerOrderDataError("trade record must be an object")
    trade_id = _required_text(record, "trade_id")
    order_id = _required_text(record, "order_id")
    instrument = _required_text(record, "instrument_token")
    side = _required_text(record, "transaction_type").upper()
    if side not in {"BUY", "SELL"}:
        raise BrokerOrderDataError("transaction_type must be BUY or SELL")
    quantity = _nonnegative_int(record.get("quantity"), "quantity")
    if quantity <= 0:
        raise BrokerOrderDataError("trade quantity must be positive")
    raw_price = record.get("average_price")
    try:
        price = Decimal(str(raw_price))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise BrokerOrderDataError("average_price must be a finite positive number") from exc
    if not price.is_finite() or price <= 0:
        raise BrokerOrderDataError("average_price must be a finite positive number")
    if len(trade_id) > 128 or len(order_id) > 128 or len(instrument) > 128:
        raise BrokerOrderDataError("trade, order and instrument identifiers must be at most 128 characters")

    product_value = record.get("product")
    order_type_value = record.get("order_type")
    exchange_value = record.get("exchange")
    symbol_value = record.get("trading_symbol") or record.get("tradingsymbol")
    exchange_order_value = record.get("exchange_order_id")
    order_ref_value = record.get("order_ref_id")
    def optional_text(value: Any, field: str, limit: int = 128) -> str | None:
        if value is None or value == "":
            return None
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
            raise BrokerOrderDataError(f"{field} must be non-empty text of at most {limit} characters")
        return value.strip()

    return NormalizedBrokerFill(
        broker_trade_id=trade_id,
        broker_order_id=order_id,
        instrument_key=instrument,
        side=side,
        quantity=quantity,
        price=price,
        executed_at=_parse_upstox_trade_timestamp(record.get("exchange_timestamp")),
        product=optional_text(product_value, "product", 16),
        exchange=optional_text(exchange_value, "exchange", 16),
        order_type=optional_text(order_type_value, "order_type", 16),
        trading_symbol=optional_text(symbol_value, "trading_symbol"),
        exchange_order_id=optional_text(exchange_order_value, "exchange_order_id"),
        order_ref_id=optional_text(order_ref_value, "order_ref_id"),
    )


@dataclass(frozen=True)
class FillEvidenceResolution:
    state: str
    reason: str


def resolve_order_state_with_fill_evidence(
    observed_state: str,
    *,
    requested_quantity: int,
    persisted_fill_quantity: int,
) -> FillEvidenceResolution:
    """Resolve stale status observations against persisted trade evidence.

    Trade identities are stronger evidence than a stale active/cancel status, but
    contradictory quantities/statuses are quarantined rather than guessed.
    """
    observed = observed_state.strip().upper()
    if requested_quantity <= 0 or persisted_fill_quantity < 0:
        return FillEvidenceResolution("RECONCILIATION_REQUIRED", "invalid requested or persisted fill quantity")
    if persisted_fill_quantity > requested_quantity:
        return FillEvidenceResolution("RECONCILIATION_REQUIRED", "persisted fills exceed requested order quantity")
    if persisted_fill_quantity == 0:
        return FillEvidenceResolution(observed, "no persisted fill evidence")
    if persisted_fill_quantity == requested_quantity:
        return FillEvidenceResolution("FILLED", "persisted trade quantities confirm the full requested quantity")
    if observed in {"OPEN", "PENDING", "TRIGGER_PENDING", "CANCEL_PENDING", "PARTIALLY_FILLED"}:
        return FillEvidenceResolution("PARTIALLY_FILLED", "persisted trades override stale active order status")
    if observed == "CANCELLED":
        return FillEvidenceResolution(
            "PARTIALLY_FILLED_CANCELLED",
            "persisted trades confirm partial execution before cancellation",
        )
    if observed in {"FILLED", "REJECTED"}:
        return FillEvidenceResolution(
            "RECONCILIATION_REQUIRED",
            "broker status conflicts with persisted partial trade quantity",
        )
    if observed == "PARTIALLY_FILLED_CANCELLED":
        return FillEvidenceResolution(observed, "partial fill and cancellation both confirmed")
    return FillEvidenceResolution(
        "RECONCILIATION_REQUIRED",
        "fill evidence conflicts with the observed broker status",
    )
