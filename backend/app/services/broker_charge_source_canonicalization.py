"""Explicit source-row to canonical accounting-component mapping.

This module only canonicalizes reviewed transcribed source rows. It does not
authenticate a contract note, allocate values to fills, approve tariff rules,
or establish the GST taxable base. Promotion remains a separate gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable

from app.services.broker_charge_representation_contract import CONTRACT_VERSION

CANONICAL_MAPPING_VERSION = "source-charge-canonical-mapping-v1"
CANONICAL_COMPONENTS = (
    "brokerage",
    "stt",
    "exchange_charges",
    "sebi_charges",
    "stamp_duty",
    "gst",
)
DIRECT_COMPONENTS = frozenset({"brokerage", "stt", "exchange_charges", "sebi_charges", "stamp_duty", "gst", "demat_transaction_charges"})
OPTIONAL_CANONICAL_COMPONENTS = frozenset({"demat_transaction_charges"})
REPRESENTATION_COMPONENTS = frozenset({"transaction_charges", "ipft"})
UNSUPPORTED_EVIDENCE_COMPONENTS = frozenset({
    "clearing_charges", "other_charges"
})


@dataclass(frozen=True)
class SourceChargeRow:
    component_name: str
    source_amount: Decimal | str | int
    source_label: str | None
    representation_mode: str | None = None
    representation_contract_version: str | None = None


def _amount(row: SourceChargeRow) -> Decimal:
    try:
        amount = row.source_amount if isinstance(row.source_amount, Decimal) else Decimal(str(row.source_amount))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid source amount for {row.component_name}.") from exc
    if not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal("0.01")):
        raise ValueError(f"Source amount for {row.component_name} must be finite, nonnegative INR paise.")
    return amount


def canonicalize_reviewed_source_components(rows: Iterable[SourceChargeRow]) -> dict[str, object]:
    """Map reviewed source rows to six core totals and optional DP/demat.

    Combined transaction/IPFT is represented by one transaction_charges row
    whose amount already includes IPFT. Split representation requires separate
    transaction_charges and ipft rows and sums them once. Original rows remain
    the caller's immutable evidence; this result is a derived mapping only.
    """
    source_rows = tuple(rows)
    if not source_rows:
        raise ValueError("At least one reviewed source component is required.")
    names = [row.component_name for row in source_rows]
    if any(not isinstance(name, str) or not name.strip() for name in names):
        raise ValueError("Every source row requires a normalized component name.")
    if len(names) != len(set(names)):
        raise ValueError("Duplicate source component rows are ambiguous.")
    if any(not isinstance(row.source_label, str) or not row.source_label.strip() for row in source_rows):
        raise ValueError("Every source component requires its original non-empty source label.")
    unsupported = set(names) & UNSUPPORTED_EVIDENCE_COMPONENTS
    if unsupported:
        raise ValueError(
            "Unsupported evidence-only components block canonicalization until an explicit reviewed mapping exists: "
            + ", ".join(sorted(unsupported))
        )
    unknown = set(names) - DIRECT_COMPONENTS - REPRESENTATION_COMPONENTS
    if unknown:
        raise ValueError("Unsupported source components cannot be silently omitted: " + ", ".join(sorted(unknown)))

    amounts = {row.component_name: _amount(row) for row in source_rows}
    modes = {row.representation_mode for row in source_rows if row.component_name in REPRESENTATION_COMPONENTS}
    versions = {row.representation_contract_version for row in source_rows if row.component_name in REPRESENTATION_COMPONENTS}
    has_transaction = "transaction_charges" in amounts
    has_ipft = "ipft" in amounts
    has_direct_exchange = "exchange_charges" in amounts

    if has_direct_exchange and (has_transaction or has_ipft):
        raise ValueError("Direct exchange_charges cannot coexist with transaction/IPFT rows; double mapping is ambiguous.")
    if has_ipft and not has_transaction:
        raise ValueError("A separate IPFT row requires a transaction_charges row.")
    if has_transaction:
        if len(modes) != 1 or len(versions) != 1:
            raise ValueError("Transaction/IPFT rows must declare one consistent representation mode and version.")
        mode = next(iter(modes))
        version = next(iter(versions))
        if mode not in {"COMBINED_TRANSACTION_AND_IPFT", "SPLIT_TRANSACTION_AND_IPFT"}:
            raise ValueError("Transaction/IPFT representation mode must be explicitly reviewed.")
        if version != CONTRACT_VERSION:
            raise ValueError("Transaction/IPFT representation contract version is missing or unsupported.")
        transaction_rows = [row for row in source_rows if row.component_name == "transaction_charges"]
        ipft_rows = [row for row in source_rows if row.component_name == "ipft"]
        if any(row.representation_mode != mode or row.representation_contract_version != version
               for row in transaction_rows + ipft_rows):
            raise ValueError("Transaction/IPFT source rows disagree on representation mode or contract version.")
        if mode == "COMBINED_TRANSACTION_AND_IPFT":
            if has_ipft:
                raise ValueError("Combined transaction charges must not include a separate IPFT row.")
            amounts["exchange_charges"] = amounts.pop("transaction_charges")
        else:
            if not has_ipft:
                raise ValueError("Split representation requires both transaction_charges and ipft.")
            amounts["exchange_charges"] = (
                amounts.pop("transaction_charges") + amounts.pop("ipft")
            ).quantize(Decimal("0.01"))
    elif has_ipft:
        raise ValueError("A separate IPFT row requires transaction_charges.")

    missing = set(CANONICAL_COMPONENTS) - set(amounts)
    allowed = set(CANONICAL_COMPONENTS) | set(OPTIONAL_CANONICAL_COMPONENTS)
    extra = set(amounts) - allowed
    if missing or extra:
        raise ValueError(
            f"Canonical source set mismatch; missing={sorted(missing)}, extra={sorted(extra)}."
        )

    source_names_by_canonical: dict[str, list[str]] = {}
    for row in source_rows:
        if row.component_name == "demat_transaction_charges":
            source_names_by_canonical.setdefault("demat_transaction_charges", []).append(row.component_name)
        elif row.component_name == "transaction_charges" or row.component_name == "ipft":
            source_names_by_canonical.setdefault("exchange_charges", []).append(row.component_name)
        else:
            source_names_by_canonical.setdefault(row.component_name, []).append(row.component_name)

    return {
        "mapping_version": CANONICAL_MAPPING_VERSION,
        "representation_contract_version": CONTRACT_VERSION if has_transaction else None,
        "canonical_components": {
            name: format(amounts[name].quantize(Decimal("0.01")), "f")
            for name in amounts
        },
        "source_components_by_canonical": {
            name: source_names_by_canonical[name]
            for name in amounts
        },
        "accounting_approved": False,
    }
