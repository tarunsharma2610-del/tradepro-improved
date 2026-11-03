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



@pytest.mark.asyncio
async def test_two_workers_never_process_same_user_instrument_concurrently():
    dispatcher = MarketQuoteDispatcher(max_pending_keys=2)
    assert dispatcher.publish(Observation(version=1))
    first_entered = asyncio.Event()
    release_first = asyncio.Event()
    second_entered = asyncio.Event()
    seen = []
    active = 0
    max_active = 0

    async def handler(item):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        seen.append(item.version)
        try:
            if item.version == 1:
                first_entered.set()
                await release_first.wait()
            elif item.version == 2:
                second_entered.set()
        finally:
            active -= 1

    # Hold the first quote in-flight, then add a newer coalesced quote while
    # another worker is available. Either worker may receive the successor;
    # the invariant is that the same key is never handled concurrently.
    workers = [
        asyncio.create_task(MarketQuoteDispatchWorker(dispatcher, handler).run())
    ]
    await asyncio.wait_for(first_entered.wait(), timeout=1)
    workers.append(
        asyncio.create_task(MarketQuoteDispatchWorker(dispatcher, handler).run())
    )
    assert dispatcher.publish(Observation(version=2, ltp=101))
    await asyncio.sleep(0)
    assert not second_entered.is_set()
    assert active == 1
    assert max_active == 1

    release_first.set()
    await asyncio.wait_for(second_entered.wait(), timeout=1)
    assert seen == [1, 2]
    assert max_active == 1

    for _ in range(100):
        if dispatcher.pending_keys == 0 and dispatcher.inflight_keys == 0:
            break
        await asyncio.sleep(0)
    assert dispatcher.pending_keys == 0
    assert dispatcher.inflight_keys == 0
    await asyncio.wait_for(dispatcher._queue.join(), timeout=1)

    for task in workers:
        task.cancel()
    for task in workers:
        with pytest.raises(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_worker_pool_bounds_unique_keys_and_accounts_for_queue_completion():
    dispatcher = MarketQuoteDispatcher(max_pending_keys=2)
    assert dispatcher.publish(Observation(instrument_key="NSE_EQ|ONE"))
    assert dispatcher.publish(Observation(instrument_key="NSE_EQ|TWO"))
    assert not dispatcher.publish(Observation(instrument_key="NSE_EQ|THREE"))
    assert dispatcher.dropped_unique_keys == 1

    entered = []
    release = asyncio.Event()
    both_entered = asyncio.Event()

    async def handler(item):
        entered.append(item.instrument_key)
        if len(entered) == 2:
            both_entered.set()
        await release.wait()

    worker_instances = [MarketQuoteDispatchWorker(dispatcher, handler) for _ in range(2)]
    workers = [asyncio.create_task(worker.run()) for worker in worker_instances]
    await asyncio.wait_for(both_entered.wait(), timeout=1)
    assert set(entered) == {"NSE_EQ|ONE", "NSE_EQ|TWO"}
    assert dispatcher.inflight_keys == 2
    assert dispatcher.pending_keys == 0

    release.set()
    async def wait_for_acknowledgements():
        while sum(worker.processed_count for worker in worker_instances) != 2:
            await asyncio.sleep(0)
    await asyncio.wait_for(wait_for_acknowledgements(), timeout=1)

    # Check the queue accounting before cancelling idle consumers. Cancellation
    # must not be used as a substitute for acknowledgement of completed work.
    assert dispatcher.pending_keys == 0
    assert dispatcher.inflight_keys == 0
    await asyncio.wait_for(dispatcher._queue.join(), timeout=1)

    for task in workers:
        task.cancel()
    for task in workers:
        with pytest.raises(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_exhausted_quote_releases_worker_and_preserves_newer_coalesced_snapshot(monkeypatch):
    dispatcher = MarketQuoteDispatcher(max_pending_keys=2)
    assert dispatcher.publish(Observation(version=1))
    first_attempt = asyncio.Event()
    allow_retry = asyncio.Event()
    completed = asyncio.Event()
    attempts = []
    exhausted = []

    async def handler(item):
        attempts.append(item.version)
        if item.version == 1:
            if attempts.count(1) == 1:
                first_attempt.set()
                await allow_retry.wait()
            raise RuntimeError("persistent database failure")
        completed.set()

    worker = MarketQuoteDispatchWorker(
        dispatcher,
        handler,
        min_backoff_seconds=0,
        max_backoff_seconds=0,
        max_attempts=2,
        on_exhausted=exhausted.append,
    )
    task = asyncio.create_task(worker.run())
    await asyncio.wait_for(first_attempt.wait(), timeout=1)

    # The newest authoritative quote coalesces behind the failing observation.
    assert dispatcher.publish(Observation(version=2, ltp=101))
    allow_retry.set()
    await asyncio.wait_for(completed.wait(), timeout=1)

    assert attempts == [1, 1, 2]
    assert [item.version for item in exhausted] == [1]
    assert worker.exhausted_count == 1
    assert worker.processed_count == 1
    assert dispatcher.pending_keys == 0
    assert dispatcher.inflight_keys == 0
    await asyncio.wait_for(dispatcher._queue.join(), timeout=1)

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


def test_worker_rejects_non_positive_max_attempts():
    dispatcher = MarketQuoteDispatcher()

    async def handler(_item):
        return None

    with pytest.raises(ValueError, match="max_attempts"):
        MarketQuoteDispatchWorker(dispatcher, handler, max_attempts=0)
