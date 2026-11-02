"""PostgreSQL-only race test for durable charge allocation serialization.

This test is skipped on local runs without TEST_POSTGRES_URL. CI provisions a
PostgreSQL service and sets that variable, so the race is exercised there.
"""
import hashlib
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 register every model table
from app.models.execution import Execution
from app.models.live_position import LivePosition
from app.core.config import settings
from app.core.database import Base
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.tariff_estimate_variance_record import TariffEstimateVarianceRecord
from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.user import User
from app.services.broker_charge_allocation_persistence_service import (
    allocate_and_persist_component,
)
from app.services.broker_charge_allocation_reconciliation_service import (
    promote_verified_component_allocations,
)
from app.services.broker_charge_source_reconciliation_service import (
    verify_component_allocation_ledger,
)
from app.services.broker_charge_document_storage_service import store_document
from app.services.broker_charge_component_set_contract import LIVE_FILL_COMPONENT_SET_VERSION
from app.services.live_fill_accounting_service import (
    LiveFillAccountingService,
    LiveFillChargeBreakdown,
)
from app.services.broker_tariff_rules import TariffRule
from app.services.tariff_estimate_snapshot import build_tariff_estimate_snapshot
from app.services.tariff_estimate_persistence_service import persist_tariff_estimate_snapshot
from app.services.tariff_estimate_variance_service import compare_estimate_to_reviewed_actual


@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="requires dedicated PostgreSQL test database")
def test_concurrent_conflicting_fill_sets_serialize_on_evidence():
    url = os.environ["TEST_POSTGRES_URL"]
    engine = create_engine(url, pool_size=5, max_overflow=0, pool_pre_ping=True)
    # This test runs before the separate migration-check step in CI, so create
    # the current ORM schema in its dedicated, disposable test database.
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid4().hex[:10]
    user_id, connection_id, evidence_id = uuid4(), uuid4(), uuid4()
    trade_a_id, trade_b_id = uuid4(), uuid4()
    report_ref = f"CN-RACE-{suffix}"
    filename = f"race-{suffix}.pdf"
    digest = hashlib.sha256(suffix.encode()).hexdigest()

    try:
        # Schema is migrated by CI before tests. Use unique IDs/references so
        # parallel test runs do not collide with existing rows.
        order_a_id, order_b_id = uuid4(), uuid4()
        broker_order_a_id, broker_order_b_id = uuid4(), uuid4()
        portfolio_id, instrument_id = uuid4(), uuid4()
        with Session.begin() as db:
            db.add(User(
                id=user_id, email=f"race-{suffix}@example.invalid",
                password_hash="test-hash", full_name="Race Test", is_admin=False,
            ))
            # Flush the parent row before inserting dependent rows in the same
            # transaction; these test objects do not declare ORM relationships.
            db.flush()
            db.add(Portfolio(
                id=portfolio_id, user_id=user_id, name=f"race-{suffix}",
                virtual_capital=Decimal("10000.00"), cash_balance=Decimal("10000.00"),
            ))
            db.add(Instrument(
                id=instrument_id, instrument_key=f"TEST|{suffix}", exchange="NSE",
                segment="NSE_EQ", instrument_type="EQUITY", trading_symbol=f"RACE{suffix}",
                name="Concurrency Test Instrument",
            ))
            db.add(BrokerConnection(
                id=connection_id, user_id=user_id, broker="upstox",
                api_key_encrypted="test-key", api_secret_encrypted="test-secret",
                redirect_uri="https://example.invalid/callback", is_connected=True,
            ))
            for order_id in (order_a_id, order_b_id):
                db.add(Order(
                    id=order_id, portfolio_id=portfolio_id, instrument_id=instrument_id,
                    side="BUY", order_type="MARKET", segment="EQUITY_INTRADAY",
                    quantity=1, status="FILLED", trading_mode="PAPER",
                    execution_reason="MANUAL", placed_at=datetime.now(timezone.utc),
                ))
        with Session.begin() as db:
            db.add(BrokerChargeEvidence(
                id=evidence_id, broker_connection_id=connection_id,
                source_kind="CONTRACT_NOTE", broker_report_reference=report_ref,
                source_filename=filename, source_sha256=digest, byte_size=1,
                status="REVIEWED", reviewed_at=datetime.now(timezone.utc),
                reviewed_by_user_id=user_id, review_note="PostgreSQL race test",
            ))
            for broker_order_id, order_id in ((broker_order_a_id, order_a_id), (broker_order_b_id, order_b_id)):
                db.add(BrokerOrder(
                    id=broker_order_id, broker_connection_id=connection_id, order_id=order_id,
                    broker_name="upstox", broker_order_id=f"broker-order-{broker_order_id}",
                    requested_quantity=1, filled_quantity=1, status="COMPLETE",
                ))
            for trade_id, broker_order_id, trade_ref in (
                (trade_a_id, broker_order_a_id, f"trade-a-{suffix}"),
                (trade_b_id, broker_order_b_id, f"trade-b-{suffix}"),
            ):
                db.add(BrokerTradeRecord(
                    id=trade_id, broker_connection_id=connection_id,
                    broker_order_ref_id=broker_order_id, broker_trade_id=trade_ref,
                    quantity=1, price=Decimal("100.00"), side="BUY",
                    instrument_token="NSE_TEST", exchange_timestamp=datetime.now(timezone.utc).isoformat(),
                ))

        barrier = threading.Barrier(2)
        results = []
        result_lock = threading.Lock()

        def attempt(fill_id):
            with Session() as db:
                barrier.wait(timeout=10)
                try:
                    rows = allocate_and_persist_component(
                        db,
                        evidence_id=evidence_id,
                        broker_connection_id=connection_id,
                        broker_report_reference=report_ref,
                        reviewer_user_id=user_id,
                        source_component_total=Decimal("1.00"),
                        charge_component="brokerage",
                        fill_weights={fill_id: Decimal("1")},
                        allocation_basis="EXPLICIT_REVIEWED",
                    )
                    db.commit()
                    result = ("success", len(rows))
                except Exception as exc:
                    db.rollback()
                    result = ("error", type(exc).__name__, str(exc))
                with result_lock:
                    results.append(result)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(attempt, trade_a_id), pool.submit(attempt, trade_b_id)]
            for future in futures:
                future.result(timeout=30)

        # Exactly one fill set can own the source component. The other request
        # must fail closed after the evidence-row lock is released.
        assert sum(r[0] == "success" for r in results) == 1, results
        with Session() as db:
            rows = db.execute(
                text("SELECT broker_trade_record_id, allocated_amount FROM broker_charge_allocations WHERE evidence_id = :eid AND charge_component = 'brokerage'"),
                {"eid": str(evidence_id)},
            ).all()
            assert len(rows) == 1, rows
            assert Decimal(str(rows[0][1])) == Decimal("1.00")
    finally:
        # Remove only this test's isolated records. Foreign-key order matters.
        with Session.begin() as db:
            db.execute(text("DELETE FROM broker_charge_allocations WHERE evidence_id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_trade_records WHERE broker_connection_id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM broker_orders WHERE broker_connection_id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM broker_charge_evidence WHERE id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_connections WHERE id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM orders WHERE id IN (:a, :b)"), {"a": str(order_a_id), "b": str(order_b_id)})
            db.execute(text("DELETE FROM instruments WHERE id = :id"), {"id": str(instrument_id)})
            db.execute(text("DELETE FROM portfolios WHERE id = :id"), {"id": str(portfolio_id)})
            db.execute(text("DELETE FROM users WHERE id = :id"), {"id": str(user_id)})
        engine.dispose()



