"""PostgreSQL concurrency tests for live order intent idempotency/state transitions.

These tests use independent database sessions and synchronize workers at the
start of each operation. They run only in the dedicated PostgreSQL CI step.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.broker_connection import BrokerConnection
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.user import User
from app.services.live_execution_service import LiveExecutionBlocked, LiveOrderIntent, LiveOrderPreflight
from app.services.live_order_recovery_service import LiveOrderRecoveryService


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


def _create_intent_context(session_factory):
    with session_factory() as db:
        suffix = uuid4().hex
        user = User(
            email=f"pg-order-recovery-{suffix}@example.test",
            password_hash="integration-test-only",
            full_name="PostgreSQL Order Recovery",
            is_admin=False,
        )
        db.add(user)
        db.flush()
        portfolio = Portfolio(
            user_id=user.id,
            name="Concurrent intent test",
            virtual_capital=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
            is_active=True,
        )
        instrument = Instrument(
            instrument_key=f"NSE_EQ|TEST{suffix[:12]}",
            exchange="NSE",
            segment="NSE_EQ",
            instrument_type="EQUITY",
            trading_symbol=f"TST{suffix[:8]}",
            name="Concurrency Test Instrument",
            lot_size=1,
            tick_size=Decimal("0.05"),
            is_active=True,
        )
        connection = BrokerConnection(
            user_id=user.id,
            broker="upstox",
            api_key_encrypted="integration-test-key",
            api_secret_encrypted="integration-test-secret",
            redirect_uri="https://example.invalid/callback",
            access_token_encrypted="integration-test-token",
            access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_connected=True,
        )
        db.add_all([portfolio, instrument, connection])
        db.commit()
        return user.id, portfolio.id, instrument.id, instrument.instrument_key, connection.id


def _intent_plan(user_id, portfolio_id, instrument_id, instrument_key, connection_id):
    intent = LiveOrderIntent(
        portfolio_id=portfolio_id,
        instrument_id=instrument_id,
        side="BUY",
        order_type="MARKET",
        segment="EQUITY_DELIVERY",
        quantity=2,
    )
    plan = LiveOrderPreflight(
        user_id=user_id,
        portfolio_id=portfolio_id,
        instrument_id=instrument_id,
        broker_name="upstox",
        broker_connection_id=connection_id,
        instrument_key=instrument_key,
        side="BUY",
        order_type="MARKET",
        segment="EQUITY_DELIVERY",
        quantity=2,
        limit_price=None,
    )
    return intent, plan


def test_postgres_concurrent_same_intent_persists_exactly_one_row(pg_sessions):
    user_id, portfolio_id, instrument_id, instrument_key, connection_id = _create_intent_context(pg_sessions)
    intent, plan = _intent_plan(user_id, portfolio_id, instrument_id, instrument_key, connection_id)
    barrier = Barrier(2)

    def persist():
        barrier.wait(timeout=10)
        with pg_sessions() as db:
            return LiveOrderRecoveryService(db).persist_preflighted_intent(
                user_id, intent, plan, idempotency_key="concurrent-identical-intent"
            ).id

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(persist) for _ in range(2)]
        order_ids = [future.result(timeout=20) for future in futures]

    assert order_ids[0] == order_ids[1]
    with pg_sessions() as db:
        orders = db.query(Order).filter(
            Order.portfolio_id == portfolio_id,
            Order.idempotency_key == "concurrent-identical-intent",
        ).all()
        assert len(orders) == 1
        assert orders[0].status == "PENDING_SUBMISSION"
        assert orders[0].trading_mode == "LIVE"
        assert orders[0].broker_tag


def test_postgres_concurrent_submission_unknown_transition_is_idempotent(pg_sessions):
    user_id, portfolio_id, instrument_id, instrument_key, connection_id = _create_intent_context(pg_sessions)
    intent, plan = _intent_plan(user_id, portfolio_id, instrument_id, instrument_key, connection_id)
    with pg_sessions() as db:
        order = LiveOrderRecoveryService(db).persist_preflighted_intent(
            user_id, intent, plan, idempotency_key="concurrent-state-transition"
        )
        order_id = order.id

    barrier = Barrier(2)

    def mark_unknown():
        barrier.wait(timeout=10)
        with pg_sessions() as db:
            changed = LiveOrderRecoveryService(db).mark_submission_unknown(user_id, order_id)
            return changed.status

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(mark_unknown) for _ in range(2)]
        states = [future.result(timeout=20) for future in futures]

    assert states == ["SUBMISSION_UNKNOWN", "SUBMISSION_UNKNOWN"]
    with pg_sessions() as db:
        order = db.get(Order, order_id)
        assert order is not None
        assert order.status == "SUBMISSION_UNKNOWN"
        assert order.trading_mode == "LIVE"


def test_postgres_concurrent_submission_claim_has_exactly_one_winner(pg_sessions):
    user_id, portfolio_id, instrument_id, instrument_key, connection_id = _create_intent_context(pg_sessions)
    intent, plan = _intent_plan(user_id, portfolio_id, instrument_id, instrument_key, connection_id)
    with pg_sessions() as db:
        order = LiveOrderRecoveryService(db).persist_preflighted_intent(
            user_id, intent, plan, idempotency_key="concurrent-submission-claim"
        )
        order_id = order.id

    barrier = Barrier(2)

    def claim():
        barrier.wait(timeout=10)
        with pg_sessions() as db:
            try:
                result = LiveOrderRecoveryService(db).claim_submission_attempt(user_id, order_id)
                return result.status
            except LiveExecutionBlocked:
                return "BLOCKED"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(claim) for _ in range(2)]
        outcomes = [future.result(timeout=20) for future in futures]

    assert outcomes.count("SUBMISSION_CLAIMED") == 1
    assert outcomes.count("BLOCKED") == 1
    with pg_sessions() as db:
        order = db.get(Order, order_id)
        assert order is not None
        assert order.status == "SUBMISSION_CLAIMED"
        assert order.trading_mode == "LIVE"
