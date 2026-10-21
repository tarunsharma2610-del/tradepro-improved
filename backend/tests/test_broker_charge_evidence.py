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
