import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.core.config import settings
from app.models.broker_charge_canonical_component import BrokerChargeCanonicalComponent
from app.models.broker_charge_canonical_source_link import BrokerChargeCanonicalSourceLink
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.broker_connection import BrokerConnection
from app.models.user import User
from app.services.broker_charge_allocation_service import METHOD_VERSION
from app.services.broker_charge_component_set_contract import LIVE_FILL_COMPONENT_SET_VERSION
from app.services.broker_charge_canonical_component_snapshot_service import (
    materialize_canonical_charge_component_snapshots,
)
from app.services.broker_charge_canonical_component_review_service import (
    review_canonical_charge_component_snapshot,
)
from app.services.broker_charge_canonical_allocation_persistence_service import (
    allocate_and_persist_canonical_snapshot,
)
from app.services.broker_charge_canonical_allocation_reconciliation_service import (
    verify_canonical_component_allocation_ledger,
    promote_verified_canonical_component_allocations,
)
from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.services.broker_charge_document_storage_service import store_document
from app.services.broker_charge_representation_contract import CONTRACT_VERSION


def _context(db, make_user, monkeypatch, tmp_path):
    reviewer = make_user(email=f"canonical-reviewer-{uuid4().hex}@example.com")
    reviewer.is_admin = True
    db.commit()
    extractor = make_user(email=f"canonical-extractor-{uuid4().hex}@example.com")
    connection = BrokerConnection(
        user_id=reviewer.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=True,
    )
    db.add(connection)
    db.commit()
    original = b"synthetic canonical source contract note"
    evidence = BrokerChargeEvidence(
        broker_connection_id=connection.id,
        source_kind="CONTRACT_NOTE",
        broker_report_reference=f"CN-{uuid4().hex[:12]}",
        source_filename="synthetic-contract-note.pdf",
        source_sha256=hashlib.sha256(original).hexdigest(),
        byte_size=len(original),
        status="REVIEWED",
        reviewed_by_user_id=reviewer.id,
        reviewed_at=datetime.now(timezone.utc),
        review_note="Synthetic reviewed evidence",
    )
    db.add(evidence)
    db.commit()
    storage_key = evidence.id.hex
    store_document(original, root=tmp_path, storage_key=storage_key)
    evidence.storage_key = storage_key
    db.commit()
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    fill_ids = sorted([str(uuid4()), str(uuid4())])
    for index, fill_id in enumerate(fill_ids, start=1):
        db.add(BrokerTradeRecord(
            id=UUID(fill_id),
            broker_connection_id=connection.id,
            broker_order_ref_id=uuid4(),
            broker_trade_id=f"canonical-snapshot-fill-{index}-{uuid4().hex[:8]}",
            quantity=1,
            price=Decimal("100.0000"),
            side="BUY",
            instrument_token="NSE_EQ|CANONICAL",
            exchange_timestamp="2026-10-25T10:00:00+05:30",
        ))
    db.commit()
    manifest = json.dumps(fill_ids, separators=(",", ":"))
    manifest_hash = hashlib.sha256(manifest.encode()).hexdigest()
    weights = json.dumps(
        [{"fill_record_id": fill_id, "weight": "1"} for fill_id in fill_ids],
        separators=(",", ":"),
    )
    values = [
        ("brokerage", "20.00", "Brokerage", None, None),
        ("stt", "0.20", "STT", None, None),
        ("sebi_charges", "0.01", "SEBI Turnover", None, None),
        ("stamp_duty", "0.03", "Stamp Duty", None, None),
        ("gst", "58.91", "GST", None, None),
    ]
    if getattr(_context, "split_exchange", False):
        values.extend([
            ("transaction_charges", "306.99", "Transaction Charges", "SPLIT_TRANSACTION_AND_IPFT", CONTRACT_VERSION),
            ("ipft", "0.01", "IPFT", "SPLIT_TRANSACTION_AND_IPFT", CONTRACT_VERSION),
        ])
    else:
        values.append(("exchange_charges", "307.00", "Exchange Charges", None, None))
    for index, (name, amount, label, mode, contract_version) in enumerate(values, start=1):
        db.add(BrokerChargeSourceComponent(
            evidence_id=evidence.id,
            source_sha256=evidence.source_sha256,
            component_name=name,
            source_label=label,
            representation_mode=mode,
            representation_contract_version=contract_version,
            component_set_version=LIVE_FILL_COMPONENT_SET_VERSION,
            revision=1,
            source_amount=Decimal(amount),
            currency="INR",
            extraction_method="MANUAL_TRANSCRIPTION",
            parser_version="manual-transcription-v1",
            source_locator=f"page=1,row={index}",
            eligible_fill_ids_json=manifest,
            eligible_fill_weights_json=weights,
            eligible_fill_set_sha256=manifest_hash,
            rounding_policy=METHOD_VERSION,
            allocation_basis="EXPLICIT_REVIEWED",
            extracted_by_user_id=extractor.id,
            status="VERIFIED",
            reviewed_by_user_id=reviewer.id,
            reviewed_at=datetime.now(timezone.utc),
            review_note="Independent synthetic review",
        ))
    db.commit()
    return reviewer, evidence


