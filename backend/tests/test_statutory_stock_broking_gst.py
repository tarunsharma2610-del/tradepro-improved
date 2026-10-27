from decimal import Decimal

import pytest

from app.services.statutory_stock_broking_gst import (
    GstValuationLine,
    PureAgentEvidence,
    calculate_statutory_stock_broking_gst,
)


def qualifying_evidence(**overrides):
    values = {
        "recipient_authorized_payment": True,
        "agreement_identifies_pure_agent": True,
        "recipient_is_liable_for_third_party_payment": True,
        "payment_is_on_recipient_behalf": True,
        "separately_indicated_on_invoice": True,
        "procured_in_addition_to_own_service": True,
        "no_title_to_procured_supply": True,
        "supplier_does_not_use_procured_supply": True,
        "recovers_actual_amount_without_markup": True,
    }
    values.update(overrides)
    return PureAgentEvidence(**values)


def test_section_15_includes_third_party_recovery_without_complete_rule_33_proof():
    result = calculate_statutory_stock_broking_gst(
        [
            GstValuationLine("brokerage", "20.00"),
            GstValuationLine("exchange_fee", "5.68", "THIRD_PARTY_RECOVERY"),
            GstValuationLine("ipft", "0.17", "THIRD_PARTY_RECOVERY"),
        ],
        supplier_state_code="27",
        recipient_state_code_in_supplier_records="27",
    )
    assert result.taxable_base == Decimal("25.85")
    assert result.total_gst == Decimal("4.66")
    assert result.tax_type == "CGST_SGST"
    assert result.cgst == Decimal("2.33")
    assert result.sgst == Decimal("2.33")
    assert result.igst == Decimal("0.00")
    assert result.included_components == ("brokerage", "exchange_fee", "ipft")


def test_rule_33_exclusion_requires_every_condition():
    lines = [
        GstValuationLine(
            "stamp_duty",
            "3.00",
            "THIRD_PARTY_RECOVERY",
            qualifying_evidence(),
        ),
        GstValuationLine(
            "stt",
            "10.00",
            "THIRD_PARTY_RECOVERY",
            qualifying_evidence(recovers_actual_amount_without_markup=False),
        ),
        GstValuationLine("brokerage", "20.00"),
    ]
    result = calculate_statutory_stock_broking_gst(
        lines,
        supplier_state_code="27",
        recipient_state_code_in_supplier_records="29",
    )
    assert result.taxable_base == Decimal("30.00")
    assert result.total_gst == Decimal("5.40")
    assert result.tax_type == "IGST"
    assert result.igst == Decimal("5.40")
    assert result.cgst == Decimal("0.00")
    assert result.sgst == Decimal("0.00")
    assert result.excluded_pure_agent_components == ("stamp_duty",)
    assert result.included_components == ("stt", "brokerage")


def test_missing_recipient_state_uses_supplier_state_fallback():
    result = calculate_statutory_stock_broking_gst(
        [GstValuationLine("brokerage", "20")],
        supplier_state_code="09",
        recipient_state_code_in_supplier_records=None,
    )
    assert result.place_of_supply_state_code == "09"
    assert result.place_of_supply_basis == "SUPPLIER_STATE_FALLBACK_RECIPIENT_STATE_NOT_RECORDED"
    assert result.tax_type == "CGST_SGST"


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-0.01", "not-money"])
def test_rejects_invalid_amounts(amount):
    with pytest.raises(ValueError):
        calculate_statutory_stock_broking_gst(
            [GstValuationLine("brokerage", amount)],
            supplier_state_code="27",
            recipient_state_code_in_supplier_records="27",
        )


def test_rejects_duplicate_component_names_and_invalid_state_codes():
    with pytest.raises(ValueError, match="unique"):
        calculate_statutory_stock_broking_gst(
            [GstValuationLine("brokerage", "1"), GstValuationLine("brokerage", "2")],
            supplier_state_code="27",
            recipient_state_code_in_supplier_records="27",
        )
    with pytest.raises(ValueError, match="two-digit"):
        calculate_statutory_stock_broking_gst(
            [GstValuationLine("brokerage", "1")],
            supplier_state_code="0",
            recipient_state_code_in_supplier_records="27",
        )


def test_sub_paise_valuation_line_is_rejected_instead_of_silently_rounded():
    with pytest.raises(ValueError, match="paise precision"):
        calculate_statutory_stock_broking_gst(
            [GstValuationLine("brokerage", "0.025")],
            supplier_state_code="27",
            recipient_state_code_in_supplier_records="27",
        )


def test_paise_precision_and_zero_are_explicit():
    result = calculate_statutory_stock_broking_gst(
        [GstValuationLine("brokerage", "0.03")],
        supplier_state_code="27",
        recipient_state_code_in_supplier_records="27",
    )
    assert result.taxable_base == Decimal("0.03")
    # Each 9% intra-state tax head rounds independently to paise.
    assert result.cgst == Decimal("0.00")
    assert result.sgst == Decimal("0.00")
    assert result.total_gst == Decimal("0.00")
