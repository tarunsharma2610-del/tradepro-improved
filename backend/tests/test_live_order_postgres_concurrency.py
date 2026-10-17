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
            session.add_all([user, portfolio, connection])
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
