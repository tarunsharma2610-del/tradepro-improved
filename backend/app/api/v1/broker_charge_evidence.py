"""Authenticated contract-note intake and source-component review endpoints."""
from datetime import date, datetime, timezone
import hashlib
import json
import logging
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.broker_connection import BrokerConnection
from app.models.user import User
from app.services.broker_charge_document_storage_service import (
    delete_document,
    read_verified_document,
    store_document,
)

router = APIRouter(prefix="/broker-charge-evidence", tags=["broker charge evidence"])
logger = logging.getLogger(__name__)
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
SUPPORTED_COMPONENTS = {"brokerage", "stt", "exchange_charges", "sebi_charges", "stamp_duty", "gst"}


class SourceComponentInput(BaseModel):
    component_name: str
    source_amount: Decimal = Field(ge=Decimal("0"), max_digits=16, decimal_places=2)
    currency: str = "INR"
    source_locator: str = Field(min_length=1, max_length=200)


class SourceComponentReviewInput(BaseModel):
    confirm_source_matches: bool
    eligible_fill_record_ids: list[UUID] = Field(min_length=1, max_length=500)
    rounding_policy: Literal["largest-remainder-v1"] = "largest-remainder-v1"
    allocation_basis: Literal["QUANTITY", "NOTIONAL", "EXPLICIT_REVIEWED"] = "EXPLICIT_REVIEWED"
    review_note: str | None = Field(default=None, max_length=500)


class SourceComponentRejectInput(BaseModel):
    confirm_source_matches: bool
    review_note: str | None = Field(default=None, max_length=500)


def _safe_filename(filename: str | None) -> str:
    name = Path(filename or "").name
    name = "".join(ch for ch in name if ch.isprintable() and ch not in {'"', "\\", "/"})
    name = name.strip().strip(".")
    if not name or len(name) > 255:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A valid source filename is required.")
    return name


def _owned_evidence(
    db: Session, *, evidence_id: UUID, user_id: UUID, lock: bool = False, allow_admin_review: bool = False
):
    query = db.query(BrokerChargeEvidence).join(
        BrokerConnection, BrokerConnection.id == BrokerChargeEvidence.broker_connection_id
    ).filter(BrokerChargeEvidence.id == evidence_id)
    # Only the existing platform-admin role can review another user's evidence.
    # Ordinary upload/download/transcription operations remain owner-scoped.
    if not allow_admin_review:
        query = query.filter(BrokerConnection.user_id == user_id)
    if lock:
        query = query.with_for_update()
    evidence = query.populate_existing().first()
    if evidence is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contract-note evidence not found.")
    return evidence


def _cleanup_failed_upload(storage_key: str) -> None:
    """Best-effort compensation; preserve the original DB error if cleanup fails.

    A failed cleanup can leave an orphaned file, which the read-only storage audit
    can report. Never hide the primary failure or silently claim cleanup succeeded.
    """
    try:
        delete_document(root=settings.BROKER_CHARGE_DOCUMENT_ROOT, storage_key=storage_key)
    except OSError:
        logger.exception("Failed to clean up contract-note upload; storage audit required")


