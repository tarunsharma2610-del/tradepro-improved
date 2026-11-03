import asyncio
from dataclasses import dataclass

from app.services.market_quote_dispatcher import MarketQuoteDispatcher


@dataclass(frozen=True)
class Observation:
    user_id: str
    instrument_key: str
    epoch: str
    version: int
    ltp: float


def obs(user="user-a", instrument="NSE_EQ|INE002A01018", epoch="epoch-1", version=1, ltp=100.0):
    return Observation(user, instrument, epoch, version, ltp)


def test_dispatcher_coalesces_to_newest_quote_for_same_user_instrument():
    dispatcher = MarketQuoteDispatcher(max_pending_keys=2)
    assert dispatcher.publish(obs(version=1, ltp=100.0))
    assert dispatcher.publish(obs(version=2, ltp=101.0))
    assert dispatcher.publish(obs(version=3, ltp=102.0))
    assert dispatcher.pending_keys == 1

    async def read():
        item = await dispatcher.get()
        dispatcher.task_done()
        return item

    item = asyncio.run(read())
    assert item.user_id == "user-a"
    assert item.instrument_key == "NSE_EQ|INE002A01018"
    assert item.version == 3
    assert item.observation.ltp == 102.0
    assert dispatcher.pending_keys == 0


def test_dispatcher_bounds_unique_keys_and_fails_closed_on_overflow():
    dispatcher = MarketQuoteDispatcher(max_pending_keys=1)
    assert dispatcher.publish(obs(instrument="NSE_EQ|ONE"))
    assert not dispatcher.publish(obs(instrument="NSE_EQ|TWO"))
    assert dispatcher.dropped_unique_keys == 1
    assert dispatcher.pending_keys == 1

    async def read():
        item = await dispatcher.get()
        dispatcher.task_done()
        return item

    assert asyncio.run(read()).instrument_key == "NSE_EQ|ONE"


def test_dispatcher_rejects_duplicate_or_out_of_order_versions():
    dispatcher = MarketQuoteDispatcher()
    assert dispatcher.publish(obs(version=4))
    assert not dispatcher.publish(obs(version=4))
    assert not dispatcher.publish(obs(version=3))
    assert dispatcher.rejected_updates == 2


def test_dispatcher_keeps_users_and_instruments_isolated():
    dispatcher = MarketQuoteDispatcher(max_pending_keys=3)
    assert dispatcher.publish(obs(user="user-a", instrument="NSE_EQ|ONE"))
    assert dispatcher.publish(obs(user="user-b", instrument="NSE_EQ|ONE"))
    assert dispatcher.publish(obs(user="user-a", instrument="NSE_EQ|TWO"))

    async def read_all():
        items = []
        for _ in range(3):
            items.append(await dispatcher.get())
            dispatcher.task_done()
        return items

    items = asyncio.run(read_all())
    assert {(item.user_id, item.instrument_key) for item in items} == {
        ("user-a", "NSE_EQ|ONE"),
        ("user-b", "NSE_EQ|ONE"),
        ("user-a", "NSE_EQ|TWO"),
    }


def test_dispatcher_accepts_new_epoch_replacing_pending_old_epoch():
    dispatcher = MarketQuoteDispatcher()
    assert dispatcher.publish(obs(epoch="old", version=99, ltp=99.0))
    assert dispatcher.publish(obs(epoch="new", version=1, ltp=101.0))

    async def read():
        item = await dispatcher.get()
        dispatcher.task_done()
        return item

    item = asyncio.run(read())
    assert item.epoch == "new"
    assert item.version == 1
    assert item.observation.ltp == 101.0


def test_dispatcher_rejects_invalid_observations():
    dispatcher = MarketQuoteDispatcher()
    assert not dispatcher.publish(object())
    assert not dispatcher.publish(obs(user="", version=0))
    assert dispatcher.rejected_updates == 2



def test_dispatcher_enforces_single_flight_and_replays_latest_after_ack():
    dispatcher = MarketQuoteDispatcher(max_pending_keys=2)

    async def scenario():
        assert dispatcher.publish(obs(version=1, ltp=100.0))
        first = await dispatcher.get()
        assert first.version == 1
        assert dispatcher.inflight_keys == 1

        # A newer observation is retained but not made available to another
        # worker while the first worker still owns this instrument key.
        assert dispatcher.publish(obs(version=2, ltp=101.0))
        assert dispatcher.publish(obs(version=3, ltp=102.0))
        assert dispatcher.pending_keys == 1

        async def consume_coalesced_update():
            second = await dispatcher.get()
            assert second.version == 3
            assert second.observation.ltp == 102.0
            dispatcher.task_done()
            return second

        second_consumer = asyncio.create_task(consume_coalesced_update())
        await asyncio.sleep(0)
        assert not second_consumer.done()
        assert dispatcher.inflight_keys == 1

        dispatcher.task_done()
        second = await asyncio.wait_for(second_consumer, timeout=1)
        assert second.version == 3
        assert second.observation.ltp == 102.0
        assert dispatcher.inflight_keys == 0
        assert dispatcher.pending_keys == 0

    asyncio.run(scenario())


