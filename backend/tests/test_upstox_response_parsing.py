import pytest
from decimal import Decimal

from app.brokers.upstox.response_parsing import (
    parse_order_details,
    parse_order_history,
    parse_order_trades,
    parse_place_order_response,
)


def test_parse_place_order_response_supports_multiple_child_order_ids():
    payload = {"status": "success", "data": {"order_ids": ["child-1", "child-2"]}}
    assert parse_place_order_response(payload) == ("child-1", "child-2")


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"status": "error", "data": {"order_ids": ["child-1"]}},
        {"status": "success", "data": {}},
        {"status": "success", "data": {"order_ids": []}},
        {"status": "success", "data": {"order_ids": ["child-1", " "]}},
        {"status": "success", "data": {"order_ids": ["child-1", "child-1"]}},
    ],
)
def test_parse_place_order_response_rejects_malformed_or_duplicate_ids(payload):
    with pytest.raises(ValueError):
        parse_place_order_response(payload)


def test_parse_order_details_validates_identity_and_partial_fill_fields():
    payload = {
        "status": "success",
        "data": {
            "order_id": "child-1",
            "status": "partially filled",
            "quantity": 10,
            "filled_quantity": 3,
            "average_price": 123.45,
            "tag": "tp-tag",
            "instrument_token": "NSE_EQ|TEST",
            "transaction_type": "BUY",
        },
    }
    parsed = parse_order_details(payload, "child-1")
    assert parsed.order_id == "child-1"
    assert parsed.status == "partially filled"
    assert parsed.quantity == 10
    assert parsed.filled_quantity == 3
    assert parsed.average_price == Decimal("123.45")
    assert parsed.transaction_type == "BUY"


@pytest.mark.parametrize(
    ("payload", "expected_id"),
    [
        ({"status": "success", "data": {"order_id": "other", "status": "open", "quantity": 1, "filled_quantity": 0, "average_price": 0}}, "child-1"),
        ({"status": "success", "data": {"status": "open", "quantity": 1, "filled_quantity": 0, "average_price": 0}}, "child-1"),
        ({"status": "success", "data": {"order_id": "child-1", "status": "open", "quantity": 0, "filled_quantity": 0, "average_price": 0}}, "child-1"),
        ({"status": "success", "data": {"order_id": "child-1", "status": "open", "quantity": 1, "filled_quantity": 2, "average_price": 0}}, "child-1"),
        ({"status": "success", "data": {"order_id": "child-1", "status": "open", "quantity": 1, "filled_quantity": 0, "average_price": "NaN"}}, "child-1"),
    ],
)
def test_parse_order_details_rejects_invalid_identity_or_numbers(payload, expected_id):
    with pytest.raises(ValueError):
        parse_order_details(payload, expected_id)


def test_parse_order_history_accepts_empty_list_and_valid_rows():
    assert parse_order_history({"status": "success", "data": []}) == ()
    payload = {
        "status": "success",
        "data": [
            {
                "order_id": "child-1",
                "status": "complete",
                "quantity": 2,
                "filled_quantity": 2,
                "average_price": 123.4,
                "tag": "tp-tag",
                "transaction_type": "SELL",
            }
        ],
    }
    rows = parse_order_history(payload)
    assert len(rows) == 1
    assert rows[0].order_id == "child-1"
    assert rows[0].filled_quantity == 2
    assert rows[0].transaction_type == "SELL"


def test_parse_order_history_rejects_mismatched_and_duplicate_order_ids():
    with pytest.raises(ValueError, match="does not match"):
        parse_order_history(
            {"status": "success", "data": [{"order_id": "other", "status": "open", "quantity": 1}]},
            expected_order_id="child-1",
        )
    with pytest.raises(ValueError, match="duplicate"):
        parse_order_history(
            {
                "status": "success",
                "data": [
                    {"order_id": "child-1", "status": "open", "quantity": 1},
                    {"order_id": "child-1", "status": "complete", "quantity": 1},
                ],
            }
        )


def test_parse_order_trades_accepts_empty_and_valid_trade_rows():
    assert parse_order_trades({"status": "success", "data": []}, "child-1") == ()
    payload = {
        "status": "success",
        "data": [
            {
                "order_id": "child-1",
                "trade_id": "trade-1",
                "quantity": 2,
                "average_price": 123.45,
                "transaction_type": "BUY",
                "instrument_token": "NSE_EQ|TEST",
            }
        ],
    }
    trades = parse_order_trades(payload, "child-1")
    assert len(trades) == 1
    assert trades[0].trade_id == "trade-1"
    assert trades[0].quantity == 2
    assert trades[0].price == Decimal("123.45")
    assert trades[0].side == "BUY"


@pytest.mark.parametrize(
    "rows",
    [
        [{"order_id": "other", "trade_id": "trade-1", "quantity": 1, "average_price": 10, "transaction_type": "BUY"}],
        [{"order_id": "child-1", "trade_id": "", "quantity": 1, "average_price": 10, "transaction_type": "BUY"}],
        [{"order_id": "child-1", "trade_id": "trade-1", "quantity": 0, "average_price": 10, "transaction_type": "BUY"}],
        [{"order_id": "child-1", "trade_id": "trade-1", "quantity": 1, "average_price": -10, "transaction_type": "BUY"}],
        [{"order_id": "child-1", "trade_id": "trade-1", "quantity": 1, "average_price": 10, "transaction_type": "SHORT"}],
        [
            {"order_id": "child-1", "trade_id": "trade-1", "quantity": 1, "average_price": 10, "transaction_type": "BUY"},
            {"order_id": "child-1", "trade_id": "trade-1", "quantity": 1, "average_price": 10, "transaction_type": "BUY"},
        ],
    ],
)
def test_parse_order_trades_rejects_malformed_or_duplicate_trades(rows):
    with pytest.raises(ValueError):
        parse_order_trades({"status": "success", "data": rows}, "child-1")
