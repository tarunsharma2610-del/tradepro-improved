"""PostgreSQL-only race test for durable charge allocation serialization.

This test is skipped on local runs without TEST_POSTGRES_URL. CI provisions a
PostgreSQL service and sets that variable, so the race is exercised there.
"""
import hashlib
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

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
from app.services.live_fill_accounting_service import (
    LiveFillAccountingService,
    LiveFillChargeBreakdown,
)


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
    """Verification racing promotion sees a complete pending or reconciled ledger."""
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

        barrier = threading.Barrier(2)
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

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(verify), pool.submit(promote)]
            for future in futures:
                future.result(timeout=45)

        errors = [result for result in results if result[0] == "error"]
        assert not errors, results
        verification_results = [result[1] for result in results if result[0] == "verify"]
        assert verification_results in (
            ["VERIFIED_PENDING_PROMOTION"], ["ALREADY_RECONCILED"]
        ), results
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
                component = BrokerChargeSourceComponent(
                    evidence_id=evidence_id, source_sha256=digest,
                    component_name=component_name, revision=1, source_amount=amount,
                    currency="INR", extraction_method="MANUAL_TRANSCRIPTION",
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
                    extracted_by_user_id=extractor_id, status="VERIFIED",
                    reviewed_by_user_id=reviewer_id, reviewed_at=datetime.now(timezone.utc),
                    review_note="Independent synthetic review",
                )
                db.add(component)
                db.flush()
                db.add(BrokerChargeAllocation(
                    evidence_id=evidence_id, broker_connection_id=connection_id,
                    broker_trade_record_id=trade_id, charge_component=component_name,
                    source_component_total=amount, allocated_amount=amount, currency="INR",
                    allocation_basis="EXPLICIT_REVIEWED", method_version="largest-remainder-v1",
                    status="RECONCILED",
                    reconciliation_reference=(
                        f"charge-component:{component.id}:sha256:{digest}:fills:{manifest_hash}"
                    ),
                ))

        barrier = threading.Barrier(2)
        outcomes = []
        outcomes_lock = threading.Lock()

        def verify_ledger():
            with Session() as db:
                barrier.wait(timeout=10)
                try:
                    component = db.query(BrokerChargeSourceComponent).filter_by(
                        evidence_id=evidence_id, component_name="brokerage"
                    ).one()
                    result = verify_component_allocation_ledger(
                        db, evidence_id=evidence_id, source_component_id=component.id
                    )
                    db.commit()
                    outcome = ("verify", result["status"])
                except Exception as exc:
                    db.rollback()
                    outcome = ("error", "verify", type(exc).__name__, str(exc))
                with outcomes_lock:
                    outcomes.append(outcome)

        def promote_fill():
            with Session() as db:
                barrier.wait(timeout=10)
                try:
                    result = LiveFillAccountingService(db).promote_trade(
                        owner_id,
                        trade_id,
                        LiveFillChargeBreakdown(
                            **amounts, total_charges=sum(amounts.values(), Decimal("0.00")),
                            source="BROKER_REPORTED", reference=report_ref,
                            evidence_id=evidence_id, reviewer_user_id=reviewer_id,
                        ),
                    )
                    outcome = ("promote", result.inserted, result.execution_id)
                except Exception as exc:
                    db.rollback()
                    outcome = ("error", "promote", type(exc).__name__, str(exc))
                with outcomes_lock:
                    outcomes.append(outcome)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(verify_ledger), pool.submit(promote_fill)]
            for future in futures:
                future.result(timeout=60)

        errors = [item for item in outcomes if item[0] == "error"]
        assert not errors, outcomes
        assert ("verify", "ALREADY_RECONCILED") in outcomes, outcomes
        promotions = [item for item in outcomes if item[0] == "promote"]
        assert len(promotions) == 1 and promotions[0][1] is True, outcomes
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
            db.execute(text("DELETE FROM broker_charge_source_components WHERE evidence_id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_trade_records WHERE broker_connection_id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM broker_orders WHERE broker_connection_id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM broker_charge_evidence WHERE id = :id"), {"id": str(evidence_id)})
            db.execute(text("DELETE FROM broker_connections WHERE id = :id"), {"id": str(connection_id)})
            db.execute(text("DELETE FROM orders WHERE id = :id"), {"id": str(order_id)})
            db.execute(text("DELETE FROM instruments WHERE id = :id"), {"id": str(instrument_id)})
            db.execute(text("DELETE FROM portfolios WHERE id = :id"), {"id": str(portfolio_id)})
            db.execute(text("DELETE FROM users WHERE id IN (:owner, :reviewer, :extractor)"),
                        {"owner": str(owner_id), "reviewer": str(reviewer_id), "extractor": str(extractor_id)})
        engine.dispose()
