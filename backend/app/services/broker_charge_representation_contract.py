"""Versioned source representation contract for exchange transaction charges and IPFT.

This module validates representation declarations before any accounting mapping.
It does not derive tariffs, GST composition, or per-fill allocations.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping


CONTRACT_VERSION = "exchange-charge-representation-v1"
CENT = Decimal("0.01")

# Canonical names accepted by the source-component ledger. Raw source labels must
# be retained separately; these names are normalized review labels, not evidence.
KNOWN_COMPONENTS = frozenset({
    "brokerage",
    "stt",
    "exchange_charges",
    "transaction_charges",
    "clearing_charges",
    "ipft",
    "other_charges",
    "demat_transaction_charges",
    "sebi_charges",
    "stamp_duty",
    "gst",
})


@dataclass(frozen=True)
class ChargeRepresentation:
    """Reviewer-declared representation of exchange transaction charges."""

    contract_version: str
    mode: str
    raw_labels: tuple[str, ...]
    components: Mapping[str, Decimal]


def validate_charge_representation(value: ChargeRepresentation) -> dict[str, object]:
    """Validate an explicit combined/split declaration without guessing.

    COMBINED means transaction_charges already includes IPFT and a separate
    ipft amount is forbidden. SPLIT means transaction_charges excludes IPFT and
    both amounts must be present. Other source components are preserved and
    included in the returned component map, never silently discarded.
    """
    if value.contract_version != CONTRACT_VERSION:
        raise ValueError("Unsupported charge representation contract version.")
    if value.mode not in {"COMBINED_TRANSACTION_AND_IPFT", "SPLIT_TRANSACTION_AND_IPFT"}:
        raise ValueError("Charge representation mode must be explicitly reviewed.")
    if not value.raw_labels or any(not isinstance(label, str) or not label.strip() for label in value.raw_labels):
        raise ValueError("Original non-empty source labels must be retained.")
    if len(set(value.raw_labels)) != len(value.raw_labels):
        raise ValueError("Duplicate raw source labels are ambiguous.")
    if not value.components:
        raise ValueError("At least one normalized source component is required.")

    normalized: dict[str, str] = {}
    for name, amount in value.components.items():
        if name not in KNOWN_COMPONENTS:
            raise ValueError(f"Unsupported normalized charge component: {name}.")
        try:
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid amount for charge component {name}.") from exc
        if not decimal_amount.is_finite() or decimal_amount < 0:
            raise ValueError(f"Invalid amount for charge component {name}.")
        if decimal_amount != decimal_amount.quantize(CENT):
            raise ValueError(f"Charge component {name} must be rounded to paise before review.")
        normalized[name] = format(decimal_amount, "f")

    has_transaction = "transaction_charges" in normalized
    has_ipft = "ipft" in normalized
    if value.mode == "COMBINED_TRANSACTION_AND_IPFT":
        if not has_transaction:
            raise ValueError("Combined representation requires transaction_charges.")
        if has_ipft:
            raise ValueError("Combined representation must not also include a separate IPFT amount.")
    else:
        if not has_transaction or not has_ipft:
            raise ValueError("Split representation requires both transaction_charges and ipft.")

    return {
        "contract_version": CONTRACT_VERSION,
        "mode": value.mode,
        "raw_labels": list(value.raw_labels),
        "components": normalized,
        "total_components": format(sum((Decimal(v) for v in normalized.values()), Decimal("0")).quantize(CENT), "f"),
        "reviewable": True,
        "accounting_approved": False,
    }
