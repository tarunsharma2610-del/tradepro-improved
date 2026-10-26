"""Build a fail-closed per-fill allocation plan from verified source rows.

This joins source-to-canonical mapping with deterministic paise allocation but
does not write the database or promote accounting. Persistence callers must
revalidate the evidence and reviewed fill manifest under locks.
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Iterable
from uuid import UUID

from app.services.broker_charge_allocation_service import METHOD_VERSION, allocate_component_total
from app.services.broker_charge_verified_component_canonicalization import (
    canonicalize_verified_component_records,
)

SUPPORTED_CANONICAL_COMPONENTS = frozenset({
    "brokerage", "stt", "exchange_charges", "sebi_charges", "stamp_duty", "gst", "demat_transaction_charges"
})


def build_verified_component_allocation_plan(
    records: Iterable[object],
    *,
    evidence_id: UUID | str,
    source_sha256: str,
    canonical_component: str,
) -> dict[str, object]:
    """Return an exact per-fill plan tied to verified source-row provenance.

    All source rows contributing to a canonical component must independently
    carry the same canonical fill manifest, explicit reviewed weights, basis,
    and rounding policy. Generic QUANTITY/NOTIONAL plans are deliberately not
    enabled here: effective-dated component-specific tariff rules are not yet
    approved.
    """
    if canonical_component not in SUPPORTED_CANONICAL_COMPONENTS:
        raise ValueError("Unsupported canonical accounting component.")
    rows = tuple(records)
    canonical = canonicalize_verified_component_records(
        rows,
        expected_evidence_id=evidence_id,
        expected_source_sha256=source_sha256,
    )
    contributing_names = set(canonical["source_components_by_canonical"][canonical_component])
    contributing = [
        row for row in rows
        if getattr(row, "component_name", None) in contributing_names
    ]
    if not contributing:
        raise ValueError("Verified source rows do not provide the requested canonical component.")
    # A combined transaction/IPFT representation can use one source row;
    # split representation requires both rows and the canonicalizer validates it.
    manifests = {getattr(row, "eligible_fill_ids_json", None) for row in contributing}
    weights_json_values = {getattr(row, "eligible_fill_weights_json", None) for row in contributing}
    bases = {getattr(row, "allocation_basis", None) for row in contributing}
    rounding = {getattr(row, "rounding_policy", None) for row in contributing}
    if len(manifests) != 1 or None in manifests or "" in manifests:
        raise ValueError("Contributing source rows must share one reviewed eligible-fill manifest.")
    if len(weights_json_values) != 1 or None in weights_json_values or "" in weights_json_values:
        raise ValueError("Contributing source rows must share explicit reviewed per-fill weights.")
    if len(bases) != 1 or bases != {"EXPLICIT_REVIEWED"}:
        raise ValueError("Only a consistent EXPLICIT_REVIEWED allocation basis is enabled.")
    if len(rounding) != 1 or rounding != {METHOD_VERSION}:
        raise ValueError("Source rows must use the supported deterministic allocation method.")

    manifest_json = next(iter(manifests))
    try:
        manifest = json.loads(manifest_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Eligible-fill manifest is invalid JSON.") from exc
    if not isinstance(manifest, list) or not manifest or any(not isinstance(value, str) for value in manifest):
        raise ValueError("Eligible-fill manifest must be a non-empty list of fill UUID strings.")
    try:
        fill_ids = [str(UUID(value)) for value in manifest]
    except (TypeError, ValueError) as exc:
        raise ValueError("Eligible-fill manifest contains an invalid UUID.") from exc
    if len(set(fill_ids)) != len(fill_ids) or fill_ids != sorted(fill_ids):
        raise ValueError("Eligible-fill manifest must contain unique UUIDs in canonical sorted order.")
    canonical_manifest = json.dumps(fill_ids, separators=(",", ":"))
    if canonical_manifest != manifest_json:
        raise ValueError("Eligible-fill manifest is not in canonical JSON representation.")
    expected_manifest_hash = hashlib.sha256(canonical_manifest.encode("utf-8")).hexdigest()
    if any(getattr(row, "eligible_fill_set_sha256", None) != expected_manifest_hash for row in contributing):
        raise ValueError("Eligible-fill manifest fingerprint does not match.")

    weights_json = next(iter(weights_json_values))
    try:
        weight_items = json.loads(weights_json)
        if not isinstance(weight_items, list):
            raise ValueError("Explicit reviewed weights must be a JSON list.")
        weights: dict[str, Decimal] = {}
        for item in weight_items:
            if not isinstance(item, dict) or set(item) != {"fill_record_id", "weight"}:
                raise ValueError("Explicit reviewed weight entry is malformed.")
            fill_id = str(UUID(item["fill_record_id"]))
            weight = Decimal(str(item["weight"]))
            if not weight.is_finite() or weight < 0 or fill_id in weights:
                raise ValueError("Explicit reviewed weights are invalid.")
            weights[fill_id] = weight
    except (TypeError, KeyError, ValueError, ArithmeticError) as exc:
        raise ValueError("Explicit reviewed per-fill weights are invalid.") from exc
    if set(weights) != set(fill_ids) or list(weights) != fill_ids:
        raise ValueError("Explicit reviewed weights must match the canonical fill manifest order.")
    canonical_weights = json.dumps(
        [{"fill_record_id": fill_id, "weight": str(weights[fill_id])} for fill_id in fill_ids],
        separators=(",", ":"),
    )
    if canonical_weights != weights_json:
        raise ValueError("Explicit reviewed weights are not in canonical JSON representation.")

    total = Decimal(canonical["canonical_components"][canonical_component])
    allocations = allocate_component_total(
        total,
        weights,
        allocation_basis="EXPLICIT_REVIEWED",
    )
    if sum(allocations.values(), Decimal("0")) != total:
        raise ValueError("Planned per-fill amounts do not reconcile to the canonical source total.")
    return {
        "evidence_id": canonical["evidence_id"],
        "source_sha256": canonical["source_sha256"],
        "canonical_mapping_version": canonical["mapping_version"],
        "representation_contract_version": canonical["representation_contract_version"],
        "canonical_component": canonical_component,
        "canonical_source_total": format(total, ".2f"),
        "allocation_basis": "EXPLICIT_REVIEWED",
        "method_version": METHOD_VERSION,
        "eligible_fill_ids": fill_ids,
        "eligible_fill_set_sha256": expected_manifest_hash,
        "allocations": {fill_id: format(amount, ".2f") for fill_id, amount in allocations.items()},
        "source_record_provenance": [
            item for item in canonical["source_record_provenance"]
            if item["component_name"] in contributing_names
        ],
        "accounting_approved": False,
        "persisted": False,
    }
