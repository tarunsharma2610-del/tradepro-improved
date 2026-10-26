"""Fail-closed adapter from reviewed source-component rows to canonical totals.

This is the boundary between persisted reviewer decisions and the pure
source-to-canonical mapping contract. It returns a derived view only: callers
must still use the ledger's existing locked verification/promotion protocol.
"""
from __future__ import annotations

from typing import Iterable
from uuid import UUID

from app.services.broker_charge_source_canonicalization import (
    SourceChargeRow,
    canonicalize_reviewed_source_components,
)


def canonicalize_verified_component_records(
    records: Iterable[object],
    *,
    expected_evidence_id: UUID | str,
    expected_source_sha256: str,
) -> dict[str, object]:
    """Canonicalize one evidence document's latest independently reviewed rows.

    Every row must already be VERIFIED, tied to the same evidence ID and
    immutable source hash, have reviewer provenance, and be INR-denominated.
    No status is promoted or database row mutated by this function.
    """
    rows = tuple(records)
    if not rows:
        raise ValueError("Verified source component records are required.")
    expected_id = str(expected_evidence_id)
    if len(expected_source_sha256) != 64 or any(
        char not in "0123456789abcdef" for char in expected_source_sha256.lower()
    ):
        raise ValueError("Expected evidence source SHA-256 must be a 64-character hexadecimal digest.")

    source_rows: list[SourceChargeRow] = []
    provenance: list[dict[str, str | int]] = []
    seen_ids: set[str] = set()
    for record in rows:
        record_id = str(getattr(record, "id", "") or "")
        if not record_id or record_id in seen_ids:
            raise ValueError("Every reviewed source row requires a unique persisted ID.")
        seen_ids.add(record_id)
        if str(getattr(record, "evidence_id", "")) != expected_id:
            raise ValueError("Source component belongs to a different evidence record.")
        source_hash = getattr(record, "source_sha256", None)
        if not isinstance(source_hash, str) or source_hash.lower() != expected_source_sha256.lower():
            raise ValueError("Source component hash does not match the expected evidence bytes.")
        if getattr(record, "status", None) != "VERIFIED":
            raise ValueError("Only independently VERIFIED source components can be canonicalized.")
        reviewer_id = getattr(record, "reviewed_by_user_id", None)
        extractor_id = getattr(record, "extracted_by_user_id", None)
        if reviewer_id is None or getattr(record, "reviewed_at", None) is None:
            raise ValueError("Verified source components require reviewer identity and timestamp.")
        if extractor_id is None or reviewer_id == extractor_id:
            raise ValueError("Verified source components require a reviewer distinct from the extractor.")
        if getattr(record, "currency", None) != "INR":
            raise ValueError("Only INR source components are supported.")
        label = getattr(record, "source_label", None)
        locator = getattr(record, "source_locator", None)
        if not isinstance(locator, str) or not locator.strip():
            raise ValueError("Every verified source component requires a source locator.")

        source_rows.append(SourceChargeRow(
            component_name=getattr(record, "component_name", None),
            source_amount=getattr(record, "source_amount", None),
            source_label=label,
            representation_mode=getattr(record, "representation_mode", None),
            representation_contract_version=getattr(record, "representation_contract_version", None),
        ))
        provenance.append({
            "record_id": record_id,
            "component_name": str(getattr(record, "component_name", "")),
            "revision": int(getattr(record, "revision", 0)),
            "source_locator": locator.strip(),
            "reviewer_id": str(getattr(record, "reviewed_by_user_id")),
        })

    canonical = canonicalize_reviewed_source_components(source_rows)
    canonical["evidence_id"] = expected_id
    canonical["source_sha256"] = expected_source_sha256.lower()
    canonical["source_record_provenance"] = sorted(
        provenance, key=lambda item: (str(item["component_name"]), int(item["revision"]), str(item["record_id"]))
    )
    # Canonicalization is not accounting approval. Promotion remains a separate,
    # transaction-owning service that must lock/revalidate all reviewed rows.
    canonical["accounting_approved"] = False
    return canonical
