"""Regression fixtures transcribed from user-provided Upstox contract notes.

These are daily aggregate invoice values, not per-fill allocations. IPFT was not
separately identified in the supplied note text, so this fixture deliberately
does not infer a zero IPFT amount or manufacture a separate IPFT component.
"""
from decimal import Decimal

import pytest

from app.services.statutory_stock_broking_gst import (
    GstValuationLine,
    calculate_statutory_stock_broking_gst,
)


# trade date, brokerage, transaction charges, SEBI fees, invoice taxable value,
# brokerage IGST, charges IGST, invoice total IGST
UPSTOX_DAILY_CONTRACT_NOTES = [
    ("2023-01-23", "360.00", "41.34", "0.08", "401.42", "64.80", "7.46", "72.26"),
    ("2023-01-24", "160.00", "16.78", "0.03", "176.81", "28.80", "3.03", "31.83"),
    ("2023-01-25", "160.00", "10.40", "0.02", "170.42", "28.80", "1.88", "30.68"),
    ("2023-01-27", "200.00", "24.54", "0.05", "224.59", "36.00", "4.43", "40.43"),
    ("2023-01-30", "120.00", "18.55", "0.04", "138.59", "21.60", "3.35", "24.95"),
]


@pytest.mark.parametrize(
    "trade_date,brokerage,transaction_charges,sebi_fees,taxable_value,"
    "brokerage_igst,charges_igst,total_igst",
    UPSTOX_DAILY_CONTRACT_NOTES,
)
def test_historical_upstox_contract_note_gst_reconciles(
    trade_date,
    brokerage,
    transaction_charges,
    sebi_fees,
    taxable_value,
    brokerage_igst,
    charges_igst,
    total_igst,
):
    """Match disclosed daily invoice base and GST without inventing IPFT data."""
    brokerage = Decimal(brokerage)
    transaction_charges = Decimal(transaction_charges)
    sebi_fees = Decimal(sebi_fees)
    taxable_value = Decimal(taxable_value)
    brokerage_igst = Decimal(brokerage_igst)
    charges_igst = Decimal(charges_igst)
    total_igst = Decimal(total_igst)

    # Contract note explicitly identifies these three taxable components.
    assert brokerage + transaction_charges + sebi_fees == taxable_value
    # Broker's displayed split GST is 18% on brokerage and 18% on other
    # disclosed taxable charges, rounded to paise per displayed tax line.
    assert (brokerage * Decimal("0.18")).quantize(Decimal("0.01")) == brokerage_igst
    expected_charges_gst = (
        (transaction_charges + sebi_fees) * Decimal("0.18")
    ).quantize(Decimal("0.01"))
    assert expected_charges_gst == charges_igst
    assert brokerage_igst + charges_igst == total_igst

    # Independent statutory valuation primitive must reproduce the same total
    # tax when supplied the explicitly disclosed taxable components. The
    # supplied invoice shows IGST and identifies a Maharashtra supplier (27).
    # Recipient state 29 here is a synthetic cross-state test input, not a
    # claim that the transcribed invoice disclosed the recipient's state.
    result = calculate_statutory_stock_broking_gst(
        [
            GstValuationLine("brokerage", brokerage),
            GstValuationLine("transaction_charges", transaction_charges),
            GstValuationLine("sebi_fees", sebi_fees),
        ],
        supplier_state_code="27",
        recipient_state_code_in_supplier_records="29",
    )
    assert result.taxable_base == taxable_value, trade_date
    assert result.tax_type == "IGST", trade_date
    assert result.igst == total_igst, trade_date
    assert result.total_gst == total_igst, trade_date
    assert result.included_components == (
        "brokerage", "transaction_charges", "sebi_fees"
    )


def test_historical_contract_note_does_not_infer_ipft_zero_from_missing_line():
    """Absence of a separate IPFT label is not proof the amount was zero."""
    sample = {
        "brokerage": Decimal("360.00"),
        "transaction_charges": Decimal("41.34"),
        "sebi_fees": Decimal("0.08"),
    }
    assert "ipft" not in sample
    # Deliberately no zero-value IPFT is inserted: source text did not disclose
    # a distinct amount or establish whether it was bundled in another charge.
