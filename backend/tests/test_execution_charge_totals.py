from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.schemas.order import ExecutionOut
from app.services.execution_charge_totals import (
    calculate_execution_total_charges,
    execution_charge_total_is_complete,
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
        "demat_charge_status": "UNKNOWN",
        "total_charges": Decimal("0.00"),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_null_demat_remains_unknown_and_does_not_change_legacy_core_total():
    row = execution()
    assert recompute_execution_total_charges(row) == Decimal("27.75")
    assert row.total_charges == Decimal("27.75")
    assert row.demat_transaction_charges is None
    assert not execution_charge_total_is_complete(row)


def test_explicit_demat_is_added_exactly_once_to_total():
    row = execution(
        demat_transaction_charges=Decimal("20.00"), demat_charge_status="KNOWN"
    )
    assert recompute_execution_total_charges(row) == Decimal("47.75")
    assert row.total_charges == Decimal("47.75")
    assert execution_charge_total_is_complete(row)


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


def test_not_applicable_is_complete_without_fabricating_a_zero_amount():
    row = execution(demat_charge_status="NOT_APPLICABLE")
    assert recompute_execution_total_charges(row) == Decimal("27.75")
    assert row.demat_transaction_charges is None
    assert execution_charge_total_is_complete(row)


def test_known_status_without_amount_fails_closed():
    with pytest.raises(ValueError, match="requires an explicit"):
        calculate_execution_total_charges(
            brokerage="20.00", stt="0.20", exchange_charges="3.07",
            sebi_charges="0.10", stamp_duty="0.15", gst="4.23",
            demat_transaction_charges=None, demat_charge_status="KNOWN",
        )


def test_unknown_status_with_amount_fails_closed():
    with pytest.raises(ValueError, match="must not carry"):
        calculate_execution_total_charges(
            brokerage="20.00", stt="0.20", exchange_charges="3.07",
            sebi_charges="0.10", stamp_duty="0.15", gst="4.23",
            demat_transaction_charges="20.00", demat_charge_status="UNKNOWN",
        )


def test_unknown_is_not_interpreted_as_zero_or_complete():
    row = execution(demat_charge_status="UNKNOWN", demat_transaction_charges=None)
    subtotal = recompute_execution_total_charges(row)
    assert subtotal == Decimal("27.75")
    assert not execution_charge_total_is_complete(row)



def test_execution_api_exposes_unknown_demat_and_incomplete_total():
    row = execution()
    row.id = uuid4()
    row.order_id = uuid4()
    row.instrument = SimpleNamespace(id=uuid4(), trading_symbol="TEST", exchange="NSE")
    row.side = "SELL"
    row.quantity = 1
    row.price = Decimal("100.00")
    row.gross_value = Decimal("100.00")
    row.realized_pnl = Decimal("0.00")
    from datetime import datetime, timezone
    row.executed_at = datetime.now(timezone.utc)
    row.total_charges = Decimal("27.75")

    payload = ExecutionOut.model_validate(row)
    assert payload.demat_transaction_charges is None
    assert payload.demat_charge_status == "UNKNOWN"
    assert payload.total_charges_complete is False


def test_execution_api_exposes_confirmed_not_applicable_as_complete():
    row = execution(demat_charge_status="NOT_APPLICABLE")
    row.id = uuid4()
    row.order_id = uuid4()
    row.instrument = SimpleNamespace(id=uuid4(), trading_symbol="TEST", exchange="NSE")
    row.side = "BUY"
    row.quantity = 1
    row.price = Decimal("100.00")
    row.gross_value = Decimal("100.00")
    row.realized_pnl = Decimal("0.00")
    from datetime import datetime, timezone
    row.executed_at = datetime.now(timezone.utc)
    row.total_charges = Decimal("27.75")

    payload = ExecutionOut.model_validate(row)
    assert payload.demat_transaction_charges is None
    assert payload.demat_charge_status == "NOT_APPLICABLE"
    assert payload.total_charges_complete is True


def test_execution_model_completeness_property_requires_reconciled_total():
    from app.models.execution import Execution

    row = Execution(
        brokerage=Decimal("20.00"),
        stt=Decimal("0.20"),
        exchange_charges=Decimal("3.07"),
        sebi_charges=Decimal("0.10"),
        stamp_duty=Decimal("0.15"),
        gst=Decimal("4.23"),
        total_charges=Decimal("27.75"),
        demat_charge_status="UNKNOWN",
    )
    assert row.total_charges_complete is False
    row.demat_charge_status = "NOT_APPLICABLE"
    assert row.total_charges_complete is True
    row.total_charges = Decimal("27.74")
    assert row.total_charges_complete is False


def test_stale_or_tampered_total_cannot_be_marked_complete():
    row = execution(
        demat_charge_status="NOT_APPLICABLE",
        total_charges=Decimal("27.74"),
    )
    assert not execution_charge_total_is_complete(row)
    row.total_charges = Decimal("27.75")
    assert execution_charge_total_is_complete(row)
    row.gst = Decimal("4.24")
    assert not execution_charge_total_is_complete(row)


@pytest.mark.parametrize(
    "status,demat_amount",
    [
        ("INVALID", None),
        ("UNKNOWN", Decimal("0.00")),
        ("KNOWN", None),
        ("NOT_APPLICABLE", Decimal("1.00")),
        ("KNOWN", Decimal("NaN")),
        ("KNOWN", Decimal("-0.01")),
        ("KNOWN", Decimal("1.001")),
    ],
)
def test_inconsistent_or_invalid_demat_state_is_not_complete(status, demat_amount):
    row = execution(demat_charge_status=status, demat_transaction_charges=demat_amount)
    assert not execution_charge_total_is_complete(row)

def test_execution_api_uses_model_completeness_for_invalid_demat_status():
    from datetime import datetime, timezone
    from app.models.execution import Execution

    row = Execution(
        demat_charge_status="INVALID",
        demat_transaction_charges=None,
    )
    row.id = uuid4()
    row.order_id = uuid4()
    row.instrument = SimpleNamespace(
        id=uuid4(), trading_symbol="TEST", exchange="NSE"
    )
    row.side = "SELL"
    row.quantity = 1
    row.price = Decimal("100.00")
    row.gross_value = Decimal("100.00")
    row.brokerage = Decimal("20.00")
    row.stt = Decimal("0.20")
    row.exchange_charges = Decimal("3.07")
    row.sebi_charges = Decimal("0.10")
    row.stamp_duty = Decimal("0.15")
    row.gst = Decimal("4.23")
    row.total_charges = Decimal("27.75")
    row.realized_pnl = Decimal("0.00")
    row.executed_at = datetime.now(timezone.utc)

    payload = ExecutionOut.model_validate(row)
    assert payload.demat_charge_status == "INVALID"
    assert payload.demat_transaction_charges is None
    assert payload.total_charges_complete is False