@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="requires dedicated PostgreSQL test database")
def test_concurrent_source_verification_and_promotion_serialize_on_evidence(
    tmp_path, monkeypatch
):
    """Verification and duplicate promotions serialize to one complete ledger state."""
    url = os.environ["TEST_POSTGRES_URL"]
    engine = create_engine(url, pool_size=5, max_overflow=0, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid4().hex[:10]
    user_id, extractor_id, connection_id, evidence_id = (
        uuid4(), uuid4(), uuid4(), uuid4()
    )
    component_id = uuid4()
    trade_a_id, trade_b_id = uuid4(), uuid4()
    order_a_id, order_b_id = uuid4(), uuid4()
    broker_order_a_id, broker_order_b_id = uuid4(), uuid4()
    portfolio_id, instrument_id = uuid4(), uuid4()
    report_ref = f"CN-VERIFY-PROMOTE-{suffix}"
    storage_key = evidence_id.hex
    original_document = f"synthetic contract note {suffix}\n".encode("utf-8")
    digest = hashlib.sha256(original_document).hexdigest()
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))
    store_document(original_document, root=tmp_path, storage_key=storage_key)

    try:
        with Session.begin() as db:
            db.add_all([
                User(
                    id=user_id, email=f"race-admin-{suffix}@example.invalid",
                    password_hash="test-hash", full_name="Race Admin", is_admin=True,
                ),
                User(
                    id=extractor_id, email=f"race-extractor-{suffix}@example.invalid",
                    password_hash="test-hash", full_name="Race Extractor", is_admin=False,
                ),
            ])
            db.flush()
            db.add(Portfolio(
                id=portfolio_id, user_id=user_id, name=f"race-verify-{suffix}",
                virtual_capital=Decimal("10000.00"), cash_balance=Decimal("10000.00"),
            ))
            db.add(Instrument(
                id=instrument_id, instrument_key=f"TEST|VERIFY|{suffix}", exchange="NSE",
                segment="NSE_EQ", instrument_type="EQUITY", trading_symbol=f"VERIFY{suffix}",
                name="Verification Race Instrument",
            ))
            db.add(BrokerConnection(
                id=connection_id, user_id=user_id, broker="upstox",
                api_key_encrypted="test-key", api_secret_encrypted="test-secret",
                redirect_uri="https://example.invalid/callback", is_connected=True,
            ))
            for order_id in (order_a_id, order_b_id):
                db.add(Order(
                    id=order_id, portfolio_id=portfolio_id, instrument_id=instrument_id,
                    side="BUY", order_type="MARKET", segment="EQUITY_INTRADAY",
                    quantity=1, status="FILLED", trading_mode="PAPER",
                    execution_reason="MANUAL", placed_at=datetime.now(timezone.utc),
                ))
        with Session.begin() as db:
            db.add(BrokerChargeEvidence(
                id=evidence_id, broker_connection_id=connection_id,
                source_kind="CONTRACT_NOTE", broker_report_reference=report_ref,
                source_filename="synthetic-contract-note.pdf", source_sha256=digest,
                byte_size=len(original_document), storage_key=storage_key,
                status="REVIEWED", reviewed_at=datetime.now(timezone.utc),
                reviewed_by_user_id=user_id, review_note="Synthetic PostgreSQL race test",
            ))
            for broker_order_id, order_id in (
                (broker_order_a_id, order_a_id), (broker_order_b_id, order_b_id)
            ):
                db.add(BrokerOrder(
                    id=broker_order_id, broker_connection_id=connection_id, order_id=order_id,
                    broker_name="upstox", broker_order_id=f"broker-order-{broker_order_id}",
                    requested_quantity=1, filled_quantity=1, status="COMPLETE",
                ))
            for trade_id, broker_order_id, trade_ref in (
                (trade_a_id, broker_order_a_id, f"verify-trade-a-{suffix}"),
                (trade_b_id, broker_order_b_id, f"verify-trade-b-{suffix}"),
            ):
                db.add(BrokerTradeRecord(
                    id=trade_id, broker_connection_id=connection_id,
                    broker_order_ref_id=broker_order_id, broker_trade_id=trade_ref,
                    quantity=1, price=Decimal("100.00"), side="BUY",
                    instrument_token="NSE_TEST", exchange_timestamp=datetime.now(timezone.utc).isoformat(),
                ))
        manifest = sorted([str(trade_a_id), str(trade_b_id)])
        manifest_json = json.dumps(manifest, separators=(",", ":"))
        with Session.begin() as db:
            db.add(BrokerChargeSourceComponent(
                id=component_id, evidence_id=evidence_id, source_sha256=digest,
                component_name="brokerage", source_amount=Decimal("1.00"), currency="INR",
                extraction_method="MANUAL_TRANSCRIPTION", parser_version="manual-transcription-v1",
                source_locator="page 1, brokerage row", extracted_by_user_id=extractor_id,
                status="VERIFIED", reviewed_by_user_id=user_id,
                reviewed_at=datetime.now(timezone.utc), review_note="Independent synthetic review",
                eligible_fill_ids_json=manifest_json,
                eligible_fill_weights_json=json.dumps([{"fill_record_id": fill_id, "weight": "1"} for fill_id in manifest], separators=(",", ":")),
                eligible_fill_set_sha256=hashlib.sha256(manifest_json.encode("utf-8")).hexdigest(),
                rounding_policy="largest-remainder-v1", allocation_basis="EXPLICIT_REVIEWED",
            ))
            allocate_and_persist_component(
                db, evidence_id=evidence_id, broker_connection_id=connection_id,
                broker_report_reference=report_ref, reviewer_user_id=user_id,
                source_component_total=Decimal("1.00"), charge_component="brokerage",
                fill_weights={trade_a_id: Decimal("1"), trade_b_id: Decimal("1")},
                allocation_basis="EXPLICIT_REVIEWED",
            )

        # Two promotion attempts for the same reviewed component must both
        # resolve idempotently to the same durable allocation set. The verifier
        # races with them to ensure it observes only a complete pending or
        # reconciled ledger, never a mixed intermediate state.
        barrier = threading.Barrier(3)
        results = []
        result_lock = threading.Lock()

        def verify():
            with Session() as db:
                barrier.wait(timeout=10)
                try:
                    result = verify_component_allocation_ledger(
                        db, evidence_id=evidence_id, source_component_id=component_id
                    )
                    db.commit()
                    outcome = ("verify", result["status"])
                except Exception as exc:
                    db.rollback()
                    outcome = ("error", type(exc).__name__, str(exc))
                with result_lock:
                    results.append(outcome)

        def promote():
            with Session() as db:
                barrier.wait(timeout=10)
                try:
                    rows = promote_verified_component_allocations(
                        db, evidence_id=evidence_id, source_component_id=component_id,
                        reviewer_user_id=user_id,
                    )
                    db.commit()
                    outcome = ("promote", len(rows))
                except Exception as exc:
                    db.rollback()
                    outcome = ("error", type(exc).__name__, str(exc))
                with result_lock:
                    results.append(outcome)

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [
                pool.submit(verify),
                pool.submit(promote),
                pool.submit(promote),
            ]
            for future in futures:
                future.result(timeout=45)

        errors = [result for result in results if result[0] == "error"]
        assert not errors, results
        verification_results = [result[1] for result in results if result[0] == "verify"]
        assert verification_results in (
            ["VERIFIED_PENDING_PROMOTION"], ["ALREADY_RECONCILED"]
        ), results
        promotion_results = [result for result in results if result[0] == "promote"]
        assert promotion_results == [("promote", 2), ("promote", 2)], results
        with Session() as db:
            rows = db.query(BrokerChargeAllocation).filter_by(
                evidence_id=evidence_id, charge_component="brokerage"
            ).all()
            assert len(rows) == 2
            assert {row.status for row in rows} == {"RECONCILED"}
            assert len({row.reconciliation_reference for row in rows}) == 1
    finally:
        with Session.begin() as db:
            db.execute(text("DELETE FROM broker_charge_allocations WHERE evidence_id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_charge_canonical_source_links WHERE canonical_component_id IN (SELECT id FROM broker_charge_canonical_components WHERE evidence_id = :id)"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_charge_canonical_components WHERE evidence_id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_charge_source_components WHERE evidence_id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_trade_records WHERE broker_connection_id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM broker_orders WHERE broker_connection_id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM broker_charge_evidence WHERE id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_connections WHERE id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM orders WHERE id IN (:a, :b)"), {"a": str(order_a_id), "b": str(order_b_id)})
            db.execute(text("DELETE FROM instruments WHERE id = :id"), {"id": str(instrument_id)})
            db.execute(text("DELETE FROM portfolios WHERE id = :id"), {"id": str(portfolio_id)})
            db.execute(text("DELETE FROM users WHERE id IN (:a, :b)"), {"a": str(user_id), "b": str(extractor_id)})
        engine.dispose()


@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="requires dedicated PostgreSQL test database")
def test_live_fill_promotion_races_with_component_ledger_verification(tmp_path, monkeypatch):
    """Full accounting promotion and independent ledger verification serialize safely."""
    url = os.environ["TEST_POSTGRES_URL"]
    engine = create_engine(url, pool_size=5, max_overflow=0, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid4().hex[:10]
    owner_id, reviewer_id, extractor_id = uuid4(), uuid4(), uuid4()
    snapshot_creator_id, canonical_reviewer_id = uuid4(), uuid4()
    connection_id, evidence_id = uuid4(), uuid4()
    portfolio_id, instrument_id, order_id = uuid4(), uuid4(), uuid4()
    broker_order_id, trade_id = uuid4(), uuid4()
    report_ref = f"CN-LIVE-VERIFY-RACE-{suffix}"
    storage_key = evidence_id.hex
    source_document = f"synthetic reviewed note for race test {suffix}".encode()
    digest = hashlib.sha256(source_document).hexdigest()
    amounts = {
        "brokerage": Decimal("20.00"),
        "stt": Decimal("0.20"),
        "exchange_charges": Decimal("0.01"),
        "sebi_charges": Decimal("0.01"),
        "stamp_duty": Decimal("0.03"),
        "gst": Decimal("3.61"),
    }
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))
    store_document(source_document, root=tmp_path, storage_key=storage_key)

    try:
        with Session.begin() as db:
            db.add_all([
                User(id=owner_id, email=f"owner-{suffix}@example.invalid",
                     password_hash="test-hash", full_name="Race Owner", is_admin=False),
                User(id=reviewer_id, email=f"reviewer-{suffix}@example.invalid",
                     password_hash="test-hash", full_name="Race Reviewer", is_admin=True),
                User(id=extractor_id, email=f"extractor-{suffix}@example.invalid",
                     password_hash="test-hash", full_name="Race Extractor", is_admin=False),
                User(id=snapshot_creator_id, email=f"snapshot-creator-{suffix}@example.invalid",
                     password_hash="test-hash", full_name="Snapshot Creator", is_admin=True),
                User(id=canonical_reviewer_id, email=f"canonical-reviewer-{suffix}@example.invalid",
                     password_hash="test-hash", full_name="Canonical Reviewer", is_admin=True),
            ])
            db.flush()
            db.add(Portfolio(
                id=portfolio_id, user_id=owner_id, name=f"live-race-{suffix}",
                virtual_capital=Decimal("10000.00"), cash_balance=Decimal("10000.00"),
            ))
            db.add(Instrument(
                id=instrument_id, instrument_key=f"TEST|LIVE|{suffix}", exchange="NSE",
                segment="NSE_EQ", instrument_type="EQUITY", trading_symbol=f"LIVERACE{suffix}",
                name="Live Accounting Race Instrument",
            ))
            db.add(BrokerConnection(
                id=connection_id, user_id=owner_id, broker="upstox",
                api_key_encrypted="test-key", api_secret_encrypted="test-secret",
                redirect_uri="https://example.invalid/callback", is_connected=True,
            ))
            db.add(Order(
                id=order_id, portfolio_id=portfolio_id, instrument_id=instrument_id,
                side="BUY", order_type="MARKET", segment="EQUITY_DELIVERY",
                quantity=1, status="PENDING", trading_mode="LIVE",
                execution_reason="MANUAL", placed_at=datetime.now(timezone.utc),
            ))

        with Session.begin() as db:
            db.add(BrokerChargeEvidence(
                id=evidence_id, broker_connection_id=connection_id,
                source_kind="CONTRACT_NOTE", broker_report_reference=report_ref,
                source_filename="synthetic-reviewed-contract-note.pdf",
                source_sha256=digest, byte_size=len(source_document), storage_key=storage_key,
                status="REVIEWED", reviewed_at=datetime.now(timezone.utc),
                reviewed_by_user_id=reviewer_id, review_note="Synthetic PostgreSQL concurrency test",
            ))
            db.add(BrokerOrder(
                id=broker_order_id, broker_connection_id=connection_id, order_id=order_id,
                broker_name="upstox", broker_order_id=f"broker-order-{suffix}",
                requested_quantity=1, filled_quantity=1, status="COMPLETE",
            ))
            db.flush()
            db.add(BrokerTradeRecord(
                id=trade_id, broker_connection_id=connection_id,
                broker_order_ref_id=broker_order_id, broker_trade_id=f"live-trade-{suffix}",
                quantity=1, price=Decimal("100.00"), side="BUY",
                instrument_token=f"TEST|LIVE|{suffix}",
                exchange_timestamp=datetime.now(timezone.utc).isoformat(),
            ))

        manifest = json.dumps([str(trade_id)], separators=(",", ":"))
        manifest_hash = hashlib.sha256(manifest.encode()).hexdigest()
        with Session.begin() as db:
            for component_name, amount in amounts.items():
                db.add(BrokerChargeSourceComponent(
                    evidence_id=evidence_id,
                    source_sha256=digest,
                    component_name=component_name,
                    source_label=component_name,
                    revision=1,
                    source_amount=amount,
                    component_set_version=LIVE_FILL_COMPONENT_SET_VERSION,
                    currency="INR",
                    extraction_method="MANUAL_TRANSCRIPTION",
                    parser_version="manual-transcription-v1",
                    source_locator=f"synthetic note / {component_name}",
                    eligible_fill_ids_json=manifest,
                    eligible_fill_set_sha256=manifest_hash,
                    eligible_fill_weights_json=json.dumps(
                        [{"fill_record_id": str(trade_id), "weight": "1"}],
                        separators=(",", ":"),
                    ),
                    rounding_policy="largest-remainder-v1",
                    allocation_basis="EXPLICIT_REVIEWED",
                    extracted_by_user_id=extractor_id,
                    status="VERIFIED",
                    reviewed_by_user_id=reviewer_id,
                    reviewed_at=datetime.now(timezone.utc),
                    review_note="Independent synthetic review",
                ))

        from app.services.broker_charge_canonical_component_snapshot_service import (
            materialize_canonical_charge_component_snapshots,
        )
        with Session.begin() as db:
            snapshots = materialize_canonical_charge_component_snapshots(
                db, evidence_id=evidence_id, requested_by_user_id=snapshot_creator_id
            )
            snapshot_ids = {row.canonical_component: row.id for row in snapshots}
        assert set(snapshot_ids) == set(amounts)

        from app.services.broker_charge_canonical_component_review_service import (
            review_canonical_charge_component_snapshot,
        )
        for snapshot_id in snapshot_ids.values():
            with Session.begin() as db:
                review_canonical_charge_component_snapshot(
                    db,
                    snapshot_id=snapshot_id,
                    reviewer_user_id=canonical_reviewer_id,
                    decision="VERIFIED",
                    review_note="Independent canonical snapshot review",
                )

        from app.services.broker_charge_canonical_allocation_persistence_service import (
            allocate_and_persist_canonical_snapshot,
        )
        for snapshot_id in snapshot_ids.values():
            with Session.begin() as db:
                allocate_and_persist_canonical_snapshot(
                    db,
                    snapshot_id=snapshot_id,
                    broker_connection_id=connection_id,
                    broker_report_reference=report_ref,
                )

        from app.services.broker_charge_canonical_allocation_reconciliation_service import (
            promote_verified_canonical_component_allocations,
        )
        brokerage_snapshot_id = snapshot_ids["brokerage"]
        for component_name, snapshot_id in snapshot_ids.items():
            if component_name == "brokerage":
                continue
            with Session.begin() as db:
                promote_verified_canonical_component_allocations(
                    db, snapshot_id=snapshot_id, reviewer_user_id=canonical_reviewer_id
                )

        barrier = threading.Barrier(2)
        outcomes = []
        outcomes_lock = threading.Lock()
        charge_payload = LiveFillChargeBreakdown(
            **amounts, total_charges=sum(amounts.values(), Decimal("0.00")),
            source="BROKER_REPORTED", reference=report_ref,
            evidence_id=evidence_id, reviewer_user_id=reviewer_id,
        )

        def promote_component():
            with Session() as db:
                barrier.wait(timeout=10)
                try:
                    rows = promote_verified_canonical_component_allocations(
                        db, snapshot_id=brokerage_snapshot_id,
                        reviewer_user_id=canonical_reviewer_id,
                    )
                    db.commit()
                    outcome = ("ledger_promotion", "ok", len(rows))
                except Exception as exc:
                    db.rollback()
                    outcome = ("error", "ledger_promotion", type(exc).__name__, str(exc))
                with outcomes_lock:
                    outcomes.append(outcome)

        def promote_fill():
            with Session() as db:
                barrier.wait(timeout=10)
                try:
                    result = LiveFillAccountingService(db).promote_trade(
                        owner_id, trade_id, charge_payload,
                    )
                    outcome = ("live_fill", "ok", result.inserted, str(result.execution_id))
                except ValueError as exc:
                    db.rollback()
                    outcome = ("live_fill", "blocked", type(exc).__name__, str(exc))
                except Exception as exc:
                    db.rollback()
                    outcome = ("error", "live_fill", type(exc).__name__, str(exc))
                with outcomes_lock:
                    outcomes.append(outcome)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(promote_component), pool.submit(promote_fill)]
            for future in futures:
                future.result(timeout=60)

        # Ledger promotion must succeed. Live accounting may safely win after the
        # row is reconciled, or fail closed while it is still pending; it must
        # never leave partial execution/position writes on that failed attempt.
        assert not [item for item in outcomes if item[0] == "error"], outcomes
        ledger_results = [item for item in outcomes if item[0] == "ledger_promotion"]
        assert ledger_results == [("ledger_promotion", "ok", 1)], outcomes
        fill_results = [item for item in outcomes if item[0] == "live_fill"]
        assert len(fill_results) == 1, outcomes
        if fill_results[0][1] == "blocked":
            assert fill_results[0][2] == "ValueError", outcomes
            assert (
                "Canonical allocation rows do not match" in fill_results[0][3]
                or "exactly six canonical per-fill charge allocations" in fill_results[0][3]
                or "Canonical component must be fully verified" in fill_results[0][3]
            ), outcomes
            with Session() as db:
                assert db.query(Execution).filter_by(
                    broker_connection_id=connection_id, broker_trade_id=f"live-trade-{suffix}"
                ).count() == 0
                assert db.query(LivePosition).filter_by(
                    broker_connection_id=connection_id, instrument_id=instrument_id
                ).count() == 0
            with Session() as db:
                retry = LiveFillAccountingService(db).promote_trade(owner_id, trade_id, charge_payload)
                assert retry.inserted is True
                db.commit()
        else:
            assert fill_results[0][2] is True, outcomes

        # A durable exact replay must be idempotent; conflicting charges must
        # be rejected without changing the single execution/position.
        with Session() as db:
            replay = LiveFillAccountingService(db).promote_trade(owner_id, trade_id, charge_payload)
            assert replay.inserted is False
            db.commit()
        with Session() as db:
            with pytest.raises(ValueError, match="conflict|match|charge|evidence"):
                LiveFillAccountingService(db).promote_trade(
                    owner_id, trade_id,
                    LiveFillChargeBreakdown(
                        **{**amounts, "brokerage": Decimal("19.99")},
                        total_charges=Decimal("23.85"),
                        source="BROKER_REPORTED", reference=report_ref,
                        evidence_id=evidence_id, reviewer_user_id=reviewer_id,
                    ),
                )
            db.rollback()

        with Session() as db:
            executions = db.query(Execution).filter_by(
                broker_connection_id=connection_id, broker_trade_id=f"live-trade-{suffix}"
            ).all()
            positions = db.query(LivePosition).filter_by(
                broker_connection_id=connection_id, instrument_id=instrument_id
            ).all()
            allocations = db.query(BrokerChargeAllocation).filter_by(evidence_id=evidence_id).all()
            assert len(executions) == 1
            assert executions[0].total_charges == Decimal("23.86")
            assert len(positions) == 1 and positions[0].quantity == 1
            assert len(allocations) == 6
            assert {row.status for row in allocations} == {"RECONCILED"}
            assert sum((Decimal(row.allocated_amount) for row in allocations if row.charge_component == "brokerage"), Decimal("0")) == Decimal("20.00")
    finally:
        with Session.begin() as db:
            db.execute(text("DELETE FROM executions WHERE broker_connection_id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM live_positions WHERE broker_connection_id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM broker_charge_allocations WHERE evidence_id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_charge_canonical_source_links WHERE canonical_component_id IN (SELECT id FROM broker_charge_canonical_components WHERE evidence_id = :id)"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_charge_canonical_components WHERE evidence_id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_charge_source_components WHERE evidence_id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_trade_records WHERE broker_connection_id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM broker_orders WHERE broker_connection_id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM broker_charge_evidence WHERE id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_connections WHERE id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM orders WHERE id = :id"), {"id": str(order_id)})
            db.execute(text("DELETE FROM instruments WHERE id = :id"), {"id": str(instrument_id)})
            db.execute(text("DELETE FROM portfolios WHERE id = :id"), {"id": str(portfolio_id)})
            db.execute(text("DELETE FROM users WHERE id IN (:owner, :reviewer, :extractor, :creator, :canonical_reviewer)"),
                        {"owner": str(owner_id), "reviewer": str(reviewer_id), "extractor": str(extractor_id),
                         "creator": str(snapshot_creator_id), "canonical_reviewer": str(canonical_reviewer_id)})
        engine.dispose()



@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="requires dedicated PostgreSQL test database")
@pytest.mark.parametrize("conflicting_payload", [False, True], ids=["exact-replay", "conflicting-payload"])
def test_concurrent_tariff_estimate_persistence_exact_replay_and_conflict(conflicting_payload):
    """The unique DB key arbitrates concurrent estimate inserts without overwrites."""
    url = os.environ["TEST_POSTGRES_URL"]
    engine = create_engine(url, pool_size=2, max_overflow=0, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid4().hex
    today = datetime.now(timezone.utc).date()
    rule = TariffRule(
        component="brokerage", broker="Upstox", exchange="NSE", segment="FO",
        product="FUTURES", transaction_side="SELL", calculation_basis="ORDER_NOTIONAL",
        rate=Decimal("0.05"), rate_unit="PERCENT",
        effective_from=date(2026, 4, 1), effective_to=None,
        source_url="https://upstox.com/brokerage-charges/",
        source_retrieved_on=date(2026, 10, 23), source_sha256=hashlib.sha256(b"test-tariff").hexdigest(),
        review_status="APPROVED",
    )

    def snapshot(base):
        return build_tariff_estimate_snapshot(
            rule, trade_date=today, calculation_base=base,
            source_identity=f"postgres-race:{suffix}:brokerage",
        )

    snapshots = [snapshot("100000"), snapshot("200000" if conflicting_payload else "100000")]
    barrier = threading.Barrier(2)
    outcomes = []
    outcome_lock = threading.Lock()

    def persist(candidate):
        with Session() as db:
            barrier.wait(timeout=10)
            try:
                record, status = persist_tariff_estimate_snapshot(db, candidate)
                db.commit()
                outcome = ("ok", status, record.idempotency_key, record.snapshot_sha256)
            except Exception as exc:
                db.rollback()
                outcome = ("error", type(exc).__name__, str(exc))
            with outcome_lock:
                outcomes.append(outcome)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(persist, candidate) for candidate in snapshots]
        for future in futures:
            future.result(timeout=30)

    successes = [row for row in outcomes if row[0] == "ok"]
    errors = [row for row in outcomes if row[0] == "error"]
    if not conflicting_payload:
        assert len(successes) == 2, outcomes
        assert not errors, outcomes
        assert sorted(row[1] for row in successes) == ["CREATED", "EXACT_REPLAY"], outcomes
    else:
        assert len(successes) == 1, outcomes
        assert len(errors) == 1 and "Conflicting tariff estimate replay" in errors[0][2], outcomes

    with Session() as db:
        from app.models.tariff_estimate_snapshot_record import TariffEstimateSnapshotRecord
        rows = db.query(TariffEstimateSnapshotRecord).filter_by(
            idempotency_key=snapshots[0].idempotency_key
        ).all()
        assert len(rows) == 1
        assert rows[0].snapshot_sha256 == successes[0][3]
        assert rows[0].snapshot_json in {candidate.canonical_json() for candidate in snapshots}

@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="requires dedicated PostgreSQL test database")
def test_concurrent_variance_comparison_exact_replay_is_audit_only(tmp_path, monkeypatch):
    """Two simultaneous comparisons create one immutable audit record and no ledger writes."""
    url = os.environ["TEST_POSTGRES_URL"]
    engine = create_engine(url, pool_size=3, max_overflow=0, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid4().hex[:12]
    owner_id, reviewer_id = uuid4(), uuid4()
    connection_id, evidence_id, component_id = uuid4(), uuid4(), uuid4()
    broker_order_id, trade_id = uuid4(), uuid4()
    report_ref = f"CN-VARIANCE-RACE-{suffix}"
    trade_date = datetime.now(timezone.utc).date()
    original = b"%PDF-1.7\\nsynthetic concurrency contract note\\n"
    storage_key = uuid4().hex
    source_digest, source_size = store_document(original, root=tmp_path, storage_key=storage_key)
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))
    manifest_json = json.dumps([str(trade_id)], separators=(",", ":"))
    manifest_digest = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()
    portfolio_id, instrument_id, order_id = uuid4(), uuid4(), uuid4()
    snapshot_id = None

    try:
        with Session.begin() as db:
            db.add_all([
                User(id=owner_id, email=f"variance-owner-{suffix}@example.invalid",
                     password_hash="test-hash", full_name="Variance Owner", is_admin=False),
                User(id=reviewer_id, email=f"variance-reviewer-{suffix}@example.invalid",
                     password_hash="test-hash", full_name="Variance Reviewer", is_admin=False),
            ])
            db.flush()
            db.add(BrokerConnection(
                id=connection_id, user_id=owner_id, broker="upstox",
                api_key_encrypted="test-key", api_secret_encrypted="test-secret",
                redirect_uri="https://example.invalid/callback", is_connected=True,
            ))
            db.flush()
            db.add(Portfolio(
                id=portfolio_id, user_id=owner_id, name=f"variance-race-{suffix}",
                virtual_capital=Decimal("10000.00"), cash_balance=Decimal("10000.00"),
            ))
            db.add(Instrument(
                id=instrument_id, instrument_key=f"TEST|VARIANCE|{suffix}", exchange="NSE",
                segment="NSE_FO", instrument_type="FUTURES", trading_symbol=f"VAR{suffix}",
                name="Variance Concurrency Test Instrument",
            ))
            db.flush()
            db.add(Order(
                id=order_id, portfolio_id=portfolio_id, instrument_id=instrument_id,
                side="SELL", order_type="MARKET", segment="EQUITY_INTRADAY", quantity=1,
                status="FILLED", trading_mode="PAPER", execution_reason="MANUAL",
                placed_at=datetime.now(timezone.utc),
            ))
            db.flush()
            db.add(BrokerOrder(
                id=broker_order_id, broker_connection_id=connection_id, order_id=order_id,
                broker_name="upstox", broker_order_id=f"variance-order-{suffix}",
                requested_quantity=1, filled_quantity=1, status="COMPLETE",
            ))
            db.flush()
            db.add(BrokerTradeRecord(
                id=trade_id, broker_connection_id=connection_id,
                broker_order_ref_id=broker_order_id, broker_trade_id=f"variance-trade-{suffix}",
                quantity=1, price=Decimal("100.00"), side="SELL",
                instrument_token="NSE_FO_TEST",
                exchange_timestamp=datetime.combine(trade_date, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
            ))
            db.add(BrokerChargeEvidence(
                id=evidence_id, broker_connection_id=connection_id, source_kind="CONTRACT_NOTE",
                broker_report_reference=report_ref, report_date=trade_date, segment="FO",
                source_filename=f"variance-{suffix}.pdf", storage_key=storage_key,
                source_sha256=source_digest, byte_size=source_size, received_by_user_id=owner_id,
                status="REVIEWED", reviewed_by_user_id=reviewer_id,
                reviewed_at=datetime.now(timezone.utc), review_note="Synthetic concurrency fixture",
            ))
            db.flush()
            db.add(BrokerChargeSourceComponent(
                id=component_id, evidence_id=evidence_id, source_sha256=source_digest,
                component_name="brokerage", revision=1, source_amount=Decimal("1.00"),
                currency="INR", extraction_method="MANUAL_TRANSCRIPTION",
                parser_version="test-v1", source_locator="page 1, row 1",
                eligible_fill_ids_json=manifest_json, eligible_fill_set_sha256=manifest_digest,
                rounding_policy="largest-remainder-v1", allocation_basis="EXPLICIT_REVIEWED",
                extracted_by_user_id=owner_id, status="VERIFIED",
                reviewed_by_user_id=reviewer_id, reviewed_at=datetime.now(timezone.utc),
                review_note="Synthetic concurrency fixture",
            ))

        rule = TariffRule(
            component="brokerage", broker="Upstox", exchange="NSE", segment="FO",
            product="FUTURES", transaction_side="SELL", calculation_basis="ORDER_NOTIONAL",
            rate=Decimal("0.05"), rate_unit="PERCENT",
            effective_from=date(2026, 4, 1), effective_to=None,
            source_url="https://upstox.com/brokerage-charges/",
            source_retrieved_on=trade_date, source_sha256=hashlib.sha256(b"race-tariff").hexdigest(),
            review_status="APPROVED",
        )
        snapshot = build_tariff_estimate_snapshot(
            rule, trade_date=trade_date, calculation_base=Decimal("1000"),
            source_identity=f"variance-race:{suffix}:brokerage",
            source_trade_record_id=trade_id,
        )
        with Session() as db:
            persisted_snapshot, snapshot_status = persist_tariff_estimate_snapshot(db, snapshot)
            assert snapshot_status == "CREATED"
            snapshot_id = persisted_snapshot.id
            db.commit()

        barrier = threading.Barrier(2)
        outcomes = []
        outcome_lock = threading.Lock()

        def compare():
            with Session() as db:
                barrier.wait(timeout=10)
                try:
                    record, status = compare_estimate_to_reviewed_actual(
                        db, estimate_snapshot_id=snapshot_id, source_component_id=component_id
                    )
                    db.commit()
                    outcome = ("ok", status, str(record.id))
                except Exception as exc:
                    db.rollback()
                    outcome = ("error", type(exc).__name__, str(exc))
                with outcome_lock:
                    outcomes.append(outcome)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(compare), pool.submit(compare)]
            for future in futures:
                future.result(timeout=45)

        successes = [row for row in outcomes if row[0] == "ok"]
        assert len(successes) == 2, outcomes
        assert sorted(row[1] for row in successes) == ["CREATED", "EXACT_REPLAY"], outcomes
        assert successes[0][2] == successes[1][2]
        with Session() as db:
            records = db.query(TariffEstimateVarianceRecord).filter_by(
                estimate_snapshot_id=snapshot_id, source_component_id=component_id
            ).all()
            assert len(records) == 1
            assert records[0].status == "VARIANCE_ONLY"
            assert db.query(BrokerChargeAllocation).filter_by(evidence_id=evidence_id).count() == 0
    finally:
        # Variance records are append-only by database trigger. Keep this isolated
        # synthetic fixture intact rather than weakening the immutability boundary.
        engine.dispose()


