"""Low-cardinality, process-local counters for PAPER market-data operations.

These counters are operational hints, not a fleet-wide source of truth.
A multi-replica deployment must scrape each process or export to a shared
metrics backend before aggregating values. No user or instrument identifiers
are ever recorded here.
"""
from threading import Lock

_lock = Lock()
_counters: dict[str, int] = {}


def increment(name: str, amount: int = 1) -> None:
    if not name or not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
        raise ValueError("Metric name and non-negative integer increment are required.")
    with _lock:
        _counters[name] = _counters.get(name, 0) + amount


def snapshot() -> dict[str, object]:
    with _lock:
        return {
            "scope": "process_local",
            "trading_mode": "PAPER",
            "counters": dict(sorted(_counters.items())),
        }
