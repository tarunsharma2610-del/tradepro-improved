"""Authenticated upload and integrity-checked retrieval of contract-note source documents."""
from datetime import date
from pathlib import Path
from urllib.parse import quote
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_connection import BrokerConnection
from app.models.user import User
from app.services.broker_charge_document_storage_service import (
    delete_document,
    read_verified_document,
    store_document,
)

router = APIRouter(prefix="/broker-charge-evidence", tags=["broker charge evidence"])
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024


def _safe_filename(filename: str | None) -> str:
    # Never use the submitted filename as a path or storage key.
    name = Path(filename or "").name
    name = "".join(ch for ch in name if ch.isprintable() and ch not in {'"', "\\", "/"})
    name = name.strip().strip(".")
    if not name or len(name) > 255:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A valid source filename is required.")
    return name


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
        status="RECEIVED",
    )
    try:
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
    except IntegrityError as exc:
        db.rollback()
        delete_document(root=settings.BROKER_CHARGE_DOCUMENT_ROOT, storage_key=storage_key)
        raise HTTPException(status.HTTP_409_CONFLICT, "This contract-note evidence conflicts with an existing record.") from exc
    except Exception:
        db.rollback()
        delete_document(root=settings.BROKER_CHARGE_DOCUMENT_ROOT, storage_key=storage_key)
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
    """Return original bytes only to the owner and only after hash/size verification."""
    evidence = (
        db.query(BrokerChargeEvidence)
        .join(BrokerConnection, BrokerConnection.id == BrokerChargeEvidence.broker_connection_id)
        .filter(BrokerChargeEvidence.id == evidence_id, BrokerConnection.user_id == user.id)
        .first()
    )
    if evidence is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contract-note evidence not found.")
    if not evidence.storage_key:
        raise HTTPException(status.HTTP_410_GONE, "The original contract-note document is not available.")
    try:
        content = read_verified_document(
            root=settings.BROKER_CHARGE_DOCUMENT_ROOT,
            storage_key=evidence.storage_key,
            expected_sha256=evidence.source_sha256,
            expected_size=evidence.byte_size,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
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
