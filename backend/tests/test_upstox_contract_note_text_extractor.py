from decimal import Decimal

import pytest

from app.services.upstox_contract_note_text_extractor import (
    extract_upstox_contract_note_text,
)


def test_extracts_upstox_multisegment_and_itemized_charge_lines_without_classifying_tax():
    result = extract_upstox_contract_note_text(
        """Contract Note Cum Tax Invoice
NSE-EQ NSE-F&O NSE-CD MCX
Brokerage: ₹20.00
Exchange Txn Charge ₹3.07
SEBI Turnover Fees ₹0.10
IPFT Fee ₹0.05
DP Charges ₹18.50
CGST @ 9% ₹3.75
SGST @ 9% ₹3.75
STT ₹12.50
Stamp Duty ₹0.15
"""
    )

    assert result.segments == ("NSE-EQ", "NSE-F&O", "NSE-CD", "MCX")
    amounts = {item.component: item.amount for item in result.line_items}
    assert amounts == {
        "brokerage": Decimal("20.00"),
        "transaction_charges": Decimal("3.07"),
        "sebi_charges": Decimal("0.10"),
        "ipft": Decimal("0.05"),
        "demat_transaction_charges": Decimal("18.50"),
        "gst_cgst": Decimal("3.75"),
        "gst_sgst": Decimal("3.75"),
        "stt": Decimal("12.50"),
        "stamp_duty": Decimal("0.15"),
    }
    # Extraction does not infer a GST base, bundle IPFT, or approve accounting.
    assert result.ambiguous_components == ()
    assert all(item.source_line for item in result.line_items)


def test_duplicate_component_is_flagged_not_silently_overwritten():
    result = extract_upstox_contract_note_text(
        "NSE-EQ\nBrokerage ₹20.00\nBrokerage ₹10.00\n"
    )
    assert result.ambiguous_components == ("brokerage",)
    assert [item.amount for item in result.line_items] == [
        Decimal("20.00"),
        Decimal("10.00"),
    ]


def test_unknown_charge_line_is_preserved_for_review():
    result = extract_upstox_contract_note_text(
        "NSE-F&O\nInvestor Protection Fund Contribution ₹0.01\n"
    )
    assert result.line_items == ()
    assert result.unmapped_candidate_lines == (
        (2, "Investor Protection Fund Contribution ₹0.01"),
    )


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "Brokerage ₹NaN",
        "Brokerage ₹-1.00",
        "Brokerage ₹1.001",
    ],
)
def test_invalid_or_empty_text_fails_closed(text):
    if not text.strip():
        with pytest.raises(ValueError, match="Non-empty"):
            extract_upstox_contract_note_text(text)
    elif "NaN" in text or "-1.00" in text or "1.001" in text:
        # Unsupported numeric forms are deliberately not treated as valid values.
        result = extract_upstox_contract_note_text(text)
        assert result.line_items == ()
        assert result.unmapped_candidate_lines
