"""PostgreSQL 16 SQLAlchemy pool exhaustion and recovery regression.

Uses a deliberately bounded test-only QueuePool. Production engine settings are
not changed. The test proves checkout timeout, waiter recovery after a returned
connection, and zero checked-out connections after cleanup.
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError


TEST_POSTGRES_URL = os.getenv("TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not TEST_POSTGRES_URL,
    reason="requires dedicated PostgreSQL 16 test database",
)


def test_postgres_pool_exhaustion_times_out_and_recovers_waiting_work():
    engine = create_engine(
        TEST_POSTGRES_URL,
        pool_size=2,
        max_overflow=0,
        pool_timeout=0.25,
        pool_pre_ping=True,
    )
    first = second = None
    try:
        first = engine.connect()
        second = engine.connect()
        assert first.execute(text("SELECT 1")).scalar_one() == 1
        assert second.execute(text("SELECT 1")).scalar_one() == 1
        assert engine.pool.checkedout() == 2

        # A third checkout is bounded by the test-only pool timeout.
        with pytest.raises(SQLAlchemyTimeoutError):
            engine.connect()
        assert engine.pool.checkedout() == 2

        attempting_checkout = threading.Event()

        def waiting_database_work():
            attempting_checkout.set()
            with engine.connect() as connection:
                return connection.execute(text("SELECT 1")).scalar_one()

        with ThreadPoolExecutor(max_workers=1) as executor:
            waiting = executor.submit(waiting_database_work)
            assert attempting_checkout.wait(timeout=1)
            assert not waiting.done()

            # Returning one checked-out connection must unblock the waiter.
            first.close()
            first = None
            assert waiting.result(timeout=2) == 1

        assert engine.pool.checkedout() == 1
        second.close()
        second = None
        assert engine.pool.checkedout() == 0

        # The pool remains usable after saturation and waiter recovery.
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
        assert engine.pool.checkedout() == 0
    finally:
        if first is not None:
            first.close()
        if second is not None:
            second.close()
        assert engine.pool.checkedout() == 0
        engine.dispose()
