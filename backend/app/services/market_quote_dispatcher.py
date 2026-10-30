"""Bounded, coalescing in-process dispatch for validated market observations.

This component deliberately performs no database, broker, or order work.
It retains at most one pending observation per user/instrument key and
coalesces newer updates while that key is waiting to be consumed.
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
    """Bounded FIFO by key with latest-value coalescing per key."""

    def __init__(self, *, max_pending_keys: int = 1024) -> None:
        if isinstance(max_pending_keys, bool) or not isinstance(max_pending_keys, int) or max_pending_keys <= 0:
            raise ValueError("Dispatcher capacity must be a positive integer.")
        self._queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue(maxsize=max_pending_keys)
        self._pending: dict[tuple[str, str], DispatchedMarketObservation] = {}
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
        previous = self._pending.get(key)
        if previous is not None:
            if previous.epoch == epoch and version <= previous.version:
                self.rejected_updates += 1
                return False
            # The scanner/consumer owns epoch validation. For a new accepted
            # epoch, replace the pending value while preserving this key's FIFO slot.
            self._pending[key] = DispatchedMarketObservation(
                user_id, instrument_key, epoch, version, observation
            )
            return True

        if self._queue.full():
            self.dropped_unique_keys += 1
            return False

        self._pending[key] = DispatchedMarketObservation(
            user_id, instrument_key, epoch, version, observation
        )
        self._queue.put_nowait(key)
        return True

    async def get(self) -> DispatchedMarketObservation:
        """Wait for the next key and atomically take its newest pending value."""
        key = await self._queue.get()
        item = self._pending.pop(key, None)
        if item is None:
            # Defensive invariant guard; queue keys and pending entries are
            # mutated synchronously on the same event loop.
            self._queue.task_done()
            return await self.get()
        return item

    def task_done(self) -> None:
        self._queue.task_done()

    @property
    def pending_keys(self) -> int:
        return len(self._pending)

    @property
    def capacity(self) -> int:
        return self._queue.maxsize
