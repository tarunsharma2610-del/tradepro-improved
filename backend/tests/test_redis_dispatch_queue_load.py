"""Bounded real-Redis quote-to-dispatch load evidence (PAPER only).

This measures Redis snapshot publication/read plus the in-process scanner and
dispatcher. The handler is deliberately synthetic: PostgreSQL execution
throughput is measured by the separate PostgreSQL PAPER benchmark.
"""
import asyncio
import json
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from redis.asyncio import Redis

from app.services.market_quote_dispatcher import MarketQuoteDispatcher
from app.services.market_quote_dispatch_worker import MarketQuoteDispatchWorker
from app.services.market_scan_dispatch_pipeline import MarketScanDispatchPipeline
from app.services.market_scanner import MarketScanner
from app.services.redis_market_quote_consumer import RedisMarketQuoteConsumer
from app.services.redis_market_quote_publisher import RedisMarketQuotePublisher
from app.services.upstox_market_data_streamer import MarketTick

REDIS_TEST_URL = os.getenv("REDIS_TEST_URL")
pytestmark = pytest.mark.skipif(
    not REDIS_TEST_URL, reason="real Redis 7 service is required"
)


def _percentile(values, fraction):
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(len(ordered) * fraction + 0.999999) - 1))
    return round(ordered[index], 3)


@pytest.mark.asyncio
async def test_real_redis_quote_dispatch_load_and_latency_report():
    user_id = uuid4()
    instrument_count = 48
    worker_count = 4
    keys = [f"NSE_EQ|LOAD{index:05d}" for index in range(instrument_count)]
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=15)
    consumer = RedisMarketQuoteConsumer(redis, user_id, max_age_seconds=15)
    dispatcher = MarketQuoteDispatcher(max_pending_keys=64)
    pipeline = MarketScanDispatchPipeline(
        scanner=MarketScanner(), dispatcher=dispatcher
    )
    submitted_at = {}
    latencies_ms = []
    completed = 0
    completion = asyncio.Event()
    peak_queued = 0
    handler_delay_seconds = 0.002

    async def handle(item):
        nonlocal completed
        await asyncio.sleep(handler_delay_seconds)
        latencies_ms.append((time.perf_counter() - submitted_at[item.instrument_key]) * 1000)
        completed += 1
        if completed == instrument_count:
            completion.set()

    workers = [
        MarketQuoteDispatchWorker(
            dispatcher, handle, min_backoff_seconds=0,
            max_backoff_seconds=0, max_attempts=1,
        )
        for _ in range(worker_count)
    ]
    tasks = []
    started = time.perf_counter()
    try:
        assert await redis.ping()
        memory_before = int((await redis.info("memory"))["used_memory"])
        tasks = [asyncio.create_task(worker.run()) for worker in workers]

        for index, key in enumerate(keys):
            now = datetime.now(timezone.utc)
            submitted_at[key] = time.perf_counter()
            tick = MarketTick(
                instrument_key=key,
                ltp=100.0 + index,
                exchange_timestamp_ms=int(now.timestamp() * 1000),
                received_at=now,
                received_monotonic=time.monotonic(),
                volume_traded_today=1000 + index,
                open_interest=5000 + index,
            )
            assert await publisher.publish(tick)
            quote = await consumer.get_quote(key)
            assert quote is not None
            assert pipeline.on_quote(user_id, quote)
            peak_queued = max(
                peak_queued, dispatcher.pending_keys + dispatcher.inflight_keys
            )

        async with asyncio.timeout(15):
            await completion.wait()
        elapsed = time.perf_counter() - started
        ping_started = time.perf_counter()
        assert await redis.ping()
        ping_latency_ms = (time.perf_counter() - ping_started) * 1000
        memory_after = int((await redis.info("memory"))["used_memory"])

        assert completed == instrument_count
        assert dispatcher.pending_keys == 0
        assert dispatcher.inflight_keys == 0
        assert pipeline.accepted_observations == instrument_count
        assert pipeline.rejected_quotes == 0
        assert pipeline.rejected_dispatches == 0

        report = {
            "mode": "PAPER",
            "measurement_scope": "real Redis snapshot publish/read plus in-process scanner/dispatcher; synthetic handler, no PostgreSQL execution",
            "redis_service": "Redis 7 (CI service)",
            "unique_instruments": instrument_count,
            "workers": worker_count,
            "dispatcher_capacity": dispatcher.capacity,
            "completed": completed,
            "failed": sum(worker.failure_count for worker in workers),
            "elapsed_seconds": round(elapsed, 4),
            "completed_per_second": round(completed / elapsed, 2),
            "publish_to_handler_latency_ms": {
                "p50": _percentile(latencies_ms, 0.50),
                "p95": _percentile(latencies_ms, 0.95),
                "p99": _percentile(latencies_ms, 0.99),
                "mean": round(statistics.fmean(latencies_ms), 3),
            },
            "queue": {
                "peak_pending_plus_inflight": peak_queued,
                "pending_after_drain": dispatcher.pending_keys,
                "inflight_after_drain": dispatcher.inflight_keys,
                "accepted_unique": pipeline.accepted_observations,
                "rejected_unique": pipeline.rejected_dispatches,
            },
            "redis": {
                "used_memory_before_bytes": memory_before,
                "used_memory_after_bytes": memory_after,
                "ping_latency_ms": round(ping_latency_ms, 3),
            },
            "handler_delay_ms": handler_delay_seconds * 1000,
            "scope_limit": "bounded CI transport/dispatch measurement, not a sustained soak, PostgreSQL benchmark, production capacity or SLA certification",
        }
        Path("redis-dispatch-load-results.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await redis.delete(*[
            key_name
            for instrument_key in keys
            for key_name in (
                publisher.snapshot_key(instrument_key),
                publisher.snapshot_key(instrument_key) + ":version",
            )
        ])
        await redis.aclose()
