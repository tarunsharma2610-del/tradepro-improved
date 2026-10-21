"""Fail-closed validation for reviewed broker charge evidence.

This is a reusable boundary for the Phase 3 accounting integration. A review
status is a human workflow decision, not proof of broker authenticity; callers
must still preserve and inspect the source document before approving it.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.broker_charge_evidence import BrokerChargeEvidence


def require_reviewed_charge_evidence(
    db: Session,
    *,
    evidence_id: UUID,
    broker_connection_id: UUID,
    broker_report_reference: str,
    reviewer_user_id: UUID,
) -> BrokerChargeEvidence:
    """Return matching reviewed evidence or fail closed.

    Evidence must belong to the same broker connection, be a contract note,
    match the exact normalized report reference, and have an explicit review
    actor and timestamp. This validates workflow/provenance linkage only; it
    does not cryptographically authenticate a broker document.
    """
    if not isinstance(broker_report_reference, str) or not broker_report_reference.strip():
        raise ValueError("A non-empty broker contract-note reference is required.")
    if not isinstance(evidence_id, UUID) or not isinstance(broker_connection_id, UUID):
        raise ValueError("A persisted broker charge evidence ID and connection ID are required.")
    if not isinstance(reviewer_user_id, UUID):
        raise ValueError("A reviewer identity is required for charge evidence validation.")

    evidence = (
        db.query(BrokerChargeEvidence)
        .filter(
            BrokerChargeEvidence.id == evidence_id,
            BrokerChargeEvidence.broker_connection_id == broker_connection_id,
        )
        .with_for_update()
        .populate_existing()
        .first()
    )
    if evidence is None:
        raise ValueError("Reviewed broker charge evidence was not found for this connection.")
    if evidence.source_kind != "CONTRACT_NOTE":
        raise ValueError("Live-fill charge evidence must originate from a contract note.")
    if evidence.status != "REVIEWED":
        raise ValueError("Broker charge evidence must be reviewed before accounting promotion.")
    if evidence.reviewed_by_user_id != reviewer_user_id or evidence.reviewed_at is None:
        raise ValueError("Reviewed charge evidence must include the matching reviewer and review timestamp.")
    expected_reference = broker_report_reference.strip()
    if not evidence.broker_report_reference or evidence.broker_report_reference.strip() != expected_reference:
        raise ValueError("Broker charge evidence reference does not match the requested contract note.")
    return evidence