def test_materialize_canonical_snapshots_are_pending_and_idempotent(db_session, make_user, monkeypatch, tmp_path):
    reviewer, evidence = _context(db_session, make_user, monkeypatch, tmp_path)
    first = materialize_canonical_charge_component_snapshots(
        db_session, evidence_id=evidence.id, requested_by_user_id=reviewer.id
    )
    db_session.commit()
    second = materialize_canonical_charge_component_snapshots(
        db_session, evidence_id=evidence.id, requested_by_user_id=reviewer.id
    )
    assert len(first) == 6
    assert {row.status for row in first} == {"PENDING_REVIEW"}
    assert {row.id for row in first} == {row.id for row in second}
    assert db_session.query(BrokerChargeCanonicalComponent).filter_by(evidence_id=evidence.id).count() == 6


def test_split_transaction_and_ipft_materialize_one_exchange_snapshot(db_session, make_user, monkeypatch, tmp_path):
    _context.split_exchange = True
    try:
        reviewer, evidence = _context(db_session, make_user, monkeypatch, tmp_path)
    finally:
        _context.split_exchange = False
    snapshots = materialize_canonical_charge_component_snapshots(
        db_session, evidence_id=evidence.id, requested_by_user_id=reviewer.id
    )
    exchange = next(row for row in snapshots if row.canonical_component == "exchange_charges")
    source_ids = json.loads(exchange.source_component_ids_json)
    source_rows = db_session.query(BrokerChargeSourceComponent).filter(
        BrokerChargeSourceComponent.id.in_([UUID(value) for value in source_ids])
    ).all()
    assert Decimal(exchange.canonical_amount) == Decimal("307.00")
    assert {row.component_name for row in source_rows} == {"transaction_charges", "ipft"}
    assert len(source_ids) == 2
    source_links = db_session.query(BrokerChargeCanonicalSourceLink).filter_by(
        canonical_component_id=exchange.id
    ).order_by(BrokerChargeCanonicalSourceLink.source_ordinal).all()
    assert [str(link.source_component_id) for link in source_links] == source_ids
    assert [link.source_ordinal for link in source_links] == [0, 1]
    assert exchange.status == "PENDING_REVIEW"


def test_snapshot_materialization_rejects_unverified_source_row(db_session, make_user, monkeypatch, tmp_path):
    reviewer, evidence = _context(db_session, make_user, monkeypatch, tmp_path)
    row = db_session.query(BrokerChargeSourceComponent).filter_by(
        evidence_id=evidence.id, component_name="brokerage"
    ).one()
    row.status = "PENDING_REVIEW"
    db_session.commit()
    with pytest.raises(ValueError, match="independently verified"):
        materialize_canonical_charge_component_snapshots(
            db_session, evidence_id=evidence.id, requested_by_user_id=reviewer.id
        )
    assert db_session.query(BrokerChargeCanonicalComponent).filter_by(evidence_id=evidence.id).count() == 0


def test_snapshot_materialization_rejects_tampered_original_document(db_session, make_user, monkeypatch, tmp_path):
    reviewer, evidence = _context(db_session, make_user, monkeypatch, tmp_path)
    (tmp_path / evidence.storage_key).write_bytes(b"tampered source")
    with pytest.raises(ValueError, match="source integrity check failed"):
        materialize_canonical_charge_component_snapshots(
            db_session, evidence_id=evidence.id, requested_by_user_id=reviewer.id
        )
    assert db_session.query(BrokerChargeCanonicalComponent).filter_by(evidence_id=evidence.id).count() == 0