@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="requires dedicated PostgreSQL test database")
def test_concurrent_canonical_snapshot_promotions_are_atomic_and_idempotent(tmp_path, monkeypatch):
    """Two concurrent promotions must leave the complete canonical set consistently reconciled."""
    from app.models.broker_charge_canonical_component import BrokerChargeCanonicalComponent
    from app.models.broker_charge_canonical_source_link import BrokerChargeCanonicalSourceLink
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
        promote_verified_canonical_component_allocations,
    )
    from app.services.broker_charge_representation_contract import CONTRACT_VERSION

    url = os.environ["TEST_POSTGRES_URL"]
    engine = create_engine(url, pool_size=5, max_overflow=0, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid4().hex[:10]
    owner_id, canonical_reviewer_id, extractor_id, connection_id, evidence_id = (
        uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
    )
    portfolio_id, instrument_id = uuid4(), uuid4()
    order_ids = [uuid4(), uuid4()]
    broker_order_ids = [uuid4(), uuid4()]
    report_ref = f"CN-CANONICAL-PROMOTION-RACE-{suffix}"
    original = f"synthetic canonical source note {suffix}".encode()
    digest = hashlib.sha256(original).hexdigest()
    monkeypatch.setattr(settings, "BROKER_CHARGE_DOCUMENT_ROOT", str(tmp_path))
    store_document(original, root=tmp_path, storage_key=evidence_id.hex)
    fill_ids = sorted([str(uuid4()), str(uuid4())])
    now = datetime.now(timezone.utc)
    try:
        with Session.begin() as db:
            db.add_all([
                User(id=owner_id, email=f"canonical-owner-{suffix}@example.invalid",
                     password_hash="test", full_name="Source Reviewer", is_admin=True),
                User(id=canonical_reviewer_id, email=f"canonical-reviewer-{suffix}@example.invalid",
                     password_hash="test", full_name="Canonical Reviewer", is_admin=True),
                User(id=extractor_id, email=f"canonical-extractor-{suffix}@example.invalid",
                     password_hash="test", full_name="Extractor", is_admin=False),
            ])
            db.flush()
            db.add(BrokerConnection(
                id=connection_id, user_id=owner_id, broker="upstox",
                api_key_encrypted="test-key", api_secret_encrypted="test-secret",
                redirect_uri="https://example.invalid/callback", is_connected=True,
            ))
            db.flush()
            db.add(Portfolio(
                id=portfolio_id, user_id=owner_id, name=f"canonical-race-{suffix}",
                virtual_capital=Decimal("10000.00"), cash_balance=Decimal("10000.00"),
            ))
            db.add(Instrument(
                id=instrument_id, instrument_key=f"TEST|CANONICAL-RACE-{suffix}",
                exchange="NSE", segment="NSE_EQ", instrument_type="EQUITY",
                trading_symbol=f"CRACE{suffix}", name="Canonical Race Test Instrument",
            ))
            db.flush()
            for order_id in order_ids:
                db.add(Order(
                    id=order_id, portfolio_id=portfolio_id, instrument_id=instrument_id,
                    side="BUY", order_type="MARKET", segment="EQUITY_INTRADAY",
                    quantity=1, status="FILLED", trading_mode="PAPER",
                    execution_reason="MANUAL", placed_at=now,
                ))
            db.flush()
            for index, broker_order_id in enumerate(broker_order_ids, start=1):
                db.add(BrokerOrder(
                    id=broker_order_id, broker_connection_id=connection_id,
                    order_id=order_ids[index - 1], broker_name="upstox",
                    broker_order_id=f"canonical-race-order-{suffix}-{index}",
                    requested_quantity=1, filled_quantity=1, status="COMPLETE",
                ))
            db.flush()
            db.add(BrokerChargeEvidence(
                id=evidence_id, broker_connection_id=connection_id,
                source_kind="CONTRACT_NOTE", broker_report_reference=report_ref,
                source_filename=f"canonical-race-{suffix}.pdf", source_sha256=digest,
                byte_size=len(original), storage_key=evidence_id.hex, status="REVIEWED",
                reviewed_at=now, reviewed_by_user_id=owner_id,
                review_note="Synthetic PostgreSQL canonical promotion race",
            ))
            db.flush()
            manifest = json.dumps(fill_ids, separators=(",", ":"))
            weights = json.dumps(
                [{"fill_record_id": fill_id, "weight": "1"} for fill_id in fill_ids],
                separators=(",", ":"),
            )
            manifest_hash = hashlib.sha256(manifest.encode()).hexdigest()
            for index, fill_id in enumerate(fill_ids, start=1):
                db.add(BrokerTradeRecord(
                    id=UUID(fill_id), broker_connection_id=connection_id,
                    broker_order_ref_id=broker_order_ids[index - 1],
                    broker_trade_id=f"canonical-race-{suffix}-{index}",
                    quantity=1, price=Decimal("100.0000"), side="BUY",
                    instrument_token="NSE_EQ|CANONICAL-RACE",
                    exchange_timestamp=now.isoformat(),
                ))
            db.flush()
            values = [
                ("brokerage", "20.00", "Brokerage", None, None),
                ("stt", "0.20", "STT", None, None),
                ("sebi_charges", "0.01", "SEBI Turnover", None, None),
                ("stamp_duty", "0.03", "Stamp Duty", None, None),
                ("gst", "58.91", "GST", None, None),
                ("exchange_charges", "307.00", "Exchange Charges", None, None),
            ]
            for index, (name, amount, label, mode, contract_version) in enumerate(values, start=1):
                db.add(BrokerChargeSourceComponent(
                    evidence_id=evidence_id, source_sha256=digest,
                    component_name=name, source_label=label,
                    representation_mode=mode, representation_contract_version=contract_version,
                    component_set_version=LIVE_FILL_COMPONENT_SET_VERSION, revision=1,
                    source_amount=Decimal(amount), currency="INR",
                    extraction_method="MANUAL_TRANSCRIPTION", parser_version="manual-transcription-v1",
                    source_locator=f"page=1,row={index}", eligible_fill_ids_json=manifest,
                    eligible_fill_weights_json=weights, eligible_fill_set_sha256=manifest_hash,
                    rounding_policy="largest-remainder-v1", allocation_basis="EXPLICIT_REVIEWED",
                    extracted_by_user_id=extractor_id, status="VERIFIED",
                    reviewed_by_user_id=owner_id, reviewed_at=now,
                    review_note="Independent synthetic source review",
                ))
        with Session.begin() as db:
            snapshots = materialize_canonical_charge_component_snapshots(
                db, evidence_id=evidence_id, requested_by_user_id=owner_id
            )
        exchange = next(row for row in snapshots if row.canonical_component == "exchange_charges")
        with Session.begin() as db:
            review_canonical_charge_component_snapshot(
                db, snapshot_id=exchange.id, reviewer_user_id=canonical_reviewer_id,
                decision="VERIFIED", review_note="Independent canonical snapshot review",
            )
        with Session.begin() as db:
            allocations = allocate_and_persist_canonical_snapshot(
                db, snapshot_id=exchange.id, broker_connection_id=connection_id,
                broker_report_reference=report_ref,
            )
        assert len(allocations) == 2

        barrier = threading.Barrier(2)
        results = []
        result_lock = threading.Lock()

        def promote():
            with Session() as db:
                barrier.wait(timeout=10)
                try:
                    rows = promote_verified_canonical_component_allocations(
                        db, snapshot_id=exchange.id, reviewer_user_id=canonical_reviewer_id
                    )
                    db.commit()
                    result = ("success", [str(row.id) for row in rows])
                except Exception as exc:
                    db.rollback()
                    result = ("error", type(exc).__name__, str(exc))
                with result_lock:
                    results.append(result)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(promote), pool.submit(promote)]
            for future in futures:
                future.result(timeout=45)

        assert len(results) == 2 and all(result[0] == "success" for result in results), results
        with Session() as db:
            rows = db.query(BrokerChargeAllocation).filter_by(
                canonical_component_id=exchange.id
            ).order_by(BrokerChargeAllocation.broker_trade_record_id).all()
            assert len(rows) == 2
            assert {row.status for row in rows} == {"RECONCILED"}
            references = {row.reconciliation_reference for row in rows}
            assert len(references) == 1 and None not in references
            assert sum((Decimal(row.allocated_amount) for row in rows), Decimal("0")) == Decimal("307.00")
            assert all(set(result[1]) == {str(row.id) for row in rows} for result in results)

    finally:
        with Session.begin() as db:
            db.execute(text("DELETE FROM broker_charge_allocations WHERE evidence_id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_charge_canonical_source_links WHERE canonical_component_id IN (SELECT id FROM broker_charge_canonical_components WHERE evidence_id = :id)"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_charge_canonical_components WHERE evidence_id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_charge_source_components WHERE evidence_id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_trade_records WHERE broker_connection_id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM broker_orders WHERE broker_connection_id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM broker_charge_evidence WHERE id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_connections WHERE id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM orders WHERE id IN (:order_a, :order_b)"),
                       {"order_a": str(order_ids[0]), "order_b": str(order_ids[1])})
            db.execute(text("DELETE FROM instruments WHERE id = :id"), {"id": str(instrument_id)})
            db.execute(text("DELETE FROM portfolios WHERE id = :id"), {"id": str(portfolio_id)})
            db.execute(text("DELETE FROM users WHERE id IN (:owner, :reviewer, :extractor)"),
                       {"owner": str(owner_id), "reviewer": str(canonical_reviewer_id), "extractor": str(extractor_id)})
        engine.dispose()
