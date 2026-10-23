from decimal import Decimal

import pytest

from app.services.broker_charge_allocation_service import (
    METHOD_VERSION,
    allocate_component_total,
)


def test_allocation_reconciles_source_total_with_deterministic_residual():
    result = allocate_component_total(
        "1.00",
        {"fill-b": "1", "fill-a": "1", "fill-c": "1"},
        allocation_basis="EXPLICIT_REVIEWED",
    )
    assert result == {
        "fill-a": Decimal("0.34"),
        "fill-b": Decimal("0.33"),
        "fill-c": Decimal("0.33"),
    }
    assert sum(result.values()) == Decimal("1.00")


def test_allocation_is_independent_of_input_mapping_order():
    first = allocate_component_total(
        "0.05", {"fill-z": 1, "fill-a": 1, "fill-m": 1},
        allocation_basis="QUANTITY",
    )
    second = allocate_component_total(
        "0.05", {"fill-m": 1, "fill-z": 1, "fill-a": 1},
        allocation_basis="QUANTITY",
    )
    assert first == second
    assert first == {
        "fill-a": Decimal("0.02"),
        "fill-m": Decimal("0.02"),
        "fill-z": Decimal("0.01"),
    }


def test_zero_weight_targets_receive_no_charge_even_when_residual_is_one_paise():
    result = allocate_component_total(
        "0.01", {"fill-a": 0, "fill-b": 1, "fill-c": 1},
        allocation_basis="NOTIONAL",
    )
    assert result == {
        "fill-a": Decimal("0.00"),
        "fill-b": Decimal("0.01"),
        "fill-c": Decimal("0.00"),
    }


def test_zero_weight_targets_receive_no_charge_when_multiple_paise_residuals_exist():
    result = allocate_component_total(
        "0.02", {"fill-a": 0, "fill-b": 1, "fill-c": 1},
        allocation_basis="NOTIONAL",
    )
    assert result == {
        "fill-a": Decimal("0.00"),
        "fill-b": Decimal("0.01"),
        "fill-c": Decimal("0.01"),
    }


@pytest.mark.parametrize(
    ("total", "weights", "basis", "message"),
    [
        ("-0.01", {"a": 1}, "QUANTITY", "cannot be negative"),
        ("1.001", {"a": 1}, "QUANTITY", "paise precision"),
        ("1.00", {}, "QUANTITY", "At least one fill"),
        ("1.00", {"a": 0, "b": 0}, "QUANTITY", "weight must be positive"),
        ("1.00", {"a": -1, "b": 2}, "QUANTITY", "weights cannot be negative"),
        ("1.00", {"a": 1}, "UNKNOWN", "reviewed allocation basis"),
        ("NaN", {"a": 1}, "QUANTITY", "finite decimal"),
    ],
)
def test_allocation_fails_closed_for_invalid_inputs(total, weights, basis, message):
    with pytest.raises(ValueError, match=message):
        allocate_component_total(total, weights, allocation_basis=basis)


def test_allocation_method_version_is_explicit_and_versioned():
    assert METHOD_VERSION == "largest-remainder-v1"


@pytest.mark.parametrize(
    ("charges", "cap", "expected"),
    [
        ({"fill-a": "10.00", "fill-b": "15.00"}, "40.00", "25.00"),
        ({"fill-a": "10.00", "fill-b": "15.00"}, "20.00", "20.00"),
        ({"fill-a": "0.00", "fill-b": "0.00"}, "20.00", "0.00"),
    ],
)
def test_order_brokerage_cap_applies_to_combined_order_total(charges, cap, expected):
    from app.services.broker_charge_allocation_service import capped_order_brokerage_total

    assert capped_order_brokerage_total(charges, cap) == Decimal(expected)


@pytest.mark.parametrize(
    ("charges", "cap", "message"),
    [
        ({}, "20.00", "At least one fill"),
        ({"fill-a": "-0.01"}, "20.00", "cannot be negative"),
        ({"fill-a": "1.001"}, "20.00", "paise precision"),
        ({"fill-a": "1.00"}, "-0.01", "cap cannot be negative"),
        ({"fill-a": "1.00"}, "1.001", "paise precision"),
    ],
)
def test_order_brokerage_cap_rejects_invalid_inputs(charges, cap, message):
    from app.services.broker_charge_allocation_service import capped_order_brokerage_total

    with pytest.raises(ValueError, match=message):
        capped_order_brokerage_total(charges, cap)
