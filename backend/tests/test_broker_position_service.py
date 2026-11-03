import pytest

from app.services.broker_position_service import normalize_upstox_positions


def _payload():
    return {
        "status": "success",
        "data": [
            {
                "exchange": "NFO",
                "product": "D",
                "instrument_token": "NSE_FO|52618",
                "average_price": 2.65,
                "quantity": 15,
                "last_price": 1.75,
                "pnl": 26.25,
                "unrealised": -658304.25,
                "realised": -0.0,
                "trading_symbol": "BANKNIFTY23OCT38000PE",
            },
            {
                "exchange": "NSE",
                "product": "D",
                "instrument_token": "NSE_EQ|INE062A01020",
                "average_price": None,
                "quantity": 0,
                "last_price": 571.2,
                "pnl": 0.45,
                "unrealised": 0.0,
                "realised": 0.45,
                "trading_symbol": "SBIN",
            },
        ],
    }


def test_normalizes_broker_positions_without_conflating_realised_and_unrealised():
    positions = normalize_upstox_positions(_payload())
    assert len(positions) == 2
    assert positions[0]["instrument_key"] == "NSE_FO|52618"
    assert positions[0]["quantity"] == 15
    assert positions[0]["average_price"] == "2.6500"
    assert positions[0]["broker_reported_unrealised"] == "-658304.25"
    assert positions[0]["broker_reported_realised"] == "0.00"
    assert positions[1]["average_price"] is None
    assert positions[1]["quantity"] == 0


def test_empty_positions_is_a_valid_verified_snapshot():
    assert normalize_upstox_positions({"status": "success", "data": []}) == []


@pytest.mark.parametrize("payload", [
    None,
    {},
    {"status": "error", "data": []},
    {"status": "success", "data": {}},
    {"status": "success", "data": [None]},
    {"status": "success", "data": [{"instrument_token": "NSE_EQ|X", "trading_symbol": "X", "exchange": "NSE", "product": "D", "quantity": True}]},
])
def test_rejects_malformed_positions_responses(payload):
    with pytest.raises(ValueError):
        normalize_upstox_positions(payload)


def test_rejects_non_finite_broker_position_values():
    payload = _payload()
    payload["data"][0]["pnl"] = float("nan")
    with pytest.raises(ValueError):
        normalize_upstox_positions(payload)


def test_normalizes_negative_zero_as_unsigned_zero():
    payload = _payload()
    payload["data"][0]["realised"] = -0.0
    positions = normalize_upstox_positions(payload)
    assert positions[0]["broker_reported_realised"] == "0.00"
