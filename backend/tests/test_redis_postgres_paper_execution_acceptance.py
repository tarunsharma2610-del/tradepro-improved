"""End-to-end PAPER acceptance using real Redis 7 and PostgreSQL 16.

The production Redis publisher/consumer, scanner/dispatcher and durable PAPER
handler run together. Every handler-owned database session is PostgreSQL-backed.
No broker order-write endpoint is invoked; only the market quote read is stubbed.
"""
import asyncio
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import pytest
from redis.asyncio import Redis

from app.core.database import Base
from app.core.encryption import encrypt_value
from app.models.broker_connection import BrokerConnection
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.models.user import User
from app.services.market_quote_dispatcher import MarketQuoteDispatcher
from app.services.market_scanner import MarketScanner
from app.services.market_quote_dispatch_worker import MarketQuoteDispatchWorker
from app.services.market_scan_dispatch_pipeline import MarketScanDispatchPipeline
from app.services.paper_stop_event_dispatch_handler import handle_paper_market_observation
from app.services.redis_market_quote_consumer import RedisMarketQuoteConsumer
from app.services.redis_market_quote_publisher import RedisMarketQuotePublisher
from app.services.upstox_market_data_streamer import MarketTick

REDIS_TEST_URL = os.getenv("REDIS_TEST_URL")
TEST_POSTGRES_URL = os.getenv("TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not REDIS_TEST_URL or not TEST_POSTGRES_URL,
    reason="real Redis 7 and PostgreSQL 16 services are required",
)


def _quote_patch(instrument):
    from unittest.mock import AsyncMock, patch
    from app.brokers.base import BrokerCallResult

    now = datetime.now(timezone.utc).isoformat()
    level = {"price": "97.00", "quantity": 100000, "orders": 10}
    quote = {
        "instrument_token": instrument.instrument_key,
        "last_price": "97.00",
        "last_trade_time": str(int(datetime.now(timezone.utc).timestamp() * 1000)),
        "timestamp": now,
        "depth": {"buy": [level], "sell": [level]},
    }
    adapter = type("FakeAdapter", (), {
        "get_full_quote": AsyncMock(return_value=BrokerCallResult(
            ok=True, data={"data": {instrument.instrument_key: quote}}
        ))
    })()
    return patch("app.services.execution_service.get_broker_adapter", return_value=adapter)


