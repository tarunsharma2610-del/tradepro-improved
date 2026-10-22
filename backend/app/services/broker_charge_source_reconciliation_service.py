"""Fail-closed verification of pending charge allocations against reviewed source evidence."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.broker_trade_record import BrokerTradeRecord
from app.services.broker_charge_allocation_service import METHOD_VERSION
from app.services.broker_charge_document_storage_service import read_verified_document

PAISE = Decimal("0.01")


def verify_component_allocation_ledger(
    db: Session, *, evidence_id: UUID, source_component_id: UUID
) -> dict[str, object]:
    """Verify the complete pending ledger against a reviewed source component.

    This function is intentionally read-only: it never changes allocation
    status. The source component review must include a durable exact fill-set
    manifest and approved rounding/method version. Callers must execute it in
    the same transaction as any later promotion and recheck/lock rows there.
    """
    evidence = (
        db.query(BrokerChargeEvidence)
        .filter(BrokerChargeEvidence.id == evidence_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if evidence is None or evidence.source_kind != "CONTRACT_NOTE":
        raise ValueError("Contract-note evidence was not found.")
    if evidence.status != "REVIEWED" or evidence.reviewed_by_user_id is None or evidence.reviewed_at is None:
        raise ValueError("Contract-note evidence must be reviewed before allocation verification.")
    if not evidence.storage_key:
        raise ValueError("Original contract-note document is unavailable.")
    try:
        read_verified_document(
            root=settings.BROKER_CHARGE_DOCUMENT_ROOT,
            storage_key=evidence.storage_key,
            expected_sha256=evidence.source_sha256,
            expected_size=evidence.byte_size,
        )
    except ValueError as exc:
        raise ValueError("Contract-note source integrity check failed.") from exc

    component = (
        db.query(BrokerChargeSourceComponent)
        .filter(
            BrokerChargeSourceComponent.id == source_component_id,
            BrokerChargeSourceComponent.evidence_id == evidence_id,
        )
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if component is None or component.status != "VERIFIED":
        raise ValueError("A verified source component is required before allocation verification.")
    if component.source_sha256 != evidence.source_sha256:
        raise ValueError("Source component fingerprint does not match the reviewed contract note.")
    if (
        component.reviewed_by_user_id is None
        or component.reviewed_at is None
        or component.reviewed_by_user_id == component.extracted_by_user_id
    ):
        raise ValueError("Source component lacks independent review provenance.")
    if component.reviewed_by_user_id != evidence.reviewed_by_user_id:
        raise ValueError("Evidence and component review provenance do not match.")
    if component.currency != "INR" or not component.eligible_fill_ids_json:
        raise ValueError("A reviewed INR source component and exact eligible-fill manifest are required.")
    if component.rounding_policy != METHOD_VERSION:
        raise ValueError("Source component rounding policy does not match the supported allocation method.")
    if component.allocation_basis not in {"QUANTITY", "NOTIONAL", "EXPLICIT_REVIEWED"}:
        raise ValueError("A reviewer-approved allocation basis is required.")

    try:
        manifest_ids = json.loads(component.eligible_fill_ids_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Eligible-fill manifest is invalid.") from exc
    if not isinstance(manifest_ids, list) or not manifest_ids or any(not isinstance(value, str) for value in manifest_ids):
        raise ValueError("Eligible-fill manifest must be a non-empty list of fill UUIDs.")
    try:
        parsed_ids = [UUID(value) for value in manifest_ids]
    except ValueError as exc:
        raise ValueError("Eligible-fill manifest contains an invalid UUID.") from exc
    if len(set(parsed_ids)) != len(parsed_ids):
        raise ValueError("Eligible-fill manifest contains duplicate fill IDs.")
    canonical_json = json.dumps([str(value) for value in sorted(parsed_ids, key=str)], separators=(",", ":"))
    if manifest_ids != [str(value) for value in sorted(parsed_ids, key=str)]:
        raise ValueError("Eligible-fill manifest is not in canonical sorted order.")
    manifest_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    if manifest_hash != component.eligible_fill_set_sha256:
        raise ValueError("Eligible-fill manifest fingerprint does not match.")

    allocations = (
        db.query(BrokerChargeAllocation)
        .filter(
            BrokerChargeAllocation.evidence_id == evidence_id,
            BrokerChargeAllocation.charge_component == component.component_name,
        )
        .with_for_update()
        .all()
    )
    if not allocations:
        raise ValueError("No allocation rows exist for this source component.")
    allocation_ids = {row.broker_trade_record_id for row in allocations}
    if allocation_ids != set(parsed_ids):
        raise ValueError("Allocation ledger fill set does not exactly match the reviewed eligible-fill manifest.")
    if any(row.broker_connection_id != evidence.broker_connection_id for row in allocations):
        raise ValueError("Allocation ledger contains a fill from another broker connection.")

    expected_total = Decimal(component.source_amount).quantize(PAISE)
    if any(Decimal(row.source_component_total).quantize(PAISE) != expected_total for row in allocations):
        raise ValueError("Allocation source total does not match the independently reviewed source component.")
    if any(row.currency != component.currency for row in allocations):
        raise ValueError("Allocation currency does not match the reviewed source component.")
    if any(row.method_version != component.rounding_policy for row in allocations):
        raise ValueError("Allocation method version does not match the reviewed rounding policy.")
    if any(row.allocation_basis != component.allocation_basis for row in allocations):
        raise ValueError("Allocation basis does not match the reviewer-approved allocation basis.")
    if any(not row.allocation_basis for row in allocations):
        raise ValueError("Allocation basis is missing.")
    reconciliation_reference = (
        f"charge-component:{component.id}:sha256:{evidence.source_sha256}:fills:{manifest_hash}"
    )
    statuses = {row.status for row in allocations}
    if statuses == {"PENDING_RECONCILIATION"}:
        if any(row.reconciliation_reference is not None for row in allocations):
            raise ValueError("Pending allocations must not carry a stale reconciliation reference.")
        verification_status = "VERIFIED_PENDING_PROMOTION"
    elif statuses == {"RECONCILED"}:
        if any(row.reconciliation_reference != reconciliation_reference for row in allocations):
            raise ValueError("Reconciled allocation reference does not match the verified source and fill set.")
        verification_status = "ALREADY_RECONCILED"
    else:
        raise ValueError("Allocation rows have mixed or rejected statuses; component verification fails closed.")
    allocated_total = sum((Decimal(row.allocated_amount) for row in allocations), Decimal("0")).quantize(PAISE)
    if allocated_total != expected_total:
        raise ValueError("Allocated amounts do not reconcile exactly to the reviewed source component total.")

    trades = (
        db.query(BrokerTradeRecord)
        .filter(BrokerTradeRecord.id.in_(list(parsed_ids)))
        .with_for_update()
        .all()
    )
    if {trade.id for trade in trades} != set(parsed_ids):
        raise ValueError("Reviewed eligible-fill manifest references missing trade records.")
    if any(trade.broker_connection_id != evidence.broker_connection_id for trade in trades):
        raise ValueError("Reviewed eligible-fill manifest contains a trade from another broker connection.")

    return {
        "evidence_id": str(evidence.id),
        "source_component_id": str(component.id),
        "component_name": component.component_name,
        "source_sha256": evidence.source_sha256,
        "source_amount": str(expected_total),
        "currency": component.currency,
        "eligible_fill_set_sha256": manifest_hash,
        "rounding_policy": component.rounding_policy,
        "allocation_basis": component.allocation_basis,
        "reviewed_by_user_id": str(component.reviewed_by_user_id),
        "reconciliation_reference": reconciliation_reference,
        "allocation_count": len(allocations),
        "allocated_total": str(allocated_total),
        "status": verification_status,
    }