def test_changed_reviewed_allocation_metadata_creates_new_snapshot_revision(db_session, make_user, monkeypatch, tmp_path):
    reviewer, evidence = _context(db_session, make_user, monkeypatch, tmp_path)
    first = materialize_canonical_charge_component_snapshots(
        db_session, evidence_id=evidence.id, requested_by_user_id=reviewer.id
    )
    db_session.commit()
    new_weights = json.dumps(
        [
            {"fill_record_id": item["fill_record_id"], "weight": "1" if index == 0 else "2"}
            for index, item in enumerate(json.loads(first[0].eligible_fill_weights_json))
        ],
        separators=(",", ":"),
    )
    for row in db_session.query(BrokerChargeSourceComponent).filter_by(evidence_id=evidence.id).all():
        row.eligible_fill_weights_json = new_weights
    db_session.commit()

    second = materialize_canonical_charge_component_snapshots(
        db_session, evidence_id=evidence.id, requested_by_user_id=reviewer.id
    )
    assert len(second) == 6
    assert all(row.revision == 2 for row in second)
    assert db_session.query(BrokerChargeCanonicalComponent).filter_by(evidence_id=evidence.id).count() == 12


def test_independent_admin_can_verify_split_exchange_snapshot_idempotently(db_session, make_user, monkeypatch, tmp_path):
    _context.split_exchange = True
    try:
        creator, evidence = _context(db_session, make_user, monkeypatch, tmp_path)
    finally:
        _context.split_exchange = False
    snapshots = materialize_canonical_charge_component_snapshots(
        db_session, evidence_id=evidence.id, requested_by_user_id=creator.id
    )
    db_session.commit()
    reviewer = make_user(email=f"canonical-second-reviewer-{uuid4().hex}@example.com")
    reviewer.is_admin = True
    db_session.commit()
    exchange = next(row for row in snapshots if row.canonical_component == "exchange_charges")

    reviewed = review_canonical_charge_component_snapshot(
        db_session, snapshot_id=exchange.id, reviewer_user_id=reviewer.id,
        decision="VERIFIED", review_note="Confirmed split transaction and IPFT sum",
    )
    db_session.commit()
    replay = review_canonical_charge_component_snapshot(
        db_session, snapshot_id=exchange.id, reviewer_user_id=reviewer.id,
        decision="VERIFIED", review_note="Confirmed split transaction and IPFT sum",
    )
    assert reviewed.status == "VERIFIED"
    assert reviewed.reviewed_by_user_id == reviewer.id
    assert replay.id == reviewed.id
    assert Decimal(reviewed.canonical_amount) == Decimal("307.00")


def test_snapshot_creator_cannot_self_review(db_session, make_user, monkeypatch, tmp_path):
    creator, evidence = _context(db_session, make_user, monkeypatch, tmp_path)
    snapshots = materialize_canonical_charge_component_snapshots(
        db_session, evidence_id=evidence.id, requested_by_user_id=creator.id
    )
    db_session.commit()
    with pytest.raises(ValueError, match="distinct from creator"):
        review_canonical_charge_component_snapshot(
            db_session, snapshot_id=snapshots[0].id, reviewer_user_id=creator.id,
            decision="VERIFIED", review_note="Self-review must be blocked",
        )
    db_session.refresh(snapshots[0])
    assert snapshots[0].status == "PENDING_REVIEW"


def test_snapshot_review_rejects_changed_source_fingerprint(db_session, make_user, monkeypatch, tmp_path):
    creator, evidence = _context(db_session, make_user, monkeypatch, tmp_path)
    snapshots = materialize_canonical_charge_component_snapshots(
        db_session, evidence_id=evidence.id, requested_by_user_id=creator.id
    )
    db_session.commit()
    reviewer = make_user(email=f"canonical-fingerprint-reviewer-{uuid4().hex}@example.com")
    reviewer.is_admin = True
    db_session.commit()
    source = db_session.query(BrokerChargeSourceComponent).filter_by(
        evidence_id=evidence.id, component_name="brokerage"
    ).one()
    source.source_locator = "changed after snapshot"
    db_session.commit()

    brokerage = next(row for row in snapshots if row.canonical_component == "brokerage")
    with pytest.raises(ValueError, match="source fingerprint is stale"):
        review_canonical_charge_component_snapshot(
            db_session, snapshot_id=brokerage.id, reviewer_user_id=reviewer.id,
            decision="VERIFIED", review_note="Source changed after snapshot",
        )
    db_session.refresh(brokerage)
    assert brokerage.status == "PENDING_REVIEW"


