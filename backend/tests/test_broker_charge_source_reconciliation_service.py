import hashlib
from dataclasses import replace
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.tariff_estimate_variance_record import TariffEstimateVarianceRecord
from app.models.broker_connection import BrokerConnection
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.user import User
from app.services.broker_charge_allocation_persistence_service import allocate_and_persist_component
from app.services.broker_charge_allocation_reconciliation_service import promote_verified_component_allocations
from app.services.broker_charge_document_storage_service import store_document
from app.services.broker_charge_source_reconciliation_service import verify_component_allocation_ledger
from app.services.broker_tariff_rules import TariffRule
from app.services.tariff_estimate_snapshot import build_tariff_estimate_snapshot
from app.services.tariff_estimate_persistence_service import persist_tariff_estimate_snapshot
from app.services.tariff_estimate_variance_service import compare_estimate_to_reviewed_actual


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


@pytest.mark.parametrize("component_name", [
    "brokerage", "stt", "exchange_charges", "sebi_charges", "stamp_duty", "gst"
])
@pytest.mark.parametrize("allocation_basis", ["QUANTITY", "NOTIONAL"])
def test_verification_fails_closed_for_automatic_basis_until_tariff_rules_exist(
    reconciliation_context, component_name, allocation_basis
):
    db, evidence, component, _trades, _rows = _setup(reconciliation_context)
    component.component_name = component_name
    component.allocation_basis = allocation_basis
    db.commit()

    with pytest.raises(ValueError, match="Automatic quantity/notional allocation is disabled"):
        verify_component_allocation_ledger(
            db, evidence_id=evidence.id, source_component_id=component.id
        )

    assert {row.status for row in db.query(BrokerChargeAllocation).all()} == {"PENDING_RECONCILIATION"}



def _variance_snapshot_for_trade(trade, *, include_fill_identity=True):
    rule = TariffRule(
        component="brokerage", broker="Upstox", exchange="NSE", segment="FO",
        product="FUTURES", transaction_side="BUY", calculation_basis="ORDER_NOTIONAL",
        rate=Decimal("0.05"), rate_unit="PERCENT",
        effective_from=date(2026, 4, 1), effective_to=None,
        source_url="https://upstox.com/brokerage-charges/",
        source_retrieved_on=date(2026, 10, 23), source_sha256=hashlib.sha256(b"variance-tariff").hexdigest(),
        review_status="APPROVED",
    )
    args = {
        "trade_date": date(2026, 10, 22),
        "calculation_base": "1500.00",
        "source_identity": f"broker-trade:{trade.id}:brokerage",
    }
    if include_fill_identity:
        args["source_trade_record_id"] = trade.id
    return build_tariff_estimate_snapshot(rule, **args)


def test_estimate_actual_variance_is_reviewed_variance_only_and_idempotent(reconciliation_context):
    db, evidence, component, trades, allocations = _setup(reconciliation_context, manifest_count=1)
    snapshot = _variance_snapshot_for_trade(trades[0])
    persisted_snapshot, _ = persist_tariff_estimate_snapshot(db, snapshot)
    db.commit()

    record, status = compare_estimate_to_reviewed_actual(
        db, estimate_snapshot_id=persisted_snapshot.id, source_component_id=component.id
    )
    assert status == "CREATED"
    assert record.status == "VARIANCE_ONLY"
    assert record.component_name == "brokerage"
    assert record.estimated_amount == Decimal("0.75")
    assert record.actual_amount == Decimal("1.00")
    assert record.variance_amount == Decimal("0.25")
    assert record.variance_percent == Decimal("33.333333")
    assert record.evidence_id == evidence.id
    assert {row.status for row in allocations} == {"PENDING_RECONCILIATION"}
    db.commit()

    replay, replay_status = compare_estimate_to_reviewed_actual(
        db, estimate_snapshot_id=persisted_snapshot.id, source_component_id=component.id
    )
    assert replay_status == "EXACT_REPLAY"
    assert replay.id == record.id
    assert db.query(TariffEstimateVarianceRecord).count() == 1
    assert {row.status for row in db.query(BrokerChargeAllocation).all()} == {"PENDING_RECONCILIATION"}
    db.commit()


