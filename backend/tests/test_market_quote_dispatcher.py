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
