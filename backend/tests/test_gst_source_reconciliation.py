from decimal import Decimal

import pytest

from app.services.gst_source_reconciliation import reconcile_reported_gst


def test_real_statement_visible_charges_preserve_two_paise_variance():
    result = reconcile_reported_gst(
        source_label="GST on charges",
        explicitly_reviewed_taxable_base="111.83",
        rate_percent="18",
        source_reported_tax="20.15",
    )
    assert result.expected_tax == Decimal("20.13")
    assert result.reported_tax == Decimal("20.15")
    assert result.variance == Decimal("0.02")
    assert result.matches is False


def test_brokerage_gst_on_real_statement_matches():
    result = reconcile_reported_gst(
        source_label="GST on brokerage",
        explicitly_reviewed_taxable_base="1000.00",
        rate_percent="18",
        source_reported_tax="180.00",
    )
    assert result.expected_tax == result.reported_tax == Decimal("180.00")
    assert result.variance == Decimal("0.00")
    assert result.matches is True


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-0.01", "0.001", "not-money"])
def test_invalid_or_sub_paise_money_is_rejected(amount):
    with pytest.raises(ValueError):
        reconcile_reported_gst(
            source_label="GST on charges",
            explicitly_reviewed_taxable_base=amount,
            rate_percent="18",
            source_reported_tax="20.15",
        )