def test_variance_comparison_rejects_estimate_without_exact_fill_identity(reconciliation_context):
    db, _evidence, component, trades, _allocations = _setup(reconciliation_context, manifest_count=1)
    snapshot = _variance_snapshot_for_trade(trades[0], include_fill_identity=False)
    persisted_snapshot, _ = persist_tariff_estimate_snapshot(db, snapshot)
    db.commit()

    with pytest.raises(ValueError, match="exact broker fill"):
        compare_estimate_to_reviewed_actual(
            db, estimate_snapshot_id=persisted_snapshot.id, source_component_id=component.id
        )
    db.rollback()
    assert db.query(TariffEstimateVarianceRecord).count() == 0


def test_variance_records_reject_direct_sql_update_and_delete(reconciliation_context):
    db, _evidence, component, trades, _allocations = _setup(reconciliation_context, manifest_count=1)
    snapshot = _variance_snapshot_for_trade(trades[0])
    persisted_snapshot, _ = persist_tariff_estimate_snapshot(db, snapshot)
    db.commit()
    record, _ = compare_estimate_to_reviewed_actual(
        db, estimate_snapshot_id=persisted_snapshot.id, source_component_id=component.id
    )
    db.commit()

    with pytest.raises(IntegrityError, match="append-only"):
        db.execute(
            text("UPDATE tariff_estimate_variance_records SET variance_amount = :amount WHERE id = :id"),
            {"amount": "9.99", "id": record.id.hex},
        )
    db.rollback()
    with pytest.raises(IntegrityError, match="append-only"):
        db.execute(
            text("DELETE FROM tariff_estimate_variance_records WHERE id = :id"),
            {"id": record.id.hex},
        )
    db.rollback()
    assert db.query(TariffEstimateVarianceRecord).filter_by(id=record.id).one().variance_amount == Decimal("0.25")



def test_variance_comparison_rejects_tampered_fill_manifest_digest(reconciliation_context):
    db, _evidence, component, trades, _allocations = _setup(reconciliation_context, manifest_count=1)
    snapshot = _variance_snapshot_for_trade(trades[0])
    persisted_snapshot, _ = persist_tariff_estimate_snapshot(db, snapshot)
    db.commit()

    component.eligible_fill_set_sha256 = "0" * 64
    db.commit()

    with pytest.raises(ValueError, match="manifest digest does not match"):
        compare_estimate_to_reviewed_actual(
            db, estimate_snapshot_id=persisted_snapshot.id, source_component_id=component.id
        )
    db.rollback()
    assert db.query(TariffEstimateVarianceRecord).count() == 0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("transaction_side", "SELL", "transaction side does not match"),
        ("trade_date", "2026-10-21", "trade date does not match"),
    ],
)
def test_variance_comparison_rejects_estimate_fill_scope_mismatch(
    reconciliation_context, field, value, message
):
    db, _evidence, component, trades, _allocations = _setup(reconciliation_context, manifest_count=1)
    snapshot = _variance_snapshot_for_trade(trades[0])
    snapshot = replace(snapshot, **{field: value})
    persisted_snapshot, _ = persist_tariff_estimate_snapshot(db, snapshot)
    db.commit()

    with pytest.raises(ValueError, match=message):
        compare_estimate_to_reviewed_actual(
            db, estimate_snapshot_id=persisted_snapshot.id, source_component_id=component.id
        )
    db.rollback()
    assert db.query(TariffEstimateVarianceRecord).count() == 0


def test_order_fill_set_variance_requires_exact_same_order_and_fill_manifest(reconciliation_context):
    db, _user, _connection, _evidence = reconciliation_context
    db, evidence, component, trades, _allocations = _setup(reconciliation_context, manifest_count=2)
    trades[1].broker_order_ref_id = trades[0].broker_order_ref_id
    db.commit()
    rule = TariffRule(
        component="brokerage", broker="Upstox", exchange="NSE", segment="FO",
        product="FUTURES", transaction_side="BUY", calculation_basis="ORDER_NOTIONAL",
        rate=Decimal("0.05"), rate_unit="PERCENT",
        effective_from=date(2026, 4, 1), effective_to=None,
        source_url="https://upstox.com/brokerage-charges/",
        source_retrieved_on=date(2026, 10, 23),
        source_sha256=hashlib.sha256(b"aggregate-variance-tariff").hexdigest(),
        review_status="APPROVED",
    )
    snapshot = build_tariff_estimate_snapshot(
        rule,
        trade_date=date(2026, 10, 22),
        calculation_base="1000.00",
        source_identity=f"broker-order:{trades[0].broker_order_ref_id}:brokerage",
        comparison_scope="ORDER_FILL_SET",
        source_fill_record_ids=[trade.id for trade in trades],
    )
    persisted, _ = persist_tariff_estimate_snapshot(db, snapshot)
    db.commit()

    record, status = compare_estimate_to_reviewed_actual(
        db, estimate_snapshot_id=persisted.id, source_component_id=component.id
    )
    assert status == "CREATED"
    assert record.comparison_scope == "ORDER_FILL_SET"
    assert record.source_fill_set_sha256 == component.eligible_fill_set_sha256
    assert record.actual_amount == Decimal("1.00")
    assert record.estimated_amount == Decimal("0.50")
    assert record.variance_amount == Decimal("0.50")
    db.commit()

    replay, replay_status = compare_estimate_to_reviewed_actual(
        db, estimate_snapshot_id=persisted.id, source_component_id=component.id
    )
    assert replay_status == "EXACT_REPLAY"
    assert replay.id == record.id


