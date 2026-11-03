"""PostgreSQL 16 concurrent PAPER stop-event execution and replay tests.

Two independent workers execute the same durable claim against real PostgreSQL.
The portfolio/event locks and event-linked order uniqueness must yield one
filled order, one execution/accounting effect, and the same order to both
callers. This test never calls a broker write API.
"""
import asyncio
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.database import Base
from app.core.encryption import encrypt_value
from app.brokers.base import BrokerCallResult
from app.models.broker_connection import BrokerConnection
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.models.user import User
from app.services.paper_stop_event_claim_service import PaperStopEventClaimService
from app.services.paper_stop_event_execution_service import PaperStopEventExecutionService


pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_POSTGRES_URL"),
    reason="requires dedicated PostgreSQL 16 test database",
)


def _seed_execution_fixture(Session, suffix):
    user_id, portfolio_id, instrument_id, strategy_id, position_id = (
        uuid4() for _ in range(5)
    )
    with Session.begin() as db:
        db.add(User(
            id=user_id,
            email=f"paper-stop-exec-{suffix}@example.invalid",
            password_hash="test-only",
            full_name="PAPER Stop Execution Concurrency Test",
            is_admin=False,
        ))
        db.flush()
        db.add(Portfolio(
            id=portfolio_id,
            user_id=user_id,
            name=f"paper-stop-exec-{suffix}",
            virtual_capital=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
            is_active=True,
        ))
        db.add(Instrument(
            id=instrument_id,
            instrument_key=f"TEST|PAPER-EXEC|{suffix}",
            exchange="NSE",
            segment="NSE_EQ",
            instrument_type="EQUITY",
            trading_symbol=f"PEXEC{suffix[:8]}",
            name="PAPER stop execution concurrency test",
        ))
        db.flush()
        db.add(Strategy(
            id=strategy_id,
            portfolio_id=portfolio_id,
            instrument_id=instrument_id,
            name=f"paper-stop-exec-strategy-{suffix}",
            segment="EQUITY_INTRADAY",
            quantity=1,
            is_active=True,
            max_daily_loss=Decimal("1000.00"),
            current_watermark=Decimal("110.00"),
        ))
        db.add(Position(
            id=position_id,
            portfolio_id=portfolio_id,
            instrument_id=instrument_id,
            quantity=5,
            avg_price=Decimal("100.0000"),
            realized_pnl=Decimal("0.00"),
        ))
        db.add(BrokerConnection(
            user_id=user_id,
            broker="upstox",
            api_key_encrypted=encrypt_value("test-key"),
            api_secret_encrypted=encrypt_value("test-secret"),
            redirect_uri="https://example.invalid/callback",
            access_token_encrypted=encrypt_value("test-access"),
            access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            analytics_token_encrypted=encrypt_value("test-analytics"),
            analytics_token_expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            is_connected=True,
        ))
    return user_id, portfolio_id, instrument_id, strategy_id


def _cleanup_execution_fixture(Session, ids):
    user_id, portfolio_id, instrument_id, strategy_id = ids
    with Session.begin() as db:
        db.execute(text(
            "DELETE FROM executions WHERE portfolio_id = :id"
        ), {"id": str(portfolio_id)})
        db.execute(text(
            "DELETE FROM orders WHERE portfolio_id = :id"
        ), {"id": str(portfolio_id)})
        db.execute(text(
            "DELETE FROM paper_stop_events WHERE strategy_id = :id"
        ), {"id": str(strategy_id)})
        db.execute(text(
            "DELETE FROM positions WHERE portfolio_id = :id"
        ), {"id": str(portfolio_id)})
        db.execute(text(
            "DELETE FROM strategies WHERE id = :id"
        ), {"id": str(strategy_id)})
        db.execute(text(
            "DELETE FROM broker_connections WHERE user_id = :id"
        ), {"id": str(user_id)})
        db.execute(text(
            "DELETE FROM portfolios WHERE id = :id"
        ), {"id": str(portfolio_id)})
        db.execute(text(
            "DELETE FROM instruments WHERE id = :id"
        ), {"id": str(instrument_id)})
        db.execute(text(
            "DELETE FROM users WHERE id = :id"
        ), {"id": str(user_id)})


