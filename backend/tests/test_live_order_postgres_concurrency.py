"""PostgreSQL-only concurrency coverage for durable live-order idempotency."""
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_POSTGRES_URL"),
    reason="TEST_POSTGRES_URL is only configured in the PostgreSQL CI job",
)


def test_simultaneous_same_key_requests_create_one_intent_and_outbox():
    from app.models import __dict__ as _registered_models  # noqa: F401
    from app.core.database import Base
    from app.models.broker_connection import BrokerConnection
    from app.models.live_order_records import LiveOrderEvent, LiveOrderIntent, LiveOrderOutbox
    from app.models.portfolio import Portfolio
    from app.models.user import User
    from app.repositories.live_order_repository import LiveOrderRepository

    engine = create_engine(os.environ["TEST_POSTGRES_URL"], pool_pre_ping=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        owner_id = uuid.uuid4()
        portfolio_id = uuid.uuid4()
        connection_id = uuid.uuid4()
        with SessionLocal() as session:
            user = User(
                id=owner_id,
                email=f"concurrency-{owner_id}@example.invalid",
                password_hash="test-only",
                full_name="Concurrency Test",
            )
            portfolio = Portfolio(
                id=portfolio_id,
                user_id=owner_id,
                name="Concurrency test",
                virtual_capital=100000,
                cash_balance=100000,
                is_active=True,
            )
            connection = BrokerConnection(
                id=connection_id,
                user_id=owner_id,
                broker="upstox",
                api_key_encrypted="test-only",
                api_secret_encrypted="test-only",
                redirect_uri="https://example.invalid/callback",
                is_connected=False,
            )
            session.add(user)
            session.commit()
            session.add_all([portfolio, connection])
            session.commit()

        args = {
            "user_id": owner_id,
            "portfolio_id": portfolio_id,
            "broker_connection_id": connection_id,
            "client_idempotency_key": f"simultaneous-{uuid.uuid4()}",
            "order_snapshot": {
                "instrument_key": "NSE_EQ|TEST",
                "side": "BUY",
                "order_type": "LIMIT",
                "quantity": 1,
                "limit_price": "100.00",
                "product": "D",
            },
            "correlation_id": "postgres-concurrency-test",
        }
        barrier = threading.Barrier(2)

        def create_request():
            with SessionLocal() as session:
                repository = LiveOrderRepository(session)
                original_lookup = repository.get_by_idempotency_key
                first_empty_lookup = {"done": False}

                def synchronized_lookup(*lookup_args):
                    existing = original_lookup(*lookup_args)
                    if existing is None and not first_empty_lookup["done"]:
                        first_empty_lookup["done"] = True
                        barrier.wait(timeout=15)
                    return existing

                repository.get_by_idempotency_key = synchronized_lookup
                intent, created = repository.create_or_get_intent(**args)
                return intent.id, created

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: create_request(), range(2)))

        assert sum(created for _, created in results) == 1
        assert results[0][0] == results[1][0]
        with SessionLocal() as session:
            assert session.query(LiveOrderIntent).count() == 1
            assert session.query(LiveOrderOutbox).count() == 1
            assert session.query(LiveOrderEvent).count() == 1
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()



def test_simultaneous_reconciliation_lease_claims_allow_only_one_worker():
    from datetime import datetime, timezone

    from app.models import __dict__ as _registered_models  # noqa: F401
    from app.core.database import Base
    from app.models.broker_connection import BrokerConnection
    from app.models.live_order_records import LiveReconciliationLease
    from app.models.user import User
    from app.repositories.live_reconciliation_lease_repository import LiveReconciliationLeaseRepository

    engine = create_engine(os.environ["TEST_POSTGRES_URL"], pool_pre_ping=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        owner_id = uuid.uuid4()
        connection_id = uuid.uuid4()
        with SessionLocal() as session:
            user = User(
                id=owner_id,
                email=f"lease-concurrency-{owner_id}@example.invalid",
                password_hash="test-only",
                full_name="Lease Concurrency Test",
            )
            session.add(user)
            session.commit()
            session.add(BrokerConnection(
                id=connection_id,
                user_id=owner_id,
                broker="upstox",
                api_key_encrypted="test-only",
                api_secret_encrypted="test-only",
                redirect_uri="https://example.invalid/callback",
                is_connected=False,
            ))
            session.commit()

        now = datetime.now(timezone.utc)

        def claim():
            with SessionLocal() as session:
                return LiveReconciliationLeaseRepository(session).claim(
                    user_id=owner_id,
                    broker_connection_id=connection_id,
                    now=now,
                    lease_seconds=120,
                )

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: claim(), range(2)))

        assert sum(token is not None for token in results) == 1
        winner = next(token for token in results if token is not None)
        with SessionLocal() as session:
            lease = session.query(LiveReconciliationLease).filter_by(
                broker_connection_id=connection_id
            ).one()
            assert lease.lease_token == winner
            assert lease.generation == 1
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()



