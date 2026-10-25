from decimal import Decimal

import pytest

from app.services.broker_charge_representation_contract import (
    CONTRACT_VERSION,
    ChargeRepresentation,
    validate_charge_representation,
)


def representation(mode, components, labels=None):
    if labels is None:
        labels = tuple(name.replace("_", " ").title() for name in components)
    return ChargeRepresentation(
        contract_version=CONTRACT_VERSION,
        mode=mode,
        raw_labels=labels,
        components={name: Decimal(amount) for name, amount in components.items()},
    )


def test_combined_representation_preserves_label_and_does_not_add_ipft_twice():
    result = validate_charge_representation(representation(
        "COMBINED_TRANSACTION_AND_IPFT",
        {"transaction_charges": "307.00", "gst": "55.26"},
    ))
    assert result["components"] == {"transaction_charges": "307.00", "gst": "55.26"}
    assert result["total_components"] == "362.26"
    assert result["raw_labels"] == ["Transaction Charges", "Gst"]
    assert result["accounting_approved"] is False


def test_split_representation_preserves_both_components_and_same_exchange_base():
    result = validate_charge_representation(representation(
        "SPLIT_TRANSACTION_AND_IPFT",
        {"transaction_charges": "306.99", "ipft": "0.01", "gst": "55.26"},
        labels=("Transaction Charges", "IPFT", "GST"),
    ))
    assert result["components"]["transaction_charges"] == "306.99"
    assert result["components"]["ipft"] == "0.01"
    assert Decimal(result["components"]["transaction_charges"]) + Decimal(result["components"]["ipft"]) == Decimal("307.00")
    assert result["total_components"] == "362.26"
    assert result["accounting_approved"] is False


def test_combined_mode_rejects_separately_reported_ipft_to_prevent_double_count():
    with pytest.raises(ValueError, match="must not also include a separate IPFT"):
        validate_charge_representation(representation(
            "COMBINED_TRANSACTION_AND_IPFT",
            {"transaction_charges": "307.00", "ipft": "0.01"},
            labels=("Transaction Charges (includes IPFT)", "IPFT"),
        ))


def test_split_mode_requires_both_components():
    with pytest.raises(ValueError, match="requires both"):
        validate_charge_representation(representation(
            "SPLIT_TRANSACTION_AND_IPFT", {"transaction_charges": "307.00"}
        ))


@pytest.mark.parametrize("mode", ["", "AUTO", "INFER_FROM_RATE"])
def test_unknown_or_inferred_representation_fails_closed(mode):
    with pytest.raises(ValueError, match="explicitly reviewed"):
        validate_charge_representation(representation(mode, {"transaction_charges": "307.00"}))


def test_unsupported_component_is_not_silently_dropped():
    with pytest.raises(ValueError, match="Unsupported normalized charge component"):
        validate_charge_representation(representation(
            "COMBINED_TRANSACTION_AND_IPFT",
            {"transaction_charges": "307.00", "misc_fee": "1.00"},
        ))


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-1.00", "0.001"])
def test_invalid_or_unrounded_component_amount_is_rejected(amount):
    with pytest.raises(ValueError):
        validate_charge_representation(representation(
            "COMBINED_TRANSACTION_AND_IPFT", {"transaction_charges": amount}
        ))


@pytest.mark.parametrize("labels", [(), ("",), ("IPFT", "IPFT")])
def test_missing_or_duplicate_raw_source_labels_are_rejected(labels):
    with pytest.raises(ValueError):
        validate_charge_representation(representation(
            "SPLIT_TRANSACTION_AND_IPFT",
            {"transaction_charges": "306.99", "ipft": "0.01"},
            labels=labels,
        ))


def test_each_normalized_component_requires_its_own_source_label():
    with pytest.raises(ValueError, match="exactly one original source label"):
        validate_charge_representation(representation(
            "SPLIT_TRANSACTION_AND_IPFT",
            {"transaction_charges": "306.99", "ipft": "0.01"},
            labels=("Transaction Charges",),
        ))


def test_contract_version_is_pinned():
    value = ChargeRepresentation(
        contract_version="future-version",
        mode="COMBINED_TRANSACTION_AND_IPFT",
        raw_labels=("Transaction Charges",),
        components={"transaction_charges": Decimal("307.00")},
    )
    with pytest.raises(ValueError, match="Unsupported charge representation contract version"):
        validate_charge_representation(value)
