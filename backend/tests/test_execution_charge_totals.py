from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.execution_charge_totals import (
    calculate_execution_total_charges,
    recompute_execution_total_charges,
)


def execution(**overrides):
    values = {
        "brokerage": Decimal("20.00"),
        "stt": Decimal("0.20"),
        "exchange_charges": Decimal("3.07"),
        "sebi_charges": Decimal("0.10"),
        "stamp_duty": Decimal("0.15"),
        "gst": Decimal("4.23"),
        "demat_transaction_charges": None,
        "total_charges": Decimal("0.00"),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_null_demat_remains_unknown_and_does_not_change_legacy_core_total():
    row = execution()
    assert recompute_execution_total_charges(row) == Decimal("27.75")
    assert row.total_charges == Decimal("27.75")
    assert row.demat_transaction_charges is None


def test_explicit_demat_is_added_exactly_once_to_total():
    row = execution(demat_transaction_charges=Decimal("20.00"))
    assert recompute_execution_total_charges(row) == Decimal("47.75")
    assert row.total_charges == Decimal("47.75")


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-0.01", "0.001", "not-money"])
def test_invalid_demat_amount_fails_closed(value):
    with pytest.raises(ValueError, match="demat_transaction_charges"):
        calculate_execution_total_charges(
            brokerage="20.00",
            stt="0.20",
            exchange_charges="3.07",
            sebi_charges="0.10",
            stamp_duty="0.15",
            gst="4.23",
            demat_transaction_charges=value,
        )


def test_core_components_are_required_finite_nonnegative_paise():
    with pytest.raises(ValueError, match="brokerage"):
        calculate_execution_total_charges(
            brokerage=None, stt="0.20", exchange_charges="3.07",
            sebi_charges="0.10", stamp_duty="0.15", gst="4.23",
        )
