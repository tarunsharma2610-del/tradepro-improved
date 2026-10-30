"""Integration tests against an actual Redis 7 service (not a fake client)."""
import asyncio
import json
import os
import subprocess
import shutil
import socket
import sys
import textwrap
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
        assert 0 < await redis.ttl(publisher_a.snapshot_key(instrument) + ":version") <= publisher_a.version_ttl_seconds
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
async def test_real_redis_version_counter_survives_quote_snapshot_expiry():
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=2)
    try:
        assert await publisher.publish(make_tick(instrument, 2500.0))
        version_key = publisher.snapshot_key(instrument) + ":version"
        first_quote = await RedisMarketQuoteConsumer(redis, user_id, max_age_seconds=15).get_quote(instrument)
        assert first_quote is not None
        epoch = first_quote["epoch"]
        counter_state = await redis.get(version_key)
        assert counter_state == f"{epoch}:1"
        assert 0 < await redis.ttl(version_key) <= publisher.version_ttl_seconds

        # Let the real Redis TTL expire the quiet instrument's snapshot.
        await redis.pexpire(publisher.snapshot_key(instrument), 1)
        await asyncio.sleep(0.02)
        assert await redis.get(publisher.snapshot_key(instrument)) is None
        assert await publisher.publish(make_tick(instrument, 2501.0))
        snapshot = json.loads(await redis.get(publisher.snapshot_key(instrument)))
        assert snapshot["version"] == 2
        assert snapshot["epoch"] == epoch
        assert await redis.get(version_key) == f"{epoch}:2"
        assert 0 < await redis.ttl(version_key) <= publisher.version_ttl_seconds
    finally:
        await redis.delete(
            publisher.snapshot_key(instrument),
            publisher.snapshot_key(instrument) + ":version",
        )
        await redis.aclose()


@pytest.mark.asyncio
async def test_real_redis_expired_version_counter_starts_new_epoch_and_consumer_accepts_reset():
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=15, version_ttl_seconds=30)
    consumer = RedisMarketQuoteConsumer(redis, user_id, max_age_seconds=15)
    version_key = publisher.snapshot_key(instrument) + ":version"
    try:
        assert await publisher.publish(make_tick(instrument, 2500.0))
        first = await consumer.get_quote(instrument)
        assert first is not None and first["version"] == 1

        assert await publisher.publish(make_tick(instrument, 2500.5))
        second = await consumer.get_quote(instrument)
        assert second is not None and second["version"] == 2
        assert second["epoch"] == first["epoch"]

        # Model the bounded counter reaching its retention limit. The next
        # publisher creates a new epoch; version 1 is valid in that epoch.
        await redis.pexpire(version_key, 1)
        await asyncio.sleep(0.02)
        assert await redis.get(version_key) is None
        assert await publisher.publish(make_tick(instrument, 2501.0))
        third = await consumer.get_quote(instrument)
        assert third is not None
        assert third["version"] == 1
        assert third["epoch"] != second["epoch"]
        assert await redis.ttl(version_key) > 0
    finally:
        await redis.delete(
            publisher.snapshot_key(instrument),
            version_key,
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
        assert json.loads(snapshot)["epoch"]
        notifications = await redis.pubsub_numsub(publisher.channel)
        assert notifications[0][1] == 0
        assert 0 < await redis.ttl(publisher.snapshot_key(instrument) + ":version") <= publisher.version_ttl_seconds
    finally:
        await redis.delete(
            publisher.snapshot_key(instrument),
            publisher.snapshot_key(instrument) + ":version",
        )
        await redis.aclose()



@pytest.mark.asyncio
async def test_real_redis_pubsub_connection_loss_resubscribes_and_recovers_latest_snapshot():
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    admin = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=15)
    consumer = RedisMarketQuoteConsumer(redis, user_id, max_age_seconds=15)
    listener = consumer.listen(
        [instrument],
        max_reconnect_attempts=1,
        min_backoff_seconds=0.01,
        max_backoff_seconds=0.02,
    )
    try:
        assert await publisher.publish(make_tick(instrument, 2500.0))
        initial = await asyncio.wait_for(anext(listener), timeout=3)
        assert initial["ltp"] == 2500.0

        # Redis 7 closes the consumer's real Pub/Sub TCP connection. The
        # listener must create a new subscription and sweep the latest snapshot.
        killed = await admin.execute_command("CLIENT", "KILL", "TYPE", "PUBSUB")
        assert killed >= 1
        assert await publisher.publish(make_tick(instrument, 2501.0))

        recovered = await asyncio.wait_for(anext(listener), timeout=3)
        assert recovered["ltp"] == 2501.0
        assert recovered["version"] == 2
    finally:
        await listener.aclose()
        await redis.delete(
            publisher.snapshot_key(instrument),
            publisher.snapshot_key(instrument) + ":version",
        )
        await admin.aclose()
        await redis.aclose()



