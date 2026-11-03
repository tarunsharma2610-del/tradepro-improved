"""PostgreSQL-backed concurrent PAPER stop-event handler load smoke test.

This benchmark drives the production durable handler and PAPER accounting path
through the bounded dispatcher. It uses a fake market-depth adapter and a
dedicated PostgreSQL test database; it never submits broker order writes.
The separate Redis acceptance test covers Redis snapshot ingestion.
"""
import asyncio
import os
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
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
from app.services.market_quote_dispatcher import (
    DispatchedMarketObservation,
    MarketQuoteDispatcher,
)
from app.services.market_quote_dispatch_worker import MarketQuoteDispatchWorker
from app.services.market_scanner import MarketScanObservation
from app.services.paper_stop_event_dispatch_handler import handle_paper_market_observation


pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_POSTGRES_URL"),
    reason="requires dedicated PostgreSQL 16 test database",
)


def _seed(Session, count: int):
    suffix = uuid4().hex[:12]
    user_id = uuid4()
    portfolio_ids = [uuid4() for _ in range(count)]
    instrument_ids = [uuid4() for _ in range(count)]
    strategy_ids = [uuid4() for _ in range(count)]
    with Session.begin() as db:
        db.add(User(
            id=user_id,
            email=f"paper-load-{suffix}@example.invalid",
            password_hash="test-only",
            full_name="PAPER sustained-load test",
            is_admin=False,
        ))
        db.flush()
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
        for index, (portfolio_id, instrument_id, strategy_id) in enumerate(
            zip(portfolio_ids, instrument_ids, strategy_ids, strict=True)
        ):
            db.add(Portfolio(
                id=portfolio_id,
                user_id=user_id,
                name=f"paper-load-{suffix}-{index}",
                virtual_capital=Decimal("100000.00"),
                cash_balance=Decimal("100000.00"),
                is_active=True,
            ))
            db.add(Instrument(
                id=instrument_id,
                instrument_key=f"TEST|PAPER-LOAD|{suffix}|{index}",
                exchange="NSE",
                segment="NSE_EQ",
                instrument_type="EQUITY",
                trading_symbol=f"PLOAD{suffix[:6]}{index}",
                name="PAPER sustained-load instrument",
            ))
            db.add(Strategy(
                id=strategy_id,
                portfolio_id=portfolio_id,
                instrument_id=instrument_id,
                name=f"paper-load-strategy-{suffix}-{index}",
                segment="EQUITY_INTRADAY",
                quantity=2,
                is_active=True,
                max_daily_loss=Decimal("1000.00"),
                trailing_stop_pct=Decimal("2"),
                current_watermark=Decimal("100.00"),
            ))
            db.add(Position(
                portfolio_id=portfolio_id,
                instrument_id=instrument_id,
                quantity=2,
                avg_price=Decimal("100.00"),
                realized_pnl=Decimal("0.00"),
            ))
    return user_id, portfolio_ids, instrument_ids, strategy_ids


def _cleanup(Session, ids):
    user_id, portfolio_ids, instrument_ids, strategy_ids = ids
    with Session.begin() as db:
        for portfolio_id in portfolio_ids:
            db.execute(text("DELETE FROM executions WHERE portfolio_id = :id"), {"id": str(portfolio_id)})
            db.execute(text("DELETE FROM orders WHERE portfolio_id = :id"), {"id": str(portfolio_id)})
            db.execute(text("DELETE FROM positions WHERE portfolio_id = :id"), {"id": str(portfolio_id)})
        for strategy_id in strategy_ids:
            db.execute(text("DELETE FROM paper_stop_events WHERE strategy_id = :id"), {"id": str(strategy_id)})
            db.execute(text("DELETE FROM strategies WHERE id = :id"), {"id": str(strategy_id)})
        db.execute(text("DELETE FROM broker_connections WHERE user_id = :id"), {"id": str(user_id)})
        for portfolio_id in portfolio_ids:
            db.execute(text("DELETE FROM portfolios WHERE id = :id"), {"id": str(portfolio_id)})
        for instrument_id in instrument_ids:
            db.execute(text("DELETE FROM instruments WHERE id = :id"), {"id": str(instrument_id)})
        db.execute(text("DELETE FROM users WHERE id = :id"), {"id": str(user_id)})


