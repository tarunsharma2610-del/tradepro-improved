"""Low-cardinality PAPER market-data counters and Redis fleet aggregation.

Local counters are cheap and synchronous for dispatcher hot paths. The worker
periodically exports monotonic deltas to Redis using an idempotent batch key,
so multiple worker replicas contribute to one fleet total without double
counting a retry after an uncertain Redis response. The local snapshot remains
available for unit tests and process diagnostics; admin reads use fleet totals.
No user or instrument identifiers are recorded.
"""
from threading import Lock
from typing import Callable
from uuid import uuid4

_ALLOWED_COUNTERS = frozenset({
    "market_quote_dispatch_accepted_unique_total",
    "market_quote_dispatch_coalesced_total",
    "market_quote_dispatch_dropped_unique_total",
    "market_quote_dispatch_rejected_total",
    "market_quote_dispatch_handler_failures_total",
    "market_quote_dispatch_exhausted_total",
    "market_quote_dispatch_processed_total",
})

_TOTALS_KEY = "tradepro:metrics:v1:market-quote-dispatch:totals"
_WORKERS_KEY = "tradepro:metrics:v1:market-quote-dispatch:workers"
_WORKER_KEY_PREFIX = "tradepro:metrics:v1:market-quote-dispatch:worker:"
_FLUSH_KEY_PREFIX = "tradepro:metrics:v1:market-quote-dispatch:flush:"
_FLUSH_LUA = """
if redis.call('EXISTS', KEYS[3]) == 1 then
    return 0
end
redis.call('SET', KEYS[3], '1', 'EX', ARGV[1])
local now = redis.call('TIME')
local now_ms = (tonumber(now[1]) * 1000) + math.floor(tonumber(now[2]) / 1000)
redis.call('ZADD', KEYS[4], now_ms, ARGV[2])
redis.call('ZREMRANGEBYSCORE', KEYS[4], '-inf', now_ms - ARGV[3])
for i = 5, #ARGV, 2 do
    redis.call('HINCRBY', KEYS[1], ARGV[i], ARGV[i + 1])
    redis.call('HINCRBY', KEYS[2], ARGV[i], ARGV[i + 1])
end
redis.call('EXPIRE', KEYS[2], ARGV[4])
return 1
"""

_lock = Lock()
_counters: dict[str, int] = {}


def increment(name: str, amount: int = 1) -> None:
    """Increment one fixed, low-cardinality process-local counter."""
    if name not in _ALLOWED_COUNTERS:
        raise ValueError("Unknown market-data metric counter.")
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
        raise ValueError("Metric increment must be a non-negative integer.")
    with _lock:
        _counters[name] = _counters.get(name, 0) + amount


def snapshot() -> dict[str, object]:
    """Return this process's counters; never mistake these for fleet totals."""
    with _lock:
        return {
            "scope": "process_local",
            "trading_mode": "PAPER",
            "counters": {
                name: _counters.get(name, 0)
                for name in sorted(_ALLOWED_COUNTERS)
            },
        }


class RedisDispatchMetricsExporter:
    """Idempotently export local counter deltas into shared Redis totals."""

    def __init__(
        self,
        *,
        worker_id: str | None = None,
        snapshot_provider: Callable[[], dict[str, object]] = snapshot,
    ) -> None:
        self.worker_id = worker_id or uuid4().hex
        self._snapshot_provider = snapshot_provider
        self._last_flushed = dict(snapshot_provider()["counters"])
        self._sequence = 0
        self._pending_batch = None

    async def flush_once(self, redis_client) -> bool:
        """Flush one delta batch; safe to retry the same sequence after errors.

        Redis Lua makes the dedupe marker and all counter increments atomic.
        A duplicate sequence is treated as already applied, which handles the
        case where Redis committed but the client lost the response.
        """
        if self._pending_batch is None:
            current = self._snapshot_provider()["counters"]
            deltas = {
                name: current[name] - self._last_flushed[name]
                for name in sorted(_ALLOWED_COUNTERS)
            }
            if any(value < 0 for value in deltas.values()):
                raise RuntimeError("Process-local metric counters unexpectedly regressed.")
            # Freeze the exact payload across retries. If Redis committed but
            # its response was lost, later local increments belong to the next
            # sequence and must not be marked flushed by the dedupe response.
            self._pending_batch = (dict(current), dict(deltas))
        current, deltas = self._pending_batch

        sequence = self._sequence
        worker_key = f"{_WORKER_KEY_PREFIX}{self.worker_id}"
        dedupe_key = f"{_FLUSH_KEY_PREFIX}{self.worker_id}:{sequence}"
        args = [86400, self.worker_id, 60, 604800]
        for name, amount in deltas.items():
            args.extend((name, amount))

        await redis_client.eval(
            _FLUSH_LUA,
            4,
            _TOTALS_KEY,
            worker_key,
            dedupe_key,
            _WORKERS_KEY,
            *args,
        )
        self._last_flushed = dict(current)
        self._sequence += 1
        self._pending_batch = None
        return any(deltas.values())


async def _active_worker_count(redis_client) -> int:
    """Count workers with a heartbeat in the last 60 seconds."""
    server_time = await redis_client.time()
    now_ms = (int(server_time[0]) * 1000) + (int(server_time[1]) // 1000)
    await redis_client.zremrangebyscore(_WORKERS_KEY, "-inf", now_ms - 60000)
    return int(await redis_client.zcard(_WORKERS_KEY))


async def fleet_snapshot(redis_client) -> dict[str, object]:
    """Read shared PAPER counters; caller handles Redis availability errors."""
    raw = await redis_client.hgetall(_TOTALS_KEY)
    counters = {}
    for name in sorted(_ALLOWED_COUNTERS):
        value = raw.get(name, raw.get(name.encode()))
        counters[name] = int(value or 0)
        if counters[name] < 0:
            raise RuntimeError("Redis market-data metric counter is invalid.")
    return {
        "scope": "fleet_aggregated",
        "source": "redis_atomic_counters",
        "worker_count": int(await _active_worker_count(redis_client)),
        "trading_mode": "PAPER",
        "counters": counters,
    }