def test_two_postgres_workers_execute_one_stop_event_once():
    """A racing duplicate returns the first order and cannot double-fill."""
    engine = create_engine(
        os.environ["TEST_POSTGRES_URL"],
        pool_size=4,
        max_overflow=0,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    import app.services.paper_stop_event_dispatch_handler as handler
    monkeypatch.setattr(handler, "SessionLocal", Session)
    ids = _seed_execution_fixture(Session, uuid4().hex[:12])
    user_id, portfolio_id, instrument_id, strategy_id = ids

    with Session.begin() as db:
        event = PaperStopEventClaimService(db).claim_trailing_stop(
            user_id=user_id,
            portfolio_id=portfolio_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            quote_epoch=f"postgres-exec-{uuid4()}",
            quote_version=1,
            trigger_price=Decimal("98.25"),
            lease_seconds=120,
        )
        assert event is not None
        event_id, claim_token = event.id, event.claim_token

    now = datetime.now(timezone.utc).isoformat()
    instrument_key = f"TEST|PAPER-EXEC|{ids[2].hex[:12]}"
    # Read the persisted key rather than assuming UUID formatting or suffix.
    with Session() as db:
        instrument_key = db.get(Instrument, instrument_id).instrument_key
    level = {"price": "99.00", "quantity": 100000, "orders": 10}
    quote = {
        "instrument_token": instrument_key,
        "last_price": "99.00",
        "last_trade_time": "1600000000000",
        "timestamp": now,
        "depth": {"buy": [level], "sell": [level]},
    }
    adapter = type("FakeAdapter", (), {
        "get_full_quote": AsyncMock(return_value=BrokerCallResult(
            ok=True, data={"data": {instrument_key: quote}}
        ))
    })()
    barrier = threading.Barrier(2)
    results = []
    result_lock = threading.Lock()

    def execute():
        with Session() as db:
            barrier.wait(timeout=10)
            try:
                order = asyncio.run(
                    PaperStopEventExecutionService(db).execute_claimed(
                        user_id=user_id,
                        event_id=event_id,
                        claim_token=claim_token,
                    )
                )
                result = ("ok", str(order.id), order.status)
            except Exception as exc:
                result = ("error", type(exc).__name__, str(exc))
            with result_lock:
                results.append(result)

    try:
        with patch(
            "app.services.execution_service.get_broker_adapter",
            return_value=adapter,
        ), patch(
            "app.services.execution_service.settings.UPSTOX_CHARGE_ESTIMATES_ENABLED",
            False,
        ):
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(execute), pool.submit(execute)]
                for future in futures:
                    future.result(timeout=60)

        assert len(results) == 2, results
        assert all(result[0] == "ok" for result in results), results
        assert results[0][1] == results[1][1], results
        assert all(result[2] == "FILLED" for result in results), results
        assert adapter.get_full_quote.await_count == 1

        with Session() as db:
            saved_event = db.get(PaperStopEvent, event_id)
            saved_position = db.query(Position).filter_by(
                portfolio_id=portfolio_id,
                instrument_id=instrument_id,
            ).one()
            orders = db.query(Order).filter(
                Order.paper_stop_event_id == event_id
            ).all()
            executions = db.query(Execution).join(
                Order, Execution.order_id == Order.id
            ).filter(Order.paper_stop_event_id == event_id).all()
            assert saved_event.state == "COMPLETED"
            assert len(orders) == 1 and orders[0].status == "FILLED"
            assert len(executions) == 1
            assert saved_position.quantity == 0
    finally:
        _cleanup_execution_fixture(Session, ids)
        engine.dispose()