@pytest.mark.asyncio
async def test_real_redis_market_quotes_cross_independent_os_processes():
    """Publisher and consumer processes share snapshots through Redis only."""
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    admin = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=15)
    consumer = RedisMarketQuoteConsumer(redis, user_id, max_age_seconds=15)
    env = os.environ.copy()
    env["REDIS_TEST_URL"] = REDIS_TEST_URL
    try:
        # A separate Python interpreter publishes; this process consumes.
        publish_script = textwrap.dedent("""
            import asyncio, os
            from datetime import datetime, timezone
            from uuid import UUID
            from redis.asyncio import Redis
            from app.services.redis_market_quote_publisher import RedisMarketQuotePublisher
            from app.services.upstox_market_data_streamer import MarketTick

            async def main():
                redis = Redis.from_url(os.environ["REDIS_TEST_URL"], decode_responses=True)
                now = datetime.now(timezone.utc)
                tick = MarketTick(
                    instrument_key=os.environ["INSTRUMENT_KEY"],
                    ltp=2750.25,
                    exchange_timestamp_ms=int(now.timestamp() * 1000),
                    received_at=now,
                    received_monotonic=1.0,
                )
                publisher = RedisMarketQuotePublisher(redis, UUID(os.environ["USER_ID"]), ttl_seconds=15)
                try:
                    assert await publisher.publish(tick)
                finally:
                    await redis.aclose()

            asyncio.run(main())
        """)
        env.update({"INSTRUMENT_KEY": instrument, "USER_ID": str(user_id)})
        result = subprocess.run(
            [sys.executable, "-c", publish_script],
            env=env, capture_output=True, text=True, timeout=10, check=False,
        )
        assert result.returncode == 0, result.stderr
        from_child = await consumer.get_quote(instrument)
        assert from_child is not None
        assert from_child["ltp"] == 2750.25

        # Conversely, a separate interpreter consumes the parent-published snapshot.
        assert await publisher.publish(make_tick(instrument, 2751.5))
        consume_script = textwrap.dedent("""
            import asyncio, json, os
            from uuid import UUID
            from redis.asyncio import Redis
            from app.services.redis_market_quote_consumer import RedisMarketQuoteConsumer

            async def main():
                redis = Redis.from_url(os.environ["REDIS_TEST_URL"], decode_responses=True)
                consumer = RedisMarketQuoteConsumer(redis, UUID(os.environ["USER_ID"]), max_age_seconds=15)
                try:
                    quote = await consumer.get_quote(os.environ["INSTRUMENT_KEY"])
                    print(json.dumps(quote))
                finally:
                    await redis.aclose()

            asyncio.run(main())
        """)
        result = subprocess.run(
            [sys.executable, "-c", consume_script],
            env=env, capture_output=True, text=True, timeout=10, check=False,
        )
        assert result.returncode == 0, result.stderr
        child_quote = json.loads(result.stdout.strip().splitlines()[-1])
        assert child_quote["user_id"] == str(user_id)
        assert child_quote["instrument_key"] == instrument
        assert child_quote["ltp"] == 2751.5
        assert child_quote["version"] == 2
    finally:
        await admin.delete(
            publisher.snapshot_key(instrument),
            publisher.snapshot_key(instrument) + ":version",
        )
        await admin.aclose()
        await redis.aclose()



