"""Database-backed regression tests for ORDER_FILL_SET variance comparisons."""
import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.services.broker_charge_document_storage_service import store_document
from app.services.broker_tariff_rules import TariffRule
from app.services.tariff_estimate_persistence_service import persist_tariff_estimate_snapshot
from app.services.tariff_estimate_snapshot import build_tariff_estimate_snapshot
from app.services.tariff_estimate_variance_service import compare_estimate_to_reviewed_actual
from app.core.config import settings


@pytest.fixture()
def aggregate_variance_case(db_session, make_user, tmp_path, monkeypatch):
    extractor = make_user("extractor@example.com")
    reviewer = make_user("reviewer@example.com")
    connection = BrokerConnection(
        user_id=extractor.id,
        broker="upstox",
        api_key_encrypted="test-key",
        api_secret_encrypted="test-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=True,
    )
    db_session.add(connection)
    db_session.flush()

    broker_order = BrokerOrder(
        broker_connection_id=connection.id,
        order_id=uuid4(),
        broker_name="upstox",
        broker_order_id="order-aggregate-test",
        requested_quantity=3,
        filled_quantity=3,
        status="COMPLETE",
    )
    db_session.add(broker_order)
    db_session.flush()

    fill_ids = sorted([uuid4(), uuid4()], key=str)
    for index, fill_id in enumerate(fill_ids):
        db_session.add(BrokerTradeRecord(
            id=fill_id,
            broker_connection_id=connection.id,
            broker_order_ref_id=broker_order.id,
            broker_trade_id=f"trade-aggregate-{index}",
            quantity=index + 1,
            price=Decimal("100.00"),
            side="SELL",
            instrument_token="NSE_FO_TEST",
            exchange_timestamp=f"2026-10-23T10:0{index}:00+00:00",
        ))

    content = b"%PDF-1.7\\nsynthetic contract-note fixture\\n"
    storage_key = uuid4().hex
    digest, size = store_document(content, root=tmp_path, storage_key=storage_key)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))

    evidence = BrokerChargeEvidence(
        broker_connection_id=connection.id,
        source_kind="CONTRACT_NOTE",
        source_filename="synthetic-contract-note.pdf",
        storage_key=storage_key,
        source_sha256=digest,
        byte_size=size,
        received_by_user_id=extractor.id,
        status="REVIEWED",
        reviewed_by_user_id=reviewer.id,
        reviewed_at=datetime.now(timezone.utc),
        review_note="Synthetic test evidence only",
    )
    db_session.add(evidence)
    db_session.flush()

    manifest_ids = [str(value) for value in fill_ids]
    manifest_json = json.dumps(manifest_ids, separators=(",", ":"))
    manifest_digest = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()
    component = BrokerChargeSourceComponent(
        evidence_id=evidence.id,
        source_sha256=digest,
        component_name="brokerage",
        revision=1,
        source_amount=Decimal("52.00"),
        currency="INR",
        extraction_method="MANUAL_TRANSCRIPTION",
        parser_version="test-v1",
        source_locator="page 1, row 1",
        eligible_fill_ids_json=manifest_json,
        eligible_fill_set_sha256=manifest_digest,
        rounding_policy="largest-remainder-paise-v1",
        allocation_basis="EXPLICIT_REVIEWED",
        extracted_by_user_id=extractor.id,
        status="VERIFIED",
        reviewed_by_user_id=reviewer.id,
        reviewed_at=datetime.now(timezone.utc),
        review_note="Independent synthetic review",
    )
    db_session.add(component)

    rule = TariffRule(
        component="brokerage",
        broker="Upstox",
        exchange="NSE",
        segment="FO",
        product="FUTURES",
        transaction_side="SELL",
        calculation_basis="ORDER_NOTIONAL",
        rate=Decimal("0.05"),
        rate_unit="PERCENT",
        effective_from=date(2026, 4, 1),
        effective_to=None,
        source_url="https://upstox.com/brokerage-charges/",
        source_retrieved_on=date(2026, 10, 23),
        source_sha256="a" * 64,
        review_status="APPROVED",
    )
    snapshot = build_tariff_estimate_snapshot(
        rule,
        trade_date=date(2026, 10, 23),
        calculation_base="100000",
        source_identity="aggregate-variance-test:order-1:brokerage",
        comparison_scope="ORDER_FILL_SET",
        source_fill_record_ids=fill_ids,
    )
    snapshot_record, _ = persist_tariff_estimate_snapshot(db_session, snapshot)
    db_session.commit()
    return db_session, snapshot_record, component, fill_ids


def test_order_fill_set_variance_creates_audit_only_record(aggregate_variance_case):
    db, snapshot, component, fill_ids = aggregate_variance_case

    record, status = compare_estimate_to_reviewed_actual(
        db, estimate_snapshot_id=snapshot.id, source_component_id=component.id
    )

    assert status == "CREATED"
    assert record.comparison_scope == "ORDER_FILL_SET"
    assert record.source_fill_set_sha256 == component.eligible_fill_set_sha256
    assert record.estimated_amount == Decimal("50.00")
    assert record.actual_amount == Decimal("52.00")
    assert record.variance_amount == Decimal("2.00")
    assert record.status == "VARIANCE_ONLY"
    assert db.query(type(record)).count() == 1
    assert len(fill_ids) == 2


