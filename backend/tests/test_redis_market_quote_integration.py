"""Integration tests against an actual Redis 7 service (not a fake client)."""
import asyncio
import json
import os
import subprocess
import shutil
import socket
import sys
import time
import textwrap
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from redis.asyncio import Redis

from app.services.redis_market_quote_consumer import RedisMarketQuoteConsumer
from app.services.redis_market_quote_publisher import RedisMarketQuotePublisher
from app.services.market_quote_dispatcher import MarketQuoteDispatcher
from app.services.market_scan_dispatch_pipeline import MarketScanDispatchPipeline
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


@pytest.mark.asyncio
async def test_real_redis_snapshot_flows_into_scanner_dispatch_pipeline():
    """Exercise actual Redis snapshot recovery through scanner and bounded dispatch."""
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=15)
    consumer = RedisMarketQuoteConsumer(redis, user_id, max_age_seconds=15)
    dispatcher = MarketQuoteDispatcher(max_pending_keys=8)
    pipeline = MarketScanDispatchPipeline(dispatcher=dispatcher)
    listener = consumer.listen(
        [instrument],
        max_reconnect_attempts=1,
        min_backoff_seconds=0.01,
        max_backoff_seconds=0.02,
    )
    now = datetime.now(timezone.utc)
    tick = MarketTick(
        instrument_key=instrument,
        ltp=110.0,
        exchange_timestamp_ms=int(now.timestamp() * 1000),
        received_at=now,
        received_monotonic=1.0,
        volume_traded_today=1200,
        open_interest=4500,
        total_buy_quantity=700,
        total_sell_quantity=300,
        ohlc=({"interval": "1d", "close": 100.0},),
    )
    try:
        assert await publisher.publish(tick)
        # The listener's startup snapshot sweep reads the authoritative Redis
        # value and feeds the same callback used by the runtime worker.
        recovered_quote = await asyncio.wait_for(anext(listener), timeout=3)
        assert recovered_quote["user_id"] == str(user_id)
        assert pipeline.on_quote(user_id, recovered_quote) is True

        # Keep get() and task_done() in this same task: dispatcher ownership is task-scoped.
        dispatched = await dispatcher.get()
        assert dispatched.user_id == str(user_id)
        assert dispatched.instrument_key == instrument
        assert dispatched.version == 1
        assert dispatched.observation.ltp == 110.0
        assert dispatched.observation.price_change_pct == 10.0
        assert dispatched.observation.volume_traded_today == 1200
        assert dispatched.observation.open_interest == 4500
        assert dispatched.observation.buy_sell_imbalance == 0.4
        assert pipeline.accepted_observations == 1
        assert pipeline.rejected_quotes == 0
        assert pipeline.rejected_dispatches == 0
        dispatcher.task_done()
    finally:
        await listener.aclose()
        await redis.delete(
            publisher.snapshot_key(instrument),
            publisher.snapshot_key(instrument) + ":version",
        )
        await redis.aclose()