@pytest.mark.asyncio
async def test_real_redis_snapshot_reaches_postgres_paper_fill_and_ledger(monkeypatch):
    from unittest.mock import patch
    import app.services.paper_stop_event_dispatch_handler as handler

    engine = create_engine(
        TEST_POSTGRES_URL, pool_size=5, max_overflow=0, pool_pre_ping=True
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    db_session = Session()
    user_id = uuid4()
    suffix = uuid4().hex[:10]
    from app.core.security import hash_password
    user = User(
        id=user_id, email=f"redis-paper-{suffix}@example.invalid",
        password_hash=hash_password("test-only-password"),
        full_name="Redis PostgreSQL PAPER acceptance", is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    portfolio = Portfolio(
        user_id=user.id, name="Redis PAPER acceptance",
        virtual_capital=Decimal("100000"), cash_balance=Decimal("100000"),
        is_active=True,
    )
    instrument = Instrument(
        instrument_key=f"NSE_EQ|{uuid4().hex[:12]}", exchange="NSE",
        segment="NSE_EQ", instrument_type="EQUITY",
        trading_symbol=f"RP{suffix.upper()}", name="Redis PostgreSQL PAPER acceptance",
    )
    db_session.add_all([portfolio, instrument])
    db_session.flush()
    strategy = Strategy(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        name="Redis PAPER trailing stop", segment="EQUITY_INTRADAY",
        quantity=1, is_active=True, max_daily_loss=1000,
        trailing_stop_pct=Decimal("2"), current_watermark=Decimal("100"),
    )
    position = Position(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        quantity=2, avg_price=Decimal("100"), realized_pnl=Decimal("0"),
    )
    db_session.add_all([strategy, position])
    db_session.add(BrokerConnection(
        user_id=user.id, broker="upstox",
        api_key_encrypted=encrypt_value("test-key"),
        api_secret_encrypted=encrypt_value("test-secret"),
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted=encrypt_value("test-access"),
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        analytics_token_encrypted=encrypt_value("test-analytics"),
        analytics_token_expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        is_connected=True,
    ))
    db_session.commit()

    # Handler transactions must use separate PostgreSQL sessions, not the
    # SQLite pytest fixture or the seed/assertion session.
    monkeypatch.setattr(handler, "SessionLocal", Session)
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    publisher = RedisMarketQuotePublisher(redis, user.id, ttl_seconds=15)
    consumer = RedisMarketQuoteConsumer(redis, user.id, max_age_seconds=15)
    dispatcher = MarketQuoteDispatcher(max_pending_keys=8)
    scanner = MarketScanner()
    pipeline = MarketScanDispatchPipeline(scanner=scanner, dispatcher=dispatcher)
    instrument_key = instrument.instrument_key
    dispatched_items = []
    handler_attempts = 0

    async def handle_and_capture(dispatched):
        nonlocal handler_attempts
        handler_attempts += 1
        dispatched_items.append(dispatched)
        # Simulate an uncertain response after the durable PAPER transaction:
        # the event/order/fill may already be committed when the worker sees
        # an exception and retries the same quote identity.
        await handle_paper_market_observation(dispatched)
        if handler_attempts <= 5:
            raise RuntimeError("simulated post-commit response loss")

    dispatch_worker = MarketQuoteDispatchWorker(
        dispatcher,
        handle_and_capture,
        min_backoff_seconds=0,
        max_backoff_seconds=0,
        max_attempts=5,
        on_exhausted=lambda item: scanner.clear_instrument(
            item.user_id, item.instrument_key
        ),
    )
    worker_task = None

    try:
        assert await redis.ping()
        now = datetime.now(timezone.utc)
        tick = MarketTick(
            instrument_key=instrument_key, ltp=97.0,
            exchange_timestamp_ms=int(now.timestamp() * 1000),
            received_at=now, received_monotonic=1.0,
            volume_traded_today=1200, open_interest=4500,
            total_buy_quantity=700, total_sell_quantity=300,
            ohlc=({"interval": "1d", "close": 100.0},),
        )
        assert await publisher.publish(tick)

        recovered = await consumer.get_quote(instrument_key)
        assert recovered is not None
        with patch(
            "app.services.execution_service.settings.UPSTOX_CHARGE_ESTIMATES_ENABLED",
            False,
        ), _quote_patch(instrument):
            worker_task = asyncio.create_task(dispatch_worker.run())
            assert pipeline.on_quote(user.id, recovered) is True
            async with asyncio.timeout(3):
                while dispatch_worker.exhausted_count != 1:
                    await asyncio.sleep(0.01)

            # Exhaustion must clear scanner high-water state so the same
            # authoritative Redis snapshot can be admitted again.
            replayed = await consumer.recover([instrument_key])
            assert instrument_key in replayed
            assert replayed[instrument_key]["epoch"] == recovered["epoch"]
            assert replayed[instrument_key]["version"] == recovered["version"]
            assert pipeline.on_quote(user.id, replayed[instrument_key]) is True
            async with asyncio.timeout(3):
                while dispatch_worker.processed_count != 1:
                    await asyncio.sleep(0.01)

        assert handler_attempts == 6
        assert dispatch_worker.exhausted_count == 1
        assert dispatch_worker.processed_count == 1
        dispatched = dispatched_items[0]
        assert dispatched.observation.ltp == 97.0
        assert dispatched.observation.price_change_pct == -3.0
        assert dispatcher.pending_keys == 0
        assert dispatcher.inflight_keys == 0
        db_session.expire_all()
        saved_event = db_session.query(PaperStopEvent).filter(
            PaperStopEvent.user_id == user.id,
            PaperStopEvent.instrument_id == instrument.id,
            PaperStopEvent.quote_epoch == recovered["epoch"],
            PaperStopEvent.quote_version == recovered["version"],
        ).one()
        saved_order = db_session.query(Order).filter(
            Order.paper_stop_event_id == saved_event.id
        ).one()
        db_session.refresh(portfolio)
        db_session.refresh(position)
        assert saved_event.state == "COMPLETED"
        assert saved_order.status == "FILLED"
        assert saved_order.trading_mode == "PAPER"
        assert position.quantity == 0
        assert portfolio.cash_balance > Decimal("100000")
        assert db_session.query(Execution).filter(
            Execution.order_id == saved_order.id
        ).count() == 1

        # Re-deliver the same quote identity: it must not create another fill.
        cash_after_fill = Decimal(str(portfolio.cash_balance))
        await handle_paper_market_observation(dispatched)
        db_session.refresh(portfolio)
        assert Decimal(str(portfolio.cash_balance)) == cash_after_fill
        assert db_session.query(Order).filter(
            Order.paper_stop_event_id == saved_event.id
        ).count() == 1
        assert db_session.query(Execution).filter(
            Execution.order_id == saved_order.id
        ).count() == 1
    finally:
        if worker_task is not None:
            worker_task.cancel()
            await asyncio.gather(worker_task, return_exceptions=True)
        await redis.delete(
            publisher.snapshot_key(instrument_key),
            publisher.snapshot_key(instrument_key) + ":version",
        )
        await redis.aclose()
        # Capture scalar identifiers before closing the ORM session; detached
        # model instances cannot safely lazy-refresh attributes during cleanup.
        cleanup_ids = {
            "portfolio": str(portfolio.id),
            "strategy": str(strategy.id),
            "instrument": str(instrument.id),
            "user": str(user.id),
        }
        db_session.close()
        # Remove only this test's rows from the CI-shared PostgreSQL database.
        with engine.begin() as connection:
            cleanup = (
                ("DELETE FROM executions WHERE portfolio_id = :id", cleanup_ids["portfolio"]),
                ("DELETE FROM orders WHERE portfolio_id = :id", cleanup_ids["portfolio"]),
                ("DELETE FROM paper_stop_events WHERE strategy_id = :id", cleanup_ids["strategy"]),
                ("DELETE FROM positions WHERE portfolio_id = :id", cleanup_ids["portfolio"]),
                ("DELETE FROM strategies WHERE id = :id", cleanup_ids["strategy"]),
                ("DELETE FROM broker_connections WHERE user_id = :id", cleanup_ids["user"]),
                ("DELETE FROM portfolios WHERE id = :id", cleanup_ids["portfolio"]),
                ("DELETE FROM instruments WHERE id = :id", cleanup_ids["instrument"]),
                ("DELETE FROM users WHERE id = :id", cleanup_ids["user"]),
            )
            for statement, value in cleanup:
                connection.execute(text(statement), {"id": value})
        engine.dispose()


@pytest.mark.asyncio
async def test_real_redis_restart_and_dispatch_worker_interruption_recover_one_postgres_paper_fill(
    monkeypatch, tmp_path,
):
    """A committed claim survives worker cancellation and Redis volatile-data loss."""
    import shutil
    import socket
    import subprocess

    import app.services.paper_stop_event_dispatch_handler as handler
    from app.services.paper_stop_event_execution_service import PaperStopEventExecutionService

    redis_server = shutil.which("redis-server")
    if not redis_server:
        pytest.skip("redis-server executable is required for combined recovery acceptance")

    engine = create_engine(
        TEST_POSTGRES_URL, pool_size=5, max_overflow=0, pool_pre_ping=True
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    db_session = Session()
    user_id = uuid4()
    suffix = uuid4().hex[:10]
    from app.core.security import hash_password
    user = User(
        id=user_id, email=f"redis-recovery-{suffix}@example.invalid",
        password_hash=hash_password("test-only-password"),
        full_name="Redis restart PostgreSQL PAPER recovery", is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    portfolio = Portfolio(
        user_id=user.id, name="Redis restart PAPER recovery",
        virtual_capital=Decimal("100000"), cash_balance=Decimal("100000"),
        is_active=True,
    )
    instrument = Instrument(
        instrument_key=f"NSE_EQ|{uuid4().hex[:12]}", exchange="NSE",
        segment="NSE_EQ", instrument_type="EQUITY",
        trading_symbol=f"RR{suffix.upper()}", name="Redis restart PAPER recovery",
    )
    db_session.add_all([portfolio, instrument])
    db_session.flush()
    strategy = Strategy(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        name="Redis restart trailing stop", segment="EQUITY_INTRADAY",
        quantity=1, is_active=True, max_daily_loss=1000,
        trailing_stop_pct=Decimal("2"), current_watermark=Decimal("100"),
    )
    position = Position(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        quantity=2, avg_price=Decimal("100"), realized_pnl=Decimal("0"),
    )
    db_session.add_all([strategy, position])
    db_session.add(BrokerConnection(
        user_id=user.id, broker="upstox",
        api_key_encrypted=encrypt_value("test-key"),
        api_secret_encrypted=encrypt_value("test-secret"),
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted=encrypt_value("test-access"),
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        analytics_token_encrypted=encrypt_value("test-analytics"),
        analytics_token_expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        is_connected=True,
    ))
    db_session.commit()
    monkeypatch.setattr(handler, "SessionLocal", Session)

    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]
    redis_url = f"redis://127.0.0.1:{port}/0"
    data_dir = tmp_path / "redis-recovery-data"
    data_dir.mkdir()

    def start_redis():
        return subprocess.Popen(
            [
                redis_server, "--bind", "127.0.0.1", "--port", str(port),
                "--protected-mode", "no", "--save", "", "--appendonly", "no",
                "--dir", str(data_dir),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    async def wait_redis(client, process):
        deadline = asyncio.get_running_loop().time() + 8
        while asyncio.get_running_loop().time() < deadline:
            if process.poll() is not None:
                raise AssertionError("Redis exited before becoming ready")
            try:
                if await client.ping():
                    return
            except Exception:
                await asyncio.sleep(0.05)
        raise AssertionError("Redis did not become ready")

    server = start_redis()
    redis = Redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=1)
    instrument_key = instrument.instrument_key
    publisher = RedisMarketQuotePublisher(redis, user.id, ttl_seconds=15)
    consumer = RedisMarketQuoteConsumer(redis, user.id, max_age_seconds=15)
    dispatcher = MarketQuoteDispatcher(max_pending_keys=4)
    scanner = MarketScanner()
    pipeline = MarketScanDispatchPipeline(scanner=scanner, dispatcher=dispatcher)
    claim_execution_entered = asyncio.Event()
    worker_task = None
    original_execute_claimed = PaperStopEventExecutionService.execute_claimed

    async def pause_after_claim_commit(self, **kwargs):
        claim_execution_entered.set()
        await asyncio.Future()

    try:
        await wait_redis(redis, server)
        now = datetime.now(timezone.utc)
        tick = MarketTick(
            instrument_key=instrument_key, ltp=97.0,
            exchange_timestamp_ms=int(now.timestamp() * 1000),
            received_at=now, received_monotonic=1.0,
            volume_traded_today=1200, open_interest=4500,
            total_buy_quantity=700, total_sell_quantity=300,
            ohlc=({"interval": "1d", "close": 100.0},),
        )
        assert await publisher.publish(tick)
        original_quote = await consumer.get_quote(instrument_key)
        assert original_quote is not None

        # Stop the worker only after the intake service committed the durable
        # CLAIMED event, but before the execution transaction can begin.
        monkeypatch.setattr(
            PaperStopEventExecutionService, "execute_claimed", pause_after_claim_commit
        )
        dispatch_worker = MarketQuoteDispatchWorker(
            dispatcher, handle_paper_market_observation,
            min_backoff_seconds=0, max_backoff_seconds=0, max_attempts=5,
            on_exhausted=lambda item: scanner.clear_instrument(
                item.user_id, item.instrument_key
            ),
        )
        with _quote_patch(instrument):
            worker_task = asyncio.create_task(dispatch_worker.run())
            assert pipeline.on_quote(user.id, original_quote) is True
            await asyncio.wait_for(claim_execution_entered.wait(), timeout=5)

            db_session.expire_all()
            claimed = db_session.query(PaperStopEvent).filter(
                PaperStopEvent.user_id == user.id,
                PaperStopEvent.instrument_id == instrument.id,
                PaperStopEvent.quote_epoch == original_quote["epoch"],
                PaperStopEvent.quote_version == original_quote["version"],
            ).one()
            event_id, old_claim_token = claimed.id, claimed.claim_token
            assert claimed.state == "CLAIMED"

            worker_task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await worker_task
            worker_task = None
            # The in-memory dispatcher retains the item on cancellation, but
            # a process restart discards that queue. PostgreSQL is authoritative.
            assert dispatcher.pending_keys == 1
            assert dispatcher.inflight_keys == 0

        server.terminate()
        await asyncio.to_thread(server.wait, 5)
        assert await consumer.get_quote(instrument_key) is None

        server = start_redis()
        await wait_redis(redis, server)
        restarted_tick = MarketTick(
            instrument_key=instrument_key, ltp=96.0,
            exchange_timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000),
            received_at=datetime.now(timezone.utc), received_monotonic=2.0,
            volume_traded_today=1300, open_interest=4600,
            ohlc=({"interval": "1d", "close": 100.0},),
        )
        assert await publisher.publish(restarted_tick)
        restarted_quote = await consumer.get_quote(instrument_key)
        assert restarted_quote is not None
        assert restarted_quote["epoch"] != original_quote["epoch"]
        assert restarted_quote["version"] == 1

        # Restore the real execution method. Expire the durable claim to model
        # process death after commit; the PostgreSQL sweeper must recover it
        # without relying on the lost Redis queue or the new Redis epoch.
        monkeypatch.setattr(
            PaperStopEventExecutionService, "execute_claimed", original_execute_claimed
        )
        db_session.expire_all()
        claimed = db_session.get(PaperStopEvent, event_id)
        claimed.claimed_until = datetime.now(timezone.utc) - timedelta(seconds=1)
        db_session.commit()

        with patch(
            "app.services.execution_service.settings.UPSTOX_CHARGE_ESTIMATES_ENABLED",
            False,
        ), _quote_patch(instrument):
            recovered_count = await handler.recover_expired_paper_stop_events_once()
            assert recovered_count == 1

            db_session.expire_all()
            completed = db_session.get(PaperStopEvent, event_id)
            saved_order = db_session.query(Order).filter(
                Order.paper_stop_event_id == event_id
            ).one()
            saved_token = completed.claim_token
            assert completed.state == "COMPLETED"
            assert saved_token != old_claim_token
            assert completed.attempt_count == 2
            assert saved_order.status == "FILLED"
            assert saved_order.trading_mode == "PAPER"

            # A duplicate delivery carrying the recovered claim token returns
            # the original order and cannot apply a second fill or ledger row.
            duplicate = await PaperStopEventExecutionService(db_session).execute_claimed(
                user_id=user.id, event_id=event_id, claim_token=saved_token,
            )
            assert duplicate.id == saved_order.id

        db_session.refresh(portfolio)
        db_session.refresh(position)
        assert position.quantity == 0
        assert portfolio.cash_balance > Decimal("100000")
        assert db_session.query(PaperStopEvent).filter(
            PaperStopEvent.user_id == user.id,
            PaperStopEvent.instrument_id == instrument.id,
        ).count() == 1
        assert db_session.query(Order).filter(
            Order.paper_stop_event_id == event_id
        ).count() == 1
        assert db_session.query(Execution).filter(
            Execution.order_id == saved_order.id
        ).count() == 1
        assert dispatcher.pending_keys == 1  # Lost with the simulated process; never reused.
    finally:
        if worker_task is not None:
            worker_task.cancel()
            await asyncio.gather(worker_task, return_exceptions=True)
        await redis.aclose()
        try:
            server.terminate()
            await asyncio.to_thread(server.wait, 5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            server.kill()
            await asyncio.to_thread(server.wait)
        cleanup_ids = {
            "portfolio": str(portfolio.id),
            "strategy": str(strategy.id),
            "instrument": str(instrument.id),
            "user": str(user.id),
        }
        db_session.close()
        with engine.begin() as connection:
            cleanup = (
                ("DELETE FROM executions WHERE portfolio_id = :id", cleanup_ids["portfolio"]),
                ("DELETE FROM orders WHERE portfolio_id = :id", cleanup_ids["portfolio"]),
                ("DELETE FROM paper_stop_events WHERE strategy_id = :id", cleanup_ids["strategy"]),
                ("DELETE FROM positions WHERE portfolio_id = :id", cleanup_ids["portfolio"]),
                ("DELETE FROM strategies WHERE id = :id", cleanup_ids["strategy"]),
                ("DELETE FROM broker_connections WHERE user_id = :id", cleanup_ids["user"]),
                ("DELETE FROM portfolios WHERE id = :id", cleanup_ids["portfolio"]),
                ("DELETE FROM instruments WHERE id = :id", cleanup_ids["instrument"]),
                ("DELETE FROM users WHERE id = :id", cleanup_ids["user"]),
            )
            for statement, value in cleanup:
                connection.execute(text(statement), {"id": value})
        engine.dispose()
