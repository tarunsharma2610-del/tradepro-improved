"""End-to-end PAPER acceptance: real Redis snapshot through scanner to ledger.

This test intentionally exercises the production Redis publisher/consumer,
scanner/dispatcher and durable PAPER stop-event handler. It never invokes a
broker order-write endpoint; the execution service's market quote is stubbed.
"""
import asyncio
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from redis.asyncio import Redis

from app.core.encryption import encrypt_value
from app.models.broker_connection import BrokerConnection
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.services.market_quote_dispatcher import MarketQuoteDispatcher
from app.services.market_scanner import MarketScanner
from app.services.market_quote_dispatch_worker import MarketQuoteDispatchWorker
from app.services.market_scan_dispatch_pipeline import MarketScanDispatchPipeline
from app.services.paper_stop_event_dispatch_handler import handle_paper_market_observation
from app.services.redis_market_quote_consumer import RedisMarketQuoteConsumer
from app.services.redis_market_quote_publisher import RedisMarketQuotePublisher
from app.services.upstox_market_data_streamer import MarketTick

REDIS_TEST_URL = os.getenv("REDIS_TEST_URL")
pytestmark = pytest.mark.skipif(
    not REDIS_TEST_URL, reason="REDIS_TEST_URL is required for real Redis acceptance"
)


class _SessionProxy:
    """Keep the pytest-owned DB session open across production handler scopes."""

    def __init__(self, session):
        self._session = session

    def __getattr__(self, name):
        return getattr(self._session, name)

    def close(self):
        return None


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
async def test_real_redis_snapshot_reaches_durable_paper_fill_and_ledger(
    db_session, make_user, monkeypatch
):
    from unittest.mock import patch
    import app.services.paper_stop_event_dispatch_handler as handler

    user = make_user(email=f"redis-paper-{uuid4().hex}@example.invalid")
    portfolio = Portfolio(
        user_id=user.id, name="Redis PAPER acceptance",
        virtual_capital=Decimal("100000"), cash_balance=Decimal("100000"),
        is_active=True,
    )
    instrument = Instrument(
        instrument_key=f"NSE_EQ|{uuid4().hex[:12]}", exchange="NSE",
        segment="NSE_EQ", instrument_type="EQUITY",
        trading_symbol="REDISPAPER", name="Redis PAPER acceptance",
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

    monkeypatch.setattr(handler, "SessionLocal", lambda: _SessionProxy(db_session))
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