@pytest.mark.asyncio
async def test_real_redis_worker_process_crash_expires_lease_and_allows_failover():
    """A killed worker cannot strand a user lease; a replacement resumes consumption."""
    from app.services.redis_market_quote_worker import RedisMarketQuoteWorker

    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    user_id = uuid4()
    instrument = "NSE_EQ|INE002A01018"
    marker_key = f"tradepro:test:worker-ready:{user_id}"
    lease_key = RedisMarketQuoteWorker._lease_key(user_id)
    child_script = textwrap.dedent(
        """
        import asyncio, os
        from redis.asyncio import Redis
        from app.services.redis_market_quote_worker import RedisMarketQuoteWorker

        class BlockingConsumer:
            def __init__(self, client, marker):
                self.client, self.marker = client, marker
            async def listen(self, keys):
                await self.client.set(self.marker, "ready", ex=20)
                yield {"instrument_key": keys[0], "ltp": 2500.0}
                await asyncio.Future()

        async def main():
            client = Redis.from_url(os.environ["REDIS_TEST_URL"], decode_responses=True)
            user_id = os.environ["TEST_USER_ID"]
            marker = os.environ["TEST_MARKER"]
            worker = RedisMarketQuoteWorker(
                redis_client=client,
                subscription_loader=lambda: {__import__("uuid").UUID(user_id): ["NSE_EQ|INE002A01018"]},
                consumer_factory=lambda _client, _owner: BlockingConsumer(client, marker),
                lease_seconds=3,
                reconcile_seconds=0.05,
            )
            await worker.reconcile_once()
            task = worker._tasks[__import__("uuid").UUID(user_id)][1]
            deadline = asyncio.get_running_loop().time() + 6
            while await client.get(marker) != "ready":
                if task.done():
                    error = task.exception()
                    raise RuntimeError(f"worker consumer task exited before readiness: {error!r}")
                if asyncio.get_running_loop().time() >= deadline:
                    raise TimeoutError("worker consumer did not become ready")
                await asyncio.sleep(0.05)
            await asyncio.Future()

        asyncio.run(main())
        """
    )
    env = os.environ.copy()
    env["REDIS_TEST_URL"] = REDIS_TEST_URL
    env["TEST_USER_ID"] = str(user_id)
    env["TEST_MARKER"] = marker_key
    child = None
    replacement = None
    replacement_loop = None
    try:
        child = subprocess.Popen(
            [sys.executable, "-c", child_script],
            env=env,
            cwd=os.getcwd(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        async with asyncio.timeout(8):
            while await redis.get(marker_key) != "ready":
                if child.poll() is not None:
                    stderr = child.stderr.read() if child.stderr else ""
                    raise AssertionError(f"worker child exited early: {stderr}")
                await asyncio.sleep(0.05)

        assert await redis.get(lease_key) is not None
        child.kill()
        child.wait(timeout=3)

        # The process is gone but Redis retains its lease until its short TTL.
        assert await redis.get(lease_key) is not None

        class ReplacementConsumer:
            async def listen(self, keys):
                now = datetime.now(timezone.utc)
                yield {
                    "instrument_key": keys[0],
                    "ltp": 2501.25,
                    "received_at": now.isoformat(),
                }
                await asyncio.Future()

        replacement = RedisMarketQuoteWorker(
            redis_client=redis,
            subscription_loader=lambda: {user_id: [instrument]},
            consumer_factory=lambda _client, _owner: ReplacementConsumer(),
            lease_seconds=3,
            reconcile_seconds=0.05,
        )
        replacement_loop = asyncio.create_task(replacement.run_forever())
        async with asyncio.timeout(8):
            while replacement.latest_quote(user_id, instrument) is None:
                await asyncio.sleep(0.05)

        quote = replacement.latest_quote(user_id, instrument)
        assert quote is not None
        assert quote["ltp"] == 2501.25
        assert await redis.get(lease_key) is not None
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.wait(timeout=3)
        if replacement_loop is not None:
            replacement_loop.cancel()
            await asyncio.gather(replacement_loop, return_exceptions=True)
        if replacement is not None:
            await replacement.close()
        await redis.delete(marker_key, lease_key)
        await redis.aclose()


@pytest.mark.asyncio
async def test_real_redis_parallel_process_publish_load_preserves_versions_and_measures_latency():
    """Exercise concurrent publisher processes against Redis 7, not an in-memory fake."""
    redis = Redis.from_url(REDIS_TEST_URL, decode_responses=True)
    process_count = 4
    publishes_per_process = 100
    instrument = "NSE_EQ|MULTIPROCESS_LOAD"
    workers = [
        {
            "worker_id": f"load-worker-{index}",
            "user_id": str(uuid4()),
            "base_price": 1000.0 + (index * 100.0),
        }
        for index in range(process_count)
    ]
    child_script = textwrap.dedent(
        """
        import asyncio
        import json
        import os
        import time
        from datetime import datetime, timezone
        from uuid import UUID

        from redis.asyncio import Redis
        from app.services.redis_market_quote_publisher import RedisMarketQuotePublisher
        from app.services.upstox_market_data_streamer import MarketTick

        async def main():
            redis = Redis.from_url(os.environ["REDIS_TEST_URL"], decode_responses=True)
            user_id = UUID(os.environ["LOAD_USER_ID"])
            instrument = os.environ["LOAD_INSTRUMENT"]
            count = int(os.environ["LOAD_COUNT"])
            base_price = float(os.environ["LOAD_BASE_PRICE"])
            publisher = RedisMarketQuotePublisher(redis, user_id, ttl_seconds=15)
            latencies_ms = []
            started = time.perf_counter()
            for sequence in range(1, count + 1):
                now = datetime.now(timezone.utc)
                tick = MarketTick(
                    instrument_key=instrument,
                    ltp=base_price + sequence,
                    exchange_timestamp_ms=int(now.timestamp() * 1000),
                    received_at=now,
                    received_monotonic=time.monotonic(),
                )
                publish_started = time.perf_counter()
                if not await publisher.publish(tick):
                    raise RuntimeError(f"Redis rejected quote sequence {sequence}")
                latencies_ms.append((time.perf_counter() - publish_started) * 1000)
                await asyncio.sleep(0.005)
            ordered = sorted(latencies_ms)
            p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
            print(json.dumps({
                "worker_id": os.environ["LOAD_WORKER_ID"],
                "published": count,
                "elapsed_ms": (time.perf_counter() - started) * 1000,
                "p95_publish_ms": p95,
                "max_publish_ms": max(latencies_ms),
            }), flush=True)
            await redis.aclose()

        asyncio.run(main())
        """
    )
    processes = []
    started = time.perf_counter()
    try:
        for worker in workers:
            env = os.environ.copy()
            env.update({
                "REDIS_TEST_URL": REDIS_TEST_URL,
                "LOAD_WORKER_ID": worker["worker_id"],
                "LOAD_USER_ID": worker["user_id"],
                "LOAD_INSTRUMENT": instrument,
                "LOAD_COUNT": str(publishes_per_process),
                "LOAD_BASE_PRICE": str(worker["base_price"]),
            })
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-c",
                child_script,
                cwd=os.getcwd(),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            processes.append((worker, process))

        async with asyncio.timeout(30):
            outputs = await asyncio.gather(
                *(process.communicate() for _, process in processes)
            )

        wall_seconds = time.perf_counter() - started
        observations = []
        for (worker, process), (stdout, stderr) in zip(processes, outputs):
            assert process.returncode == 0, (
                f"{worker['worker_id']} exited {process.returncode}: "
                f"{stderr.decode(errors='replace')}"
            )
            result = json.loads(stdout.decode().strip())
            assert result["worker_id"] == worker["worker_id"]
            assert result["published"] == publishes_per_process
            assert result["elapsed_ms"] > 0
            assert result["p95_publish_ms"] >= 0
            assert result["max_publish_ms"] >= result["p95_publish_ms"]
            observations.append(result)

        total_published = sum(item["published"] for item in observations)
        observed_throughput = total_published / wall_seconds
        observed_p95_ms = max(item["p95_publish_ms"] for item in observations)
        assert total_published == process_count * publishes_per_process
        assert wall_seconds > 0
        assert observed_throughput > 0
        assert observed_p95_ms >= 0

        for worker in workers:
            user_id = UUID(worker["user_id"])
            consumer = RedisMarketQuoteConsumer(redis, user_id, max_age_seconds=15)
            quote = await consumer.get_quote(instrument)
            assert quote is not None
            assert quote["user_id"] == worker["user_id"]
            assert quote["version"] == publishes_per_process
            assert quote["ltp"] == worker["base_price"] + publishes_per_process
    finally:
        for _, process in processes:
            if process.returncode is None:
                process.kill()
                await process.wait()
        cleanup_keys = []
        for worker in workers:
            publisher = RedisMarketQuotePublisher(redis, UUID(worker["user_id"]))
            cleanup_keys.extend([
                publisher.snapshot_key(instrument),
                publisher.snapshot_key(instrument) + ":version",
            ])
        await redis.delete(*cleanup_keys)
        await redis.aclose()
