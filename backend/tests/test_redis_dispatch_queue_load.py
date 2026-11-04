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
    queue_wait_ms = []
    completed = 0
    completion = asyncio.Event()
    peak_queued = 0
    handler_delay_seconds = 0.01

    async def handle(item):
        nonlocal completed
        handler_started = time.monotonic()
        queue_wait_ms.append((handler_started - item.enqueued_at_monotonic) * 1000)
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

        async def publish_and_dispatch(index, key):
            nonlocal peak_queued
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

        # Concurrent producers intentionally build a measurable queue backlog;
        # serial publishing would mostly benchmark Redis round-trip latency.
        await asyncio.gather(*(
            publish_and_dispatch(index, key)
            for index, key in enumerate(keys)
        ))

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
            "queue_wait_latency_ms": {
                "p50": _percentile(queue_wait_ms, 0.50),
                "p95": _percentile(queue_wait_ms, 0.95),
                "p99": _percentile(queue_wait_ms, 0.99),
                "mean": round(statistics.fmean(queue_wait_ms), 3),
                "samples": len(queue_wait_ms),
                "definition": "dispatcher admission timestamp to worker handler start; excludes Redis publish and snapshot read",
            },
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


@pytest.mark.asyncio
async def test_real_dispatcher_capacity_saturation_and_backpressure_report():
    """Prove unique-key overload is bounded and accepted work drains."""
    user_id = uuid4()
    instrument_count = 48
    worker_count = 4
    capacity = 16
    keys = [f"NSE_EQ|SAT{index:05d}" for index in range(instrument_count)]
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=15)
    consumer = RedisMarketQuoteConsumer(redis, user_id, max_age_seconds=15)
    dispatcher = MarketQuoteDispatcher(max_pending_keys=capacity)
    pipeline = MarketScanDispatchPipeline(
        scanner=MarketScanner(), dispatcher=dispatcher
    )
    accepted = 0
    rejected = 0
    peak_depth = 0
    completed = 0
    queue_wait_ms = []
    completion = asyncio.Event()
    tasks = []

    async def handle(item):
        nonlocal completed
        queue_wait_ms.append(
            (time.monotonic() - item.enqueued_at_monotonic) * 1000
        )
        await asyncio.sleep(0.01)
        completed += 1
        if completed == accepted:
            completion.set()

    workers = [
        MarketQuoteDispatchWorker(
            dispatcher, handle, min_backoff_seconds=0,
            max_backoff_seconds=0, max_attempts=1,
        )
        for _ in range(worker_count)
    ]
    try:
        assert await redis.ping()
        # No consumers are running yet: this intentionally fills the bounded
        # dispatcher, so overload policy is exercised deterministically.
        for index, key in enumerate(keys):
            now = datetime.now(timezone.utc)
            tick = MarketTick(
                instrument_key=key,
                ltp=200.0 + index,
                exchange_timestamp_ms=int(now.timestamp() * 1000),
                received_at=now,
                received_monotonic=time.monotonic(),
                volume_traded_today=2000 + index,
                open_interest=6000 + index,
            )
            assert await publisher.publish(tick)
            quote = await consumer.get_quote(key)
            assert quote is not None
            if pipeline.on_quote(user_id, quote):
                accepted += 1
            else:
                rejected += 1
            depth = dispatcher.pending_keys + dispatcher.inflight_keys
            peak_depth = max(peak_depth, depth)
            assert depth <= capacity

        assert accepted > 0
        assert accepted <= capacity
        assert rejected > 0
        assert accepted + rejected == instrument_count
        assert dispatcher.pending_keys == accepted
        assert dispatcher.inflight_keys == 0
        assert dispatcher.dropped_unique_keys == rejected

        tasks = [asyncio.create_task(worker.run()) for worker in workers]
        async with asyncio.timeout(15):
            await completion.wait()

        assert completed == accepted
        assert dispatcher.pending_keys == 0
        assert dispatcher.inflight_keys == 0
        assert len(queue_wait_ms) == accepted
        assert peak_depth == capacity
        assert pipeline.accepted_observations == accepted
        assert pipeline.rejected_dispatches == rejected
        assert dispatcher.dropped_unique_keys == rejected

        report = {
            "mode": "PAPER",
            "measurement_scope": "real Redis quote snapshots plus actual bounded dispatcher and supervised workers; synthetic handler, no PostgreSQL execution",
            "unique_instruments_offered": instrument_count,
            "dispatcher_capacity": capacity,
            "workers": worker_count,
            "accepted_unique": accepted,
            "rejected_unique_at_capacity": rejected,
            "coalesced_updates": 0,
            "peak_pending_plus_inflight": peak_depth,
            "completed_accepted_work": completed,
            "pending_after_drain": dispatcher.pending_keys,
            "inflight_after_drain": dispatcher.inflight_keys,
            "queue_wait_latency_ms": {
                "p50": _percentile(queue_wait_ms, 0.50),
                "p95": _percentile(queue_wait_ms, 0.95),
                "p99": _percentile(queue_wait_ms, 0.99),
                "mean": round(statistics.fmean(queue_wait_ms), 3),
                "samples": len(queue_wait_ms),
            },
            "overload_policy": "reject new unique keys at configured capacity; preserve admitted keys; caller clears scanner high-water for rejected instrument so authoritative Redis snapshot sweep can retry",
            "scope_limit": "bounded deterministic saturation test, not a sustained overload soak or production capacity/SLA certification",
        }
        Path("redis-dispatch-saturation-results.json").write_text(
            json.dumps(report, indent=2) + "\\n", encoding="utf-8"
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



@pytest.mark.asyncio
async def test_rejected_keys_are_reswept_to_latest_version_during_quote_churn():
    """A full queue must not strand instruments whose snapshots keep changing."""
    user_id = uuid4()
    instrument_count = 48
    worker_count = 4
    capacity = 16
    keys = [f"NSE_EQ|RESWEEP{index:05d}" for index in range(instrument_count)]
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=15)
    consumer = RedisMarketQuoteConsumer(redis, user_id)
    dispatcher = MarketQuoteDispatcher(max_pending_keys=capacity)
    pipeline = MarketScanDispatchPipeline(
        scanner=MarketScanner(), dispatcher=dispatcher
    )
    handler_gate = asyncio.Event()
    four_workers_started = asyncio.Event()
    first_wave_drained = asyncio.Event()
    all_latest_processed = asyncio.Event()
    started_handlers = 0
    processed_versions = {}
    tasks = []

    async def handle(item):
        nonlocal started_handlers
        started_handlers += 1
        if started_handlers == worker_count:
            four_workers_started.set()
        await handler_gate.wait()
        processed_versions[item.instrument_key] = item.version
        if all(processed_versions.get(key) == 4 for key in keys[:capacity]):
            first_wave_drained.set()
        if (
            len(processed_versions) == instrument_count
            and all(version == 4 for version in processed_versions.values())
        ):
            all_latest_processed.set()

    workers = [
        MarketQuoteDispatchWorker(
            dispatcher, handle, min_backoff_seconds=0,
            max_backoff_seconds=0, max_attempts=1,
        )
        for _ in range(worker_count)
    ]

    async def publish_version(index, instrument_key, version):
        now = datetime.now(timezone.utc)
        tick = MarketTick(
            instrument_key=instrument_key,
            ltp=100.0 + index + version,
            exchange_timestamp_ms=int(now.timestamp() * 1000),
            received_at=now,
            received_monotonic=time.monotonic(),
            volume_traded_today=1000 + index,
            open_interest=5000 + index,
        )
        assert await publisher.publish(tick)
        quote = await consumer.get_quote(instrument_key)
        assert quote is not None
        assert quote["version"] == version
        return pipeline.on_quote(user_id, quote)

    try:
        assert await redis.ping()

        # Fill all 16 slots with the first version before workers start.
        for index, key in enumerate(keys):
            accepted = await publish_version(index, key, 1)
            assert accepted is (index < capacity)

        assert dispatcher.pending_keys == capacity
        assert dispatcher.inflight_keys == 0
        assert dispatcher.dropped_unique_keys == instrument_count - capacity

        tasks = [asyncio.create_task(worker.run()) for worker in workers]
        async with asyncio.timeout(5):
            await four_workers_started.wait()

        # Hold all four workers in-flight while every instrument publishes
        # newer snapshots. The first 16 coalesce; the other 32 are rejected
        # repeatedly and their scanner high-water entries are cleared.
        for version in (2, 3, 4):
            for index, key in enumerate(keys):
                accepted = await publish_version(index, key, version)
                assert accepted is (index < capacity)

        # Four in-flight keys may each hold one coalesced latest value in
        # pending, so the transient bound is queue capacity plus worker count.
        assert dispatcher.pending_keys == capacity
        assert dispatcher.inflight_keys == worker_count
        assert dispatcher.pending_keys + dispatcher.inflight_keys == capacity + worker_count
        assert pipeline.rejected_dispatches == (instrument_count - capacity) * 4

        handler_gate.set()
        async with asyncio.timeout(10):
            await first_wave_drained.wait()

        assert len(processed_versions) == capacity
        assert all(processed_versions[key] == 4 for key in keys[:capacity])
        await dispatcher._queue.join()
        assert dispatcher.pending_keys == 0
        assert dispatcher.inflight_keys == 0

        # This is the same authoritative snapshot sweep used by the Redis
        # consumer after its recovery interval. Previously rejected keys must
        # now be admitted using their latest version, not an old Pub/Sub event.
        recovered = await consumer.recover(keys)
        assert set(recovered) == set(keys)
        resweep_accepted = 0
        resweep_duplicates = 0
        for key, quote in recovered.items():
            if pipeline.on_quote(user_id, quote):
                resweep_accepted += 1
            else:
                resweep_duplicates += 1

        assert resweep_accepted == instrument_count - capacity
        assert resweep_duplicates == capacity

        async with asyncio.timeout(10):
            await all_latest_processed.wait()
        await dispatcher._queue.join()

        assert set(processed_versions) == set(keys)
        assert all(version == 4 for version in processed_versions.values())
        assert dispatcher.pending_keys == 0
        assert dispatcher.inflight_keys == 0
        assert dispatcher._queue.qsize() == 0
        # Accepted counter includes three coalesced updates for each of the
        # original 16 admitted keys, plus the 32 keys admitted by resweep.
        assert pipeline.accepted_observations == capacity * 4 + (instrument_count - capacity)
        assert pipeline.rejected_dispatches == (instrument_count - capacity) * 4
    finally:
        handler_gate.set()
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
