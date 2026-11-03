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
        self.sets = {}
        self.dedupe = set()
        self.raise_after_commit_once = False

    async def eval(self, script, numkeys, *args):
        assert numkeys == 4
        totals_key, worker_key, dedupe_key, workers_key = args[:4]
        ttl, worker_id, worker_ttl, worker_hash_ttl = args[4:8]
        if dedupe_key in self.dedupe:
            return 0
        self.dedupe.add(dedupe_key)
        self.sets.setdefault(workers_key, set()).add(worker_id)
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

    async def scard(self, key):
        return len(self.sets.get(key, set()))


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


async def test_redis_exporter_aggregates_deltas_from_multiple_worker_replicas():
    before = snapshot()["counters"]
    redis = _FakeRedis()
    worker_a = RedisDispatchMetricsExporter(worker_id="worker-a")
    worker_b = RedisDispatchMetricsExporter(worker_id="worker-b")

    increment("market_quote_dispatch_processed_total", 3)
    assert await worker_a.flush_once(redis) is True
    increment("market_quote_dispatch_processed_total", 2)
    assert await worker_b.flush_once(redis) is True

    result = await fleet_snapshot(redis)
    assert result["scope"] == "fleet_aggregated"
    assert result["source"] == "redis_atomic_counters"
    assert result["trading_mode"] == "PAPER"
    assert result["worker_count"] == 2
    assert result["counters"]["market_quote_dispatch_processed_total"] == (
        5 + before["market_quote_dispatch_processed_total"]
    )


async def test_redis_exporter_retry_after_lost_response_does_not_double_count():
    import pytest

    redis = _FakeRedis()
    exporter = RedisDispatchMetricsExporter(worker_id="worker-retry")
    increment("market_quote_dispatch_handler_failures_total", 4)
    redis.raise_after_commit_once = True

    with pytest.raises(ConnectionError, match="lost Redis response"):
        await exporter.flush_once(redis)

    # The exporter retries the same sequence. Redis's atomic dedupe marker
    # reports the prior commit instead of applying the batch twice.
    assert await exporter.flush_once(redis) is True
    result = await fleet_snapshot(redis)
    assert result["counters"]["market_quote_dispatch_handler_failures_total"] == 4
    assert result["worker_count"] == 1


async def test_redis_exporter_does_not_repeat_an_already_flushed_delta():
    redis = _FakeRedis()
    exporter = RedisDispatchMetricsExporter(worker_id="worker-stable")
    increment("market_quote_dispatch_exhausted_total", 2)

    assert await exporter.flush_once(redis) is True
    assert await exporter.flush_once(redis) is False
    result = await fleet_snapshot(redis)
    assert result["counters"]["market_quote_dispatch_exhausted_total"] == 2