def test_order_fill_set_variance_exact_replay_is_idempotent(aggregate_variance_case):
    db, snapshot, component, _fill_ids = aggregate_variance_case

    first, first_status = compare_estimate_to_reviewed_actual(
        db, estimate_snapshot_id=snapshot.id, source_component_id=component.id
    )
    db.commit()
    replay, replay_status = compare_estimate_to_reviewed_actual(
        db, estimate_snapshot_id=snapshot.id, source_component_id=component.id
    )

    assert first_status == "CREATED"
    assert replay_status == "EXACT_REPLAY"
    assert replay.id == first.id
    assert db.query(type(first)).count() == 1


def test_order_fill_set_variance_rejects_different_manifest(aggregate_variance_case):
    db, _snapshot, component, fill_ids = aggregate_variance_case
    from app.models.tariff_estimate_variance_record import TariffEstimateVarianceRecord

    rule = TariffRule(
        component="brokerage",
        broker="Upstox",
        exchange="NSE",
        segment="FO",
        product="FUTURES",
        transaction_side="SELL",
        calculation_basis="ORDER_NOTIONAL",
        rate=Decimal("0.05"),
        rate_unit="PERCENT",
        effective_from=date(2026, 4, 1),
        effective_to=None,
        source_url="https://upstox.com/brokerage-charges/",
        source_retrieved_on=date(2026, 10, 23),
        source_sha256="a" * 64,
        review_status="APPROVED",
    )
    mismatched_snapshot = build_tariff_estimate_snapshot(
        rule,
        trade_date=date(2026, 10, 23),
        calculation_base="100000",
        source_identity="aggregate-variance-test:order-2:brokerage",
        comparison_scope="ORDER_FILL_SET",
        source_fill_record_ids=[fill_ids[0], uuid4()],
    )
    estimate_record, _ = persist_tariff_estimate_snapshot(db, mismatched_snapshot)
    db.commit()

    with pytest.raises(ValueError, match="does not exactly match"):
        compare_estimate_to_reviewed_actual(
            db, estimate_snapshot_id=estimate_record.id, source_component_id=component.id
        )

    assert db.query(TariffEstimateVarianceRecord).count() == 0


def test_order_fill_set_variance_rejects_tampered_actual_manifest_digest(aggregate_variance_case):
    db, snapshot, component, _fill_ids = aggregate_variance_case
    from app.models.tariff_estimate_variance_record import TariffEstimateVarianceRecord

    component.eligible_fill_set_sha256 = "0" * 64
    db.flush()

    with pytest.raises(ValueError, match="manifest digest does not match"):
        compare_estimate_to_reviewed_actual(
            db, estimate_snapshot_id=snapshot.id, source_component_id=component.id
        )

    assert db.query(TariffEstimateVarianceRecord).count() == 0


def test_order_fill_set_variance_rejects_fill_side_mismatch_without_write(aggregate_variance_case):
    db, snapshot, component, fill_ids = aggregate_variance_case
    from app.models.tariff_estimate_variance_record import TariffEstimateVarianceRecord

    fill = db.query(BrokerTradeRecord).filter(BrokerTradeRecord.id == fill_ids[0]).one()
    fill.side = "BUY"
    db.flush()

    with pytest.raises(ValueError, match="does not match every identified broker fill"):
        compare_estimate_to_reviewed_actual(
            db, estimate_snapshot_id=snapshot.id, source_component_id=component.id
        )

    assert db.query(TariffEstimateVarianceRecord).count() == 0


def test_order_fill_set_variance_rejects_fills_from_different_orders_without_write(aggregate_variance_case):
    db, snapshot, component, fill_ids = aggregate_variance_case
    from app.models.tariff_estimate_variance_record import TariffEstimateVarianceRecord

    evidence = db.query(BrokerChargeEvidence).filter(
        BrokerChargeEvidence.id == component.evidence_id
    ).one()
    second_order = BrokerOrder(
        broker_connection_id=evidence.broker_connection_id,
        order_id=uuid4(),
        broker_name="upstox",
        broker_order_id="order-aggregate-test-second",
        requested_quantity=1,
        filled_quantity=1,
        status="COMPLETE",
    )
    db.add(second_order)
    db.flush()
    fill = db.query(BrokerTradeRecord).filter(BrokerTradeRecord.id == fill_ids[0]).one()
    fill.broker_order_ref_id = second_order.id
    db.flush()

    with pytest.raises(ValueError, match="different broker orders"):
        compare_estimate_to_reviewed_actual(
            db, estimate_snapshot_id=snapshot.id, source_component_id=component.id
        )

    assert db.query(TariffEstimateVarianceRecord).count() == 0


def test_order_fill_set_variance_rejects_trade_date_mismatch_without_write(aggregate_variance_case):
    db, snapshot, component, fill_ids = aggregate_variance_case
    from app.models.tariff_estimate_variance_record import TariffEstimateVarianceRecord

    fill = db.query(BrokerTradeRecord).filter(BrokerTradeRecord.id == fill_ids[0]).one()
    fill.exchange_timestamp = "2026-10-22T10:00:00+00:00"
    db.flush()

    with pytest.raises(ValueError, match="does not match every identified broker fill"):
        compare_estimate_to_reviewed_actual(
            db, estimate_snapshot_id=snapshot.id, source_component_id=component.id
        )

    assert db.query(TariffEstimateVarianceRecord).count() == 0