def _verified_bytes(evidence: BrokerChargeEvidence) -> bytes:
    if not evidence.storage_key:
        raise HTTPException(status.HTTP_409_CONFLICT, "Original contract-note document is not available.")
    try:
        return read_verified_document(
            root=settings.BROKER_CHARGE_DOCUMENT_ROOT,
            storage_key=evidence.storage_key,
            expected_sha256=evidence.source_sha256,
            expected_size=evidence.byte_size,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/connections/{broker_connection_id}/contract-notes", status_code=status.HTTP_201_CREATED)
async def upload_contract_note(
    broker_connection_id: UUID,
    file: UploadFile = File(...),
    broker_report_reference: str = Form(..., min_length=1, max_length=200),
    report_date: date | None = Form(default=None),
    segment: str | None = Form(default=None, max_length=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Store a source document as RECEIVED; upload does not mark it reviewed."""
    connection = (
        db.query(BrokerConnection)
        .filter(BrokerConnection.id == broker_connection_id, BrokerConnection.user_id == user.id)
        .first()
    )
    if connection is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Broker connection not found.")
    filename = _safe_filename(file.filename)
    reference = broker_report_reference.strip()
    if not reference:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A contract-note reference is required.")
    content = await file.read(MAX_DOCUMENT_BYTES + 1)
    if not content:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Contract-note document must not be empty.")
    if len(content) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Contract-note document exceeds 10 MiB.")
    evidence_id = uuid4()
    storage_key = evidence_id.hex
    try:
        digest, byte_size = store_document(
            content, root=settings.BROKER_CHARGE_DOCUMENT_ROOT, storage_key=storage_key
        )
    except (OSError, ValueError) as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Contract-note storage is unavailable.") from exc
    evidence = BrokerChargeEvidence(
        id=evidence_id,
        broker_connection_id=connection.id,
        source_kind="CONTRACT_NOTE",
        broker_report_reference=reference,
        report_date=report_date,
        segment=segment.strip() if segment else None,
        source_filename=filename,
        storage_key=storage_key,
        source_sha256=digest,
        byte_size=byte_size,
        received_by_user_id=user.id,
        status="RECEIVED",
    )
    try:
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
    except IntegrityError as exc:
        db.rollback()
        _cleanup_failed_upload(storage_key)
        raise HTTPException(status.HTTP_409_CONFLICT, "This contract-note evidence conflicts with an existing record.") from exc
    except Exception:
        db.rollback()
        _cleanup_failed_upload(storage_key)
        raise
    return {
        "id": str(evidence.id),
        "broker_connection_id": str(evidence.broker_connection_id),
        "broker_report_reference": evidence.broker_report_reference,
        "source_filename": evidence.source_filename,
        "source_sha256": evidence.source_sha256,
        "byte_size": evidence.byte_size,
        "status": evidence.status,
        "received_at": evidence.received_at,
    }


@router.get("/{evidence_id}/document")
def download_contract_note(
    evidence_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    evidence = _owned_evidence(db, evidence_id=evidence_id, user_id=user.id)
    content = _verified_bytes(evidence)
    disposition_name = quote(evidence.source_filename, safe="")
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{disposition_name}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        },
    )


@router.post("/{evidence_id}/components", status_code=status.HTTP_201_CREATED)
def record_source_component(
    evidence_id: UUID,
    payload: SourceComponentInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Record a human-transcribed amount as pending; never treat input as verified."""
    if payload.component_name not in SUPPORTED_COMPONENTS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unsupported charge component.")
    if payload.currency != "INR":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Only INR source components are supported.")
    if not payload.source_locator.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A source page/row locator is required.")
    evidence = _owned_evidence(db, evidence_id=evidence_id, user_id=user.id, lock=True)
    if evidence.status == "REJECTED":
        raise HTTPException(status.HTTP_409_CONFLICT, "Rejected contract-note evidence cannot accept new components; upload a new evidence revision.")
    _verified_bytes(evidence)
    prior_components = (
        db.query(BrokerChargeSourceComponent)
        .filter(
            BrokerChargeSourceComponent.evidence_id == evidence.id,
            BrokerChargeSourceComponent.component_name == payload.component_name,
        )
        .with_for_update()
        .all()
    )
    if any(row.status != "REJECTED" for row in prior_components):
        raise HTTPException(status.HTTP_409_CONFLICT, "A pending or verified record already exists for this component.")
    revision = max((row.revision for row in prior_components), default=0) + 1
    component = BrokerChargeSourceComponent(
        evidence_id=evidence.id,
        source_sha256=evidence.source_sha256,
        component_name=payload.component_name,
        revision=revision,
        source_amount=payload.source_amount,
        currency="INR",
        extraction_method="MANUAL_TRANSCRIPTION",
        parser_version="manual-transcription-v1",
        source_locator=payload.source_locator.strip(),
        extracted_by_user_id=user.id,
        status="PENDING_REVIEW",
    )
    try:
        db.add(component)
        db.commit()
        db.refresh(component)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A source record for this component already exists; use the review workflow.") from exc
    return {
        "id": str(component.id),
        "evidence_id": str(component.evidence_id),
        "source_sha256": component.source_sha256,
        "component_name": component.component_name,
        "revision": component.revision,
        "source_amount": str(component.source_amount),
        "currency": component.currency,
        "extraction_method": component.extraction_method,
        "parser_version": component.parser_version,
        "source_locator": component.source_locator,
        "extracted_by_user_id": str(component.extracted_by_user_id),
        "status": component.status,
    }


@router.post("/{evidence_id}/components/{component_id}/review")
def review_source_component(
    evidence_id: UUID,
    component_id: UUID,
    payload: SourceComponentReviewInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Second-person review against the original document, with integrity recheck."""
    if payload.confirm_source_matches is not True:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Explicit source-match confirmation is required.")
    evidence = _owned_evidence(
        db, evidence_id=evidence_id, user_id=user.id, lock=True, allow_admin_review=user.is_admin
    )
    if evidence.status == "REJECTED":
        raise HTTPException(status.HTTP_409_CONFLICT, "Rejected contract-note evidence cannot be verified.")
    if evidence.status == "REVIEWED" and evidence.reviewed_by_user_id != user.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "All components on this evidence must use the same authorized reviewer.")
    _verified_bytes(evidence)
    component = (
        db.query(BrokerChargeSourceComponent)
        .filter(
            BrokerChargeSourceComponent.id == component_id,
            BrokerChargeSourceComponent.evidence_id == evidence.id,
        )
        .with_for_update()
        .populate_existing()
        .first()
    )
    if component is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source component not found.")
    if component.status != "PENDING_REVIEW":
        raise HTTPException(status.HTTP_409_CONFLICT, "Only pending source components can be reviewed.")
    if component.source_sha256 != evidence.source_sha256:
        raise HTTPException(status.HTTP_409_CONFLICT, "Source component fingerprint no longer matches evidence.")
    if component.extracted_by_user_id == user.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "A different user must independently review this source component.")
    if len(set(payload.eligible_fill_record_ids)) != len(payload.eligible_fill_record_ids):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Eligible fill IDs must not contain duplicates.")
    fill_ids = sorted(payload.eligible_fill_record_ids, key=str)
    trades = (
        db.query(BrokerTradeRecord)
        .filter(BrokerTradeRecord.id.in_(fill_ids))
        .with_for_update()
        .all()
    )
    if {trade.id for trade in trades} != set(fill_ids):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Every eligible fill must be a persisted broker trade record.")
    if any(trade.broker_connection_id != evidence.broker_connection_id for trade in trades):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Eligible fills must belong to the evidence broker connection.")
    canonical_fill_ids = json.dumps([str(fill_id) for fill_id in fill_ids], separators=(",", ":"))
    fill_set_sha256 = hashlib.sha256(canonical_fill_ids.encode("utf-8")).hexdigest()
    component.eligible_fill_ids_json = canonical_fill_ids
    component.eligible_fill_set_sha256 = fill_set_sha256
    component.rounding_policy = payload.rounding_policy
    component.allocation_basis = payload.allocation_basis
    component.status = "VERIFIED"
    component.reviewed_by_user_id = user.id
    component.reviewed_at = datetime.now(timezone.utc)
    component.review_note = payload.review_note.strip() if payload.review_note else None
    evidence.status = "REVIEWED"
    evidence.reviewed_by_user_id = user.id
    evidence.reviewed_at = component.reviewed_at
    evidence.review_note = "Source component and eligible fill set independently reviewed."
    db.commit()
    db.refresh(component)
    return {
        "id": str(component.id),
        "evidence_id": str(component.evidence_id),
        "component_name": component.component_name,
        "source_amount": str(component.source_amount),
        "currency": component.currency,
        "status": component.status,
        "eligible_fill_record_ids": json.loads(component.eligible_fill_ids_json or "[]"),
        "eligible_fill_set_sha256": component.eligible_fill_set_sha256,
        "rounding_policy": component.rounding_policy,
        "allocation_basis": component.allocation_basis,
        "reviewed_by_user_id": str(component.reviewed_by_user_id),
        "reviewed_at": component.reviewed_at,
    }


@router.post("/{evidence_id}/components/{component_id}/reject")
def reject_source_component(
    evidence_id: UUID,
    component_id: UUID,
    payload: SourceComponentRejectInput,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Record a reviewer rejection without changing any allocation status."""
    if payload.confirm_source_matches is not False:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Explicit mismatch confirmation is required.")
    evidence = _owned_evidence(
        db, evidence_id=evidence_id, user_id=user.id, lock=True, allow_admin_review=user.is_admin
    )
    if evidence.status == "REJECTED":
        raise HTTPException(status.HTTP_409_CONFLICT, "Rejected contract-note evidence is terminal; upload a new evidence revision.")
    if evidence.status == "REVIEWED" and evidence.reviewed_by_user_id != user.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "All components on this evidence must use the same authorized reviewer.")
    _verified_bytes(evidence)
    component = (
        db.query(BrokerChargeSourceComponent)
        .filter(
            BrokerChargeSourceComponent.id == component_id,
            BrokerChargeSourceComponent.evidence_id == evidence.id,
        )
        .with_for_update()
        .populate_existing()
        .first()
    )
    if component is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source component not found.")
    if component.status != "PENDING_REVIEW":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending source components can be rejected.")
    if component.extracted_by_user_id == user.id:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="A different user must independently review this source component.")
    if payload.review_note is not None and not payload.review_note.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Review note must not be whitespace.")
    component.status = "REJECTED"
    component.reviewed_by_user_id = user.id
    component.reviewed_at = datetime.now(timezone.utc)
    component.review_note = payload.review_note.strip() if payload.review_note else "Source amount did not match."
    # A rejected component makes the evidence unusable for verification until a
    # future explicit revision/re-upload workflow exists. Keep document-level
    # status and reviewer provenance consistent with that terminal decision.
    evidence.status = "REJECTED"
    evidence.reviewed_by_user_id = user.id
    evidence.reviewed_at = component.reviewed_at
    evidence.review_note = component.review_note
    db.commit()
    db.refresh(component)
    return {
        "id": str(component.id),
        "evidence_id": str(component.evidence_id),
        "status": component.status,
        "reviewed_by_user_id": str(component.reviewed_by_user_id),
        "reviewed_at": component.reviewed_at,
    }

