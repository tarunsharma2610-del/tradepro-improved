import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.services.redis_market_quote_consumer import RedisMarketQuoteConsumer


class FakePubSub:
    def __init__(self, messages=()):
        self.messages = list(messages)
        self.subscribed = []
        self.unsubscribed = []
        self.closed = False

    async def subscribe(self, channel):
        self.subscribed.append(channel)

    async def unsubscribe(self, channel):
        self.unsubscribed.append(channel)

    async def aclose(self):
        self.closed = True

    async def listen(self):
        for message in self.messages:
            yield message


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.pubsub_instance = FakePubSub()

    async def get(self, key):
        return self.values.get(key, (None, 0))[0]

    async def ttl(self, key):
        return self.values.get(key, (None, 0))[1]

    def pubsub(self):
        return self.pubsub_instance


def snapshot(expected_user_id, instrument_key="NSE_EQ|INE002A01018", **changes):
    now = datetime.now(timezone.utc)
    data = {
        "schema_version": 1, "user_id": str(expected_user_id),
        "instrument_key": instrument_key, "version": 1, "ltp": 2500.5,
        "exchange_timestamp_ms": int(now.timestamp() * 1000),
        "received_at": now.isoformat(), "published_at": now.isoformat(),
    }
    data.update(changes)
    return data


@pytest.mark.asyncio
async def test_reads_authoritative_user_scoped_snapshot_and_tracks_version():
    redis, user_id = FakeRedis(), uuid4()
    consumer = RedisMarketQuoteConsumer(redis, user_id)
    key = consumer.snapshot_key("NSE_EQ|INE002A01018")
    redis.values[key] = (json.dumps(snapshot(user_id)), 12)
    quote = await consumer.get_quote("NSE_EQ|INE002A01018")
    assert quote["ltp"] == 2500.5
    assert consumer._versions["NSE_EQ|INE002A01018"] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("ttl", [0, -1, 16])
async def test_rejects_missing_expired_or_unbounded_ttl(ttl):
    redis, user_id = FakeRedis(), uuid4()
    consumer = RedisMarketQuoteConsumer(redis, user_id)
    key = consumer.snapshot_key("NSE_EQ|INE002A01018")
    redis.values[key] = (json.dumps(snapshot(user_id)), ttl)
    assert await consumer.get_quote("NSE_EQ|INE002A01018") is None


@pytest.mark.asyncio
@pytest.mark.parametrize("changes", [
    {"user_id": str(uuid4())}, {"schema_version": 2},
    {"instrument_key": "NSE_EQ|OTHER"}, {"version": 0},
    {"ltp": float("nan")}, {"ltp": 0},
    {"exchange_timestamp_ms": 0},
    {"received_at": "2020-01-01T00:00:00"},
])
async def test_rejects_invalid_or_cross_user_snapshot(changes):
    redis, user_id = FakeRedis(), uuid4()
    consumer = RedisMarketQuoteConsumer(redis, user_id)
    instrument = "NSE_EQ|INE002A01018"
    redis.values[consumer.snapshot_key(instrument)] = (json.dumps(snapshot(user_id, **changes)), 10)
    assert await consumer.get_quote(instrument) is None


@pytest.mark.asyncio
async def test_rejects_version_regression():
    redis, user_id = FakeRedis(), uuid4()
    consumer = RedisMarketQuoteConsumer(redis, user_id)
    instrument = "NSE_EQ|INE002A01018"
    key = consumer.snapshot_key(instrument)
    redis.values[key] = (json.dumps(snapshot(user_id, version=3)), 10)
    assert (await consumer.get_quote(instrument))["version"] == 3
    redis.values[key] = (json.dumps(snapshot(user_id, version=2)), 10)
    assert await consumer.get_quote(instrument) is None


@pytest.mark.asyncio
async def test_recover_reads_latest_snapshots_after_restart():
    redis, user_id = FakeRedis(), uuid4()
    consumer = RedisMarketQuoteConsumer(redis, user_id)
    first, second = "NSE_EQ|INE002A01018", "NSE_EQ|INE009A01021"
    redis.values[consumer.snapshot_key(first)] = (json.dumps(snapshot(user_id, first)), 10)
    redis.values[consumer.snapshot_key(second)] = (json.dumps(snapshot(user_id, second)), 10)
    recovered = await consumer.recover([first, second, first])
    assert set(recovered) == {first, second}


@pytest.mark.asyncio
async def test_pubsub_notification_causes_snapshot_read_not_payload_trust():
    redis, user_id = FakeRedis(), uuid4()
    consumer = RedisMarketQuoteConsumer(redis, user_id)
    instrument = "NSE_EQ|INE002A01018"
    redis.values[consumer.snapshot_key(instrument)] = (json.dumps(snapshot(user_id)), 10)
    redis.pubsub_instance.messages = [
        {"type": "message", "data": json.dumps({"user_id": str(uuid4()), "instrument_key": instrument, "version": 1})},
        {"type": "message", "data": json.dumps({"user_id": str(user_id), "instrument_key": instrument, "version": 1, "ltp": 1})},
    ]
    results = [q async for q in consumer.listen([instrument])]
    assert len(results) == 2  # startup recovery plus validated notification
    assert all(q["ltp"] == 2500.5 for q in results)
    assert redis.pubsub_instance.closed
