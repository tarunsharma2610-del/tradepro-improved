"""Durable persistence for reviewed per-fill broker charge allocations.

The caller must choose a component-appropriate reviewed allocation basis. This
service verifies evidence review metadata and that every fill belongs to the
same broker connection, then persists deterministic allocations atomically.
A review marker is not cryptographic proof of broker-document authenticity.
"""
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_trade_record import BrokerTradeRecord
from app.services.broker_charge_allocation_service import (
    METHOD_VERSION,
    allocate_component_total,
)
from app.services.broker_charge_evidence_service import require_reviewed_charge_evidence

SUPPORTED_COMPONENTS = frozenset({
    "brokerage", "stt", "exchange_charges", "sebi_charges", "stamp_duty", "gst"
})


def allocate_and_persist_component(
    db: Session,
    *,
    evidence_id: UUID,
    broker_connection_id: UUID,
    broker_report_reference: str,
    reviewer_user_id: UUID,
    source_component_total: Decimal | str | int,
    charge_component: str,
    fill_weights: dict[UUID, Decimal | str | int],
    allocation_basis: str,
) -> list[BrokerChargeAllocation]:
    """Persist one source charge component across a reviewed set of broker fills.

    Replaying the exact same request returns existing PENDING rows. A replay
    that changes the total, basis, method, or per-fill amount fails closed.
    Once rows are RECONCILED, this allocation-writing path refuses replay so it
    cannot be mistaken for source verification; use the source-verification and
    promotion workflow for read/verification replay. The caller owns the
    surrounding transaction and must commit only after the complete operation
    succeeds.
    """
    if charge_component not in SUPPORTED_COMPONENTS:
        raise ValueError("Unsupported broker charge component.")
    if not fill_weights or any(not isinstance(fill_id, UUID) for fill_id in fill_weights):
        raise ValueError("At least one persisted broker trade record ID is required.")

    evidence = require_reviewed_charge_evidence(
        db,
        evidence_id=evidence_id,
        broker_connection_id=broker_connection_id,
        broker_report_reference=broker_report_reference,
        reviewer_user_id=reviewer_user_id,
    )
    # Serialize allocations for the same source evidence on databases that
    # support row-level locks (notably PostgreSQL). Locking only target fills
    # is insufficient: two transactions with disjoint fill sets could both
    # observe an empty component ledger and each insert a different subset.
    locked_evidence = (
        db.query(BrokerChargeEvidence)
        .filter(BrokerChargeEvidence.id == evidence_id)
        .with_for_update()
        .one_or_none()
    )
    if locked_evidence is None:
        raise ValueError("Reviewed broker charge evidence no longer exists.")
    trades = (
        db.query(BrokerTradeRecord)
        .filter(BrokerTradeRecord.id.in_(list(fill_weights)))
        .with_for_update()
        .all()
    )
    trades_by_id = {trade.id: trade for trade in trades}
    if set(trades_by_id) != set(fill_weights):
        raise ValueError("Every allocation target must be a persisted broker trade record.")
    if any(trade.broker_connection_id != broker_connection_id for trade in trades):
        raise ValueError("Every broker trade record must belong to the evidence connection.")

    allocations = allocate_component_total(
        source_component_total,
        {str(fill_id): weight for fill_id, weight in fill_weights.items()},
        allocation_basis=allocation_basis,
    )
    total = Decimal(str(source_component_total)).quantize(Decimal("0.01"))

    # Savepoint keeps partial inserts/updates out if any validation fails.
    with db.begin_nested():
        existing_rows = (
            db.query(BrokerChargeAllocation)
            .filter(
                BrokerChargeAllocation.evidence_id == evidence_id,
                BrokerChargeAllocation.charge_component == charge_component,
            )
            .with_for_update()
            .all()
        )
        existing_by_trade = {row.broker_trade_record_id: row for row in existing_rows}
        expected_ids = set(fill_weights)
        if existing_rows and set(existing_by_trade) != expected_ids:
            raise ValueError("Conflicting replay: the source component has a different fill set.")
        for fill_id, amount in allocations.items():
            trade_id = UUID(fill_id)
            existing = existing_by_trade.get(trade_id)
            if existing is not None:
                if (
                    existing.broker_connection_id != broker_connection_id
                    or Decimal(existing.source_component_total) != total
                    or Decimal(existing.allocated_amount) != amount
                    or existing.allocation_basis != allocation_basis
                    or existing.method_version != METHOD_VERSION
                    or existing.currency != "INR"
                ):
                    raise ValueError("Conflicting replay: existing allocation values differ.")
                continue
            db.add(BrokerChargeAllocation(
                evidence_id=evidence_id,
                broker_connection_id=broker_connection_id,
                broker_trade_record_id=trade_id,
                charge_component=charge_component,
                source_component_total=total,
                allocated_amount=amount,
                currency="INR",
                allocation_basis=allocation_basis,
                method_version=METHOD_VERSION,
                status="PENDING_RECONCILIATION",
            ))
        db.flush()
        rows = (
            db.query(BrokerChargeAllocation)
            .filter(
                BrokerChargeAllocation.evidence_id == evidence_id,
                BrokerChargeAllocation.charge_component == charge_component,
            )
            .with_for_update()
            .all()
        )
        if {row.broker_trade_record_id for row in rows} != expected_ids:
            raise ValueError("Allocation ledger is incomplete for this source component.")
        if any(Decimal(row.source_component_total) != total for row in rows):
            raise ValueError("Source component total differs across allocation rows.")
        if sum((Decimal(row.allocated_amount) for row in rows), Decimal("0")) != total:
            raise ValueError("Allocated amounts do not reconcile to the source component total.")
        # Arithmetic equality only proves that the stored allocations sum
        # to the caller-supplied number. This function does not parse or
        # independently verify the source document's component total, so it
        # must not promote rows to RECONCILED. A separate source-verification
        # workflow must perform that comparison before changing status.
        for row in rows:
            if row.status == "REJECTED":
                raise ValueError("Rejected allocations cannot be reconciled.")
            if row.status == "RECONCILED":
                raise ValueError(
                    "Allocation was already reconciled; source verification must not be bypassed."
                )
            row.status = "PENDING_RECONCILIATION"
            row.reconciliation_reference = None
        db.flush()
    return sorted(rows, key=lambda row: str(row.broker_trade_record_id))
