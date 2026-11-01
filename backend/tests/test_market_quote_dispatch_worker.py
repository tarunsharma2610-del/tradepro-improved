import asyncio
from dataclasses import dataclass

import pytest

from app.services.market_quote_dispatcher import MarketQuoteDispatcher
from app.services.market_quote_dispatch_worker import MarketQuoteDispatchWorker


@dataclass(frozen=True)
class Observation:
    user_id: str = "user-a"
    instrument_key: str = "NSE_EQ|TEST"
    epoch: str = "epoch-1"
    version: int = 1
    ltp: float = 100.0


@pytest.mark.asyncio
async def test_worker_retries_failed_handler_with_bounded_backoff_then_acks(monkeypatch):
    dispatcher = MarketQuoteDispatcher(max_pending_keys=2)
    dispatcher.publish(Observation())
    attempts = []
    completed = asyncio.Event()

    async def handler(item):
        attempts.append(item.version)
        if len(attempts) == 1:
            raise RuntimeError("transient")
        completed.set()

    sleeps = []

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr("app.services.market_quote_dispatch_worker.asyncio.sleep", fake_sleep)
    worker = MarketQuoteDispatchWorker(
        dispatcher, handler, min_backoff_seconds=0.1, max_backoff_seconds=0.2
    )
    task = asyncio.create_task(worker.run())
    await asyncio.wait_for(completed.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert attempts == [1, 1]
    assert sleeps == [0.1]
    assert worker.failure_count == 1
    assert worker.processed_count == 1
    assert dispatcher.pending_keys == 0
    assert dispatcher.inflight_keys == 0


@pytest.mark.asyncio
async def test_worker_cancellation_releases_inflight_quote_for_next_worker():
    dispatcher = MarketQuoteDispatcher(max_pending_keys=2)
    dispatcher.publish(Observation())
    entered = asyncio.Event()
    never = asyncio.Event()

    async def blocked_handler(_item):
        entered.set()
        await never.wait()

    worker = MarketQuoteDispatchWorker(dispatcher, blocked_handler)
    task = asyncio.create_task(worker.run())
    await asyncio.wait_for(entered.wait(), timeout=1)
    assert dispatcher.inflight_keys == 1

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert dispatcher.inflight_keys == 0
    assert dispatcher.pending_keys == 1
    retry = await dispatcher.get()
    assert retry.version == 1
    dispatcher.task_done()


@pytest.mark.asyncio
async def test_worker_shutdown_does_not_drop_newer_coalesced_quote():
    dispatcher = MarketQuoteDispatcher(max_pending_keys=2)
    dispatcher.publish(Observation(version=1, ltp=100))
    entered = asyncio.Event()
    never = asyncio.Event()

    async def blocked_handler(_item):
        entered.set()
        await never.wait()

    task = asyncio.create_task(MarketQuoteDispatchWorker(dispatcher, blocked_handler).run())
    await asyncio.wait_for(entered.wait(), timeout=1)
    dispatcher.publish(Observation(version=2, ltp=101))
    dispatcher.publish(Observation(version=3, ltp=102))
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    retry = await dispatcher.get()
    assert retry.version == 3
    assert retry.observation.ltp == 102
    dispatcher.task_done()
    assert dispatcher.pending_keys == dispatcher.inflight_keys == 0


def test_worker_rejects_invalid_backoff_bounds():
    dispatcher = MarketQuoteDispatcher()

    async def handler(_item):
        return None

    with pytest.raises(ValueError):
        MarketQuoteDispatchWorker(
            dispatcher, handler, min_backoff_seconds=2, max_backoff_seconds=1
        )