def test_dispatcher_capacity_counts_inflight_keys():
    dispatcher = MarketQuoteDispatcher(max_pending_keys=1)

    async def scenario():
        assert dispatcher.publish(obs(instrument="NSE_EQ|ONE"))
        first = await dispatcher.get()
        assert first.instrument_key == "NSE_EQ|ONE"
        # An unrelated instrument cannot consume capacity while the first
        # key is being processed.
        assert not dispatcher.publish(obs(instrument="NSE_EQ|TWO"))
        assert dispatcher.dropped_unique_keys == 1
        dispatcher.task_done()
        assert dispatcher.inflight_keys == 0

    asyncio.run(scenario())



def test_dispatcher_requeues_inflight_observation_when_consumer_is_cancelled():
    dispatcher = MarketQuoteDispatcher(max_pending_keys=2)

    async def scenario():
        assert dispatcher.publish(obs(version=1, ltp=100.0))
        started = asyncio.Event()

        async def interrupted_consumer():
            item = await dispatcher.get()
            assert item.version == 1
            started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                dispatcher.release()
                raise

        task = asyncio.create_task(interrupted_consumer())
        await started.wait()
        assert dispatcher.inflight_keys == 1
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert dispatcher.inflight_keys == 0
        assert dispatcher.pending_keys == 1
        recovered = await dispatcher.get()
        assert recovered.version == 1
        dispatcher.task_done()
        assert dispatcher.pending_keys == 0

    asyncio.run(scenario())


def test_dispatcher_release_prefers_newest_quote_after_consumer_cancellation():
    dispatcher = MarketQuoteDispatcher(max_pending_keys=2)

    async def scenario():
        assert dispatcher.publish(obs(version=1, ltp=100.0))
        started = asyncio.Event()

        async def interrupted_consumer():
            item = await dispatcher.get()
            assert item.version == 1
            started.set()
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                dispatcher.release()
                raise

        task = asyncio.create_task(interrupted_consumer())
        await started.wait()
        assert dispatcher.publish(obs(version=2, ltp=101.0))
        assert dispatcher.publish(obs(version=3, ltp=102.0))
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        recovered = await dispatcher.get()
        assert recovered.version == 3
        assert recovered.observation.ltp == 102.0
        dispatcher.task_done()
        assert dispatcher.pending_keys == 0
        assert dispatcher.inflight_keys == 0

    asyncio.run(scenario())


def test_dispatcher_stays_bounded_under_burst_load_and_coalesces_latest_values():
    capacity = 64
    unique_keys = 512
    updates_per_key = 100
    dispatcher = MarketQuoteDispatcher(max_pending_keys=capacity)

    # Burst many more unique instruments than the configured queue capacity.
    accepted = []
    for index in range(unique_keys):
        instrument = f"NSE_EQ|BURST{index:04d}"
        if dispatcher.publish(obs(instrument=instrument, version=1, ltp=100.0)):
            accepted.append(instrument)

    assert len(accepted) == capacity
    assert dispatcher.pending_keys == capacity
    assert dispatcher.inflight_keys == 0
    assert dispatcher.dropped_unique_keys == unique_keys - capacity

    # Churn updates for every admitted key. Updates coalesce in place and
    # must not consume additional queue slots or displace other admitted keys.
    for version in range(2, updates_per_key + 1):
        for instrument in accepted:
            assert dispatcher.publish(
                obs(instrument=instrument, version=version, ltp=100.0 + version)
            )

    assert dispatcher.pending_keys == capacity
    assert dispatcher.inflight_keys == 0
    assert dispatcher.dropped_unique_keys == unique_keys - capacity
    assert dispatcher.rejected_updates == 0

    async def drain():
        received = []
        for _ in range(capacity):
            item = await dispatcher.get()
            received.append(item)
            dispatcher.task_done()
        await asyncio.wait_for(dispatcher._queue.join(), timeout=1)
        return received

    received = asyncio.run(drain())
    assert {item.instrument_key for item in received} == set(accepted)
    assert all(item.version == updates_per_key for item in received)
    assert all(item.observation.ltp == 100.0 + updates_per_key for item in received)
    assert dispatcher.pending_keys == 0
    assert dispatcher.inflight_keys == 0

    # Capacity is reusable after successful acknowledgement.
    assert dispatcher.publish(
        obs(instrument="NSE_EQ|AFTER_DRAIN", version=1, ltp=200.0)
    )
    assert dispatcher.dropped_unique_keys == unique_keys - capacity
