import pytest

from app.services.live_order_reconciliation import (
    BrokerOrderDataError,
    normalize_upstox_order,
    ReconciliationIntentCandidate,
    match_broker_order_to_intent,
)


def _order(**overrides):
    record = {
        "order_id": "upstox-order-123",
        "status": "open",
        "instrument_token": "NSE_EQ|INE062A01020",
        "transaction_type": "BUY",
        "order_type": "LIMIT",
        "quantity": 10,
        "filled_quantity": 0,
        "average_price": 0,
        "price": 100,
        "trigger_price": 0,
        "product": "D",
        "tag": "opaque-correlation",
    }
    record.update(overrides)
    return record


@pytest.mark.parametrize(
    ("raw_status", "expected"),
    [
        ("validation pending", "PENDING"),
        ("modify pending", "PENDING"),
        ("trigger pending", "TRIGGER_PENDING"),
        ("put order req received", "PENDING"),
        ("after market order req received", "PENDING"),
        ("open pending", "PENDING"),
        ("open", "OPEN"),
        ("modified", "OPEN"),
        ("not modified", "OPEN"),
        ("not cancelled", "OPEN"),
        ("cancel pending", "CANCEL_PENDING"),
        ("cancelled after market order", "CANCELLED"),
        ("cancelled", "CANCELLED"),
        ("rejected", "REJECTED"),
        ("complete", "FILLED"),
    ],
)
def test_documented_upstox_statuses_are_normalized(raw_status, expected):
    filled = 10 if raw_status == "complete" else 0
    result = normalize_upstox_order(_order(status=raw_status, filled_quantity=filled))
    assert result.state == expected
    assert result.raw_status == raw_status
    assert result.needs_review is False


def test_partial_fill_is_preserved_even_if_broker_status_is_open():
    result = normalize_upstox_order(_order(status="open", filled_quantity=3, average_price=99.5))
    assert result.state == "PARTIALLY_FILLED"
    assert result.filled_quantity == 3
    assert result.average_price == 99.5


def test_unknown_status_is_never_guessed_to_terminal_state():
    result = normalize_upstox_order(_order(status="new broker state"))
    assert result.state == "RECONCILIATION_REQUIRED"
    assert result.needs_review is True


def test_full_fill_quantity_overrides_stale_open_but_flags_review():
    result = normalize_upstox_order(_order(status="open", filled_quantity=10))
    assert result.state == "FILLED"
    assert result.needs_review is True


def test_complete_without_full_fill_is_quarantined_for_review():
    result = normalize_upstox_order(_order(status="complete", filled_quantity=2))
    assert result.state == "RECONCILIATION_REQUIRED"
    assert result.needs_review is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"order_id": None},
        {"status": ""},
        {"instrument_token": None},
        {"transaction_type": "LONG"},
        {"order_type": "STOP"},
        {"quantity": 0},
        {"quantity": -1},
        {"quantity": 1.5},
        {"filled_quantity": 11},
        {"average_price": float("nan")},
        {"average_price": -1},
    ],
)
def test_malformed_or_inconsistent_broker_data_is_rejected(overrides):
    with pytest.raises(BrokerOrderDataError):
        normalize_upstox_order(_order(**overrides))


def test_documented_instrument_key_alias_is_accepted():
    record = _order()
    record["instrument_key"] = record.pop("instrument_token")
    assert normalize_upstox_order(record).instrument_key == "NSE_EQ|INE062A01020"


def test_cancelled_order_pending_quantity_does_not_imply_fill():
    # Upstox's own order-book example can report pending_quantity equal to the
    # original quantity for a cancelled order; filled_quantity is used instead.
    result = normalize_upstox_order(_order(status="cancelled", pending_quantity=10))
    assert result.state == "CANCELLED"
    assert result.filled_quantity == 0


def _candidate(*, intent_id="intent-1", connection="connection-1", order_id=None, tag="opaque-correlation", snapshot=None):
    return ReconciliationIntentCandidate(
        intent_id=intent_id,
        broker_connection_id=connection,
        broker_order_id=order_id,
        broker_tag=tag,
        order_snapshot=snapshot or {
            "instrument_key": "NSE_EQ|INE062A01020",
            "side": "BUY",
            "order_type": "LIMIT",
            "quantity": 10,
            "limit_price": "100.00",
            "product": "D",
        },
    )


def test_intent_match_requires_exact_tag_and_all_economic_fields():
    order = normalize_upstox_order(_order())
    result = match_broker_order_to_intent(order, [_candidate()], broker_connection_id="connection-1")
    assert result.status == "MATCHED"
    assert result.intent_id == "intent-1"


def test_existing_broker_order_id_is_strong_correlation_but_not_economic_override():
    order = normalize_upstox_order(_order(order_id="upstox-order-123"))
    result = match_broker_order_to_intent(
        order, [_candidate(order_id="upstox-order-123", tag="different-tag")],
        broker_connection_id="connection-1",
    )
    assert result.status == "MATCHED"


def test_tag_match_with_wrong_instrument_is_quarantined():
    order = normalize_upstox_order(_order())
    candidate = _candidate(snapshot={
        "instrument_key": "NSE_EQ|WRONG", "side": "BUY", "order_type": "LIMIT",
        "quantity": 10, "limit_price": "100.00", "product": "D",
    })
    result = match_broker_order_to_intent(order, [candidate], broker_connection_id="connection-1")
    assert result.status == "ECONOMIC_MISMATCH"
    assert result.intent_id == "intent-1"


def test_tag_alone_cannot_match_missing_product_or_price():
    order = normalize_upstox_order(_order())
    missing_product = _candidate(snapshot={
        "instrument_key": "NSE_EQ|INE062A01020", "side": "BUY", "order_type": "LIMIT",
        "quantity": 10, "limit_price": "100.00",
    })
    result = match_broker_order_to_intent(order, [missing_product], broker_connection_id="connection-1")
    assert result.status == "ECONOMIC_MISMATCH"


def test_duplicate_tag_matches_are_ambiguous_even_if_economics_match():
    order = normalize_upstox_order(_order())
    result = match_broker_order_to_intent(
        order, [_candidate(intent_id="one"), _candidate(intent_id="two")],
        broker_connection_id="connection-1",
    )
    assert result.status == "AMBIGUOUS"
    assert result.intent_id is None


def test_candidates_from_another_broker_connection_are_never_linked():
    order = normalize_upstox_order(_order())
    result = match_broker_order_to_intent(
        order, [_candidate(connection="another-connection")],
        broker_connection_id="connection-1",
    )
    assert result.status == "NO_MATCH"


def test_unknown_or_conflicting_broker_status_is_not_auto_linked():
    order = normalize_upstox_order(_order(status="future unknown status"))
    result = match_broker_order_to_intent(order, [_candidate()], broker_connection_id="connection-1")
    assert result.status == "NEEDS_REVIEW"


def test_broker_order_id_match_with_wrong_quantity_is_quarantined():
    order = normalize_upstox_order(_order(order_id="upstox-order-123", quantity=9))
    result = match_broker_order_to_intent(
        order, [_candidate(order_id="upstox-order-123")], broker_connection_id="connection-1"
    )
    assert result.status == "ECONOMIC_MISMATCH"
