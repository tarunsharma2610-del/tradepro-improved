"""Persist per-fill allocations against an independently verified canonical snapshot."""
from __future__ import annotations

import json
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.broker_charge_canonical_component import BrokerChargeCanonicalComponent
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.services.broker_charge_allocation_persistence_service import allocate_and_persist_component
from app.services.broker_charge_canonical_component_review_service import (
    review_canonical_charge_component_snapshot,
)


def allocate_and_persist_canonical_snapshot(
    db: Session,
    *,
    snapshot_id: UUID,
    broker_connection_id: UUID,
    broker_report_reference: str,
) -> list[BrokerChargeAllocation]:
    """Persist allocations only for a VERIFIED, fingerprint-current snapshot.

    The source reviewer and canonical-snapshot reviewer are deliberately
    different identities. Existing evidence persistence checks are retained,
    while each new allocation row records the canonical snapshot foreign key.
    Caller owns the outer transaction; rows remain PENDING_RECONCILIATION.
    """
    snapshot = (
        db.query(BrokerChargeCanonicalComponent)
        .filter(BrokerChargeCanonicalComponent.id == snapshot_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if snapshot is None or snapshot.status != "VERIFIED" or snapshot.reviewed_by_user_id is None:
        raise ValueError("An independently VERIFIED canonical charge snapshot is required.")
    evidence = (
        db.query(BrokerChargeEvidence)
        .filter(
            BrokerChargeEvidence.id == snapshot.evidence_id,
            BrokerChargeEvidence.broker_connection_id == broker_connection_id,
            BrokerChargeEvidence.broker_report_reference == broker_report_reference,
            BrokerChargeEvidence.status == "REVIEWED",
        )
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if evidence is None or evidence.reviewed_by_user_id is None:
        raise ValueError("Matching reviewed contract-note evidence is required.")
    # Revalidate source bytes, source-row fingerprint, mapping and reviewer
    # authority immediately before allocation; this is an idempotent read/verify
    # replay, not a new approval.
    review_canonical_charge_component_snapshot(
        db,
        snapshot_id=snapshot.id,
        reviewer_user_id=snapshot.reviewed_by_user_id,
        decision="VERIFIED",
        review_note=snapshot.review_note or "",
    )
    if snapshot.currency != "INR" or snapshot.allocation_basis != "EXPLICIT_REVIEWED":
        raise ValueError("Canonical snapshot currency or allocation basis is not supported.")
    if not snapshot.eligible_fill_ids_json or not snapshot.eligible_fill_weights_json:
        raise ValueError("Canonical snapshot must carry a reviewed fill manifest and explicit weights.")
    try:
        fill_ids = json.loads(snapshot.eligible_fill_ids_json)
        weight_items = json.loads(snapshot.eligible_fill_weights_json)
        if not isinstance(fill_ids, list) or not isinstance(weight_items, list):
            raise ValueError("Fill manifest and weights must be JSON lists.")
        normalized_ids = [str(UUID(value)) for value in fill_ids]
        fill_weights: dict[UUID, Decimal] = {}
        for item in weight_items:
            if not isinstance(item, dict) or set(item) != {"fill_record_id", "weight"}:
                raise ValueError("Explicit reviewed weight entry is malformed.")
            fill_id = UUID(item["fill_record_id"])
            weight = Decimal(str(item["weight"]))
            if not weight.is_finite() or weight < 0 or fill_id in fill_weights:
                raise ValueError("Explicit reviewed per-fill weights are invalid.")
            fill_weights[fill_id] = weight
    except (TypeError, KeyError, ValueError, json.JSONDecodeError, ArithmeticError) as exc:
        raise ValueError("Canonical snapshot fill manifest or weights are invalid.") from exc
    if (
        not normalized_ids
        or normalized_ids != sorted(normalized_ids)
        or len(set(normalized_ids)) != len(normalized_ids)
        or set(fill_weights) != {UUID(value) for value in normalized_ids}
        or [str(fill_id) for fill_id in fill_weights] != normalized_ids
    ):
        raise ValueError("Canonical snapshot fill manifest and weights do not match in canonical order.")

    rows = allocate_and_persist_component(
        db,
        evidence_id=evidence.id,
        broker_connection_id=broker_connection_id,
        broker_report_reference=broker_report_reference,
        reviewer_user_id=evidence.reviewed_by_user_id,
        source_component_total=Decimal(snapshot.canonical_amount),
        charge_component=snapshot.canonical_component,
        fill_weights=fill_weights,
        allocation_basis=snapshot.allocation_basis,
        canonical_component_id=snapshot.id,
    )
    if any(row.canonical_component_id != snapshot.id for row in rows):
        raise ValueError("Persisted allocations are not bound to the verified canonical snapshot.")
    if sum((Decimal(row.allocated_amount) for row in rows), Decimal("0")) != Decimal(snapshot.canonical_amount):
        raise ValueError("Persisted allocations do not reconcile to the verified canonical source total.")
    return rows
