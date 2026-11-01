from decimal import Decimal

import pytest

from app.services.broker_funds_service import normalize_upstox_funds_v3


def _payload():
    return {
        "status": "success",
        "data": {
            "available_to_trade": {
                "total": 5379.03,
                "cash_available_to_trade": {"total": 5117.34},
                "pledge_available_to_trade": {"total": 261.69},
            },
            "unavailable_to_trade": {
                "cash_unavailable_to_trade": {
                    "unsettled_profit": {"todays_profit": 12.345, "previous_days": -2.345}
                }
            },
        },
    }


def test_normalizes_documented_v3_funds_fields_without_conflating_cash_and_pledge():
    result = normalize_upstox_funds_v3(_payload())
    assert result == {
        "total_available_to_trade": Decimal("5379.03"),
        "cash_available_to_trade": Decimal("5117.34"),
        "pledge_available_to_trade": Decimal("261.69"),
        "unsettled_profit_today": Decimal("12.34"),
        "unsettled_profit_previous_days": Decimal("-2.34"),
    }


@pytest.mark.parametrize("payload", [
    None,
    {},
    {"status": "error", "data": {}},
    {"status": "success", "data": []},
    {"status": "success", "data": {"available_to_trade": {}, "unavailable_to_trade": {}}},
])
def test_rejects_malformed_or_unsuccessful_funds_envelopes(payload):
    with pytest.raises(ValueError):
        normalize_upstox_funds_v3(payload)


def test_rejects_non_finite_and_boolean_amounts():
    payload = _payload()
    payload["data"]["available_to_trade"]["total"] = float("nan")
    with pytest.raises(ValueError):
        normalize_upstox_funds_v3(payload)

    payload = _payload()
    payload["data"]["available_to_trade"]["total"] = True
    with pytest.raises(ValueError):
        normalize_upstox_funds_v3(payload)
