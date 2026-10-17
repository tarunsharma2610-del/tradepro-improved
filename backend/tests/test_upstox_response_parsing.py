import pytest
from decimal import Decimal

from app.brokers.upstox.response_parsing import (
    parse_funds_and_margin_v3,
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


def test_parse_order_history_accepts_multiple_status_events_for_one_order_and_rejects_mismatch():
    # Order History is a timeline; Upstox can return multiple status events
    # carrying the same order_id. These are not duplicate child orders.
    history = parse_order_history(
        {
            "status": "success",
            "data": [
                {"order_id": "child-1", "status": "open pending", "quantity": 1},
                {"order_id": "child-1", "status": "open", "quantity": 1},
                {"order_id": "child-1", "status": "complete", "quantity": 1},
            ],
        }
    )
    assert [entry.status for entry in history] == ["open pending", "open", "complete"]

    with pytest.raises(ValueError, match="does not match"):
        parse_order_history(
            {"status": "success", "data": [{"order_id": "other", "status": "open", "quantity": 1}]},
            expected_order_id="child-1",
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


def _funds_v3_payload():
    return {
        "status": "success",
        "data": {
            "available_to_trade": {
                "total": 5379.03,
                "cash_available_to_trade": {
                    "total": 5117.34,
                    "margin_used": {
                        "loss": {"realised": 2.50, "unrealised": 1.25},
                    },
                },
                "pledge_available_to_trade": {"total": 261.69},
            },
            "unavailable_to_trade": {
                "cash_unavailable_to_trade": {
                    "unsettled_profit": {"todays_profit": -5.0, "previous_days": 10.0}
                },
                "pledge_unavailable_to_trade": {"equity": 0.0, "mutual_funds": 0.0},
            },
        },
    }


def test_parse_funds_and_margin_v3_keeps_cash_and_pledged_margin_separate():
    funds = parse_funds_and_margin_v3(_funds_v3_payload())
    assert funds.available_to_trade_total == Decimal("5379.03")
    assert funds.cash_available_to_trade_total == Decimal("5117.34")
    assert funds.pledge_available_to_trade_total == Decimal("261.69")
    assert funds.realized_loss == Decimal("2.50")
    assert funds.unrealized_loss == Decimal("1.25")
    assert funds.unsettled_profit_today == Decimal("-5.0")
    assert funds.unsettled_profit_previous_days == Decimal("10.0")
    # The total is not an alias for cash: pledged margin must not be silently
    # treated as withdrawable/settled cash by future risk code.
    assert funds.available_to_trade_total != funds.cash_available_to_trade_total


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(status="error"),
        lambda p: p["data"].pop("available_to_trade"),
        lambda p: p["data"]["available_to_trade"].pop("cash_available_to_trade"),
        lambda p: p["data"]["available_to_trade"].pop("pledge_available_to_trade"),
        lambda p: p["data"]["available_to_trade"].update(total="NaN"),
        lambda p: p["data"]["available_to_trade"]["cash_available_to_trade"].update(total=-1),
        lambda p: p["data"]["available_to_trade"]["cash_available_to_trade"]["margin_used"]["loss"].update(unrealised="Infinity"),
        lambda p: p["data"]["unavailable_to_trade"]["cash_unavailable_to_trade"]["unsettled_profit"].update(todays_profit="not-a-number"),
    ],
)
def test_parse_funds_and_margin_v3_rejects_error_or_malformed_values(mutate):
    payload = _funds_v3_payload()
    mutate(payload)
    with pytest.raises(ValueError):
        parse_funds_and_margin_v3(payload)


def test_parse_funds_and_margin_v3_rejects_423_maintenance_error_payload():
    payload = {"status": "error", "errors": [{"errorCode": "UDAPI100072"}]}
    with pytest.raises(ValueError, match="not marked successful"):
        parse_funds_and_margin_v3(payload)
