from decimal import Decimal

import pytest

from app.services.broker_charge_representation_contract import CONTRACT_VERSION
from app.services.broker_charge_source_canonicalization import (
    CANONICAL_MAPPING_VERSION,
    SourceChargeRow,
    canonicalize_reviewed_source_components,
)


def canonical_rows():
    return [
        SourceChargeRow("brokerage", "20.00", "Brokerage"),
        SourceChargeRow("stt", "0.20", "STT"),
        SourceChargeRow("exchange_charges", "307.00", "Exchange Charges"),
        SourceChargeRow("sebi_charges", "0.01", "SEBI Turnover"),
        SourceChargeRow("stamp_duty", "0.03", "Stamp Duty"),
        SourceChargeRow("gst", "58.91", "GST"),
    ]


def test_direct_canonical_source_rows_map_to_exact_six_components_without_approval():
    result = canonicalize_reviewed_source_components(canonical_rows())
    assert result["mapping_version"] == CANONICAL_MAPPING_VERSION
    assert result["canonical_components"]["exchange_charges"] == "307.00"
    assert set(result["canonical_components"]) == {
        "brokerage", "stt", "exchange_charges", "sebi_charges", "stamp_duty", "gst"
    }
    assert result["accounting_approved"] is False


def test_combined_transaction_ipft_maps_amount_once_to_exchange_charges():
    rows = canonical_rows()
    rows.remove(next(row for row in rows if row.component_name == "exchange_charges"))
    rows.append(SourceChargeRow(
        "transaction_charges", "307.00", "Transaction Charges (includes IPFT)",
        "COMBINED_TRANSACTION_AND_IPFT", CONTRACT_VERSION,
    ))
    result = canonicalize_reviewed_source_components(rows)
    assert result["canonical_components"]["exchange_charges"] == "307.00"
    assert result["source_components_by_canonical"]["exchange_charges"] == ["transaction_charges"]
    assert result["representation_contract_version"] == CONTRACT_VERSION


def test_split_transaction_ipft_maps_sum_once_to_exchange_charges():
    rows = canonical_rows()
    rows.remove(next(row for row in rows if row.component_name == "exchange_charges"))
    rows.extend([
        SourceChargeRow("transaction_charges", "306.99", "Transaction Charges", "SPLIT_TRANSACTION_AND_IPFT", CONTRACT_VERSION),
        SourceChargeRow("ipft", "0.01", "IPFT", "SPLIT_TRANSACTION_AND_IPFT", CONTRACT_VERSION),
    ])
    result = canonicalize_reviewed_source_components(rows)
    assert result["canonical_components"]["exchange_charges"] == "307.00"
    assert Decimal(result["canonical_components"]["exchange_charges"]) == Decimal("307.00")
    assert set(result["source_components_by_canonical"]["exchange_charges"]) == {"transaction_charges", "ipft"}


def test_combined_representation_rejects_separate_ipft():
    rows = canonical_rows()
    rows.remove(next(row for row in rows if row.component_name == "exchange_charges"))
    rows.extend([
        SourceChargeRow("transaction_charges", "307.00", "Transaction Charges", "COMBINED_TRANSACTION_AND_IPFT", CONTRACT_VERSION),
        SourceChargeRow("ipft", "0.01", "IPFT", "COMBINED_TRANSACTION_AND_IPFT", CONTRACT_VERSION),
    ])
    with pytest.raises(ValueError, match="must not include a separate IPFT"):
        canonicalize_reviewed_source_components(rows)


def test_split_representation_requires_both_rows():
    rows = canonical_rows()
    rows.remove(next(row for row in rows if row.component_name == "exchange_charges"))
    rows.append(SourceChargeRow("transaction_charges", "306.99", "Transaction Charges", "SPLIT_TRANSACTION_AND_IPFT", CONTRACT_VERSION))
    with pytest.raises(ValueError, match="requires both"):
        canonicalize_reviewed_source_components(rows)


def test_missing_or_mixed_representation_version_fails_closed():
    rows = canonical_rows()
    rows.remove(next(row for row in rows if row.component_name == "exchange_charges"))
    rows.extend([
        SourceChargeRow("transaction_charges", "306.99", "Transaction Charges", "SPLIT_TRANSACTION_AND_IPFT", CONTRACT_VERSION),
        SourceChargeRow("ipft", "0.01", "IPFT", "SPLIT_TRANSACTION_AND_IPFT", None),
    ])
    with pytest.raises(ValueError, match="one consistent representation mode and version"):
        canonicalize_reviewed_source_components(rows)


def test_direct_exchange_and_transaction_rows_cannot_double_map():
    rows = canonical_rows()
    rows.append(SourceChargeRow("transaction_charges", "307.00", "Transaction Charges", "COMBINED_TRANSACTION_AND_IPFT", CONTRACT_VERSION))
    with pytest.raises(ValueError, match="cannot coexist"):
        canonicalize_reviewed_source_components(rows)


def test_reviewed_dp_demat_is_an_optional_separate_canonical_component():
    rows = canonical_rows()
    rows.append(SourceChargeRow("demat_transaction_charges", "20.00", "DP Charges"))
    result = canonicalize_reviewed_source_components(rows)
    assert result["canonical_components"]["demat_transaction_charges"] == "20.00"
    assert result["source_components_by_canonical"]["demat_transaction_charges"] == [
        "demat_transaction_charges"
    ]
    assert set(result["canonical_components"]) == {
        "brokerage", "stt", "exchange_charges", "sebi_charges",
        "stamp_duty", "gst", "demat_transaction_charges",
    }
    assert result["accounting_approved"] is False


def test_absent_dp_demat_is_not_fabricated_as_zero():
    result = canonicalize_reviewed_source_components(canonical_rows())
    assert "demat_transaction_charges" not in result["canonical_components"]


def test_duplicate_or_missing_source_labels_are_rejected():
    rows = canonical_rows()
    rows[0] = SourceChargeRow("brokerage", "20.00", "")
    with pytest.raises(ValueError, match="original non-empty source label"):
        canonicalize_reviewed_source_components(rows)
    rows = canonical_rows()
    rows.append(rows[0])
    with pytest.raises(ValueError, match="Duplicate source component"):
        canonicalize_reviewed_source_components(rows)


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-0.01", "0.001"])
def test_invalid_or_non_paise_amounts_are_rejected(amount):
    rows = canonical_rows()
    rows[0] = SourceChargeRow("brokerage", amount, "Brokerage")
    with pytest.raises(ValueError, match="finite, nonnegative INR paise"):
        canonicalize_reviewed_source_components(rows)