def test_order_fill_set_variance_rejects_component_from_different_fill_set(reconciliation_context):
    db, _user, _connection, _evidence = reconciliation_context
    db, evidence, component, trades, _allocations = _setup(reconciliation_context, manifest_count=1)
    rule = TariffRule(
        component="brokerage", broker="Upstox", exchange="NSE", segment="FO",
        product="FUTURES", transaction_side="BUY", calculation_basis="ORDER_NOTIONAL",
        rate=Decimal("0.05"), rate_unit="PERCENT",
        effective_from=date(2026, 4, 1), effective_to=None,
        source_url="https://upstox.com/brokerage-charges/",
        source_retrieved_on=date(2026, 10, 23),
        source_sha256=hashlib.sha256(b"aggregate-variance-tariff-mismatch").hexdigest(),
        review_status="APPROVED",
    )
    snapshot = build_tariff_estimate_snapshot(
        rule,
        trade_date=date(2026, 10, 22),
        calculation_base="1000.00",
        source_identity=f"broker-order:{trades[0].broker_order_ref_id}:brokerage",
        comparison_scope="ORDER_FILL_SET",
        source_fill_record_ids=[trade.id for trade in trades],
    )
    persisted, _ = persist_tariff_estimate_snapshot(db, snapshot)
    db.commit()

    with pytest.raises(ValueError, match="does not exactly match the estimate comparison scope"):
        compare_estimate_to_reviewed_actual(
            db, estimate_snapshot_id=persisted.id, source_component_id=component.id
        )
    db.rollback()
    assert db.query(TariffEstimateVarianceRecord).count() == 0

def test_variance_comparison_does_not_change_reviewed_source_or_charge_allocations(reconciliation_context):
    db, evidence, component, trades, allocations = _setup(reconciliation_context, manifest_count=1)
    snapshot = _variance_snapshot_for_trade(trades[0])
    persisted_snapshot, _ = persist_tariff_estimate_snapshot(db, snapshot)
    db.commit()

    evidence_before = (
        evidence.status,
        evidence.reviewed_by_user_id,
        evidence.reviewed_at,
        evidence.source_sha256,
    )
    component_before = (
        component.status,
        component.reviewed_by_user_id,
        component.reviewed_at,
        component.source_amount,
        component.eligible_fill_ids_json,
        component.eligible_fill_set_sha256,
    )
    allocations_before = [
        (
            row.id,
            row.broker_trade_record_id,
            row.charge_component,
            row.source_component_total,
            row.allocated_amount,
            row.status,
            row.reconciliation_reference,
        )
        for row in db.query(BrokerChargeAllocation)
        .filter(BrokerChargeAllocation.evidence_id == evidence.id)
        .order_by(BrokerChargeAllocation.id)
        .all()
    ]

    record, status = compare_estimate_to_reviewed_actual(
        db, estimate_snapshot_id=persisted_snapshot.id, source_component_id=component.id
    )
    assert status == "CREATED"
    assert record.status == "VARIANCE_ONLY"
    assert (
        evidence.status,
        evidence.reviewed_by_user_id,
        evidence.reviewed_at,
        evidence.source_sha256,
    ) == evidence_before
    assert (
        component.status,
        component.reviewed_by_user_id,
        component.reviewed_at,
        component.source_amount,
        component.eligible_fill_ids_json,
        component.eligible_fill_set_sha256,
    ) == component_before
    allocations_after = [
        (
            row.id,
            row.broker_trade_record_id,
            row.charge_component,
            row.source_component_total,
            row.allocated_amount,
            row.status,
            row.reconciliation_reference,
        )
        for row in db.query(BrokerChargeAllocation)
        .filter(BrokerChargeAllocation.evidence_id == evidence.id)
        .order_by(BrokerChargeAllocation.id)
        .all()
    ]
    assert allocations_after == allocations_before
    db.commit()