def test_concurrent_live_fill_promotions_serialize_on_parent_and_child_rows():
    """Two distinct confirmed fills must not race live-position accounting."""
    from datetime import date, datetime, timezone
    from decimal import Decimal

    from app.core.database import Base
    from app.models.broker_connection import BrokerConnection
    from app.models.broker_charge_evidence import BrokerChargeEvidence
    from app.models.broker_order import BrokerOrder
    from app.models.broker_trade_record import BrokerTradeRecord
    from app.models.execution import Execution
    from app.models.instrument import Instrument
    from app.models.live_position import LivePosition
    from app.models.order import Order
    from app.models.portfolio import Portfolio
    from app.models.user import User
    from app.services.live_fill_accounting_service import (
        LiveFillAccountingService,
        LiveFillChargeBreakdown,
    )

    engine = create_engine(os.environ["TEST_POSTGRES_URL"], pool_pre_ping=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        owner_id = uuid.uuid4()
        portfolio_id = uuid.uuid4()
        connection_id = uuid.uuid4()
        instrument_id = uuid.uuid4()
        order_id = uuid.uuid4()
        child_id = uuid.uuid4()
        trade_ids = [uuid.uuid4(), uuid.uuid4()]
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            session.add(User(
                id=owner_id,
                email=f"fill-lock-{owner_id}@example.invalid",
                password_hash="test-only",
                full_name="Fill Lock Test",
            ))
            session.commit()
            portfolio = Portfolio(
                id=portfolio_id,
                user_id=owner_id,
                name="Live fill lock test",
                virtual_capital=Decimal("100000"),
                cash_balance=Decimal("100000"),
                is_active=True,
            )
            connection = BrokerConnection(
                id=connection_id,
                user_id=owner_id,
                broker="upstox",
                api_key_encrypted="test-only",
                api_secret_encrypted="test-only",
                redirect_uri="https://example.invalid/callback",
                is_connected=True,
            )
            instrument = Instrument(
                id=instrument_id,
                instrument_key="NSE_EQ|FILL-LOCK-TEST",
                exchange="NSE",
                segment="NSE_EQ",
                instrument_type="EQUITY",
                trading_symbol="FILL-LOCK-TEST",
                name="Fill lock test",
            )
            session.add_all([portfolio, connection, instrument])
            session.commit()
            order = Order(
                id=order_id,
                portfolio_id=portfolio_id,
                instrument_id=instrument_id,
                side="BUY",
                order_type="MARKET",
                segment="EQUITY_DELIVERY",
                quantity=2,
                status="PENDING",
                trading_mode="LIVE",
                execution_reason="MANUAL",
                placed_at=now,
            )
            session.add(order)
            session.commit()
            child = BrokerOrder(
                id=child_id,
                broker_connection_id=connection_id,
                order_id=order_id,
                broker_name="upstox",
                broker_order_id=f"broker-{uuid.uuid4()}",
                requested_quantity=2,
                filled_quantity=2,
                status="FILLED",
            )
            session.add(child)
            session.commit()
            records = [
                BrokerTradeRecord(
                    id=trade_ids[0],
                    broker_connection_id=connection_id,
                    broker_order_ref_id=child_id,
                    broker_trade_id=f"trade-{trade_ids[0]}",
                    quantity=1,
                    price=Decimal("100.25"),
                    side="BUY",
                    instrument_token=instrument.instrument_key,
                    exchange_timestamp=now.isoformat(),
                ),
                BrokerTradeRecord(
                    id=trade_ids[1],
                    broker_connection_id=connection_id,
                    broker_order_ref_id=child_id,
                    broker_trade_id=f"trade-{trade_ids[1]}",
                    quantity=1,
                    price=Decimal("100.25"),
                    side="BUY",
                    instrument_token=instrument.instrument_key,
                    exchange_timestamp=now.isoformat(),
                ),
            ]
            session.add_all(records)
            for trade_id in trade_ids:
                session.add(BrokerChargeEvidence(
                    broker_connection_id=connection_id,
                    source_kind="CONTRACT_NOTE",
                    broker_report_reference=f"contract-note-{trade_id}",
                    report_date=now.date(),
                    segment="NSE",
                    source_filename="contract-note.pdf",
                    source_sha256=trade_id.hex + "0" * 32,
                    byte_size=1,
                    parser_version="phase3-test",
                    status="REVIEWED",
                    reviewed_at=now,
                    reviewed_by_user_id=owner_id,
                ))
            session.commit()

        evidence_ids = {}
        with SessionLocal() as session:
            for trade_id in trade_ids:
                evidence_ids[trade_id] = session.query(BrokerChargeEvidence.id).filter_by(
                    broker_connection_id=connection_id,
                    broker_report_reference=f"contract-note-{trade_id}",
                ).scalar()

        barrier = threading.Barrier(2)

        def promote(trade_id):
            charges = LiveFillChargeBreakdown(
                brokerage=Decimal("20.00"),
                stt=Decimal("0.20"),
                exchange_charges=Decimal("0.01"),
                sebi_charges=Decimal("0.01"),
                stamp_duty=Decimal("0.03"),
                gst=Decimal("3.61"),
                total_charges=Decimal("23.86"),
                source="BROKER_REPORTED",
                reference=f"contract-note-{trade_id}",
            )
            with SessionLocal() as session:
                barrier.wait(timeout=10)
                return LiveFillAccountingService(session).promote_trade(
                    owner_id, trade_id, charges
                )

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(promote, trade_id) for trade_id in trade_ids]
            results = [future.result(timeout=20) for future in futures]

        assert all(result.inserted for result in results)
        with SessionLocal() as session:
            position = session.query(LivePosition).filter_by(
                broker_connection_id=connection_id,
                instrument_id=instrument_id,
            ).one()
            executions = session.query(Execution).filter_by(
                broker_connection_id=connection_id,
                broker_order_ref_id=child_id,
            ).all()
            assert position.quantity == 2
            assert len(executions) == 2
            assert sum(item.quantity for item in executions) == 2
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()



