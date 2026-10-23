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
from app.services.broker_charge_allocation_reconciliation_service import promote_verified_component_allocations
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
    user.is_admin = True
    db.commit()
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
        eligible_fill_weights_json=json.dumps([{"fill_record_id": fill_id, "weight": "1"} for fill_id in manifest], separators=(",", ":")),
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


def test_verification_rejects_per_fill_amounts_that_do_not_match_reviewed_weights(reconciliation_context):
    db, evidence, component, _trades, rows = _setup(reconciliation_context)
    assert len(rows) == 2
    # Preserve the correct component total while tampering with the per-fill split.
    rows[0].allocated_amount = Decimal("0.99")
    rows[1].allocated_amount = Decimal("0.01")
    db.commit()

    with pytest.raises(ValueError, match="Per-fill allocated amounts do not match"):
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



def test_promotion_is_atomic_and_idempotent(reconciliation_context):
    db, evidence, component, _trades, rows = _setup(reconciliation_context)

    promoted = promote_verified_component_allocations(
        db,
        evidence_id=evidence.id,
        source_component_id=component.id,
        reviewer_user_id=component.reviewed_by_user_id,
    )
    assert {row.status for row in promoted} == {"RECONCILED"}
    references = {row.reconciliation_reference for row in promoted}
    assert len(references) == 1
    assert next(iter(references)).startswith(f"charge-component:{component.id}:sha256:")
    db.commit()

    replay = promote_verified_component_allocations(
        db,
        evidence_id=evidence.id,
        source_component_id=component.id,
        reviewer_user_id=component.reviewed_by_user_id,
    )
    assert {row.id for row in replay} == {row.id for row in promoted}
    assert {row.status for row in replay} == {"RECONCILED"}
    assert {row.reconciliation_reference for row in replay} == references
    db.commit()


def test_promotion_rejects_non_reviewer_and_leaves_allocations_pending(reconciliation_context):
    from uuid import uuid4

    db, evidence, component, _trades, _rows = _setup(reconciliation_context)

    with pytest.raises(ValueError, match="authorized source-component reviewer"):
        promote_verified_component_allocations(
            db,
            evidence_id=evidence.id,
            source_component_id=component.id,
            reviewer_user_id=uuid4(),
        )
    db.rollback()
    assert {row.status for row in db.query(BrokerChargeAllocation).all()} == {"PENDING_RECONCILIATION"}
    assert {row.reconciliation_reference for row in db.query(BrokerChargeAllocation).all()} == {None}


def test_outer_rollback_reverts_entire_component_promotion(reconciliation_context):
    db, evidence, component, _trades, _rows = _setup(reconciliation_context)
    db.rollback()
    outer = db.begin()
    try:
        promoted = promote_verified_component_allocations(
            db,
            evidence_id=evidence.id,
            source_component_id=component.id,
            reviewer_user_id=component.reviewed_by_user_id,
        )
        assert {row.status for row in promoted} == {"RECONCILED"}
        outer.rollback()
    finally:
        if outer.is_active:
            outer.rollback()
    db.expire_all()
    assert {row.status for row in db.query(BrokerChargeAllocation).all()} == {"PENDING_RECONCILIATION"}
    assert {row.reconciliation_reference for row in db.query(BrokerChargeAllocation).all()} == {None}



def test_promotion_rechecks_admin_role_at_time_of_promotion(reconciliation_context):
    db, evidence, component, _trades, _rows = _setup(reconciliation_context)
    reviewer = db.get(User, component.reviewed_by_user_id)
    reviewer.is_admin = False
    db.commit()

    with pytest.raises(ValueError, match="active platform administrator"):
        promote_verified_component_allocations(
            db,
            evidence_id=evidence.id,
            source_component_id=component.id,
            reviewer_user_id=component.reviewed_by_user_id,
        )
    db.rollback()
    assert {row.status for row in db.query(BrokerChargeAllocation).all()} == {"PENDING_RECONCILIATION"}


def test_promotion_flush_failure_rolls_back_all_reconciliation_changes(reconciliation_context, monkeypatch):
    db, evidence, component, _trades, _rows = _setup(reconciliation_context)
    original_flush = db.flush
    injected = {"raised": False}

    def fail_when_reconciled(*args, **kwargs):
        reconciled_dirty = any(
            isinstance(obj, BrokerChargeAllocation)
            and obj.status == "RECONCILED"
            and obj.reconciliation_reference is not None
            for obj in db.dirty
        )
        if reconciled_dirty and not injected["raised"]:
            injected["raised"] = True
            raise RuntimeError("injected promotion flush failure")
        return original_flush(*args, **kwargs)

    monkeypatch.setattr(db, "flush", fail_when_reconciled)
    with pytest.raises(RuntimeError, match="injected promotion flush failure"):
        promote_verified_component_allocations(
            db,
            evidence_id=evidence.id,
            source_component_id=component.id,
            reviewer_user_id=component.reviewed_by_user_id,
        )

    assert injected["raised"] is True
    monkeypatch.setattr(db, "flush", original_flush)
    db.expire_all()
    rows = db.query(BrokerChargeAllocation).all()
    assert rows
    assert {row.status for row in rows} == {"PENDING_RECONCILIATION"}
    assert {row.reconciliation_reference for row in rows} == {None}


def test_verification_fails_closed_for_automatic_notional_basis_until_tariff_rules_exist(reconciliation_context):
    db, evidence, component, _trades, _rows = _setup(reconciliation_context)
    component.allocation_basis = "NOTIONAL"
    db.commit()

    with pytest.raises(ValueError, match="Automatic quantity/notional allocation is disabled"):
        verify_component_allocation_ledger(
            db, evidence_id=evidence.id, source_component_id=component.id
        )

    assert {row.status for row in db.query(BrokerChargeAllocation).all()} == {"PENDING_RECONCILIATION"}