@pytest.mark.asyncio
async def test_postgres_paper_stop_event_handler_sustained_load(monkeypatch, record_property):
    """Run 12 real DB-backed PAPER fills through four concurrent dispatch workers."""
    observation_count = 12
    worker_count = 4
    engine = create_engine(
        os.environ["TEST_POSTGRES_URL"],
        pool_size=worker_count * 2,
        max_overflow=worker_count,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    ids = _seed(Session, observation_count)
    user_id, portfolio_ids, instrument_ids, strategy_ids = ids

    import app.services.paper_stop_event_dispatch_handler as handler
    import app.services.execution_service as execution_service

    monkeypatch.setattr(handler, "SessionLocal", Session)
    monkeypatch.setattr(
        execution_service.settings, "UPSTOX_CHARGE_ESTIMATES_ENABLED", False
    )

    quote_requests = []

    class FakeAdapter:
        async def get_full_quote(self, access_token, instrument_tokens):
            instrument_key = instrument_tokens[0]
            quote_requests.append(instrument_key)
            # Let other dispatch workers overlap their DB-backed execution path.
            await asyncio.sleep(0.005)
            now = datetime.now(timezone.utc)
            level = {"price": "97.00", "quantity": 100000, "orders": 10}
            quote = {
                "instrument_token": instrument_key,
                "last_price": "97.00",
                "last_trade_time": str(int(now.timestamp() * 1000)),
                "timestamp": now.isoformat(),
                "depth": {"buy": [level], "sell": [level]},
            }
            return BrokerCallResult(
                ok=True, data={"data": {instrument_key: quote}}
            )

    monkeypatch.setattr(
        execution_service, "get_broker_adapter", lambda broker: FakeAdapter()
    )

    dispatcher = MarketQuoteDispatcher(max_pending_keys=observation_count)
    enqueue_times = {}
    completion_latencies_ms = []

    now = datetime.now(timezone.utc)
    epoch = f"paper-load-{uuid4().hex}"
    for index, instrument_id in enumerate(instrument_ids):
        with Session() as db:
            instrument = db.get(Instrument, instrument_id)
            instrument_key = instrument.instrument_key
        observation = MarketScanObservation(
            user_id=str(user_id),
            instrument_key=instrument_key,
            epoch=epoch,
            version=index + 1,
            ltp=97.0,
            price_change_pct=-3.0,
            volume_traded_today=1000,
            open_interest=None,
            buy_sell_imbalance=None,
            option_greeks=None,
            exchange_timestamp_ms=int(now.timestamp() * 1000),
            received_at=now.isoformat(),
        )
        item = DispatchedMarketObservation(
            user_id=str(user_id),
            instrument_key=instrument_key,
            epoch=epoch,
            version=index + 1,
            observation=observation,
        )
        assert dispatcher.publish(item)
        enqueue_times[(item.instrument_key, item.version)] = time.perf_counter()

    async def handle(item):
        await handle_paper_market_observation(item)
        key = (item.instrument_key, item.version)
        completion_latencies_ms.append(
            (time.perf_counter() - enqueue_times[key]) * 1000
        )

    workers = [
        MarketQuoteDispatchWorker(
            dispatcher, handle, min_backoff_seconds=0, max_backoff_seconds=0,
            max_attempts=3,
        )
        for _ in range(worker_count)
    ]
    tasks = [asyncio.create_task(worker.run()) for worker in workers]
    started = time.perf_counter()
    try:
        try:
            await asyncio.wait_for(dispatcher._queue.join(), timeout=90)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.perf_counter() - started

        assert sum(worker.processed_count for worker in workers) == observation_count
        assert sum(worker.failure_count for worker in workers) == 0
        assert len(completion_latencies_ms) == observation_count
        assert len(quote_requests) == observation_count
        assert dispatcher.pending_keys == 0
        assert dispatcher.inflight_keys == 0

        ordered = sorted(completion_latencies_ms)
        def percentile(p):
            return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p))]

        metrics = {
            "observations": observation_count,
            "workers": worker_count,
            "elapsed_seconds": round(elapsed, 6),
            "throughput_fills_per_second": round(observation_count / elapsed, 2),
            "completion_latency_p50_ms": round(percentile(0.50), 3),
            "completion_latency_p95_ms": round(percentile(0.95), 3),
            "completion_latency_p99_ms": round(percentile(0.99), 3),
        }
        for key, value in metrics.items():
            record_property(key, value)

        with Session() as db:
            events = db.query(PaperStopEvent).filter(
                PaperStopEvent.user_id == user_id,
                PaperStopEvent.quote_epoch == epoch,
            ).all()
            orders = db.query(Order).filter(
                Order.portfolio_id.in_(portfolio_ids),
            ).all()
            executions = db.query(Execution).filter(
                Execution.portfolio_id.in_(portfolio_ids),
            ).all()
            positions = db.query(Position).filter(
                Position.portfolio_id.in_(portfolio_ids),
            ).all()
            portfolios = db.query(Portfolio).filter(
                Portfolio.id.in_(portfolio_ids),
            ).all()
            assert len(events) == observation_count
            assert all(event.state == "COMPLETED" for event in events)
            assert len(orders) == observation_count
            assert all(order.status == "FILLED" and order.trading_mode == "PAPER" for order in orders)
            assert len(executions) == observation_count
            assert len({execution.order_id for execution in executions}) == observation_count
            assert len(positions) == observation_count
            assert all(position.quantity == 0 for position in positions)
            assert len(portfolios) == observation_count
            assert all(portfolio.cash_balance > Decimal("100000.00") for portfolio in portfolios)
    finally:
        _cleanup(Session, ids)
        engine.dispose()