def test_postgres_indicator_exit_and_stop_event_race_flatten_position_once():
    """Independent indicator and stop workers race; only one reduce-only fill wins."""
    from app.models.portfolio import Portfolio
    from app.models.strategy import Strategy
    from app.services.strategy_execution_service import StrategyExecutionService

    engine = create_engine(
        os.environ["TEST_POSTGRES_URL"],
        pool_size=4,
        max_overflow=0,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    ids = _seed_execution_fixture(Session, uuid4().hex[:12])
    user_id, portfolio_id, instrument_id, strategy_id = ids

    with Session.begin() as db:
        event = PaperStopEventClaimService(db).claim_trailing_stop(
            user_id=user_id,
            portfolio_id=portfolio_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            quote_epoch=f"postgres-exit-race-{uuid4()}",
            quote_version=1,
            trigger_price=Decimal("98.25"),
            lease_seconds=120,
        )
        assert event is not None
        event_id, claim_token = event.id, event.claim_token

    with Session() as db:
        instrument_key = db.get(Instrument, instrument_id).instrument_key
    now = datetime.now(timezone.utc).isoformat()
    level = {"price": "99.00", "quantity": 100000, "orders": 10}
    quote = {
        "instrument_token": instrument_key,
        "last_price": "99.00",
        "last_trade_time": "1600000000000",
        "timestamp": now,
        "depth": {"buy": [level], "sell": [level]},
    }
    adapter = type("FakeAdapter", (), {
        "get_full_quote": AsyncMock(return_value=BrokerCallResult(
            ok=True, data={"data": {instrument_key: quote}}
        ))
    })()
    barrier = threading.Barrier(2)
    results = []
    result_lock = threading.Lock()

    def indicator_exit():
        with Session() as db:
            portfolio = db.get(Portfolio, portfolio_id)
            strategy = db.get(Strategy, strategy_id)
            barrier.wait(timeout=10)
            try:
                result = asyncio.run(
                    StrategyExecutionService(db)._exit(
                        strategy, portfolio, 5, Decimal("0.25")
                    )
                )
                outcome = ("indicator", result.order_id, result.reason)
            except Exception as exc:
                outcome = ("indicator_error", type(exc).__name__, str(exc))
            with result_lock:
                results.append(outcome)

    def stop_exit():
        with Session() as db:
            barrier.wait(timeout=10)
            try:
                order = asyncio.run(
                    PaperStopEventExecutionService(db).execute_claimed(
                        user_id=user_id,
                        event_id=event_id,
                        claim_token=claim_token,
                    )
                )
                outcome = ("stop_filled", str(order.id), order.status)
            except Exception as exc:
                # POSITION_ALREADY_CLOSED is the expected losing outcome when
                # the indicator worker acquired the portfolio lock first.
                outcome = ("stop_obsolete", type(exc).__name__, str(exc))
            with result_lock:
                results.append(outcome)

    try:
        with patch(
            "app.services.execution_service.get_broker_adapter",
            return_value=adapter,
        ), patch(
            "app.services.execution_service.settings.UPSTOX_CHARGE_ESTIMATES_ENABLED",
            False,
        ):
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(indicator_exit), pool.submit(stop_exit)]
                for future in futures:
                    future.result(timeout=60)

        assert len(results) == 2, results
        assert not [result for result in results if result[0] == "indicator_error"], results
        assert not [result for result in results if result[0] not in {
            "indicator", "stop_filled", "stop_obsolete"
        }], results

        with Session() as db:
            saved_event = db.get(PaperStopEvent, event_id)
            saved_position = db.query(Position).filter_by(
                portfolio_id=portfolio_id,
                instrument_id=instrument_id,
            ).one()
            orders = db.query(Order).filter(
                Order.portfolio_id == portfolio_id,
                Order.instrument_id == instrument_id,
            ).all()
            executions = db.query(Execution).filter(
                Execution.portfolio_id == portfolio_id
            ).all()
            filled_orders = [order for order in orders if order.status == "FILLED"]
            assert len(filled_orders) == 1, [(o.id, o.status, o.rejection_reason) for o in orders]
            assert len(executions) == 1
            assert saved_position.quantity == 0
            assert saved_position.quantity >= 0
            assert saved_event.state in {"COMPLETED", "FAILED"}
            if saved_event.state == "FAILED":
                assert saved_event.last_error_code == "POSITION_ALREADY_CLOSED"
            else:
                assert saved_event.state == "COMPLETED"
    finally:
        _cleanup_execution_fixture(Session, ids)
        engine.dispose()


