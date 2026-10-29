"""Cross-exchange GST engine coverage for NSE, BSE and MCX.

These tests intentionally share one statutory GST engine. Exchange/segment tariffs
supply explicit charge components; this matrix does not pretend that the tariff
rates or taxable components are identical across exchanges.
"""
from decimal import Decimal

import pytest

from app.services.statutory_stock_broking_gst import (
    GstValuationLine,
    PureAgentEvidence,
    calculate_statutory_stock_broking_gst,
)

# Exchange, segment, product, sample service/fee inputs (INR).
# These are synthetic inputs for shared-engine behavior, not published tariffs.
EXCHANGE_PRODUCT_SCOPES = [
    ("NSE", "EQ", "DELIVERY"),
    ("NSE", "EQ", "INTRADAY"),
    ("NSE", "FO", "FUTURES"),
    ("NSE", "FO", "OPTIONS"),
    ("BSE", "EQ", "DELIVERY"),
    ("BSE", "EQ", "INTRADAY"),
    ("BSE", "FO", "FUTURES"),
    ("BSE", "FO", "OPTIONS"),
    ("MCX", "COMMODITY", "FUTURES"),
    ("MCX", "COMMODITY", "OPTIONS"),
]


@pytest.mark.parametrize("exchange,segment,product", EXCHANGE_PRODUCT_SCOPES)
@pytest.mark.parametrize(
    "supplier_state,recipient_state,tax_type",
    [
        ("27", "27", "CGST_SGST"),
        ("27", "29", "IGST"),
    ],
)
def test_shared_gst_engine_across_exchange_product_scopes(
    exchange, segment, product, supplier_state, recipient_state, tax_type
):
    # Explicit sample values only; tariff engines must resolve real rates and
    # component applicability for exchange/segment/product/date separately.
    lines = [
        GstValuationLine("brokerage", Decimal("20.00")),
        GstValuationLine("transaction_charges", Decimal("5.68")),
        GstValuationLine("sebi_fees", Decimal("0.17")),
    ]
    result = calculate_statutory_stock_broking_gst(
        lines,
        supplier_state_code=supplier_state,
        recipient_state_code_in_supplier_records=recipient_state,
    )
    assert result.taxable_base == Decimal("25.85"), (exchange, segment, product)
    assert result.gst_rate_percent == Decimal("18.00")
    assert result.tax_type == tax_type
    if tax_type == "IGST":
        assert result.igst == Decimal("4.65")
        assert result.cgst == result.sgst == Decimal("0.00")
    else:
        assert result.igst == Decimal("0.00")
        assert result.cgst == Decimal("2.33")
        assert result.sgst == Decimal("2.33")
    assert result.included_components == (
        "brokerage", "transaction_charges", "sebi_fees"
    )


def test_rule_33_exclusion_is_exchange_agnostic_but_requires_all_evidence():
    evidence = PureAgentEvidence(
        recipient_authorized_payment=True,
        agreement_identifies_pure_agent=True,
        recipient_is_liable_for_third_party_payment=True,
        payment_is_on_recipient_behalf=True,
        separately_indicated_on_invoice=True,
        procured_in_addition_to_own_service=True,
        no_title_to_procured_supply=True,
        supplier_does_not_use_procured_supply=True,
        recovers_actual_amount_without_markup=True,
    )
    result = calculate_statutory_stock_broking_gst(
        [
            GstValuationLine("brokerage", "20.00"),
            GstValuationLine("documented_pure_agent_recovery", "10.00",
                             "THIRD_PARTY_RECOVERY", evidence),
        ],
        supplier_state_code="27",
        recipient_state_code_in_supplier_records="29",
    )
    assert result.taxable_base == Decimal("20.00")
    assert result.igst == Decimal("3.60")
    assert result.excluded_pure_agent_components == (
        "documented_pure_agent_recovery",
    )
