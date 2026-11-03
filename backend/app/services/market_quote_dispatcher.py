"""Bounded, coalescing single-flight dispatch for validated market observations.

At most one consumer may process a user/instrument key at a time. Updates
arriving during processing are coalesced and become eligible only after the
current consumer acknowledges completion. This is in-process coordination;
durable cross-replica ownership remains the PostgreSQL claim-token service.
"""
import asyncio
from dataclasses import dataclass
from typing import Any

from app.services.market_data_metrics import increment


@dataclass(frozen=True)
class DispatchedMarketObservation:
    user_id: str
    instrument_key: str
    epoch: str
    version: int
    observation: Any


class MarketQuoteDispatcher:
    """Bounded FIFO by key with single-flight and latest-value coalescing."""

    def __init__(self, *, max_pending_keys: int = 1024) -> None:
        if isinstance(max_pending_keys, bool) or not isinstance(max_pending_keys, int) or max_pending_keys <= 0:
            raise ValueError("Dispatcher capacity must be a positive integer.")
        self._queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue(maxsize=max_pending_keys)
        self._pending: dict[tuple[str, str], DispatchedMarketObservation] = {}
        self._inflight: dict[tuple[str, str], DispatchedMarketObservation] = {}
        self._consumer_keys: dict[asyncio.Task, tuple[str, str]] = {}
        self.dropped_unique_keys = 0
        self.rejected_updates = 0

    def publish(self, observation: Any) -> bool:
        """Enqueue/coalesce an already validated observation without awaiting."""
        try:
            user_id = str(observation.user_id)
            instrument_key = observation.instrument_key
            epoch = observation.epoch
            version = observation.version
        except (AttributeError, TypeError):
            self.rejected_updates += 1
            increment("market_quote_dispatch_rejected_total")
            return False
        if (
            not user_id or not isinstance(instrument_key, str) or not instrument_key
            or not isinstance(epoch, str) or not epoch
            or isinstance(version, bool) or not isinstance(version, int) or version <= 0
        ):
            self.rejected_updates += 1
            return False

        key = (user_id, instrument_key)
        previous = self._pending.get(key) or self._inflight.get(key)
        if previous is not None:
            if previous.epoch == epoch and version <= previous.version:
                self.rejected_updates += 1
                return False
            self._pending[key] = DispatchedMarketObservation(
                user_id, instrument_key, epoch, version, observation
            )
            increment("market_quote_dispatch_coalesced_total")
            return True

        if len(self._pending) + len(self._inflight) >= self._queue.maxsize:
            self.dropped_unique_keys += 1
            increment("market_quote_dispatch_dropped_unique_total")
            return False

        self._pending[key] = DispatchedMarketObservation(
            user_id, instrument_key, epoch, version, observation
        )
        self._queue.put_nowait(key)
        increment("market_quote_dispatch_accepted_unique_total")
        return True

    async def get(self) -> DispatchedMarketObservation:
        """Wait for an eligible key and mark it in-flight for this consumer."""
        key = await self._queue.get()
        item = self._pending.pop(key, None)
        if item is None or key in self._inflight:
            self._queue.task_done()
            raise RuntimeError("Dispatcher queue/in-flight invariant violated.")
        task = asyncio.current_task()
        if task is None or task in self._consumer_keys:
            self._queue.task_done()
            raise RuntimeError("Each dispatcher consumer must acknowledge before its next get.")
        self._inflight[key] = item
        self._consumer_keys[task] = key
        return item

    def _finish_current(self, *, requeue_current: bool) -> None:
        task = asyncio.current_task()
        key = self._consumer_keys.pop(task, None) if task is not None else None
        if key is None:
            raise ValueError("The current task does not own a dispatcher item.")
        current = self._inflight.pop(key, None)
        if requeue_current and key not in self._pending and current is not None:
            # Cancellation/worker shutdown before durable handling must not
            # silently discard the only observation for this key.
            self._pending[key] = current
        self._queue.task_done()
        if key in self._pending:
            # A newer coalesced value wins over the interrupted in-flight one.
            # get() freed a queue slot, so exactly one key can be requeued.
            self._queue.put_nowait(key)

    def task_done(self) -> None:
        """Acknowledge successful handling and release a coalesced update."""
        self._finish_current(requeue_current=False)

    def release(self) -> None:
        """Release an interrupted item, retrying it unless a newer quote exists.

        Call from the same consumer task that called get(), typically in the
        CancelledError/finally path. Durable claim/execution idempotency makes
        replay after an uncertain commit safe; callers must still bound their
        own retry/backoff policy for repeated processing failures.
        """
        self._finish_current(requeue_current=True)

    @property
    def pending_keys(self) -> int:
        return len(self._pending)

    @property
    def inflight_keys(self) -> int:
        return len(self._inflight)

    @property
    def capacity(self) -> int:
        return self._queue.maxsize
