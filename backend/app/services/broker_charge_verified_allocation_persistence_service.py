"""Persist canonical allocations only after reviewed source rows form the approved set.

This first persistence adapter deliberately requires the existing six-row live
accounting component set. Split transaction/IPFT evidence can be planned by the
canonical planner, but remains non-persistable until a durable canonical-source
ledger can link multiple source rows to one canonical component.
"""
from __future__ import annotations

import json
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.services.broker_charge_allocation_persistence_service import allocate_and_persist_component
from app.services.broker_charge_canonical_allocation_plan import (
    build_verified_component_allocation_plan,
)
from app.services.broker_charge_component_set_contract import (
    LIVE_FILL_COMPONENT_SET_VERSION,
    validate_live_fill_component_set,
)


def allocate_and_persist_verified_canonical_component(
    db: Session,
    *,
    evidence_id: UUID,
    broker_connection_id: UUID,
    broker_report_reference: str,
    reviewer_user_id: UUID,
    canonical_component: str,
) -> list[object]:
    """Build and persist one direct-mapped canonical component allocation.

    The caller owns the outer transaction. This service takes evidence/source
    row locks, checks the approved six-component version and independent review,
    then delegates to the existing evidence-locked idempotent persistence
    service. It never marks allocations RECONCILED or commits.
    """
    evidence = (
        db.query(BrokerChargeEvidence)
        .filter(
            BrokerChargeEvidence.id == evidence_id,
            BrokerChargeEvidence.broker_connection_id == broker_connection_id,
            BrokerChargeEvidence.broker_report_reference == broker_report_reference,
            BrokerChargeEvidence.status == "REVIEWED",
            BrokerChargeEvidence.reviewed_by_user_id == reviewer_user_id,
        )
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if evidence is None:
        raise ValueError("Matching reviewed contract-note evidence is required.")
    records = (
        db.query(BrokerChargeSourceComponent)
        .filter(BrokerChargeSourceComponent.evidence_id == evidence_id)
        .order_by(BrokerChargeSourceComponent.component_name, BrokerChargeSourceComponent.revision)
        .with_for_update()
        .populate_existing()
        .all()
    )
    if not records:
        raise ValueError("Reviewed source components are required before allocation persistence.")
    if any(
        row.status != "VERIFIED"
        or row.reviewed_by_user_id != reviewer_user_id
        or row.reviewed_by_user_id is None
        or row.reviewed_by_user_id == row.extracted_by_user_id
        or row.reviewed_at is None
        or row.source_sha256 != evidence.source_sha256
        for row in records
    ):
        raise ValueError("Every source component must be independently verified against this reviewed evidence.")
    validate_live_fill_component_set(
        component_names=[row.component_name for row in records],
        component_set_versions=[row.component_set_version for row in records],
        component_statuses=[row.status for row in records],
    )
    plan = build_verified_component_allocation_plan(
        records,
        evidence_id=evidence_id,
        source_sha256=evidence.source_sha256,
        canonical_component=canonical_component,
    )
    source_names = {
        item["component_name"] for item in plan["source_record_provenance"]
    }
    if source_names != {canonical_component}:
        raise ValueError(
            "Persistence currently requires one direct source row per canonical component; "
            "split transaction/IPFT needs the canonical-source ledger migration first."
        )
    source = next(row for row in records if row.component_name == canonical_component)
    if Decimal(str(source.source_amount)).quantize(Decimal("0.01")) != Decimal(plan["canonical_source_total"]):
        raise ValueError("Direct source amount does not match the canonical allocation plan.")
    try:
        weight_items = json.loads(source.eligible_fill_weights_json or "")
        fill_weights = {
            UUID(item["fill_record_id"]): Decimal(str(item["weight"]))
            for item in weight_items
        }
    except (TypeError, KeyError, ValueError, json.JSONDecodeError, ArithmeticError) as exc:
        raise ValueError("Explicit reviewed per-fill weights are invalid.") from exc
    if {str(fill_id) for fill_id in fill_weights} != set(plan["eligible_fill_ids"]):
        raise ValueError("Reviewed per-fill weights do not match the canonical allocation plan.")

    rows = allocate_and_persist_component(
        db,
        evidence_id=evidence_id,
        broker_connection_id=broker_connection_id,
        broker_report_reference=broker_report_reference,
        reviewer_user_id=reviewer_user_id,
        source_component_total=Decimal(plan["canonical_source_total"]),
        charge_component=canonical_component,
        fill_weights=fill_weights,
        allocation_basis="EXPLICIT_REVIEWED",
    )
    if {str(row.broker_trade_record_id) for row in rows} != set(plan["eligible_fill_ids"]):
        raise ValueError("Persisted allocation fill set differs from the verified canonical plan.")
    if sum((Decimal(row.allocated_amount) for row in rows), Decimal("0")) != Decimal(plan["canonical_source_total"]):
        raise ValueError("Persisted allocation amounts do not reconcile to the canonical plan.")
    return rows
