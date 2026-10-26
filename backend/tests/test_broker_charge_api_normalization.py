from decimal import Decimal

import pytest

from app.services.broker_charge_api_normalization import normalize_charge_api_field


def test_charge_api_field_states_preserve_missing_null_zero_and_value():
    missing = normalize_charge_api_field({}, "ipft")
    null = normalize_charge_api_field({"ipft": None}, "ipft")
    zero = normalize_charge_api_field({"ipft": 0}, "ipft")
    value = normalize_charge_api_field({"ipft": "0.01"}, "ipft")

    assert missing["state"] == "MISSING"
    assert null["state"] == "NULL"
    assert zero["state"] == "ZERO"
    assert value["state"] == "VALUE"
    assert value["decimal_value"] == "0.01"
    assert null["state"] != zero["state"]


@pytest.mark.parametrize("raw", [True, {}, [], "NaN", "Infinity", "-0.01", "not-a-number"])
def test_charge_api_field_rejects_invalid_numeric_values_without_coercion(raw):
    result = normalize_charge_api_field({"ipft": raw}, "ipft")
    assert result["state"] == "INVALID"
    assert result["raw_value"] == raw
    assert result["decimal_value"] is None


def test_charge_api_field_preserves_raw_numeric_representation():
    result = normalize_charge_api_field({"transaction": "306.9900"}, "transaction")
    assert result["state"] == "VALUE"
    assert result["raw_value"] == "306.9900"
    assert Decimal(result["decimal_value"]) == Decimal("306.9900")


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ([], "ipft"),
        ({"ipft": 0}, ""),
        ({"ipft": 0}, None),
    ],
)
def test_charge_api_field_requires_object_and_nonempty_field(payload, field):
    with pytest.raises(ValueError):
        normalize_charge_api_field(payload, field)
