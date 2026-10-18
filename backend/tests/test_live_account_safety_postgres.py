"""PostgreSQL-only concurrency tests for persistent live account safety state.

The normal unit suite is SQLite-backed. The backend workflow runs this module
against PostgreSQL 16 after applying the complete Alembic chain.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import os
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.live_account_safety import LiveAccountSafetyEvent, LiveAccountSafetyState
from app.models.user import User
from app.services.live_account_safety_service import LiveAccountSafetyService
from app.services.live_execution_service import LiveExecutionBlocked


DATABASE_URL = os.getenv("POSTGRES_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="POSTGRES_TEST_DATABASE_URL is only set in the PostgreSQL CI integration step",
)


@pytest.fixture()
def pg_sessions():
    engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=0, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        engine.dispose()


def _create_user(session_factory):
    suffix = uuid4().hex
    with session_factory() as db:
        user = User(
            email=f"pg-safety-{suffix}@example.test",
            password_hash="integration-test-only",
            full_name="PostgreSQL Safety Integration",
            is_admin=False,
        )
        db.add(user)
        db.commit()
        return user.id


def _initialize(session_factory, user_id):
    with session_factory() as db:
        return LiveAccountSafetyService(db).initialize(
            user_id,
            actor_user_id=user_id,
            idempotency_key="initialize",
        )


def test_postgres_duplicate_safety_event_is_counted_once(pg_sessions):
    user_id = _create_user(pg_sessions)
    _initialize(pg_sessions, user_id)
    barrier = Barrier(2)

    def record_duplicate():
        barrier.wait(timeout=10)
        with pg_sessions() as db:
            return LiveAccountSafetyService(db).record_broker_error(
                user_id,
                "HTTP_502",
                "upstream temporarily unavailable",
                threshold=3,
                actor_user_id=user_id,
                idempotency_key="same-broker-error",
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(record_duplicate) for _ in range(2)]
        for future in futures:
            future.result(timeout=20)

    with pg_sessions() as db:
        state = db.query(LiveAccountSafetyState).filter_by(
            user_id=user_id, broker="upstox"
        ).one()
        event_count = db.query(LiveAccountSafetyEvent).filter_by(
            state_id=state.id, idempotency_key="same-broker-error"
        ).count()

    assert state.consecutive_broker_errors == 1
    assert state.circuit_state == "CLOSED"
    assert event_count == 1


def test_postgres_concurrent_distinct_errors_serialize_threshold_trip(pg_sessions):
    user_id = _create_user(pg_sessions)
    _initialize(pg_sessions, user_id)
    barrier = Barrier(2)

    def record_error(key):
        barrier.wait(timeout=10)
        with pg_sessions() as db:
            LiveAccountSafetyService(db).record_broker_error(
                user_id,
                "HTTP_502",
                "upstream temporarily unavailable",
                threshold=2,
                actor_user_id=user_id,
                idempotency_key=key,
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(record_error, "distinct-error-1"),
            pool.submit(record_error, "distinct-error-2"),
        ]
        for future in futures:
            future.result(timeout=20)

    with pg_sessions() as db:
        state = db.query(LiveAccountSafetyState).filter_by(
            user_id=user_id, broker="upstox"
        ).one()
        events = db.query(LiveAccountSafetyEvent).filter_by(state_id=state.id).all()

    assert state.consecutive_broker_errors == 2
    assert state.circuit_state == "OPEN"
    assert state.kill_switch_tripped
    assert sum(event.event_type == "CIRCUIT_OPENED" for event in events) == 1
    assert sum(event.event_type == "BROKER_ERROR" for event in events) == 1


def test_postgres_concurrent_manual_reset_allows_only_one_reset(pg_sessions):
    user_id = _create_user(pg_sessions)
    _initialize(pg_sessions, user_id)
    with pg_sessions() as db:
        service = LiveAccountSafetyService(db)
        service.record_broker_error(
            user_id,
            "TIMEOUT",
            "broker timeout",
            threshold=1,
            actor_user_id=user_id,
            idempotency_key="trip-circuit",
        )
        service.record_broker_success(user_id, idempotency_key="broker-recovered")
        service.record_health_check(
            user_id,
            passed=True,
            reason="broker session and account snapshots verified",
            actor_user_id=user_id,
            idempotency_key="fresh-health-check",
        )

    barrier = Barrier(2)

    def reset(key):
        barrier.wait(timeout=10)
        with pg_sessions() as db:
            try:
                LiveAccountSafetyService(db).manual_reset(
                    user_id,
                    "operator reviewed recovery",
                    actor_user_id=user_id,
                    idempotency_key=key,
                )
                return "reset"
            except LiveExecutionBlocked:
                return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(reset, "manual-reset-1"),
            pool.submit(reset, "manual-reset-2"),
        ]
        results = [future.result(timeout=20) for future in futures]

    assert sorted(results) == ["blocked", "reset"]
    with pg_sessions() as db:
        state = db.query(LiveAccountSafetyState).filter_by(
            user_id=user_id, broker="upstox"
        ).one()
        reset_count = db.query(LiveAccountSafetyEvent).filter_by(
            state_id=state.id, event_type="MANUAL_RESET"
        ).count()

    assert not state.kill_switch_tripped
    assert state.circuit_state == "CLOSED"
    assert state.consecutive_broker_errors == 0
    assert reset_count == 1
