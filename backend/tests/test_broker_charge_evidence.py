from datetime import date
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_connection import BrokerConnection


def _connection(db, user):
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="test-key",
        api_secret_encrypted="test-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=False,
    )
    db.add(connection)
    db.commit()
    return connection


def _evidence(connection, **overrides):
    values = dict(
        broker_connection_id=connection.id,
        source_kind="CONTRACT_NOTE",
        broker_report_reference="report-2026-10-18-001",
        report_date=date(2026, 10, 18),
        segment="NSE",
        source_filename="redacted-contract-note.pdf",
        source_sha256="a" * 64,
        byte_size=1024,
        parser_version=None,
        status="RECEIVED",
    )
    values.update(overrides)
    return BrokerChargeEvidence(**values)


def test_charge_evidence_metadata_persists_without_claiming_authenticity(db_session, make_user):
    user = make_user()
    connection = _connection(db_session, user)
    row = _evidence(connection)
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)

    assert row.id is not None
    assert row.source_sha256 == "a" * 64
    assert row.status == "RECEIVED"
    assert row.received_at is not None
    assert row.reviewed_at is None


def test_same_document_cannot_be_imported_twice_for_same_connection(db_session, make_user):
    user = make_user()
    connection = _connection(db_session, user)
    db_session.add(_evidence(connection))
    db_session.commit()

    db_session.add(_evidence(connection, broker_report_reference="renamed-report"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.parametrize(
    ("overrides", "constraint"),
    [
        ({"byte_size": 0}, "ck_charge_evidence_byte_size_positive"),
        ({"source_sha256": "short"}, "ck_charge_evidence_sha256_length"),
        ({"status": "AUTHENTICATED"}, "ck_charge_evidence_status"),
    ],
)
def test_invalid_charge_evidence_metadata_is_rejected(db_session, make_user, overrides, constraint):
    user = make_user()
    connection = _connection(db_session, user)
    db_session.add(_evidence(connection, **overrides))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_failed_upload_cleanup_logs_os_error_without_masking_primary_failure(monkeypatch, caplog):
    import logging

    from app.api.v1 import broker_charge_evidence as endpoint

    def fail_delete(**kwargs):
        raise OSError("simulated storage permission failure")

    monkeypatch.setattr(endpoint, "delete_document", fail_delete)

    def rollback_and_cleanup():
        # Mirror the endpoint's exception path: rollback first, best-effort cleanup,
        # then propagate the original commit error even when deletion fails.
        primary = RuntimeError("database commit failed")
        with caplog.at_level(logging.ERROR, logger=endpoint.__name__):
            endpoint._cleanup_failed_upload("a" * 32)
        raise primary

    with pytest.raises(RuntimeError, match="database commit failed"):
        rollback_and_cleanup()

    assert "Failed to clean up contract-note upload" in caplog.text
    assert "simulated storage permission failure" in caplog.text


@pytest.mark.anyio
async def test_upload_endpoint_preserves_commit_error_and_storage_audit_finds_orphan(
    tmp_path, db_session, make_user, monkeypatch, caplog
):
    """Exercise the endpoint's real storage/DB failure path, not just its helper."""
    import logging
    from io import BytesIO
    from starlette.datastructures import UploadFile

    from app.api.v1 import broker_charge_evidence as endpoint
    from app.core.config import settings
    from app.services.broker_charge_document_storage_service import audit_contract_note_storage

    user = make_user()
    connection = _connection(db_session, user)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))
    original_commit = db_session.commit

    def fail_evidence_commit():
        raise RuntimeError("simulated database commit failure")

    # Let the endpoint query the existing connection, then force its evidence
    # commit to fail after bytes have been durably written.
    monkeypatch.setattr(db_session, "commit", fail_evidence_commit)

    def fail_delete(**kwargs):
        raise OSError("simulated storage permission failure")

    monkeypatch.setattr(endpoint, "delete_document", fail_delete)
    upload = UploadFile(filename="note.pdf", file=BytesIO(b"contract-note-payload"))

    with caplog.at_level(logging.ERROR, logger=endpoint.__name__):
        with pytest.raises(RuntimeError, match="simulated database commit failure"):
            await endpoint.upload_contract_note(
                broker_connection_id=connection.id,
                file=upload,
                broker_report_reference="report-integration-001",
                report_date=None,
                segment="NSE",
                db=db_session,
                user=user,
            )

    assert "Failed to clean up contract-note upload" in caplog.text
    assert "simulated storage permission failure" in caplog.text
    # The failed evidence transaction must not leave a database row.
    monkeypatch.setattr(db_session, "commit", original_commit)
    assert db_session.query(BrokerChargeEvidence).filter_by(
        broker_report_reference="report-integration-001"
    ).count() == 0

    # The deliberately failed compensation leaves a file with no evidence row;
    # the read-only audit must report it and must not delete it.
    audit = audit_contract_note_storage(db=db_session, root=tmp_path)
    assert len(audit["unreferenced_files"]) == 1
    orphan_key = audit["unreferenced_files"][0]["storage_key"]
    assert (tmp_path / orphan_key).read_bytes() == b"contract-note-payload"
