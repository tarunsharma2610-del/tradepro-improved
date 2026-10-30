"""PostgreSQL 16 multi-session concurrency tests for PAPER stop-event claims.

These tests use independent SQLAlchemy sessions and a real PostgreSQL database.
They are skipped locally unless TEST_POSTGRES_URL is configured; backend CI
provides a PostgreSQL 16 service. They create uniquely identified rows and
clean up only those rows, never dropping shared CI tables.
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 register all tables
from app.core.database import Base
from app.models.instrument import Instrument
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.models.user import User
from app.services.paper_stop_event_claim_service import PaperStopEventClaimService


pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_POSTGRES_URL"),
    reason="requires dedicated PostgreSQL 16 test database",
)


def _seed_claim_fixture(Session, suffix):
    user_id, portfolio_id, instrument_id, strategy_id, position_id = (
        uuid4() for _ in range(5)
    )
    with Session.begin() as db:
        db.add(User(
            id=user_id,
            email=f"paper-stop-claim-{suffix}@example.invalid",
            password_hash="test-only",
            full_name="PAPER Stop Claim Concurrency Test",
            is_admin=False,
        ))
        db.flush()
        db.add(Portfolio(
            id=portfolio_id,
            user_id=user_id,
            name=f"paper-stop-claim-{suffix}",
            virtual_capital=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
            is_active=True,
        ))
        db.add(Instrument(
            id=instrument_id,
            instrument_key=f"TEST|PAPER-STOP|{suffix}",
            exchange="NSE",
            segment="NSE_EQ",
            instrument_type="EQUITY",
            trading_symbol=f"PSTOP{suffix[:8]}",
            name="PAPER stop claim concurrency test",
        ))
        db.flush()
        db.add(Strategy(
            id=strategy_id,
            portfolio_id=portfolio_id,
            instrument_id=instrument_id,
            name=f"paper-stop-strategy-{suffix}",
            segment="EQUITY_INTRADAY",
            quantity=1,
            is_active=True,
            max_daily_loss=Decimal("1000.00"),
        ))
        db.add(Position(
            id=position_id,
            portfolio_id=portfolio_id,
            instrument_id=instrument_id,
            quantity=5,
            avg_price=Decimal("100.0000"),
            realized_pnl=Decimal("0.00"),
        ))
    return user_id, portfolio_id, instrument_id, strategy_id


def _cleanup_claim_fixture(Session, ids):
    user_id, portfolio_id, instrument_id, strategy_id = ids
    with Session.begin() as db:
        db.execute(
            text("DELETE FROM paper_stop_events WHERE strategy_id = :id"),
            {"id": str(strategy_id)},
        )
        db.execute(
            text("DELETE FROM positions WHERE portfolio_id = :portfolio AND instrument_id = :instrument"),
            {"portfolio": str(portfolio_id), "instrument": str(instrument_id)},
        )
        db.execute(text("DELETE FROM strategies WHERE id = :id"), {"id": str(strategy_id)})
        db.execute(text("DELETE FROM portfolios WHERE id = :id"), {"id": str(portfolio_id)})
        db.execute(text("DELETE FROM instruments WHERE id = :id"), {"id": str(instrument_id)})
        db.execute(text("DELETE FROM users WHERE id = :id"), {"id": str(user_id)})


def test_two_postgres_workers_cannot_claim_the_same_quote_identity():
    """Two independent transactions racing the same quote yield one durable claim."""
    engine = create_engine(
        os.environ["TEST_POSTGRES_URL"],
        pool_size=4,
        max_overflow=0,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    ids = _seed_claim_fixture(Session, uuid4().hex[:12])
    user_id, portfolio_id, instrument_id, strategy_id = ids
    barrier = threading.Barrier(2)
    results = []
    results_lock = threading.Lock()

    def attempt():
        with Session() as db:
            barrier.wait(timeout=10)
            try:
                event = PaperStopEventClaimService(db).claim_trailing_stop(
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    strategy_id=strategy_id,
                    instrument_id=instrument_id,
                    quote_epoch="postgres-race-epoch",
                    quote_version=1,
                    trigger_price=Decimal("98.25"),
                    lease_seconds=30,
                )
                db.commit()
                result = ("claimed", str(event.claim_token)) if event else ("duplicate", None)
            except Exception as exc:
                db.rollback()
                result = ("error", type(exc).__name__, str(exc))
            with results_lock:
                results.append(result)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(attempt), pool.submit(attempt)]
            for future in futures:
                future.result(timeout=30)

        assert sum(result[0] == "claimed" for result in results) == 1, results
        assert sum(result[0] == "duplicate" for result in results) == 1, results
        assert not [result for result in results if result[0] == "error"], results

        with Session() as db:
            rows = db.query(PaperStopEvent).filter_by(
                strategy_id=strategy_id,
                event_type="TRAILING_STOP",
                quote_epoch="postgres-race-epoch",
                quote_version=1,
            ).all()
            assert len(rows) == 1
            assert rows[0].state == "CLAIMED"
            assert rows[0].claim_token is not None
            assert rows[0].attempt_count == 1
    finally:
        _cleanup_claim_fixture(Session, ids)
        engine.dispose()


def test_two_postgres_workers_can_claim_distinct_quote_versions():
    """Portfolio locking serializes writers without suppressing distinct quotes."""
    engine = create_engine(
        os.environ["TEST_POSTGRES_URL"],
        pool_size=4,
        max_overflow=0,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    ids = _seed_claim_fixture(Session, uuid4().hex[:12])
    user_id, portfolio_id, instrument_id, strategy_id = ids
    barrier = threading.Barrier(2)
    results = []
    results_lock = threading.Lock()

    def attempt(version):
        with Session() as db:
            barrier.wait(timeout=10)
            try:
                event = PaperStopEventClaimService(db).claim_trailing_stop(
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    strategy_id=strategy_id,
                    instrument_id=instrument_id,
                    quote_epoch="postgres-distinct-epoch",
                    quote_version=version,
                    trigger_price=Decimal("98.25"),
                    lease_seconds=30,
                )
                db.commit()
                result = ("claimed", version, str(event.claim_token)) if event else ("duplicate", version)
            except Exception as exc:
                db.rollback()
                result = ("error", version, type(exc).__name__, str(exc))
            with results_lock:
                results.append(result)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(attempt, 11), pool.submit(attempt, 12)]
            for future in futures:
                future.result(timeout=30)

        assert sorted(result[1] for result in results if result[0] == "claimed") == [11, 12], results
        assert not [result for result in results if result[0] != "claimed"], results
        with Session() as db:
            rows = db.query(PaperStopEvent).filter_by(
                strategy_id=strategy_id,
                event_type="TRAILING_STOP",
                quote_epoch="postgres-distinct-epoch",
            ).order_by(PaperStopEvent.quote_version).all()
            assert [row.quote_version for row in rows] == [11, 12]
            assert all(row.claim_token is not None and row.attempt_count == 1 for row in rows)
    finally:
        _cleanup_claim_fixture(Session, ids)
        engine.dispose()



def test_two_postgres_workers_racing_expired_lease_reclaim_only_once():
    """Concurrent reclaimers rotate one expired claim token exactly once."""
    from datetime import datetime, timedelta, timezone
    from app.services.paper_stop_event_lifecycle import PaperStopEventLifecycle

    engine = create_engine(
        os.environ["TEST_POSTGRES_URL"],
        pool_size=4,
        max_overflow=0,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    ids = _seed_claim_fixture(Session, uuid4().hex[:12])
    user_id, portfolio_id, instrument_id, strategy_id = ids
    now = datetime.now(timezone.utc).replace(microsecond=0)
    try:
        with Session.begin() as db:
            original = PaperStopEventClaimService(db).claim_trailing_stop(
                user_id=user_id,
                portfolio_id=portfolio_id,
                strategy_id=strategy_id,
                instrument_id=instrument_id,
                quote_epoch="postgres-reclaim-race",
                quote_version=1,
                trigger_price=Decimal("98.25"),
                lease_seconds=30,
                now=now - timedelta(minutes=2),
            )
            assert original is not None
            event_id = original.id
            old_token = original.claim_token

        barrier = threading.Barrier(2)
        results = []
        results_lock = threading.Lock()

        def reclaim():
            with Session() as db:
                barrier.wait(timeout=10)
                try:
                    event = PaperStopEventLifecycle(db).reclaim_expired(
                        event_id=event_id,
                        lease_seconds=30,
                        max_attempts=5,
                        now=now,
                    )
                    db.commit()
                    result = ("reclaimed", str(event.claim_token)) if event else ("lost", None)
                except Exception as exc:
                    db.rollback()
                    result = ("error", type(exc).__name__, str(exc))
                with results_lock:
                    results.append(result)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(reclaim), pool.submit(reclaim)]
            for future in futures:
                future.result(timeout=30)

        assert sum(result[0] == "reclaimed" for result in results) == 1, results
        assert sum(result[0] == "lost" for result in results) == 1, results
        assert not [result for result in results if result[0] == "error"], results

        with Session() as db:
            saved = db.get(PaperStopEvent, event_id)
            assert saved.state == "CLAIMED"
            assert saved.claim_token != old_token
            assert saved.attempt_count == 2
            winning_token = saved.claim_token

        # The former owner cannot advance the event after the token rotation.
        with Session.begin() as db:
            stale = PaperStopEventLifecycle(db).begin_execution(
                event_id=event_id,
                claim_token=old_token,
                now=now + timedelta(seconds=1),
            )
            assert stale is None

        with Session.begin() as db:
            current = PaperStopEventLifecycle(db).begin_execution(
                event_id=event_id,
                claim_token=winning_token,
                now=now + timedelta(seconds=1),
            )
            assert current is not None
            assert current.state == "EXECUTING"
    finally:
        _cleanup_claim_fixture(Session, ids)
        engine.dispose()



def test_postgres_lifecycle_transition_rolls_back_atomically():
    """A caller rollback restores the prior durable state and claim token."""
    from datetime import datetime, timedelta, timezone
    from app.services.paper_stop_event_lifecycle import PaperStopEventLifecycle

    engine = create_engine(os.environ["TEST_POSTGRES_URL"], pool_size=3, max_overflow=0, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    ids = _seed_claim_fixture(Session, uuid4().hex[:12])
    user_id, portfolio_id, instrument_id, strategy_id = ids
    now = datetime.now(timezone.utc).replace(microsecond=0)
    try:
        with Session.begin() as db:
            event = PaperStopEventClaimService(db).claim_trailing_stop(
                user_id=user_id, portfolio_id=portfolio_id, strategy_id=strategy_id,
                instrument_id=instrument_id, quote_epoch="postgres-rollback",
                quote_version=1, trigger_price=Decimal("98.25"),
                lease_seconds=30, now=now,
            )
            assert event is not None
            event_id, token = event.id, event.claim_token

        db = Session()
        try:
            advanced = PaperStopEventLifecycle(db).begin_execution(
                event_id=event_id, claim_token=token, now=now + timedelta(seconds=1)
            )
            assert advanced is not None and advanced.state == "EXECUTING"
            db.rollback()
        finally:
            db.close()

        with Session() as verify:
            saved = verify.get(PaperStopEvent, event_id)
            assert saved.state == "CLAIMED"
            assert saved.claim_token == token
            assert saved.attempt_count == 1
    finally:
        _cleanup_claim_fixture(Session, ids)
        engine.dispose()


def test_postgres_expired_executing_lease_recovers_and_fences_old_worker():
    """A crashed EXECUTING worker is recoverable, but cannot complete later."""
    from datetime import datetime, timedelta, timezone
    from app.services.paper_stop_event_lifecycle import PaperStopEventLifecycle

    engine = create_engine(os.environ["TEST_POSTGRES_URL"], pool_size=3, max_overflow=0, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    ids = _seed_claim_fixture(Session, uuid4().hex[:12])
    user_id, portfolio_id, instrument_id, strategy_id = ids
    now = datetime.now(timezone.utc).replace(microsecond=0)
    try:
        with Session.begin() as db:
            event = PaperStopEventClaimService(db).claim_trailing_stop(
                user_id=user_id, portfolio_id=portfolio_id, strategy_id=strategy_id,
                instrument_id=instrument_id, quote_epoch="postgres-executing-recovery",
                quote_version=1, trigger_price=Decimal("98.25"),
                lease_seconds=30, now=now,
            )
            assert event is not None
            event_id, original_token = event.id, event.claim_token
            executing = PaperStopEventLifecycle(db).begin_execution(
                event_id=event_id, claim_token=original_token,
                lease_seconds=10, now=now + timedelta(seconds=1),
            )
            assert executing is not None

        recovery_time = now + timedelta(seconds=12)
        with Session.begin() as db:
            recovered = PaperStopEventLifecycle(db).reclaim_expired(
                event_id=event_id, lease_seconds=30, max_attempts=5, now=recovery_time
            )
            assert recovered is not None
            replacement_token = recovered.claim_token
            assert replacement_token != original_token
            assert recovered.attempt_count == 2

        with Session.begin() as db:
            stale_completion = PaperStopEventLifecycle(db).complete(
                event_id=event_id, claim_token=original_token,
                now=recovery_time + timedelta(seconds=1),
            )
            assert stale_completion is None

        with Session.begin() as db:
            current = PaperStopEventLifecycle(db).begin_execution(
                event_id=event_id, claim_token=replacement_token,
                now=recovery_time + timedelta(seconds=1),
            )
            assert current is not None and current.state == "EXECUTING"
    finally:
        _cleanup_claim_fixture(Session, ids)
        engine.dispose()
