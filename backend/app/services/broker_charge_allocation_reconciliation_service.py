"""Transactional promotion of a verified broker-charge allocation component.

This service is not exposed as an API endpoint. The caller owns the transaction
and must commit only after the whole enclosing accounting operation succeeds.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.user import User
from app.services.broker_charge_source_reconciliation_service import (
    verify_component_allocation_ledger,
)


def promote_verified_component_allocations(
    db: Session, *, evidence_id: UUID, source_component_id: UUID, reviewer_user_id: UUID
) -> list[BrokerChargeAllocation]:
    """Atomically mark one fully verified allocation set RECONCILED.

    All source, manifest, fill-set, amount, currency, method, basis and sum
    checks are repeated while their rows are locked. The durable reconciliation
    reference is deterministic, so an exact replay is idempotent. This method
    never commits the caller's transaction.
    """
    with db.begin_nested():
        verification = verify_component_allocation_ledger(
            db, evidence_id=evidence_id, source_component_id=source_component_id
        )
        if verification["reviewed_by_user_id"] != str(reviewer_user_id):
            raise ValueError("Only the authorized source-component reviewer may promote this allocation set.")
        reviewer = (
            db.query(User)
            .filter(User.id == reviewer_user_id)
            .with_for_update()
            .populate_existing()
            .one_or_none()
        )
        if reviewer is None or not reviewer.is_active or not reviewer.is_admin:
            raise ValueError("Only an active platform administrator may promote this allocation set.")
        rows = (
            db.query(BrokerChargeAllocation)
            .filter(
                BrokerChargeAllocation.evidence_id == evidence_id,
                BrokerChargeAllocation.charge_component == verification["component_name"],
            )
            .with_for_update()
            .all()
        )
        expected_reference = verification["reconciliation_reference"]
        if verification["status"] == "ALREADY_RECONCILED":
            if not rows or any(row.reconciliation_reference != expected_reference for row in rows):
                raise ValueError("Previously reconciled allocation set does not match its durable reference.")
            return sorted(rows, key=lambda row: str(row.broker_trade_record_id))
        if verification["status"] != "VERIFIED_PENDING_PROMOTION":
            raise ValueError("Source component is not eligible for reconciliation promotion.")
        if not rows or any(row.status != "PENDING_RECONCILIATION" for row in rows):
            raise ValueError("All allocation rows must still be pending for atomic promotion.")
        for row in rows:
            row.status = "RECONCILED"
            row.reconciliation_reference = expected_reference
        db.flush()
        if any(row.status != "RECONCILED" or row.reconciliation_reference != expected_reference for row in rows):
            raise ValueError("Atomic allocation promotion did not persist the complete eligible set.")
        return sorted(rows, key=lambda row: str(row.broker_trade_record_id))