def test_concurrent_child_orders_cannot_overfill_one_local_order():
    """Parent-order locking serializes separate children against one quantity cap."""
    from datetime import datetime, timezone
    from decimal import Decimal

    from app.core.database import Base
    from app.models.broker_connection import BrokerConnection
    from app.models.broker_order import BrokerOrder
    from app.models.broker_trade_record import BrokerTradeRecord
    from app.models.execution import Execution
    from app.models.instrument import Instrument
    from app.models.live_position import LivePosition
    from app.models.order import Order
    from app.models.portfolio import Portfolio
    from app.models.user import User
    from app.services.live_fill_accounting_service import (
        LiveFillAccountingService,
        LiveFillChargeBreakdown,
    )

    engine = create_engine(os.environ["TEST_POSTGRES_URL"], pool_pre_ping=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        owner_id, portfolio_id, connection_id, instrument_id, order_id = (
            uuid.uuid4() for _ in range(5)
        )
        child_ids = [uuid.uuid4(), uuid.uuid4()]
        trade_ids = [uuid.uuid4(), uuid.uuid4()]
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            session.add(User(
                id=owner_id,
                email=f"cross-child-overfill-{owner_id}@example.invalid",
                password_hash="test-only",
                full_name="Cross Child Overfill Test",
            ))
            session.commit()
            portfolio = Portfolio(
                id=portfolio_id, user_id=owner_id, name="Cross child overfill",
                virtual_capital=Decimal("100000"), cash_balance=Decimal("100000"), is_active=True,
            )
            connection = BrokerConnection(
                id=connection_id, user_id=owner_id, broker="upstox",
                api_key_encrypted="test-only", api_secret_encrypted="test-only",
                redirect_uri="https://example.invalid/callback", is_connected=True,
            )
            instrument = Instrument(
                id=instrument_id, instrument_key="NSE_EQ|CROSS-CHILD-OVERFILL",
                exchange="NSE", segment="NSE_EQ", instrument_type="EQUITY",
                trading_symbol="CROSS-CHILD-OVERFILL", name="Cross child overfill test",
            )
            session.add_all([portfolio, connection, instrument])
            session.commit()
            order = Order(
                id=order_id, portfolio_id=portfolio_id, instrument_id=instrument_id,
                side="BUY", order_type="MARKET", segment="EQUITY_DELIVERY",
                quantity=5, status="PENDING", trading_mode="LIVE",
                execution_reason="MANUAL", placed_at=now,
            )
            session.add(order)
            session.commit()
            children = [
                BrokerOrder(
                    id=child_ids[index], broker_connection_id=connection_id, order_id=order_id,
                    broker_name="upstox", broker_order_id=f"cross-child-{index}-{uuid.uuid4()}",
                    requested_quantity=3, filled_quantity=3, status="FILLED",
                )
                for index in range(2)
            ]
            session.add_all(children)
            session.commit()
            records = [
                BrokerTradeRecord(
                    id=trade_ids[index], broker_connection_id=connection_id,
                    broker_order_ref_id=child_ids[index], broker_trade_id=f"cross-trade-{trade_ids[index]}",
                    quantity=3, price=Decimal("100.00"), side="BUY",
                    instrument_token=instrument.instrument_key, exchange_timestamp=now.isoformat(),
                )
                for index in range(2)
            ]
            session.add_all(records)
            session.commit()

        barrier = threading.Barrier(2)

        def promote(trade_id):
            charges = LiveFillChargeBreakdown(
                brokerage=Decimal("20.00"), stt=Decimal("0.20"),
                exchange_charges=Decimal("0.01"), sebi_charges=Decimal("0.01"),
                stamp_duty=Decimal("0.03"), gst=Decimal("3.61"),
                total_charges=Decimal("23.86"), source="BROKER_REPORTED",
                reference=f"contract-note-{trade_id}",
            )
            with SessionLocal() as session:
                barrier.wait(timeout=10)
                try:
                    result = LiveFillAccountingService(session).promote_trade(
                        owner_id, trade_id, charges
                    )
                    return "inserted" if result.inserted else "replayed"
                except ValueError as exc:
                    if "local order quantity" not in str(exc):
                        raise
                    return "rejected"

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(promote, trade_ids))

        assert sorted(results) == ["inserted", "rejected"]
        with SessionLocal() as session:
            executions = session.query(Execution).filter_by(order_id=order_id).all()
            position = session.query(LivePosition).filter_by(
                broker_connection_id=connection_id, instrument_id=instrument_id,
            ).one()
            assert len(executions) == 1
            assert sum(item.quantity for item in executions) == 3
            assert position.quantity == 3
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()



