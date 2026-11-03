"""Concurrent producer/consumer load test for the PAPER quote dispatcher.

This is a repeatable CI smoke benchmark, not an end-to-end production SLA.
Producers and workers run concurrently; the bounded queue is intentionally
smaller than the workload so the test exercises real queue backpressure.
"""
import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path

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
async def test_sustained_dispatch_load_records_throughput_and_latency():
    observation_count = 5_000
    worker_count = 8
    queue_capacity = 512
    dispatcher = MarketQuoteDispatcher(max_pending_keys=queue_capacity)
    enqueued_at = {}
    latencies_ms = []
    processed = 0
    rejected = 0

    async def handle(dispatched):
        nonlocal processed
        key = (dispatched.user_id, dispatched.instrument_key)
        latencies_ms.append((time.perf_counter() - enqueued_at[key]) * 1000)
        processed += 1
        # Yield to the event loop so concurrent workers genuinely interleave.
        await asyncio.sleep(0)

    workers = [
        asyncio.create_task(MarketQuoteDispatchWorker(dispatcher, handle).run())
        for _ in range(worker_count)
    ]
    started = time.perf_counter()
    try:
        # Producer remains active while workers consume. Yield periodically to
        # let consumers run and make queue saturation/backpressure observable.
        for index in range(observation_count):
            item = _BenchmarkObservation(
                user_id=f"benchmark-user-{index % 100}",
                instrument_key=f"NSE_EQ|BENCHMARK-{index}",
                epoch="benchmark-epoch",
            )
            key = (item.user_id, item.instrument_key)
            enqueued_at[key] = time.perf_counter()
            if not dispatcher.publish(item):
                rejected += 1
            if index % 25 == 24:
                await asyncio.sleep(0)

        await asyncio.wait_for(dispatcher._queue.join(), timeout=60)
    finally:
        for task in workers:
            task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    elapsed_seconds = time.perf_counter() - started
    assert rejected == 0, f"dispatcher rejected {rejected} observations"
    assert processed == observation_count
    assert len(latencies_ms) == observation_count
    assert dispatcher.dropped_unique_keys == 0
    assert dispatcher.pending_keys == 0
    assert dispatcher.inflight_keys == 0

    ordered = sorted(latencies_ms)
    def percentile(p):
        return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p))]

    result = {
        "observations": processed,
        "workers": worker_count,
        "queue_capacity": queue_capacity,
        "elapsed_seconds": round(elapsed_seconds, 6),
        "throughput_observations_per_second": round(processed / elapsed_seconds, 2),
        "latency_p50_ms": round(percentile(0.50), 4),
        "latency_p95_ms": round(percentile(0.95), 4),
        "latency_p99_ms": round(percentile(0.99), 4),
        "rejected_observations": rejected,
        "dropped_unique_keys": dispatcher.dropped_unique_keys,
    }
    Path("dispatch-benchmark-results.json").write_text(
        json.dumps(result, indent=2) + "\\n", encoding="utf-8"
    )
