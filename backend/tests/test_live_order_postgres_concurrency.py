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
                    price=Decimal("101.25"),
                    side="BUY",
                    instrument_token=instrument.instrument_key,
                    exchange_timestamp=now.isoformat(),
                ),
            ]
            session.add_all(records)
            session.commit()

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
