import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.config import settings
from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.broker_connection import BrokerConnection
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.user import User
from app.services.broker_charge_allocation_persistence_service import allocate_and_persist_component
from app.services.broker_charge_document_storage_service import store_document
from app.services.broker_charge_source_reconciliation_service import verify_component_allocation_ledger


def _trade(db, connection_id, trade_id):
    trade = BrokerTradeRecord(
        broker_connection_id=connection_id,
        broker_order_ref_id=uuid4(),
        broker_trade_id=trade_id,
        quantity=1,
        price=Decimal("100.0000"),
        side="BUY",
        instrument_token="NSE_EQ|TEST",
        exchange_timestamp="2026-10-22T10:00:00+05:30",
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade


@pytest.fixture
def reconciliation_context(db_session, make_user, monkeypatch, tmp_path):
    db = db_session
    user = make_user()
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=True,
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)

    original = b"test contract note"
    evidence = BrokerChargeEvidence(
        broker_connection_id=connection.id,
        source_kind="CONTRACT_NOTE",
        broker_report_reference="CN-2026-10-21-001",
        source_filename="contract-note.pdf",
        source_sha256=hashlib.sha256(original).hexdigest(),
        byte_size=len(original),
        received_by_user_id=user.id,
        status="REVIEWED",
        reviewed_at=datetime.now(timezone.utc),
        reviewed_by_user_id=user.id,
        review_note="Reviewed in test fixture",
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    storage_key = evidence.id.hex
    store_document(original, root=tmp_path, storage_key=storage_key)
    evidence.storage_key = storage_key
    db.commit()
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))
    return db, user, connection, evidence


def _setup(context, *, component_total="1.00", manifest_count=2):
    db, user, connection, evidence = context
    trades = [
        _trade(db, connection.id, "verify-fill-a"),
        _trade(db, connection.id, "verify-fill-b"),
    ]
    manifest = sorted([str(trade.id) for trade in trades[:manifest_count]])
    canonical = json.dumps(manifest, separators=(",", ":"))
    extractor = User(
        email="component-extractor@example.com",
        password_hash="test-hash",
        full_name="Component Extractor",
    )
    db.add(extractor)
    db.commit()
    db.refresh(extractor)
    component = BrokerChargeSourceComponent(
        evidence_id=evidence.id,
        source_sha256=evidence.source_sha256,
        component_name="brokerage",
        source_amount=Decimal(component_total),
        currency="INR",
        extraction_method="MANUAL_TRANSCRIPTION",
        parser_version="manual-transcription-v1",
        source_locator="page 1, brokerage row",
        extracted_by_user_id=extractor.id,
        status="VERIFIED",
        reviewed_by_user_id=user.id,
        reviewed_at=datetime.now(timezone.utc),
        review_note="Independently reviewed test fixture",
        eligible_fill_ids_json=canonical,
        eligible_fill_set_sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        rounding_policy="largest-remainder-v1",
        allocation_basis="EXPLICIT_REVIEWED",
    )
    db.add(component)
    db.commit()
    db.refresh(component)
    rows = allocate_and_persist_component(
        db,
        evidence_id=evidence.id,
        broker_connection_id=connection.id,
        broker_report_reference=evidence.broker_report_reference,
        reviewer_user_id=user.id,
        source_component_total="1.00",
        charge_component="brokerage",
        fill_weights={trade.id: 1 for trade in trades},
        allocation_basis="EXPLICIT_REVIEWED",
    )
    db.commit()
    return db, evidence, component, trades, rows


def test_verified_component_accepts_exact_pending_allocation_ledger(reconciliation_context):
    db, evidence, component, trades, rows = _setup(reconciliation_context)

    result = verify_component_allocation_ledger(
        db, evidence_id=evidence.id, source_component_id=component.id
    )

    assert result["status"] == "VERIFIED_PENDING_PROMOTION"
    assert result["allocation_count"] == 2
    assert result["source_amount"] == "1.00"
    assert result["allocated_total"] == "1.00"
    assert result["eligible_fill_set_sha256"] == component.eligible_fill_set_sha256
    assert result["allocation_basis"] == "EXPLICIT_REVIEWED"
    assert {row.status for row in rows} == {"PENDING_RECONCILIATION"}


def test_verification_rejects_allocation_fill_set_mismatch(reconciliation_context):
    db, evidence, component, _trades, _rows = _setup(reconciliation_context, manifest_count=1)

    with pytest.raises(ValueError, match="fill set does not exactly match"):
        verify_component_allocation_ledger(
            db, evidence_id=evidence.id, source_component_id=component.id
        )
    assert {row.status for row in db.query(BrokerChargeAllocation).all()} == {"PENDING_RECONCILIATION"}


def test_verification_rejects_source_component_total_mismatch(reconciliation_context):
    db, evidence, component, _trades, _rows = _setup(reconciliation_context, component_total="1.01")

    with pytest.raises(ValueError, match="does not match the independently reviewed source component"):
        verify_component_allocation_ledger(
            db, evidence_id=evidence.id, source_component_id=component.id
        )


def test_verification_rejects_tampered_source_document(reconciliation_context, tmp_path):
    db, evidence, component, _trades, _rows = _setup(reconciliation_context)
    (tmp_path / evidence.storage_key).write_bytes(b"tampered contract note")

    with pytest.raises(ValueError, match="source integrity check failed"):
        verify_component_allocation_ledger(
            db, evidence_id=evidence.id, source_component_id=component.id
        )
