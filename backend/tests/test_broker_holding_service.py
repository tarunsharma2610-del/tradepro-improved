import pytest

from app.services.broker_holding_service import normalize_upstox_holdings


def _payload():
    return {
        "status": "success",
        "data": [{
            "isin": "INE528G01035",
            "cnc_used_quantity": 2,
            "collateral_type": "WC",
            "company_name": "YES BANK LTD.",
            "haircut": 0.2,
            "product": "D",
            "quantity": 36,
            "trading_symbol": "YESBANK",
            "last_price": 17.05,
            "close_price": 17.05,
            "pnl": -61.2,
            "day_change": 0,
            "day_change_percentage": 0,
            "instrument_token": "NSE_EQ|INE528G01035",
            "average_price": 18.75,
            "collateral_quantity": 4,
            "collateral_update_quantity": 1,
            "t1_quantity": 3,
            "exchange": "NSE",
        }],
    }


def test_normalizes_holdings_and_keeps_quantity_classes_separate():
    holdings = normalize_upstox_holdings(_payload())
    row = holdings[0]
    assert row["isin"] == "INE528G01035"
    assert row["instrument_key"] == "NSE_EQ|INE528G01035"
    assert row["quantity"] == 36
    assert row["collateral_quantity"] == 4
    assert row["collateral_update_quantity"] == 1
    assert row["t1_quantity"] == 3
    assert row["cnc_used_quantity"] == 2
    assert row["average_price"] == "18.7500"
    assert row["broker_reported_pnl"] == "-61.20"


def test_empty_holdings_is_a_valid_verified_snapshot():
    assert normalize_upstox_holdings({"status": "success", "data": []}) == []


@pytest.mark.parametrize("payload", [
    None,
    {},
    {"status": "error", "data": []},
    {"status": "success", "data": {}},
    {"status": "success", "data": [None]},
    {"status": "success", "data": [{"isin": "INE528G01035", "quantity": True}]},
    {"status": "success", "data": [{**_payload()["data"][0], "quantity": -1}]},
    {"status": "success", "data": [{**_payload()["data"][0], "last_price": float("nan")}]},
    {"status": "success", "data": [{**_payload()["data"][0], "instrument_token": ""}]},
])
def test_rejects_malformed_holdings_payloads(payload):
    with pytest.raises(ValueError):
        normalize_upstox_holdings(payload)
