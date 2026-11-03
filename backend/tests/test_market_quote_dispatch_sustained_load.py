"""Deterministic sustained-dispatch smoke benchmark.

This measures in-process PAPER quote dispatch under a bounded multi-worker
load. It deliberately has no machine-specific throughput pass threshold:
CI records throughput and enqueue-to-handler latency so results can be compared
on the same runner over time. It does not simulate Upstox/network/DB latency.
"""
import asyncio
import time
from dataclasses import dataclass

import pytest

from app.services.market_quote_dispatcher import MarketQuoteDispatcher
from app.services.market_quote_dispatch_worker import MarketQuoteDispatchWorker


@dataclass(frozen=True)
class _BenchmarkObservation:
    user_id: str
    instrument_key: str
    epoch: str
    version: int = 1


@pytest.mark.asyncio
async def test_sustained_dispatch_load_records_throughput_and_latency(record_property):
    observation_count = 5_000
    worker_count = 8
    dispatcher = MarketQuoteDispatcher(max_pending_keys=observation_count)
    enqueued_at = {}
    latencies_ms = []
    processed = 0

    started = time.perf_counter()
    for index in range(observation_count):
        item = _BenchmarkObservation(
            user_id=f"benchmark-user-{index % 100}",
            instrument_key=f"NSE_EQ|BENCHMARK-{index}",
            epoch="benchmark-epoch",
        )
        key = (item.user_id, item.instrument_key)
        enqueued_at[key] = time.perf_counter()
        assert dispatcher.publish(item)

    async def handle(dispatched):
        nonlocal processed
        key = (dispatched.user_id, dispatched.instrument_key)
        latencies_ms.append((time.perf_counter() - enqueued_at[key]) * 1000)
        processed += 1

    workers = [
        asyncio.create_task(MarketQuoteDispatchWorker(dispatcher, handle).run())
        for _ in range(worker_count)
    ]
    try:
        await asyncio.wait_for(dispatcher._queue.join(), timeout=60)
    finally:
        for task in workers:
            task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    elapsed_seconds = time.perf_counter() - started
    assert processed == observation_count
    assert len(latencies_ms) == observation_count
    assert dispatcher.dropped_unique_keys == 0
    assert dispatcher.pending_keys == 0
    assert dispatcher.inflight_keys == 0

    ordered = sorted(latencies_ms)
    percentile = lambda p: ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p))]
    throughput = processed / elapsed_seconds
    record_property("dispatch_observations", processed)
    record_property("dispatch_workers", worker_count)
    record_property("dispatch_elapsed_seconds", round(elapsed_seconds, 6))
    record_property("dispatch_throughput_observations_per_second", round(throughput, 2))
    record_property("dispatch_latency_p50_ms", round(percentile(0.50), 4))
    record_property("dispatch_latency_p95_ms", round(percentile(0.95), 4))
    record_property("dispatch_latency_p99_ms", round(percentile(0.99), 4))
    record_property("dispatch_dropped_unique_keys", dispatcher.dropped_unique_keys)