@pytest.mark.asyncio
async def test_real_redis_server_process_restart_recovers_without_reusing_stale_quote(tmp_path):
    """A real Redis process restart clears volatile snapshots; consumer must resubscribe."""
    redis_server = shutil.which("redis-server")
    if not redis_server:
        pytest.skip("redis-server executable is required for process-restart integration test")

    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]
    url = f"redis://127.0.0.1:{port}/0"
    data_dir = tmp_path / "redis-data"
    data_dir.mkdir()

    def start_server():
        return subprocess.Popen(
            [
                redis_server, "--bind", "127.0.0.1", "--port", str(port),
                "--protected-mode", "no", "--save", "", "--appendonly", "no",
                "--dir", str(data_dir),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    async def wait_until_ready(client, process):
        deadline = asyncio.get_running_loop().time() + 8
        while asyncio.get_running_loop().time() < deadline:
            if process.poll() is not None:
                raise AssertionError("Redis server exited before becoming ready")
            try:
                if await client.ping():
                    return
            except Exception:
                await asyncio.sleep(0.05)
        raise AssertionError("Redis server did not become ready")

    server = start_server()
    redis = Redis.from_url(url, decode_responses=True, socket_connect_timeout=1)
    admin = Redis.from_url(url, decode_responses=True, socket_connect_timeout=1)
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=15)
    consumer = RedisMarketQuoteConsumer(redis, user_id, max_age_seconds=15)
    listener = consumer.listen(
        [instrument], max_reconnect_attempts=8,
        min_backoff_seconds=0.05, max_backoff_seconds=0.2,
    )
    try:
        await wait_until_ready(redis, server)
        # Listener subscription is established before publishing the first quote.
        first_waiter = asyncio.create_task(anext(listener))
        await asyncio.sleep(0.05)
        assert await publisher.publish(make_tick(instrument, 2800.0))
        first_quote = await asyncio.wait_for(first_waiter, timeout=3)
        assert first_quote["ltp"] == 2800.0
        assert first_quote["version"] == 1

        # Advance the Redis INCR counter beyond its initial value so restart
        # proves the consumer does not reject a fresh post-restart v1 snapshot.
        second_waiter = asyncio.create_task(anext(listener))
        assert await publisher.publish(make_tick(instrument, 2800.5))
        second_quote = await asyncio.wait_for(second_waiter, timeout=3)
        assert second_quote["version"] == 2

        # Async generators are demand-driven: keep an outstanding read so the
        # listener continues polling Pub/Sub while Redis is stopped/restarted.
        recovery_waiter = asyncio.create_task(anext(listener))
        await asyncio.sleep(0.05)

        # Terminate the Redis server process, not merely one client connection.
        server.terminate()
        await asyncio.to_thread(server.wait, 5)
        await asyncio.sleep(0.1)

        # A dead server means no quote is available; cached consumer state is
        # never returned as a fallback while the snapshot store is unavailable.
        assert await consumer.get_quote(instrument) is None

        server = start_server()
        await wait_until_ready(redis, server)

        # Wait until the listener has recreated its subscription on the new
        # Redis process. The restarted Redis instance has no old snapshot.
        deadline = asyncio.get_running_loop().time() + 8
        subscribed = False
        while asyncio.get_running_loop().time() < deadline:
            try:
                subscriptions = await admin.pubsub_numsub(consumer.channel)
                if subscriptions and subscriptions[0][1] == 1:
                    subscribed = True
                    break
            except Exception:
                pass
            await asyncio.sleep(0.05)
        assert subscribed, "consumer did not resubscribe after Redis process restart"

        # The restart erased volatile cache and version keys. Publish a new,
        # fresh quote and require the listener to deliver that quote, not v1.
        assert await publisher.publish(make_tick(instrument, 2801.25))
        recovered = await asyncio.wait_for(recovery_waiter, timeout=8)
        assert recovered["ltp"] == 2801.25
        assert recovered["received_at"] != first_quote["received_at"]
        assert recovered["exchange_timestamp_ms"] >= first_quote["exchange_timestamp_ms"]
        assert recovered["version"] == 1  # Redis's volatile counter starts a new epoch.
        assert recovered["epoch"] != first_quote["epoch"]
        assert consumer._versions[instrument] == 1
        assert consumer._epochs[instrument] == recovered["epoch"]
    finally:
        await listener.aclose()
        try:
            server.terminate()
            await asyncio.to_thread(server.wait, 5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            server.kill()
            await asyncio.to_thread(server.wait)
        await admin.aclose()
        await redis.aclose()
