"""Materialize immutable, pending-review snapshots of canonical source charges."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.broker_charge_canonical_component import BrokerChargeCanonicalComponent
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.user import User
from app.services.broker_charge_allocation_service import METHOD_VERSION
from app.services.broker_charge_canonical_allocation_plan import SUPPORTED_CANONICAL_COMPONENTS
from app.services.broker_charge_component_set_contract import LIVE_FILL_COMPONENT_SET_VERSION
from app.services.broker_charge_document_storage_service import read_verified_document
from app.services.broker_charge_verified_component_canonicalization import (
    canonicalize_verified_component_records,
)


def materialize_canonical_charge_component_snapshots(
    db: Session,
    *,
    evidence_id: UUID,
    requested_by_user_id: UUID,
) -> list[BrokerChargeCanonicalComponent]:
    """Create or replay six immutable PENDING_REVIEW canonical snapshots.

    The caller owns the outer transaction. Existing identical snapshots are
    returned idempotently. New snapshots preserve the exact source-row IDs and
    a fingerprint of the source values, mapping version, and fill allocation
    metadata. This operation never approves a snapshot or persists allocations.
    """
    if not isinstance(evidence_id, UUID) or not isinstance(requested_by_user_id, UUID):
        raise ValueError("Persisted evidence and requesting user IDs are required.")
    evidence = (
        db.query(BrokerChargeEvidence)
        .filter(BrokerChargeEvidence.id == evidence_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if (
        evidence is None
        or evidence.source_kind != "CONTRACT_NOTE"
        or evidence.status != "REVIEWED"
        or evidence.reviewed_by_user_id is None
        or evidence.reviewed_at is None
        or not evidence.storage_key
    ):
        raise ValueError("Reviewed contract-note evidence with stored original bytes is required.")
    actor = (
        db.query(User)
        .filter(User.id == requested_by_user_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if actor is None or not actor.is_active or not actor.is_admin:
        raise ValueError("Only an active platform administrator may materialize canonical charge snapshots.")
    try:
        read_verified_document(
            root=settings.BROKER_CHARGE_DOCUMENT_ROOT,
            storage_key=evidence.storage_key,
            expected_sha256=evidence.source_sha256,
            expected_size=evidence.byte_size,
        )
    except ValueError as exc:
        raise ValueError("Contract-note source integrity check failed.") from exc

    records = (
        db.query(BrokerChargeSourceComponent)
        .filter(BrokerChargeSourceComponent.evidence_id == evidence_id)
        .order_by(BrokerChargeSourceComponent.component_name, BrokerChargeSourceComponent.revision, BrokerChargeSourceComponent.id)
        .with_for_update()
        .populate_existing()
        .all()
    )
    if not records:
        raise ValueError("Reviewed source component records are required.")
    for row in records:
        if (
            row.status != "VERIFIED"
            or row.source_sha256 != evidence.source_sha256
            or row.currency != "INR"
            or row.reviewed_by_user_id is None
            or row.reviewed_at is None
            or row.reviewed_by_user_id != evidence.reviewed_by_user_id
            or row.reviewed_by_user_id == row.extracted_by_user_id
            or row.component_set_version != LIVE_FILL_COMPONENT_SET_VERSION
        ):
            raise ValueError("Every raw source row must be independently verified against this evidence and component-set version.")

    canonical = canonicalize_verified_component_records(
        records,
        expected_evidence_id=evidence.id,
        expected_source_sha256=evidence.source_sha256,
    )
    mapping = canonical["source_components_by_canonical"]
    if set(mapping) != SUPPORTED_CANONICAL_COMPONENTS:
        raise ValueError("Canonical source mapping must produce exactly the approved six-component set.")

    # All six components must describe the same reviewed fill population and
    # allocation policy. For split exchange charges, both source rows must agree.
    all_manifest_values = {row.eligible_fill_ids_json for row in records}
    all_weight_values = {row.eligible_fill_weights_json for row in records}
    all_manifest_hashes = {row.eligible_fill_set_sha256 for row in records}
    all_rounding = {row.rounding_policy for row in records}
    all_bases = {row.allocation_basis for row in records}
    if (
        len(all_manifest_values) != 1 or None in all_manifest_values or "" in all_manifest_values
        or len(all_weight_values) != 1 or None in all_weight_values or "" in all_weight_values
        or len(all_manifest_hashes) != 1 or None in all_manifest_hashes or "" in all_manifest_hashes
        or len(all_rounding) != 1 or all_rounding != {METHOD_VERSION}
        or len(all_bases) != 1 or all_bases != {"EXPLICIT_REVIEWED"}
    ):
        raise ValueError("All contributing source rows must share one reviewed fill manifest, explicit weights, basis, and method version.")

    manifest_json = next(iter(all_manifest_values))
    weights_json = next(iter(all_weight_values))
    manifest_hash = next(iter(all_manifest_hashes))
    try:
        manifest_ids = json.loads(manifest_json)
        weights = json.loads(weights_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Reviewed fill manifest or weight JSON is invalid.") from exc
    if not isinstance(manifest_ids, list) or not manifest_ids or any(not isinstance(value, str) for value in manifest_ids):
        raise ValueError("Reviewed fill manifest must be a non-empty list of UUID strings.")
    try:
        normalized_ids = [str(UUID(value)) for value in manifest_ids]
    except (TypeError, ValueError) as exc:
        raise ValueError("Reviewed fill manifest contains an invalid UUID.") from exc
    canonical_manifest = json.dumps(sorted(normalized_ids), separators=(",", ":"))
    if normalized_ids != sorted(normalized_ids) or len(set(normalized_ids)) != len(normalized_ids):
        raise ValueError("Reviewed fill manifest must be unique and sorted.")
    if hashlib.sha256(canonical_manifest.encode("utf-8")).hexdigest() != manifest_hash:
        raise ValueError("Reviewed fill manifest fingerprint does not match.")
    if not isinstance(weights, list):
        raise ValueError("Reviewed explicit weights must be a JSON list.")
    normalized_weight_ids: list[str] = []
    for item in weights:
        if not isinstance(item, dict) or set(item) != {"fill_record_id", "weight"}:
            raise ValueError("Reviewed explicit weight entry is malformed.")
        try:
            normalized_weight_ids.append(str(UUID(item["fill_record_id"])))
            weight = Decimal(str(item["weight"]))
        except (TypeError, ValueError, ArithmeticError) as exc:
            raise ValueError("Reviewed explicit weight entry is invalid.") from exc
        if not weight.is_finite() or weight < 0:
            raise ValueError("Reviewed explicit weights must be finite and nonnegative.")
    if normalized_weight_ids != normalized_ids or len(set(normalized_weight_ids)) != len(normalized_weight_ids):
        raise ValueError("Reviewed explicit weights must match the canonical fill manifest order.")
    canonical_weights = json.dumps(
        [{"fill_record_id": fill_id, "weight": str(item["weight"])} for fill_id, item in zip(normalized_ids, weights)],
        separators=(",", ":"),
    )
    if canonical_weights != weights_json:
        raise ValueError("Reviewed explicit weights are not in canonical JSON representation.")

    result: list[BrokerChargeCanonicalComponent] = []
    for canonical_name in sorted(SUPPORTED_CANONICAL_COMPONENTS):
        source_names = set(mapping[canonical_name])
        source_rows = [row for row in records if row.component_name in source_names]
        source_rows.sort(key=lambda row: (row.component_name, row.revision, str(row.id)))
        source_ids = [str(row.id) for row in source_rows]
        source_ids_json = json.dumps(source_ids, separators=(",", ":"))
        fingerprint_payload = {
            "evidence_id": str(evidence.id),
            "evidence_sha256": evidence.source_sha256,
            "canonical_component": canonical_name,
            "canonical_amount": canonical["canonical_components"][canonical_name],
            "mapping_version": canonical["mapping_version"],
            "representation_contract_version": canonical["representation_contract_version"],
            "component_set_version": LIVE_FILL_COMPONENT_SET_VERSION,
            "source_rows": [
                {
                    "id": str(row.id),
                    "name": row.component_name,
                    "revision": row.revision,
                    "amount": format(Decimal(row.source_amount), ".2f"),
                    "source_sha256": row.source_sha256,
                    "source_label": row.source_label,
                    "source_locator": row.source_locator,
                    "representation_mode": row.representation_mode,
                    "representation_contract_version": row.representation_contract_version,
                    "currency": row.currency,
                    "component_set_version": row.component_set_version,
                    "eligible_fill_ids_json": row.eligible_fill_ids_json,
                    "eligible_fill_weights_json": row.eligible_fill_weights_json,
                    "eligible_fill_set_sha256": row.eligible_fill_set_sha256,
                    "rounding_policy": row.rounding_policy,
                    "allocation_basis": row.allocation_basis,
                    "reviewed_by_user_id": str(row.reviewed_by_user_id) if row.reviewed_by_user_id else None,
                    "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
                }
                for row in source_rows
            ],
        }
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        existing = (
            db.query(BrokerChargeCanonicalComponent)
            .filter(
                BrokerChargeCanonicalComponent.evidence_id == evidence.id,
                BrokerChargeCanonicalComponent.canonical_component == canonical_name,
                BrokerChargeCanonicalComponent.source_snapshot_sha256 == fingerprint,
            )
            .with_for_update()
            .one_or_none()
        )
        if existing is not None:
            result.append(existing)
            continue
        next_revision = (
            db.query(func.max(BrokerChargeCanonicalComponent.revision))
            .filter(
                BrokerChargeCanonicalComponent.evidence_id == evidence.id,
                BrokerChargeCanonicalComponent.canonical_component == canonical_name,
            )
            .scalar()
            or 0
        ) + 1
        snapshot = BrokerChargeCanonicalComponent(
            evidence_id=evidence.id,
            canonical_component=canonical_name,
            revision=next_revision,
            source_component_ids_json=source_ids_json,
            source_snapshot_sha256=fingerprint,
            mapping_version=canonical["mapping_version"],
            representation_contract_version=canonical["representation_contract_version"],
            canonical_amount=Decimal(canonical["canonical_components"][canonical_name]),
            currency="INR",
            component_set_version=LIVE_FILL_COMPONENT_SET_VERSION,
            eligible_fill_ids_json=manifest_json,
            eligible_fill_weights_json=weights_json,
            eligible_fill_set_sha256=manifest_hash,
            rounding_policy=METHOD_VERSION,
            allocation_basis="EXPLICIT_REVIEWED",
            created_by_user_id=requested_by_user_id,
            status="PENDING_REVIEW",
        )
        db.add(snapshot)
        db.flush()
        result.append(snapshot)
    return sorted(result, key=lambda row: row.canonical_component)
