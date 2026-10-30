"""Integration tests against an actual Redis 7 service (not a fake client)."""
import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from redis.asyncio import Redis

from app.services.redis_market_quote_consumer import RedisMarketQuoteConsumer
from app.services.redis_market_quote_publisher import RedisMarketQuotePublisher
from app.services.upstox_market_data_streamer import MarketTick


REDIS_TEST_URL = os.getenv("REDIS_TEST_URL")
pytestmark = pytest.mark.skipif(not REDIS_TEST_URL, reason="REDIS_TEST_URL is required for real Redis integration tests")


def make_tick(instrument_key: str, ltp: float = 2500.5) -> MarketTick:
    now = datetime.now(timezone.utc)
    return MarketTick(
        instrument_key=instrument_key,
        ltp=ltp,
        exchange_timestamp_ms=int(now.timestamp() * 1000),
        received_at=now,
        received_monotonic=1.0,
    )


@pytest.mark.asyncio
async def test_real_redis_publisher_consumer_round_trip_and_user_isolation():
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    user_a, user_b = uuid4(), uuid4()
    instrument = "NSE_EQ|INE002A01018"
    publisher_a = RedisMarketQuotePublisher(redis, user_a, ttl_seconds=15)
    publisher_b = RedisMarketQuotePublisher(redis, user_b, ttl_seconds=15)
    consumer_a = RedisMarketQuoteConsumer(redis, user_a, max_age_seconds=15)
    consumer_b = RedisMarketQuoteConsumer(redis, user_b, max_age_seconds=15)
    try:
        assert await redis.ping()
        assert await publisher_a.publish(make_tick(instrument, 2500.5))
        assert await publisher_b.publish(make_tick(instrument, 2600.5))

        quote_a = await consumer_a.get_quote(instrument)
        quote_b = await consumer_b.get_quote(instrument)
        assert quote_a is not None and quote_b is not None
        assert quote_a["user_id"] == str(user_a)
        assert quote_b["user_id"] == str(user_b)
        assert quote_a["ltp"] == 2500.5
        assert quote_b["ltp"] == 2600.5
        assert quote_a["version"] == quote_b["version"] == 1

        assert await redis.ttl(publisher_a.snapshot_key(instrument)) > 0
        assert await redis.ttl(publisher_a.snapshot_key(instrument) + ":version") > 0
        assert await redis.ttl(publisher_b.snapshot_key(instrument)) > 0
    finally:
        await redis.delete(
            publisher_a.snapshot_key(instrument),
            publisher_a.snapshot_key(instrument) + ":version",
            publisher_b.snapshot_key(instrument),
            publisher_b.snapshot_key(instrument) + ":version",
        )
        await redis.aclose()


@pytest.mark.asyncio
async def test_real_redis_pubsub_notification_then_authoritative_snapshot_read():
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=15)
    consumer = RedisMarketQuoteConsumer(redis, user_id, max_age_seconds=15)
    pubsub = redis.pubsub()
    try:
        await pubsub.subscribe(publisher.channel)
        # Consume Redis's subscription acknowledgement before publishing.
        acknowledgement = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=False, timeout=1), timeout=2)
        assert acknowledgement and acknowledgement["type"] == "subscribe"

        assert await publisher.publish(make_tick(instrument, 2511.25))
        notification = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True, timeout=1), timeout=2)
        assert notification and notification["type"] == "message"
        # The Pub/Sub payload is only a signal; consumer fetches the Redis snapshot.
        quote = await consumer.get_quote(instrument)
        assert quote is not None
        assert quote["ltp"] == 2511.25
        assert quote["user_id"] == str(user_id)
    finally:
        await pubsub.unsubscribe(publisher.channel)
        await pubsub.aclose()
        await redis.delete(
            publisher.snapshot_key(instrument),
            publisher.snapshot_key(instrument) + ":version",
        )
        await redis.aclose()


@pytest.mark.asyncio
async def test_real_redis_consumer_recovers_latest_snapshot_after_new_consumer_instance():
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=15)
    try:
        assert await publisher.publish(make_tick(instrument, 2499.0))
        # Simulate a worker restart: a fresh consumer has no local version state.
        restarted_consumer = RedisMarketQuoteConsumer(redis, user_id, max_age_seconds=15)
        recovered = await restarted_consumer.recover([instrument])
        assert instrument in recovered
        assert recovered[instrument]["ltp"] == 2499.0
        assert recovered[instrument]["version"] == 1
    finally:
        await redis.delete(
            publisher.snapshot_key(instrument),
            publisher.snapshot_key(instrument) + ":version",
        )
        await redis.aclose()


@pytest.mark.asyncio
async def test_real_redis_concurrent_publishes_preserve_atomic_version_order():
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=15)
    try:
        outcomes = await asyncio.gather(*(
            publisher.publish(make_tick(instrument, 2500.0 + index))
            for index in range(40)
        ))
        assert all(outcomes)
        snapshot = await redis.get(publisher.snapshot_key(instrument))
        assert snapshot is not None
        assert json.loads(snapshot)["version"] == 40
        notifications = await redis.pubsub_numsub(publisher.channel)
        assert notifications[0][1] == 0
        assert await redis.ttl(publisher.snapshot_key(instrument) + ":version") > 0
    finally:
        await redis.delete(
            publisher.snapshot_key(instrument),
            publisher.snapshot_key(instrument) + ":version",
        )
        await redis.aclose()
