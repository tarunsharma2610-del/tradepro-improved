"""Independent review of canonical charge snapshots before allocation use."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.broker_charge_canonical_component import BrokerChargeCanonicalComponent
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.user import User
from app.services.broker_charge_canonical_component_snapshot_service import (
    canonical_source_snapshot_fingerprint,
)
from app.services.broker_charge_component_set_contract import LIVE_FILL_COMPONENT_SET_VERSION
from app.services.broker_charge_document_storage_service import read_verified_document
from app.services.broker_charge_verified_component_canonicalization import (
    canonicalize_verified_component_records,
)


def review_canonical_charge_component_snapshot(
    db: Session,
    *,
    snapshot_id: UUID,
    reviewer_user_id: UUID,
    decision: str,
    review_note: str,
) -> BrokerChargeCanonicalComponent:
    """Verify source linkage and approve/reject one snapshot under row locks.

    Reviewer must be an active admin distinct from the snapshot creator, the
    original evidence reviewer, and every source-row extractor. The caller owns
    the outer transaction; this function never commits.
    """
    if decision not in {"VERIFIED", "REJECTED"}:
        raise ValueError("Canonical snapshot decision must be VERIFIED or REJECTED.")
    if not isinstance(review_note, str) or not review_note.strip():
        raise ValueError("A non-empty canonical snapshot review note is required.")
    snapshot = (
        db.query(BrokerChargeCanonicalComponent)
        .filter(BrokerChargeCanonicalComponent.id == snapshot_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if snapshot is None:
        raise ValueError("Canonical charge snapshot was not found.")
    evidence = (
        db.query(BrokerChargeEvidence)
        .filter(BrokerChargeEvidence.id == snapshot.evidence_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if (
        evidence is None
        or evidence.status != "REVIEWED"
        or evidence.source_kind != "CONTRACT_NOTE"
        or evidence.reviewed_by_user_id is None
        or not evidence.storage_key
    ):
        raise ValueError("Reviewed contract-note evidence is required for canonical snapshot review.")
    try:
        read_verified_document(
            root=settings.BROKER_CHARGE_DOCUMENT_ROOT,
            storage_key=evidence.storage_key,
            expected_sha256=evidence.source_sha256,
            expected_size=evidence.byte_size,
        )
    except ValueError as exc:
        raise ValueError("Contract-note source integrity check failed.") from exc

    try:
        source_ids = json.loads(snapshot.source_component_ids_json)
        parsed_ids = [UUID(value) for value in source_ids]
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Canonical snapshot source-row manifest is invalid.") from exc
    if not isinstance(source_ids, list) or not source_ids or len(set(parsed_ids)) != len(parsed_ids):
        raise ValueError("Canonical snapshot source-row manifest must contain unique source IDs.")
    records = (
        db.query(BrokerChargeSourceComponent)
        .filter(
            BrokerChargeSourceComponent.evidence_id == evidence.id,
            BrokerChargeSourceComponent.id.in_(parsed_ids),
        )
        .with_for_update()
        .populate_existing()
        .all()
    )
    if {row.id for row in records} != set(parsed_ids):
        raise ValueError("Canonical snapshot references missing or foreign source rows.")
    records.sort(key=lambda row: (row.component_name, row.revision, str(row.id)))
    if [str(row.id) for row in records] != source_ids:
        raise ValueError("Canonical snapshot source-row manifest is not in canonical order.")
    if any(
        row.status != "VERIFIED"
        or row.source_sha256 != evidence.source_sha256
        or row.currency != "INR"
        or row.component_set_version != LIVE_FILL_COMPONENT_SET_VERSION
        or row.reviewed_by_user_id != evidence.reviewed_by_user_id
        or row.reviewed_by_user_id is None
        or row.reviewed_at is None
        or row.reviewed_by_user_id == row.extracted_by_user_id
        for row in records
    ):
        raise ValueError("Canonical snapshot source rows are no longer independently verified.")

    all_records = (
        db.query(BrokerChargeSourceComponent)
        .filter(BrokerChargeSourceComponent.evidence_id == evidence.id)
        .with_for_update()
        .populate_existing()
        .all()
    )
    canonical = canonicalize_verified_component_records(
        all_records,
        expected_evidence_id=evidence.id,
        expected_source_sha256=evidence.source_sha256,
    )
    source_names = set(canonical["source_components_by_canonical"][snapshot.canonical_component])
    if {row.component_name for row in records} != source_names:
        raise ValueError("Canonical snapshot source rows no longer match the canonical mapping.")
    if canonical["canonical_components"][snapshot.canonical_component] != format(Decimal(snapshot.canonical_amount), ".2f"):
        raise ValueError("Canonical snapshot amount no longer matches its reviewed source rows.")
    if snapshot.mapping_version != canonical["mapping_version"]:
        raise ValueError("Canonical snapshot mapping version no longer matches.")
    if snapshot.representation_contract_version != canonical["representation_contract_version"]:
        raise ValueError("Canonical snapshot representation contract version no longer matches.")
    fingerprint = canonical_source_snapshot_fingerprint(
        evidence=evidence,
        canonical_component=snapshot.canonical_component,
        canonical_amount=canonical["canonical_components"][snapshot.canonical_component],
        mapping_version=canonical["mapping_version"],
        representation_contract_version=canonical["representation_contract_version"],
        source_rows=records,
    )
    if fingerprint != snapshot.source_snapshot_sha256:
        raise ValueError("Canonical snapshot source fingerprint is stale.")
    if (
        snapshot.currency != "INR"
        or snapshot.component_set_version != LIVE_FILL_COMPONENT_SET_VERSION
        or snapshot.rounding_policy != "largest-remainder-v1"
        or snapshot.allocation_basis != "EXPLICIT_REVIEWED"
        or any(
            getattr(snapshot, field) != getattr(records[0], field)
            for field in (
                "eligible_fill_ids_json",
                "eligible_fill_weights_json",
                "eligible_fill_set_sha256",
                "rounding_policy",
                "allocation_basis",
            )
        )
        or any(
            getattr(row, field) != getattr(records[0], field)
            for row in records[1:]
            for field in (
                "eligible_fill_ids_json",
                "eligible_fill_weights_json",
                "eligible_fill_set_sha256",
                "rounding_policy",
                "allocation_basis",
                "component_set_version",
            )
        )
    ):
        raise ValueError("Canonical snapshot allocation metadata no longer matches reviewed source rows.")

    actor = (
        db.query(User)
        .filter(User.id == reviewer_user_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if actor is None or not actor.is_active or not actor.is_admin:
        raise ValueError("Only an active platform administrator may review canonical snapshots.")
    source_extractors = {row.extracted_by_user_id for row in records}
    if (
        reviewer_user_id == snapshot.created_by_user_id
        or reviewer_user_id == evidence.reviewed_by_user_id
        or reviewer_user_id in source_extractors
    ):
        raise ValueError("Canonical snapshot reviewer must be distinct from creator, source reviewer, and extractors.")

    if snapshot.status in {"VERIFIED", "REJECTED"}:
        if (
            snapshot.status == decision
            and snapshot.reviewed_by_user_id == reviewer_user_id
            and snapshot.review_note == review_note.strip()
        ):
            return snapshot
        raise ValueError("Reviewed canonical snapshot decisions are immutable.")
    if snapshot.status != "PENDING_REVIEW":
        raise ValueError("Canonical snapshot is not pending review.")
    snapshot.status = decision
    snapshot.reviewed_by_user_id = reviewer_user_id
    snapshot.reviewed_at = datetime.now(timezone.utc)
    snapshot.review_note = review_note.strip()
    db.flush()
    return snapshot
