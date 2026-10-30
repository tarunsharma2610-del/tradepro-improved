import asyncio
from uuid import uuid4

import pytest

from app.services.redis_market_quote_worker import RedisMarketQuoteWorker


class FakeRedis:
    def __init__(self):
        self.values = {}

    async def set(self, key, value, nx=False, px=None):
        if nx and key in self.values:
            return None
        self.values[key] = value
        return True

    async def eval(self, script, numkeys, key, token, ttl_ms=None):
        if self.values.get(key) != token:
            return 0
        if "PEXPIRE" in script:
            return 1
        self.values.pop(key, None)
        return 1


async def wait_for_consumer(consumers):
    deadline = asyncio.get_running_loop().time() + 1
    while not consumers and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.001)
    assert consumers, "worker did not create a consumer after acquiring its lease"
    await asyncio.wait_for(consumers[0].started.wait(), timeout=1)


class FakeConsumer:
    def __init__(self, _redis, _user_id):
        self.started = asyncio.Event()
        self.stopped = asyncio.Event()

    async def listen(self, instrument_keys):
        self.started.set()
        if instrument_keys:
            yield {
                "instrument_key": instrument_keys[0],
                "ltp": 123.45,
                "version": 1,
            }
        await self.stopped.wait()


@pytest.mark.asyncio
async def test_worker_consumes_quotes_under_user_scoped_lease_and_releases_on_close():
    redis = FakeRedis()
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    consumers = []

    def consumer_factory(client, owner):
        consumer = FakeConsumer(client, owner)
        consumers.append(consumer)
        return consumer

    worker = RedisMarketQuoteWorker(
        redis_client=redis,
        subscription_loader=lambda: {user_id: [instrument]},
        consumer_factory=consumer_factory,
        lease_seconds=3,
    )
    await worker.reconcile_once()
    await wait_for_consumer(consumers)
    await asyncio.sleep(0)

    assert worker.latest_quote(user_id, instrument)["ltp"] == 123.45
    lease_key = worker._lease_key(user_id)
    assert lease_key in redis.values

    await worker.close()

    assert lease_key not in redis.values
    assert worker.latest_quote(user_id, instrument) is None


@pytest.mark.asyncio
async def test_only_one_worker_replica_owns_a_users_quote_consumer():
    redis = FakeRedis()
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    first_consumers, second_consumers = [], []

    def factory(target):
        def create(client, owner):
            consumer = FakeConsumer(client, owner)
            target.append(consumer)
            return consumer
        return create

    first = RedisMarketQuoteWorker(
        redis_client=redis,
        subscription_loader=lambda: {user_id: [instrument]},
        consumer_factory=factory(first_consumers),
        lease_seconds=3,
    )
    second = RedisMarketQuoteWorker(
        redis_client=redis,
        subscription_loader=lambda: {user_id: [instrument]},
        consumer_factory=factory(second_consumers),
        lease_seconds=3,
    )
    try:
        await first.reconcile_once()
        await wait_for_consumer(first_consumers)
        await second.reconcile_once()
        await asyncio.sleep(0)

        assert len(first_consumers) == 1
        assert second_consumers == []

        await first.close()
        await second.reconcile_once()
        await wait_for_consumer(second_consumers)
        assert len(second_consumers) == 1
    finally:
        await first.close()
        await second.close()


@pytest.mark.asyncio
async def test_worker_stops_consuming_when_its_lease_is_replaced():
    redis = FakeRedis()
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    consumers = []
    worker = RedisMarketQuoteWorker(
        redis_client=redis,
        subscription_loader=lambda: {user_id: [instrument]},
        consumer_factory=lambda client, owner: consumers.append(FakeConsumer(client, owner)) or consumers[-1],
        lease_seconds=3,
    )
    await worker.reconcile_once()
    await wait_for_consumer(consumers)

    lease_key = worker._lease_key(user_id)
    redis.values[lease_key] = "new-owner-token"
    await asyncio.sleep(1.1)

    assert redis.values[lease_key] == "new-owner-token"
    assert worker.latest_quote(user_id, instrument) is None
    await worker.close()
    assert redis.values[lease_key] == "new-owner-token"


def test_worker_latest_quote_expires_without_a_new_pubsub_message(monkeypatch):
    from app.services import redis_market_quote_worker as worker_module

    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    worker = RedisMarketQuoteWorker(
        redis_client=FakeRedis(),
        subscription_loader=lambda: {},
    )
    quote_key = (user_id, instrument)
    worker._latest_quotes[quote_key] = {"instrument_key": instrument, "ltp": 123.45}
    worker._latest_quote_times[quote_key] = 100.0
    monkeypatch.setattr(worker_module.time, "monotonic", lambda: 116.0)

    assert worker.latest_quote(user_id, instrument) is None
    assert quote_key not in worker._latest_quotes
