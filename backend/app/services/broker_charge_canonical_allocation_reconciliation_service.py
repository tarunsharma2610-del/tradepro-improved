"""Verify and atomically reconcile allocations tied to a reviewed canonical snapshot."""
from __future__ import annotations

import json
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.models.broker_charge_canonical_component import BrokerChargeCanonicalComponent
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.user import User
from app.services.broker_charge_allocation_service import METHOD_VERSION, allocate_component_total
from app.services.broker_charge_canonical_component_review_service import (
    review_canonical_charge_component_snapshot,
)


def verify_canonical_component_allocation_ledger(
    db: Session, *, snapshot_id: UUID
) -> dict[str, object]:
    """Read-only, locked verification of allocations against canonical snapshot provenance."""
    snapshot = (
        db.query(BrokerChargeCanonicalComponent)
        .filter(BrokerChargeCanonicalComponent.id == snapshot_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if (
        snapshot is None
        or snapshot.status != "VERIFIED"
        or snapshot.reviewed_by_user_id is None
        or not snapshot.review_note
    ):
        raise ValueError("An independently verified canonical snapshot is required.")
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
    ):
        raise ValueError("Reviewed contract-note evidence is required.")
    # Revalidate original document bytes, source links, mapping, source fingerprint,
    # and independent reviewer authority inside this transaction.
    review_canonical_charge_component_snapshot(
        db,
        snapshot_id=snapshot.id,
        reviewer_user_id=snapshot.reviewed_by_user_id,
        decision="VERIFIED",
        review_note=snapshot.review_note,
    )
    if (
        snapshot.currency != "INR"
        or snapshot.component_set_version is None
        or snapshot.rounding_policy != METHOD_VERSION
        or snapshot.allocation_basis != "EXPLICIT_REVIEWED"
        or not snapshot.eligible_fill_ids_json
        or not snapshot.eligible_fill_weights_json
        or not snapshot.eligible_fill_set_sha256
    ):
        raise ValueError("Canonical snapshot lacks a supported currency, allocation method, or reviewed fill manifest.")

    try:
        fill_ids = json.loads(snapshot.eligible_fill_ids_json)
        weight_items = json.loads(snapshot.eligible_fill_weights_json)
        normalized_ids = [str(UUID(value)) for value in fill_ids]
        if not isinstance(fill_ids, list) or not isinstance(weight_items, list):
            raise ValueError("Fill manifest and weights must be lists.")
        weights: dict[str, Decimal] = {}
        for item in weight_items:
            if not isinstance(item, dict) or set(item) != {"fill_record_id", "weight"}:
                raise ValueError("Reviewed fill weight entry is malformed.")
            fill_id = str(UUID(item["fill_record_id"]))
            weight = Decimal(str(item["weight"]))
            if not weight.is_finite() or weight < 0 or fill_id in weights:
                raise ValueError("Reviewed fill weights are invalid or duplicated.")
            weights[fill_id] = weight
    except (TypeError, KeyError, ValueError, json.JSONDecodeError, ArithmeticError) as exc:
        raise ValueError("Canonical snapshot fill manifest or weights are invalid.") from exc
    if (
        not normalized_ids
        or normalized_ids != sorted(normalized_ids)
        or len(set(normalized_ids)) != len(normalized_ids)
        or set(weights) != set(normalized_ids)
        or list(weights) != normalized_ids
    ):
        raise ValueError("Canonical snapshot fill manifest and weights do not match in canonical order.")

    expected_amounts = allocate_component_total(
        Decimal(snapshot.canonical_amount),
        weights,
        allocation_basis=snapshot.allocation_basis,
    )
    rows = (
        db.query(BrokerChargeAllocation)
        .filter(
            BrokerChargeAllocation.canonical_component_id == snapshot.id,
            BrokerChargeAllocation.evidence_id == evidence.id,
            BrokerChargeAllocation.charge_component == snapshot.canonical_component,
        )
        .order_by(BrokerChargeAllocation.broker_trade_record_id, BrokerChargeAllocation.id)
        .with_for_update()
        .all()
    )
    if not rows:
        raise ValueError("No allocations are linked to this canonical snapshot.")
    if {str(row.broker_trade_record_id) for row in rows} != set(normalized_ids):
        raise ValueError("Canonical allocation fill set differs from the reviewed snapshot manifest.")
    allowed_statuses = {"PENDING_RECONCILIATION", "RECONCILED"}
    if any(
        row.status not in allowed_statuses
        or row.broker_connection_id != evidence.broker_connection_id
        or row.currency != "INR"
        or row.allocation_basis != snapshot.allocation_basis
        or row.method_version != snapshot.rounding_policy
        or Decimal(row.source_component_total) != Decimal(snapshot.canonical_amount)
        or Decimal(row.allocated_amount) != expected_amounts[str(row.broker_trade_record_id)]
        for row in rows
    ):
        raise ValueError("Canonical allocation rows do not match the verified snapshot or deterministic paise allocation.")
    if len({row.status for row in rows}) != 1:
        raise ValueError("Canonical allocation ledger has mixed reconciliation states.")
    statuses = {row.status for row in rows}
    if statuses == {"RECONCILED"}:
        references = {row.reconciliation_reference for row in rows}
        if len(references) != 1 or None in references:
            raise ValueError("Reconciled canonical allocations lack one durable reference.")
        status = "ALREADY_RECONCILED"
        reference = next(iter(references))
    else:
        if any(row.reconciliation_reference is not None for row in rows):
            raise ValueError("Pending canonical allocations must not carry reconciliation references.")
        status = "VERIFIED_PENDING_PROMOTION"
        reference = (
            f"canonical-charge:{snapshot.id}:{snapshot.source_snapshot_sha256}:"
            f"{snapshot.eligible_fill_set_sha256}:{snapshot.rounding_policy}"
        )
    return {
        "snapshot_id": str(snapshot.id),
        "evidence_id": str(evidence.id),
        "canonical_component": snapshot.canonical_component,
        "canonical_amount": format(Decimal(snapshot.canonical_amount), ".2f"),
        "source_snapshot_sha256": snapshot.source_snapshot_sha256,
        "eligible_fill_set_sha256": snapshot.eligible_fill_set_sha256,
        "reviewed_by_user_id": str(snapshot.reviewed_by_user_id),
        "status": status,
        "reconciliation_reference": reference,
        "allocation_ids": [str(row.id) for row in rows],
    }


def promote_verified_canonical_component_allocations(
    db: Session, *, snapshot_id: UUID, reviewer_user_id: UUID
) -> list[BrokerChargeAllocation]:
    """Promote one complete canonical allocation set in the caller's transaction."""
    with db.begin_nested():
        verification = verify_canonical_component_allocation_ledger(db, snapshot_id=snapshot_id)
        if verification["reviewed_by_user_id"] != str(reviewer_user_id):
            raise ValueError("Only the independently authorized canonical-snapshot reviewer may promote this allocation set.")
        reviewer = (
            db.query(User)
            .filter(User.id == reviewer_user_id)
            .with_for_update()
            .populate_existing()
            .one_or_none()
        )
        if reviewer is None or not reviewer.is_active or not reviewer.is_admin:
            raise ValueError("Only an active platform administrator may promote canonical allocations.")
        snapshot = (
            db.query(BrokerChargeCanonicalComponent)
            .filter(BrokerChargeCanonicalComponent.id == snapshot_id)
            .with_for_update()
            .populate_existing()
            .one()
        )
        if snapshot.canonical_component == "demat_transaction_charges":
            raise ValueError(
                "DP/demat allocation promotion remains blocked until Execution persistence and total-charge recomputation support it."
            )
        rows = (
            db.query(BrokerChargeAllocation)
            .filter(
                BrokerChargeAllocation.canonical_component_id == snapshot.id,
                BrokerChargeAllocation.evidence_id == UUID(str(verification["evidence_id"])),
                BrokerChargeAllocation.charge_component == str(verification["canonical_component"]),
            )
            .order_by(BrokerChargeAllocation.broker_trade_record_id, BrokerChargeAllocation.id)
            .with_for_update()
            .all()
        )
        if {str(row.id) for row in rows} != set(verification["allocation_ids"]):
            raise ValueError("Canonical allocation set changed between verification and promotion.")
        reference = str(verification["reconciliation_reference"])
        if verification["status"] == "ALREADY_RECONCILED":
            if not rows or any(row.reconciliation_reference != reference for row in rows):
                raise ValueError("Previously reconciled canonical allocations do not match their durable reference.")
            return rows
        if verification["status"] != "VERIFIED_PENDING_PROMOTION":
            raise ValueError("Canonical allocation set is not eligible for reconciliation promotion.")
        if not rows or any(row.status != "PENDING_RECONCILIATION" for row in rows):
            raise ValueError("All canonical allocation rows must still be pending for atomic promotion.")
        for row in rows:
            row.status = "RECONCILED"
            row.reconciliation_reference = reference
        db.flush()
        if any(row.status != "RECONCILED" or row.reconciliation_reference != reference for row in rows):
            raise ValueError("Atomic canonical allocation promotion failed.")
        return rows
