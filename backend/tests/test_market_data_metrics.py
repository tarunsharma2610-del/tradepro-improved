import pytest

from app.services.market_data_metrics import (
    RedisDispatchMetricsExporter,
    _ALLOWED_COUNTERS,
    fleet_snapshot,
    increment,
    snapshot,
)
from app.services.market_quote_dispatcher import MarketQuoteDispatcher


class _Observation:
    def __init__(self, instrument_key, version):
        self.user_id = "opaque-test-user"
        self.instrument_key = instrument_key
        self.epoch = "epoch-1"
        self.version = version


class _FakeRedis:
    """Small deterministic Redis model for the export Lua contract."""

    def __init__(self):
        self.hashes = {}
        self.sorted_sets = {}
        self.dedupe = set()
        self.raise_after_commit_once = False
        self.now_ms = 1_800_000_000_000

    async def eval(self, script, numkeys, *args):
        assert numkeys == 4
        totals_key, worker_key, dedupe_key, workers_key = args[:4]
        ttl, worker_id, worker_ttl, worker_hash_ttl = args[4:8]
        if dedupe_key in self.dedupe:
            return 0
        self.dedupe.add(dedupe_key)
        workers = self.sorted_sets.setdefault(workers_key, {})
        workers[worker_id] = self.now_ms
        for stale_id, score in list(workers.items()):
            if score <= self.now_ms - int(worker_ttl):
                workers.pop(stale_id, None)
        totals = self.hashes.setdefault(totals_key, {})
        worker = self.hashes.setdefault(worker_key, {})
        for index in range(8, len(args), 2):
            name, amount = args[index], int(args[index + 1])
            totals[name] = totals.get(name, 0) + amount
            worker[name] = worker.get(name, 0) + amount
        if self.raise_after_commit_once:
            self.raise_after_commit_once = False
            raise ConnectionError("simulated lost Redis response after commit")
        return 1

    async def hgetall(self, key):
        return dict(self.hashes.get(key, {}))

    async def time(self):
        return (self.now_ms // 1000, (self.now_ms % 1000) * 1000)

    async def zremrangebyscore(self, key, minimum, maximum):
        workers = self.sorted_sets.setdefault(key, {})
        stale = [worker for worker, score in workers.items() if score <= int(maximum)]
        for worker in stale:
            workers.pop(worker, None)
        return len(stale)

    async def zcard(self, key):
        return len(self.sorted_sets.get(key, {}))


def test_market_data_metrics_are_aggregate_process_local_and_paper_only():
    result = snapshot()

    assert result["scope"] == "process_local"
    assert result["trading_mode"] == "PAPER"
    assert isinstance(result["counters"], dict)
    assert not any("user" in key or "instrument" in key for key in result["counters"])


def test_dispatcher_updates_operational_counters_for_accept_coalesce_drop_and_reject():
    before = snapshot()["counters"]
    dispatcher = MarketQuoteDispatcher(max_pending_keys=1)

    assert dispatcher.publish(_Observation("NSE_EQ|ONE", 1))
    assert dispatcher.publish(_Observation("NSE_EQ|ONE", 2))
    assert not dispatcher.publish(_Observation("NSE_EQ|TWO", 1))
    assert not dispatcher.publish(_Observation("NSE_EQ|ONE", 1))

    after = snapshot()["counters"]
    assert after["market_quote_dispatch_accepted_unique_total"] - before.get(
        "market_quote_dispatch_accepted_unique_total", 0
    ) == 1
    assert after["market_quote_dispatch_coalesced_total"] - before.get(
        "market_quote_dispatch_coalesced_total", 0
    ) == 1
    assert after["market_quote_dispatch_dropped_unique_total"] - before.get(
        "market_quote_dispatch_dropped_unique_total", 0
    ) == 1
    assert after["market_quote_dispatch_rejected_total"] - before.get(
        "market_quote_dispatch_rejected_total", 0
    ) == 1
    assert "opaque-test-user" not in repr(after)
    assert "NSE_EQ|ONE" not in repr(after)


def test_metric_names_are_allowlisted_to_prevent_unbounded_cardinality():
    import pytest

    with pytest.raises(ValueError, match="Unknown market-data metric"):
        increment("market_quote_dispatch_user_secret_123")


def test_snapshot_exposes_fixed_zero_initialized_counter_set():
    result = snapshot()
    assert result["scope"] == "process_local"
    assert result["trading_mode"] == "PAPER"
    assert len(result["counters"]) == len(_ALLOWED_COUNTERS)
    assert all(isinstance(value, int) and value >= 0 for value in result["counters"].values())


@pytest.mark.asyncio
async def test_redis_exporter_aggregates_deltas_from_multiple_worker_replicas():
    redis = _FakeRedis()
    local_a = {name: 0 for name in _ALLOWED_COUNTERS}
    local_b = {name: 0 for name in _ALLOWED_COUNTERS}
    provider_a = lambda: {"counters": dict(local_a)}
    provider_b = lambda: {"counters": dict(local_b)}
    worker_a = RedisDispatchMetricsExporter(
        worker_id="worker-a", snapshot_provider=provider_a
    )
    worker_b = RedisDispatchMetricsExporter(
        worker_id="worker-b", snapshot_provider=provider_b
    )

    local_a["market_quote_dispatch_processed_total"] += 3
    assert await worker_a.flush_once(redis) is True
    local_b["market_quote_dispatch_processed_total"] += 2
    assert await worker_b.flush_once(redis) is True

    result = await fleet_snapshot(redis)
    assert result["scope"] == "fleet_aggregated"
    assert result["source"] == "redis_atomic_counters"
    assert result["trading_mode"] == "PAPER"
    assert result["worker_count"] == 2
    assert result["counters"]["market_quote_dispatch_processed_total"] == 5


@pytest.mark.asyncio
async def test_redis_exporter_retry_after_lost_response_does_not_double_count():
    import pytest

    redis = _FakeRedis()
    local = {name: 0 for name in _ALLOWED_COUNTERS}
    exporter = RedisDispatchMetricsExporter(
        worker_id="worker-retry",
        snapshot_provider=lambda: {"counters": dict(local)},
    )
    local["market_quote_dispatch_handler_failures_total"] += 4
    redis.raise_after_commit_once = True

    with pytest.raises(ConnectionError, match="lost Redis response"):
        await exporter.flush_once(redis)

    # New events can arrive while the previous response is uncertain. The
    # exporter must retry the frozen batch first, then flush the new delta.
    local["market_quote_dispatch_handler_failures_total"] += 3
    assert await exporter.flush_once(redis) is True
    assert await exporter.flush_once(redis) is True
    result = await fleet_snapshot(redis)
    assert result["counters"]["market_quote_dispatch_handler_failures_total"] == 7
    assert result["worker_count"] == 1


@pytest.mark.asyncio
async def test_redis_exporter_does_not_repeat_an_already_flushed_delta():
    redis = _FakeRedis()
    local = {name: 0 for name in _ALLOWED_COUNTERS}
    exporter = RedisDispatchMetricsExporter(
        worker_id="worker-stable",
        snapshot_provider=lambda: {"counters": dict(local)},
    )
    local["market_quote_dispatch_exhausted_total"] += 2

    assert await exporter.flush_once(redis) is True
    assert await exporter.flush_once(redis) is False
    result = await fleet_snapshot(redis)
    assert result["counters"]["market_quote_dispatch_exhausted_total"] == 2


@pytest.mark.asyncio
async def test_fleet_worker_count_excludes_workers_without_recent_heartbeat():
    redis = _FakeRedis()
    local = {name: 0 for name in _ALLOWED_COUNTERS}
    exporter = RedisDispatchMetricsExporter(
        worker_id="worker-temporary",
        snapshot_provider=lambda: {"counters": dict(local)},
    )
    local["market_quote_dispatch_processed_total"] = 1
    await exporter.flush_once(redis)

    assert (await fleet_snapshot(redis))["worker_count"] == 1

    redis.now_ms += 61_000
    assert (await fleet_snapshot(redis))["worker_count"] == 0



@pytest.mark.asyncio
async def test_real_redis_concurrent_worker_exporters_preserve_fleet_totals():
    """Exercise concurrent independent exporter replicas against real Redis."""
    import asyncio
    import os
    from uuid import uuid4

    from redis.asyncio import Redis
    from app.services import market_data_metrics as metrics

    redis_url = os.getenv("REDIS_TEST_URL")
    if not redis_url:
        pytest.skip("REDIS_TEST_URL is required for real Redis metrics integration")

    redis = Redis.from_url(redis_url, decode_responses=True)
    replica_count = 8
    flushes_per_replica = 25
    counter = "market_quote_dispatch_processed_total"
    worker_ids = [f"load-{uuid4().hex}" for _ in range(replica_count)]
    exporters = []
    try:
        before = await fleet_snapshot(redis)
        for worker_id in worker_ids:
            local = {name: 0 for name in _ALLOWED_COUNTERS}
            exporters.append((
                local,
                RedisDispatchMetricsExporter(
                    worker_id=worker_id,
                    snapshot_provider=lambda state=local: {"counters": dict(state)},
                ),
            ))

        async def run_replica(local, exporter):
            for _ in range(flushes_per_replica):
                local[counter] += 1
                assert await exporter.flush_once(redis) is True

        await asyncio.gather(*(run_replica(local, exporter) for local, exporter in exporters))

        after = await fleet_snapshot(redis)
        assert after["counters"][counter] - before["counters"][counter] == (
            replica_count * flushes_per_replica
        )
        assert after["worker_count"] >= replica_count
        assert all(local[counter] == flushes_per_replica for local, _ in exporters)
    finally:
        await redis.zrem(metrics._WORKERS_KEY, *worker_ids)
        cleanup_keys = [f"{metrics._WORKER_KEY_PREFIX}{worker_id}" for worker_id in worker_ids]
        cleanup_keys.extend(
            f"{metrics._FLUSH_KEY_PREFIX}{worker_id}:{sequence}"
            for worker_id in worker_ids
            for sequence in range(flushes_per_replica)
        )
        if cleanup_keys:
            await redis.delete(*cleanup_keys)
        await redis.aclose()