def test_verified_split_snapshot_persists_allocations_linked_to_canonical_snapshot(db_session, make_user, monkeypatch, tmp_path):
    _context.split_exchange = True
    try:
        creator, evidence = _context(db_session, make_user, monkeypatch, tmp_path)
    finally:
        _context.split_exchange = False
    snapshots = materialize_canonical_charge_component_snapshots(
        db_session, evidence_id=evidence.id, requested_by_user_id=creator.id
    )
    db_session.commit()
    reviewer = make_user(email=f"canonical-allocation-reviewer-{uuid4().hex}@example.com")
    reviewer.is_admin = True
    db_session.commit()
    exchange = next(row for row in snapshots if row.canonical_component == "exchange_charges")
    review_canonical_charge_component_snapshot(
        db_session, snapshot_id=exchange.id, reviewer_user_id=reviewer.id,
        decision="VERIFIED", review_note="Approved canonical split exchange charges",
    )
    db_session.commit()

    rows = allocate_and_persist_canonical_snapshot(
        db_session,
        snapshot_id=exchange.id,
        broker_connection_id=evidence.broker_connection_id,
        broker_report_reference=evidence.broker_report_reference,
    )
    db_session.commit()
    replay = allocate_and_persist_canonical_snapshot(
        db_session,
        snapshot_id=exchange.id,
        broker_connection_id=evidence.broker_connection_id,
        broker_report_reference=evidence.broker_report_reference,
    )
    assert len(rows) == 2
    assert {row.canonical_component_id for row in rows} == {exchange.id}
    assert {row.charge_component for row in rows} == {"exchange_charges"}
    assert {row.status for row in rows} == {"PENDING_RECONCILIATION"}
    assert sum((Decimal(row.allocated_amount) for row in rows), Decimal("0")) == Decimal("307.00")
    assert {row.id for row in replay} == {row.id for row in rows}
    assert db_session.query(BrokerChargeAllocation).filter_by(
        evidence_id=evidence.id, charge_component="exchange_charges"
    ).count() == 2
    verification = verify_canonical_component_allocation_ledger(
        db_session, snapshot_id=exchange.id
    )
    assert verification["status"] == "VERIFIED_PENDING_PROMOTION"
    assert verification["canonical_amount"] == "307.00"
    promoted = promote_verified_canonical_component_allocations(
        db_session, snapshot_id=exchange.id, reviewer_user_id=reviewer.id
    )
    assert {row.status for row in promoted} == {"RECONCILED"}
    # The service must not commit the caller's transaction: rollback restores
    # the complete allocation set to pending, without losing the source ledger.
    db_session.rollback()
    rolled_back_rows = db_session.query(BrokerChargeAllocation).filter_by(
        canonical_component_id=exchange.id
    ).all()
    assert {row.status for row in rolled_back_rows} == {"PENDING_RECONCILIATION"}
    promoted = promote_verified_canonical_component_allocations(
        db_session, snapshot_id=exchange.id, reviewer_user_id=reviewer.id
    )
    db_session.commit()
    assert {row.status for row in promoted} == {"RECONCILED"}
    assert {row.reconciliation_reference for row in promoted} == {
        verification["reconciliation_reference"]
    }
    replayed = promote_verified_canonical_component_allocations(
        db_session, snapshot_id=exchange.id, reviewer_user_id=reviewer.id
    )
    assert {row.id for row in replayed} == {row.id for row in promoted}
    assert {row.status for row in replayed} == {"RECONCILED"}