def test_orphan_recovery_and_expired_lease_claim_are_serialized():
    """Recovery and a new lease claimant must not both treat the run as theirs."""
    from datetime import datetime, timedelta, timezone

    from app.core.database import Base
    from app.models.broker_connection import BrokerConnection
    from app.models.live_order_records import LiveReconciliationLease, LiveReconciliationRun
    from app.models.user import User
    from app.repositories.live_order_reconciliation_run_repository import LiveReconciliationRunRepository
    from app.repositories.live_reconciliation_lease_repository import LiveReconciliationLeaseRepository

    engine = create_engine(os.environ["TEST_POSTGRES_URL"], pool_pre_ping=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        owner_id = uuid.uuid4()
        connection_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        started_at = now - timedelta(hours=1)
        with SessionLocal() as session:
            session.add(User(
                id=owner_id,
                email=f"orphan-race-{owner_id}@example.invalid",
                password_hash="test-only",
                full_name="Orphan Race Test",
            ))
            session.commit()
            session.add(BrokerConnection(
                id=connection_id,
                user_id=owner_id,
                broker="upstox",
                api_key_encrypted="test-only",
                api_secret_encrypted="test-only",
                redirect_uri="https://example.invalid/callback",
                is_connected=False,
            ))
            session.commit()
            session.add_all([
                LiveReconciliationLease(
                    user_id=owner_id,
                    broker_connection_id=connection_id,
                    lease_token=uuid.uuid4(),
                    claimed_until=now - timedelta(minutes=10),
                    generation=1,
                    last_started_at=started_at,
                    last_error_code=None,
                ),
                LiveReconciliationRun(
                    user_id=owner_id,
                    broker_connection_id=connection_id,
                    status="RUNNING",
                    started_at=started_at,
                    summary={
                        "orders_seen": 0, "orders_matched": 0, "orders_unmatched": 0,
                        "trades_seen": 0, "fills_inserted": 0, "duplicate_fills": 0,
                        "conflicts": 0,
                    },
                ),
            ])
            session.commit()

        barrier = threading.Barrier(2)

        def recover():
            with SessionLocal() as session:
                barrier.wait(timeout=10)
                return LiveReconciliationRunRepository(session).fail_orphaned_runs(
                    user_id=owner_id,
                    broker_connection_id=connection_id,
                    stale_before=now - timedelta(minutes=5),
                    now=now,
                )

        def claim():
            with SessionLocal() as session:
                barrier.wait(timeout=10)
                return LiveReconciliationLeaseRepository(session).claim(
                    user_id=owner_id,
                    broker_connection_id=connection_id,
                    now=now,
                    lease_seconds=300,
                )

        with ThreadPoolExecutor(max_workers=2) as pool:
            recovery_future = pool.submit(recover)
            claim_future = pool.submit(claim)
            recovered_count = recovery_future.result(timeout=20)
            token = claim_future.result(timeout=20)

        assert recovered_count in (0, 1)
        assert token is not None
        with SessionLocal() as session:
            run = session.query(LiveReconciliationRun).filter_by(
                user_id=owner_id, broker_connection_id=connection_id
            ).one()
            lease = session.query(LiveReconciliationLease).filter_by(
                user_id=owner_id, broker_connection_id=connection_id
            ).one()
            assert lease.lease_token == token
            if run.status == "FAILED":
                assert run.error_code == "WORKER_INTERRUPTED"
                assert recovered_count == 1
            else:
                assert run.status == "RUNNING"
                assert recovered_count == 0
                assert lease.claimed_until > now
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
