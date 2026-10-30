import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.services.redis_market_quote_publisher import RedisMarketQuotePublisher
from app.services.upstox_market_data_streamer import MarketTick


class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.operations = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    def set(self, key, value, ex):
        self.operations.append(("set", key, value, ex))
        return self

    def publish(self, channel, value):
        self.operations.append(("publish", channel, value))
        return self

    async def execute(self):
        for op in self.operations:
            if op[0] == "set":
                self.redis.snapshots[op[1]] = (op[2], op[3])
            else:
                self.redis.messages.append((op[1], op[2]))


class FakeRedis:
    def __init__(self):
        self.snapshots, self.messages, self.versions = {}, [], {}

    async def incr(self, key):
        self.versions[key] = self.versions.get(key, 0) + 1
        return self.versions[key]

    async def expire(self, key, ttl):
        self.version_ttls = getattr(self, "version_ttls", {})
        self.version_ttls[key] = ttl
        return True

    def pipeline(self, transaction=True):
        assert transaction is True
        return FakePipeline(self)


def make_tick(*, received_at=None, exchange_timestamp_ms=None, ltp=2500.5):
    now = datetime.now(timezone.utc)
    return MarketTick(
        instrument_key="NSE_EQ|INE002A01018", ltp=ltp,
        exchange_timestamp_ms=(int(now.timestamp() * 1000) if exchange_timestamp_ms is None else exchange_timestamp_ms),
        received_at=received_at or now, received_monotonic=1.0,
    )


@pytest.mark.asyncio
async def test_publish_stores_versioned_snapshot_with_ttl_and_user_scoped_channel():
    redis, user_id = FakeRedis(), uuid4()
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=12)
    assert await publisher.publish(make_tick()) is True
    encoded, ttl = redis.snapshots[publisher.snapshot_key("NSE_EQ|INE002A01018")]
    snapshot = json.loads(encoded)
    assert ttl == 12
    assert snapshot["schema_version"] == 1
    assert snapshot["user_id"] == str(user_id)
    assert snapshot["version"] == 1
    assert snapshot["ltp"] == 2500.5
    channel, message = redis.messages[0]
    assert channel == publisher.channel
    assert json.loads(message)["version"] == 1


@pytest.mark.asyncio
async def test_publish_increments_version_for_each_snapshot():
    redis = FakeRedis()
    publisher = RedisMarketQuotePublisher(redis, uuid4())
    assert await publisher.publish(make_tick()) is True
    assert await publisher.publish(make_tick()) is True
    key = publisher.snapshot_key("NSE_EQ|INE002A01018")
    assert json.loads(redis.snapshots[key][0])["version"] == 2


@pytest.mark.asyncio
async def test_publish_rejects_stale_received_tick():
    redis = FakeRedis()
    publisher = RedisMarketQuotePublisher(redis, uuid4(), ttl_seconds=10)
    stale = make_tick(received_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
    assert await publisher.publish(stale) is False
    assert redis.snapshots == {}
    assert redis.messages == []


@pytest.mark.asyncio
async def test_publish_rejects_invalid_price_and_exchange_timestamp():
    redis = FakeRedis()
    publisher = RedisMarketQuotePublisher(redis, uuid4())
    assert await publisher.publish(make_tick(ltp=0)) is False
    assert await publisher.publish(make_tick(exchange_timestamp_ms=0)) is False
    assert redis.snapshots == {}


def test_user_namespaces_are_isolated():
    redis = FakeRedis()
    first, second = RedisMarketQuotePublisher(redis, uuid4()), RedisMarketQuotePublisher(redis, uuid4())
    assert first.snapshot_key("NSE_EQ|INE002A01018") != second.snapshot_key("NSE_EQ|INE002A01018")
    assert first.channel != second.channel
