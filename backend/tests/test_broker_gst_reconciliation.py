from decimal import Decimal

import pytest

from app.services.broker_gst_reconciliation import compare_broker_gst_estimate
from app.services.statutory_stock_broking_gst import GstValuationLine


def compare(payload, **overrides):
    values = {
        "gst_field": "gst",
        "valuation_lines": [
            GstValuationLine("brokerage", "20.00"),
            GstValuationLine("transaction_charges", "5.68"),
            GstValuationLine("sebi_fees", "0.17"),
        ],
        "supplier_state_code": "27",
        "recipient_state_code_in_supplier_records": "29",
    }
    values.update(overrides)
    return compare_broker_gst_estimate(payload, **values)


def test_api_gst_estimate_matches_independent_section_15_engine():
    result = compare({"gst": "4.65"})
    assert result.api_state == "VALUE"
    assert result.api_reported_gst == Decimal("4.65")
    assert result.engine_estimated_gst == Decimal("4.65")
    assert result.variance_api_minus_engine == Decimal("0.00")
    assert result.status == "MATCH_WITHIN_TOLERANCE"
    assert result.taxable_base == Decimal("25.85")
    assert result.tax_type == "IGST"
    assert result.evidence_class == "ESTIMATE_COMPARISON"


def test_api_gst_variance_is_visible_and_not_auto_approved():
    result = compare({"gst": "4.64"})
    assert result.api_reported_gst == Decimal("4.64")
    assert result.engine_estimated_gst == Decimal("4.65")
    assert result.variance_api_minus_engine == Decimal("-0.01")
    assert result.status == "MATCH_WITHIN_TOLERANCE"


def test_variance_over_tolerance_requires_review():
    result = compare({"gst": "4.50"})
    assert result.variance_api_minus_engine == Decimal("-0.15")
    assert result.status == "VARIANCE_REQUIRES_REVIEW"


@pytest.mark.parametrize(("payload", "state"), [
    ({}, "MISSING"),
    ({"gst": None}, "NULL"),
    ({"gst": "NaN"}, "INVALID"),
    ({"gst": -1}, "INVALID"),
])
def test_unavailable_api_gst_is_not_coerced_to_zero(payload, state):
    result = compare(payload)
    assert result.api_state == state
    assert result.api_reported_gst is None
    assert result.variance_api_minus_engine is None
    assert result.engine_estimated_gst == Decimal("4.65")
    assert result.status == "API_GST_UNAVAILABLE_REVIEW"


def test_numeric_zero_is_preserved_as_a_reported_value():
    result = compare({"gst": 0})
    assert result.api_state == "ZERO"
    assert result.api_reported_gst == Decimal("0")
    assert result.variance_api_minus_engine == Decimal("-4.65")
    assert result.status == "VARIANCE_REQUIRES_REVIEW"


def test_sub_paise_api_gst_is_invalid_for_currency_comparison():
    result = compare({"gst": "4.651"})
    assert result.api_state == "INVALID"
    assert result.api_reported_gst is None
    assert result.variance_api_minus_engine is None
    assert result.status == "API_GST_INVALID_REVIEW"


@pytest.mark.parametrize("tolerance", ["-0.01", "NaN", "0.001"])
def test_tolerance_must_be_finite_nonnegative_paise_amount(tolerance):
    with pytest.raises(ValueError):
        compare({"gst": "4.65"}, tolerance=tolerance)
