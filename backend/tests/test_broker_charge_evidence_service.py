from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_connection import BrokerConnection
from app.services.broker_charge_evidence_service import require_reviewed_charge_evidence


@pytest.fixture()
def reviewed_evidence(db_session, make_user):
    user = make_user()
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=True,
    )
    db_session.add(connection)
    db_session.flush()
    evidence = BrokerChargeEvidence(
        broker_connection_id=connection.id,
        source_kind="CONTRACT_NOTE",
        broker_report_reference="CN-2026-10-21-001",
        report_date=date(2026, 10, 21),
        segment="NSE",
        source_filename="contract-note.pdf",
        source_sha256="a" * 64,
        byte_size=1024,
        parser_version="phase3-test",
        status="REVIEWED",
        reviewed_at=datetime.now(timezone.utc),
        reviewed_by_user_id=user.id,
    )
    db_session.add(evidence)
    db_session.commit()
    return db_session, user, connection, evidence


def test_requires_matching_reviewed_evidence(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    result = require_reviewed_charge_evidence(
        db,
        evidence_id=evidence.id,
        broker_connection_id=connection.id,
        broker_report_reference="CN-2026-10-21-001",
        reviewer_user_id=user.id,
    )
    assert result.id == evidence.id


@pytest.mark.parametrize("status", ["RECEIVED", "REJECTED"])
def test_blocks_unreviewed_or_rejected_evidence(reviewed_evidence, status):
    db, user, connection, evidence = reviewed_evidence
    evidence.status = status
    db.commit()
    with pytest.raises(ValueError, match="must be reviewed"):
        require_reviewed_charge_evidence(
            db,
            evidence_id=evidence.id,
            broker_connection_id=connection.id,
            broker_report_reference="CN-2026-10-21-001",
            reviewer_user_id=user.id,
        )


def test_blocks_evidence_from_another_connection(reviewed_evidence):
    db, user, _connection, evidence = reviewed_evidence
    with pytest.raises(ValueError, match="not found for this connection"):
        require_reviewed_charge_evidence(
            db,
            evidence_id=evidence.id,
            broker_connection_id=uuid4(),
            broker_report_reference="CN-2026-10-21-001",
            reviewer_user_id=user.id,
        )


def test_blocks_reference_mismatch(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    with pytest.raises(ValueError, match="reference does not match"):
        require_reviewed_charge_evidence(
            db,
            evidence_id=evidence.id,
            broker_connection_id=connection.id,
            broker_report_reference="CN-WRONG",
            reviewer_user_id=user.id,
        )


def test_blocks_review_without_actor_or_timestamp(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    evidence.reviewed_by_user_id = None
    evidence.reviewed_at = None
    db.commit()
    with pytest.raises(ValueError, match="reviewer and review timestamp"):
        require_reviewed_charge_evidence(
            db,
            evidence_id=evidence.id,
            broker_connection_id=connection.id,
            broker_report_reference="CN-2026-10-21-001",
            reviewer_user_id=user.id,
        )
