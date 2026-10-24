from datetime import datetime, timezone
import os
import threading
from decimal import Decimal
from uuid import uuid4

import hashlib

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models  # noqa: F401
from app.models.user import User

from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.instrument import Instrument
from app.models.broker_trade_record import BrokerTradeRecord
from app.services.broker_charge_allocation_persistence_service import (
    allocate_and_persist_component,
)


def _trade(db, connection_id, trade_id):
    trade = BrokerTradeRecord(
        broker_connection_id=connection_id,
        broker_order_ref_id=uuid4(),
        broker_trade_id=trade_id,
        quantity=1,
        price=Decimal("100.0000"),
        side="BUY",
        instrument_token="NSE_EQ|TEST",
        exchange_timestamp="2026-10-21T10:00:00+05:30",
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade


def _allocate(db, user, connection, evidence, trades, weights=None, total="1.00", basis="EXPLICIT_REVIEWED"):
    return allocate_and_persist_component(
        db,
        evidence_id=evidence.id,
        broker_connection_id=connection.id,
        broker_report_reference="CN-2026-10-21-001",
        reviewer_user_id=user.id,
        source_component_total=total,
        charge_component="brokerage",
        fill_weights=weights or {trade.id: 1 for trade in trades},
        allocation_basis=basis,
    )


def test_persists_allocations_and_reconciles_source_total(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [_trade(db, connection.id, "trade-success-a"), _trade(db, connection.id, "trade-success-b")]

    rows = _allocate(db, user, connection, evidence, trades)

    assert len(rows) == 2
    assert sum((Decimal(row.allocated_amount) for row in rows), Decimal("0")) == Decimal("1.00")
    # Arithmetic totals match, but no independent source-document parser or
    # component-total verifier ran, so this service must not claim reconciliation.
    assert {row.status for row in rows} == {"PENDING_RECONCILIATION"}
    assert {row.reconciliation_reference for row in rows} == {None}
    assert db.query(BrokerChargeAllocation).count() == 2


def test_identical_replay_returns_existing_rows_without_duplicates(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [_trade(db, connection.id, "trade-replay-a"), _trade(db, connection.id, "trade-replay-b")]

    first = _allocate(db, user, connection, evidence, trades)
    second = _allocate(db, user, connection, evidence, trades)

    assert {row.id for row in first} == {row.id for row in second}
    assert db.query(BrokerChargeAllocation).count() == 2


def test_conflicting_replay_with_changed_total_fails_closed(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [_trade(db, connection.id, "trade-conflict-a"), _trade(db, connection.id, "trade-conflict-b")]
    _allocate(db, user, connection, evidence, trades, total="1.00")

    with pytest.raises(ValueError, match="Conflicting replay"):
        _allocate(db, user, connection, evidence, trades, total="1.10")


def test_rejects_fill_from_different_broker_connection(reviewed_evidence, make_user):
    db, user, connection, evidence = reviewed_evidence
    other_user = make_user(email="other@example.com")
    other_connection = BrokerConnection(
        user_id=other_user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key-2",
        api_secret_encrypted="encrypted-secret-2",
        redirect_uri="https://example.invalid/callback",
        is_connected=True,
    )
    db.add(other_connection)
    db.commit()
    db.refresh(other_connection)
    other_trade = _trade(db, other_connection.id, "trade-other-connection")

    with pytest.raises(ValueError, match="evidence connection"):
        _allocate(
            db, user, connection, evidence, [other_trade],
            weights={other_trade.id: 1},
        )
    assert db.query(BrokerChargeAllocation).count() == 0


def test_conflicting_fill_set_is_rejected_without_partial_rows(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [_trade(db, connection.id, "trade-set-a"), _trade(db, connection.id, "trade-set-b")]
    _allocate(db, user, connection, evidence, trades)

    with pytest.raises(ValueError, match="different fill set"):
        _allocate(db, user, connection, evidence, trades[:1])

    assert db.query(BrokerChargeAllocation).count() == 2


@pytest.fixture
def reviewed_evidence(db_session, make_user):
    """Create a persisted, explicitly reviewed contract-note evidence record."""
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
    db_session.commit()
    db_session.refresh(connection)

    evidence = BrokerChargeEvidence(
        broker_connection_id=connection.id,
        source_kind="CONTRACT_NOTE",
        broker_report_reference="CN-2026-10-21-001",
        source_filename="contract-note.pdf",
        source_sha256=hashlib.sha256(b"test contract note").hexdigest(),
        byte_size=len(b"test contract note"),
        status="REVIEWED",
        reviewed_at=datetime.now(timezone.utc),
        reviewed_by_user_id=user.id,
        review_note="Reviewed in test fixture",
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)
    return db_session, user, connection, evidence


def test_outer_transaction_rollback_removes_all_new_allocations(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [
        _trade(db, connection.id, "trade-rollback-a"),
        _trade(db, connection.id, "trade-rollback-b"),
    ]

    # The shared fixture commits setup rows. Start a fresh, explicit outer
    # transaction before the service opens its nested savepoint; otherwise
    # SQLite can release a SAVEPOINT without a real outer BEGIN.
    db.rollback()
    outer = db.begin()
    try:
        rows = _allocate(db, user, connection, evidence, trades)
        assert len(rows) == 2
        assert db.query(BrokerChargeAllocation).count() == 2
        outer.rollback()
    finally:
        if outer.is_active:
            outer.rollback()
    db.expire_all()

    assert db.query(BrokerChargeAllocation).count() == 0


def test_conflicting_replay_with_changed_basis_fails_closed(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [_trade(db, connection.id, "trade-basis-a"), _trade(db, connection.id, "trade-basis-b")]
    _allocate(db, user, connection, evidence, trades)

    with pytest.raises(ValueError, match="Conflicting replay"):
        _allocate(
            db, user, connection, evidence, trades,
            weights={trade.id: 1 for trade in trades},
            basis="QUANTITY",
        )


def test_reconciled_rows_cannot_be_rewritten_through_allocation_persistence(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [_trade(db, connection.id, "trade-reconciled-a"), _trade(db, connection.id, "trade-reconciled-b")]
    rows = _allocate(db, user, connection, evidence, trades)
    for row in rows:
        row.status = "RECONCILED"
        row.reconciliation_reference = "verified-source-reference"
    db.commit()

    with pytest.raises(ValueError, match="already reconciled"):
        _allocate(db, user, connection, evidence, trades)

    db.refresh(rows[0])
    assert rows[0].status == "RECONCILED"
    assert rows[0].reconciliation_reference == "verified-source-reference"
    assert db.query(BrokerChargeAllocation).count() == 2

@pytest.mark.parametrize(
    "component",
    ["ipft", "clearing_charges", "other_charges", "demat_transaction"],
)
def test_upstox_charge_components_not_yet_supported_fail_closed(reviewed_evidence, component):
    """Do not silently drop Upstox API charge components from per-fill accounting."""
    db, user, connection, evidence = reviewed_evidence

    with pytest.raises(ValueError, match="Unsupported broker charge component"):
        allocate_and_persist_component(
            db,
            evidence_id=evidence.id,
            broker_connection_id=connection.id,
            broker_report_reference="CN-2026-10-21-001",
            reviewer_user_id=user.id,
            source_component_total="1.00",
            charge_component=component,
            fill_weights={},
            allocation_basis="EXPLICIT_REVIEWED",
        )

    assert db.query(BrokerChargeAllocation).count() == 0



def test_postgres_concurrent_disjoint_fill_sets_serialize_on_evidence_lock():
    """PostgreSQL integration: disjoint concurrent fill sets cannot create split ledgers."""
    database_url = os.environ.get("TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL locking integration test.")

    schema = "phase3_alloc_" + uuid4().hex
    admin_engine = create_engine(database_url, pool_pre_ping=True)
    engine = None
    try:
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(
            database_url,
            connect_args={"options": f"-csearch_path={schema}"},
            pool_size=4,
            max_overflow=0,
            pool_pre_ping=True,
        )
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
        setup = SessionLocal()
        try:
            user = User(email=f"{schema}@example.invalid", password_hash="test-only", full_name="PG Allocation Test")
            setup.add(user)
            setup.flush()
            connection = BrokerConnection(
                user_id=user.id,
                broker="upstox",
                api_key_encrypted="test-key",
                api_secret_encrypted="test-secret",
                redirect_uri="https://example.invalid/callback",
                is_connected=True,
            )
            setup.add(connection)
            setup.flush()
            evidence = BrokerChargeEvidence(
                broker_connection_id=connection.id,
                source_kind="CONTRACT_NOTE",
                broker_report_reference="CN-PG-CONCURRENT-001",
                source_filename="synthetic-contract-note.pdf",
                source_sha256=hashlib.sha256(b"synthetic postgres concurrency evidence").hexdigest(),
                byte_size=len(b"synthetic postgres concurrency evidence"),
                status="REVIEWED",
                reviewed_at=datetime.now(timezone.utc),
                reviewed_by_user_id=user.id,
                review_note="Synthetic integration fixture",
            )
            setup.add(evidence)
            setup.flush()

            portfolio = Portfolio(
                user_id=user.id,
                name="PG allocation concurrency fixture",
                virtual_capital=Decimal("1000.00"),
                cash_balance=Decimal("1000.00"),
            )
            instrument = Instrument(
                instrument_key="NSE_EQ|PGTEST",
                exchange="NSE",
                segment="NSE_EQ",
                instrument_type="EQUITY",
                trading_symbol="PGTEST",
                name="Postgres test instrument",
            )
            setup.add_all([portfolio, instrument])
            setup.flush()
            order = Order(
                portfolio_id=portfolio.id,
                instrument_id=instrument.id,
                side="BUY",
                order_type="LIMIT",
                segment="EQUITY_DELIVERY",
                quantity=2,
                limit_price=Decimal("100.0000"),
                status="FILLED",
                trading_mode="PAPER",
                execution_reason="MANUAL",
                placed_at=datetime.now(timezone.utc),
                filled_at=datetime.now(timezone.utc),
            )
            setup.add(order)
            setup.flush()

            trades = []
            for index, trade_id in enumerate(("pg-concurrent-fill-a", "pg-concurrent-fill-b"), start=1):
                broker_order = BrokerOrder(
                    broker_connection_id=connection.id,
                    order_id=order.id,
                    broker_name="upstox",
                    broker_order_id=f"PG-ORDER-{index}",
                    requested_quantity=1,
                    filled_quantity=1,
                    status="COMPLETE",
                )
                setup.add(broker_order)
                setup.flush()
                trade = BrokerTradeRecord(
                    broker_connection_id=connection.id,
                    broker_order_ref_id=broker_order.id,
                    broker_trade_id=trade_id,
                    quantity=1,
                    price=Decimal("100.0000"),
                    side="BUY",
                    instrument_token="NSE_EQ|PGTEST",
                    exchange_timestamp="2026-10-24T10:00:00+05:30",
                )
                setup.add(trade)
                trades.append(trade)
            setup.commit()
            evidence_id, connection_id, reviewer_id = evidence.id, connection.id, user.id
            fill_ids = [trade.id for trade in trades]
        finally:
            setup.close()

        barrier = threading.Barrier(2)
        outcomes = []
        outcomes_lock = threading.Lock()

        def allocate(fill_id):
            session = SessionLocal()
            try:
                barrier.wait(timeout=10)
                try:
                    allocate_and_persist_component(
                        session,
                        evidence_id=evidence_id,
                        broker_connection_id=connection_id,
                        broker_report_reference="CN-PG-CONCURRENT-001",
                        reviewer_user_id=reviewer_id,
                        source_component_total="1.00",
                        charge_component="brokerage",
                        fill_weights={fill_id: 1},
                        allocation_basis="EXPLICIT_REVIEWED",
                    )
                    session.commit()
                    outcome = "committed"
                except ValueError:
                    session.rollback()
                    outcome = "rejected"
                with outcomes_lock:
                    outcomes.append(outcome)
            except Exception as exc:
                session.rollback()
                with outcomes_lock:
                    outcomes.append(f"unexpected:{type(exc).__name__}:{exc}")
            finally:
                session.close()

        workers = [threading.Thread(target=allocate, args=(fill_id,)) for fill_id in fill_ids]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=20)

        assert all(not worker.is_alive() for worker in workers), "PostgreSQL allocation workers deadlocked."
        assert sorted(outcomes) == ["committed", "rejected"], outcomes
        verify = SessionLocal()
        try:
            rows = verify.query(BrokerChargeAllocation).filter_by(
                evidence_id=evidence_id, charge_component="brokerage"
            ).all()
            assert len(rows) == 1
            assert rows[0].broker_trade_record_id in set(fill_ids)
            assert rows[0].status == "PENDING_RECONCILIATION"
        finally:
            verify.close()
    finally:
        if engine is not None:
            engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin_engine.dispose()
