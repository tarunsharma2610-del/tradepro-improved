"""Bounded, coalescing single-flight dispatch for validated market observations.

At most one consumer may process a user/instrument key at a time. Updates
arriving during processing are coalesced and become eligible only after the
current consumer acknowledges completion. This is in-process coordination;
durable cross-replica ownership remains the PostgreSQL claim-token service.
"""
import asyncio
from dataclasses import dataclass
from typing import Any


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
            return True

        if len(self._pending) + len(self._inflight) >= self._queue.maxsize:
            self.dropped_unique_keys += 1
            return False

        self._pending[key] = DispatchedMarketObservation(
            user_id, instrument_key, epoch, version, observation
        )
        self._queue.put_nowait(key)
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

    def task_done(self) -> None:
        """Acknowledge the current task's item and release any coalesced update."""
        task = asyncio.current_task()
        key = self._consumer_keys.pop(task, None) if task is not None else None
        if key is None:
            raise ValueError("task_done must be called by the task that received the item.")
        self._inflight.pop(key, None)
        self._queue.task_done()
        pending = self._pending.get(key)
        if pending is not None:
            # The queue slot was freed by get(); requeue exactly one coalesced
            # latest value, making the key eligible for another consumer.
            self._queue.put_nowait(key)

    @property
    def pending_keys(self) -> int:
        return len(self._pending)

    @property
    def inflight_keys(self) -> int:
        return len(self._inflight)

    @property
    def capacity(self) -> int:
        return self._queue.maxsize
