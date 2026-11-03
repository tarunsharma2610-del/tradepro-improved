"""Low-cardinality, process-local counters for PAPER market-data operations.

These counters are operational hints, not a fleet-wide source of truth.
A multi-replica deployment must scrape each process or export to a shared
metrics backend before aggregating values. No user or instrument identifiers
are ever recorded here.
"""
from threading import Lock

_ALLOWED_COUNTERS = frozenset({
    "market_quote_dispatch_accepted_unique_total",
    "market_quote_dispatch_coalesced_total",
    "market_quote_dispatch_dropped_unique_total",
    "market_quote_dispatch_rejected_total",
    "market_quote_dispatch_handler_failures_total",
    "market_quote_dispatch_exhausted_total",
    "market_quote_dispatch_processed_total",
})

_lock = Lock()
_counters: dict[str, int] = {}


def increment(name: str, amount: int = 1) -> None:
    if name not in _ALLOWED_COUNTERS:
        raise ValueError("Unknown market-data metric counter.")
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
        raise ValueError("Metric increment must be a non-negative integer.")
    with _lock:
        _counters[name] = _counters.get(name, 0) + amount


def snapshot() -> dict[str, object]:
    with _lock:
        return {
            "scope": "process_local",
            "trading_mode": "PAPER",
            "counters": {
                name: _counters.get(name, 0)
                for name in sorted(_ALLOWED_COUNTERS)
            },
        }