def test_sigkilled_execution_worker_recovers_paper_stop_without_redis(tmp_path, monkeypatch):
    """A real OS process dies after the claim commit; PostgreSQL recovery executes once.

    The child uses the production _execute_event path and is SIGKILLed only
    after that path commits the claim/token and enters execute_claimed. The
    parent then recovers solely from PostgreSQL, with no Redis delivery.
    """
    import subprocess
    import sys
    import time
    from pathlib import Path

    engine = create_engine(
        os.environ["TEST_POSTGRES_URL"],
        pool_size=4,
        max_overflow=0,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    ids = _seed_execution_fixture(Session, uuid4().hex[:12])
    user_id, portfolio_id, instrument_id, strategy_id = ids

    with Session.begin() as db:
        event = PaperStopEventClaimService(db).claim_trailing_stop(
            user_id=user_id,
            portfolio_id=portfolio_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            quote_epoch=f"postgres-sigkill-{uuid4()}",
            quote_version=1,
            trigger_price=Decimal("98.25"),
            lease_seconds=300,
        )
        assert event is not None
        event_id, original_token = event.id, event.claim_token

    marker = Path(tmp_path) / "execution-entered"
    child_script = r"""
import asyncio
import os
from uuid import UUID

os.environ["DATABASE_URL"] = os.environ["TEST_POSTGRES_URL"]
from app.services.paper_stop_event_dispatch_handler import _execute_event
from app.services.paper_stop_event_execution_service import PaperStopEventExecutionService

async def pause_after_claim_commit(self, **kwargs):
    with open(os.environ["PAPER_STOP_CRASH_MARKER"], "w", encoding="utf-8") as marker:
        marker.write(str(kwargs["claim_token"]))
        marker.flush()
        os.fsync(marker.fileno())
    while True:
        await asyncio.sleep(1)

PaperStopEventExecutionService.execute_claimed = pause_after_claim_commit
asyncio.run(_execute_event(UUID(os.environ["PAPER_STOP_EVENT_ID"]), UUID(os.environ["PAPER_STOP_USER_ID"])))
"""
    child_env = os.environ.copy()
    child_env["DATABASE_URL"] = os.environ["TEST_POSTGRES_URL"]
    child_env["PAPER_STOP_CRASH_MARKER"] = str(marker)
    child_env["PAPER_STOP_EVENT_ID"] = str(event_id)
    child_env["PAPER_STOP_USER_ID"] = str(user_id)
    child = None

    try:
        child = subprocess.Popen(
            [sys.executable, "-c", child_script],
            cwd=os.getcwd(),
            env=child_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline and not marker.exists():
            if child.poll() is not None:
                stdout, stderr = child.communicate(timeout=5)
                pytest.fail(
                    "Execution worker exited before claim-commit marker. "
                    f"exit={child.returncode}; stdout={stdout}; stderr={stderr}"
                )
            time.sleep(0.05)
        assert marker.exists(), "Execution worker never reached post-claim execution boundary"
        assert marker.read_text(encoding="utf-8") == str(original_token)

        # This is an actual process kill, not a mocked exception or cancellation.
        child.kill()
        child.wait(timeout=10)

        with Session.begin() as db:
            crashed_event = db.get(PaperStopEvent, event_id)
            assert crashed_event is not None
            assert crashed_event.state == "CLAIMED"
            assert crashed_event.claim_token == original_token
            crashed_event.claimed_until = datetime.now(timezone.utc) - timedelta(seconds=1)

        with Session() as db:
            instrument_key = db.get(Instrument, instrument_id).instrument_key

        now = datetime.now(timezone.utc).isoformat()
        level = {"price": "99.00", "quantity": 100000, "orders": 10}
        quote = {
            "instrument_token": instrument_key,
            "last_price": "99.00",
            "last_trade_time": "1600000000000",
            "timestamp": now,
            "depth": {"buy": [level], "sell": [level]},
        }
        adapter = type("FakeAdapter", (), {
            "get_full_quote": AsyncMock(return_value=BrokerCallResult(
                ok=True, data={"data": {instrument_key: quote}}
            ))
        })()

        # Recovery is called directly from PostgreSQL; no Redis publish,
        # redelivery, or market-quote worker is involved.
        with patch(
            "app.services.execution_service.get_broker_adapter",
            return_value=adapter,
        ), patch(
            "app.services.execution_service.settings.UPSTOX_CHARGE_ESTIMATES_ENABLED",
            False,
        ):
            recovered = asyncio.run(handler.recover_expired_paper_stop_events_once())

        assert recovered == 1
        assert adapter.get_full_quote.await_count == 1

        with Session() as db:
            saved_event = db.get(PaperStopEvent, event_id)
            orders = db.query(Order).filter(Order.paper_stop_event_id == event_id).all()
            executions = db.query(Execution).join(
                Order, Execution.order_id == Order.id
            ).filter(Order.paper_stop_event_id == event_id).all()
            position = db.query(Position).filter_by(
                portfolio_id=portfolio_id,
                instrument_id=instrument_id,
            ).one()
            portfolio = db.get(Portfolio, portfolio_id)

            assert saved_event.state == "COMPLETED"
            assert saved_event.claim_token != original_token
            assert saved_event.attempt_count == 2
            assert len(orders) == 1 and orders[0].status == "FILLED"
            assert len(executions) == 1
            assert position.quantity == 0
            assert portfolio.cash_balance != Decimal("100000.00")

        # The token held by the killed process is fenced after recovery.
        from app.services.paper_stop_event_execution_service import PaperStopEventExecutionRejected
        with Session() as stale_session:
            with pytest.raises(PaperStopEventExecutionRejected, match="Claim token"):
                asyncio.run(PaperStopEventExecutionService(stale_session).execute_claimed(
                    user_id=user_id,
                    event_id=event_id,
                    claim_token=original_token,
                ))
        with Session() as verify_session:
            assert verify_session.query(Order).filter(
                Order.paper_stop_event_id == event_id
            ).count() == 1
            assert verify_session.query(Execution).join(
                Order, Execution.order_id == Order.id
            ).filter(Order.paper_stop_event_id == event_id).count() == 1
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.wait(timeout=10)
        _cleanup_execution_fixture(Session, ids)
        engine.dispose()