def test_snapshot_review_fails_closed_when_normalized_source_link_is_missing(db_session, make_user, monkeypatch, tmp_path):
    creator, evidence = _context(db_session, make_user, monkeypatch, tmp_path)
    snapshots = materialize_canonical_charge_component_snapshots(
        db_session, evidence_id=evidence.id, requested_by_user_id=creator.id
    )
    db_session.commit()
    reviewer = make_user(email=f"canonical-missing-link-{uuid4().hex}@example.com")
    reviewer.is_admin = True
    db_session.commit()
    exchange = next(row for row in snapshots if row.canonical_component == "exchange_charges")
    link = db_session.query(BrokerChargeCanonicalSourceLink).filter_by(
        canonical_component_id=exchange.id
    ).first()
    assert link is not None
    db_session.delete(link)
    db_session.commit()
    with pytest.raises(ValueError, match="Normalized canonical source links disagree"):
        review_canonical_charge_component_snapshot(
            db_session, snapshot_id=exchange.id, reviewer_user_id=reviewer.id,
            decision="VERIFIED", review_note="Must reject incomplete normalized source membership",
        )
    db_session.refresh(exchange)
    assert exchange.status == "PENDING_REVIEW"


def test_canonical_reconciliation_rejects_modified_allocation_before_promotion(db_session, make_user, monkeypatch, tmp_path):
    _context.split_exchange = True
    try:
        creator, evidence = _context(db_session, make_user, monkeypatch, tmp_path)
    finally:
        _context.split_exchange = False
    snapshots = materialize_canonical_charge_component_snapshots(
        db_session, evidence_id=evidence.id, requested_by_user_id=creator.id
    )
    db_session.commit()
    reviewer = make_user(email=f"canonical-reconcile-reviewer-{uuid4().hex}@example.com")
    reviewer.is_admin = True
    db_session.commit()
    exchange = next(row for row in snapshots if row.canonical_component == "exchange_charges")
    review_canonical_charge_component_snapshot(
        db_session, snapshot_id=exchange.id, reviewer_user_id=reviewer.id,
        decision="VERIFIED", review_note="Approved canonical exchange total",
    )
    db_session.commit()
    allocations = allocate_and_persist_canonical_snapshot(
        db_session, snapshot_id=exchange.id,
        broker_connection_id=evidence.broker_connection_id,
        broker_report_reference=evidence.broker_report_reference,
    )
    db_session.commit()
    allocations[0].allocated_amount = Decimal(allocations[0].allocated_amount) + Decimal("0.01")
    db_session.commit()
    with pytest.raises(ValueError, match="deterministic paise allocation"):
        promote_verified_canonical_component_allocations(
            db_session, snapshot_id=exchange.id, reviewer_user_id=reviewer.id
        )
    db_session.refresh(allocations[0])
    assert allocations[0].status == "PENDING_RECONCILIATION"


def test_canonical_reconciliation_rejects_incomplete_allocation_fill_set(db_session, make_user, monkeypatch, tmp_path):
    """A missing fill allocation must block promotion instead of reconciling a partial set."""
    _context.split_exchange = True
    try:
        creator, evidence = _context(db_session, make_user, monkeypatch, tmp_path)
    finally:
        _context.split_exchange = False
    snapshots = materialize_canonical_charge_component_snapshots(
        db_session, evidence_id=evidence.id, requested_by_user_id=creator.id
    )
    db_session.commit()
    reviewer = make_user(email=f"canonical-conflict-reviewer-{uuid4().hex}@example.com")
    reviewer.is_admin = True
    db_session.commit()
    exchange = next(row for row in snapshots if row.canonical_component == "exchange_charges")
    review_canonical_charge_component_snapshot(
        db_session, snapshot_id=exchange.id, reviewer_user_id=reviewer.id,
        decision="VERIFIED", review_note="Approve canonical exchange-charge fill set",
    )
    db_session.commit()
    allocations = allocate_and_persist_canonical_snapshot(
        db_session, snapshot_id=exchange.id,
        broker_connection_id=evidence.broker_connection_id,
        broker_report_reference=evidence.broker_report_reference,
    )
    db_session.commit()
    assert len(allocations) == 2
    db_session.delete(allocations[0])
    db_session.commit()

    with pytest.raises(ValueError, match="fill set differs from the reviewed snapshot manifest"):
        promote_verified_canonical_component_allocations(
            db_session, snapshot_id=exchange.id, reviewer_user_id=reviewer.id
        )
    remaining = db_session.query(BrokerChargeAllocation).filter_by(
        canonical_component_id=exchange.id
    ).all()
    assert len(remaining) == 1
    assert remaining[0].status == "PENDING_RECONCILIATION"
    assert remaining[0].reconciliation_reference is None