@pytest.mark.parametrize(
    ("target", "expected_message"),
    [
        ("evidence", "Reviewed contract-note evidence"),
        ("component", "VERIFIED broker source component"),
    ],
)
def test_variance_comparison_revalidates_review_state_before_writing(
    reconciliation_context, target, expected_message
):
    db, evidence, component, trades, _allocations = _setup(reconciliation_context, manifest_count=1)
    snapshot = _variance_snapshot_for_trade(trades[0])
    persisted_snapshot, _ = persist_tariff_estimate_snapshot(db, snapshot)
    db.commit()

    if target == "evidence":
        evidence.status = "RECEIVED"
    else:
        component.status = "PENDING_REVIEW"
    db.commit()

    with pytest.raises(ValueError, match=expected_message):
        compare_estimate_to_reviewed_actual(
            db, estimate_snapshot_id=persisted_snapshot.id, source_component_id=component.id
        )
    db.rollback()
    assert db.query(TariffEstimateVarianceRecord).count() == 0


def test_aggregate_trade_charges_api_evidence_cannot_be_promoted_as_contract_note(reconciliation_context):
    db, evidence, component, _trades, rows = _setup(reconciliation_context)
    # The Upstox trade-charges endpoint is a segment/financial-year/date-range
    # report, not a contract note or a per-fill actual-charge manifest.
    evidence.source_kind = "UPSTOX_TRADE_CHARGES_API"
    db.commit()

    with pytest.raises(ValueError, match="Contract-note evidence was not found"):
        verify_component_allocation_ledger(
            db, evidence_id=evidence.id, source_component_id=component.id
        )

    db.refresh(evidence)
    assert evidence.source_kind == "UPSTOX_TRADE_CHARGES_API"
    assert {row.status for row in rows} == {"PENDING_RECONCILIATION"}
    assert all(row.reconciliation_reference is None for row in rows)

def test_variance_insert_flush_failure_rolls_back_record_without_mutating_accounting(
    reconciliation_context, monkeypatch
):
    db, evidence, component, trades, allocations = _setup(
        reconciliation_context, manifest_count=1
    )
    snapshot = _variance_snapshot_for_trade(trades[0])
    persisted_snapshot, _ = persist_tariff_estimate_snapshot(db, snapshot)
    db.commit()

    evidence_before = (evidence.status, evidence.source_sha256, evidence.reviewed_by_user_id)
    component_before = (
        component.status,
        component.source_amount,
        component.eligible_fill_ids_json,
        component.eligible_fill_set_sha256,
    )
    allocations_before = [
        (row.id, row.status, row.allocated_amount, row.reconciliation_reference)
        for row in allocations
    ]

    original_flush = db.flush
    injected = {"raised": False}

    def fail_variance_insert(*args, **kwargs):
        if (
            not injected["raised"]
            and any(isinstance(obj, TariffEstimateVarianceRecord) for obj in db.new)
        ):
            injected["raised"] = True
            raise RuntimeError("injected variance insert flush failure")
        return original_flush(*args, **kwargs)

    monkeypatch.setattr(db, "flush", fail_variance_insert)
    with pytest.raises(RuntimeError, match="injected variance insert flush failure"):
        compare_estimate_to_reviewed_actual(
            db,
            estimate_snapshot_id=persisted_snapshot.id,
            source_component_id=component.id,
        )

    assert injected["raised"] is True
    monkeypatch.setattr(db, "flush", original_flush)
    db.expire_all()
    assert db.query(TariffEstimateVarianceRecord).count() == 0
    db.refresh(evidence)
    db.refresh(component)
    assert (
        evidence.status,
        evidence.source_sha256,
        evidence.reviewed_by_user_id,
    ) == evidence_before
    assert (
        component.status,
        component.source_amount,
        component.eligible_fill_ids_json,
        component.eligible_fill_set_sha256,
    ) == component_before
    persisted_allocations = (
        db.query(BrokerChargeAllocation)
        .filter(BrokerChargeAllocation.evidence_id == evidence.id)
        .order_by(BrokerChargeAllocation.id)
        .all()
    )
    persisted_allocation_state = [
        (row.id, row.status, row.allocated_amount, row.reconciliation_reference)
        for row in persisted_allocations
    ]
    # SQL backends need not return UUID rows in the same order as the setup list.
    assert sorted(persisted_allocation_state, key=lambda item: str(item[0])) == sorted(
        allocations_before, key=lambda item: str(item[0])
    )
