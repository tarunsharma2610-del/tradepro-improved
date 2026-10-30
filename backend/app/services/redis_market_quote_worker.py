"""Leased worker-side Redis quote consumption.

The API owns Upstox WebSockets and publishes user-scoped snapshots. This
worker independently consumes those snapshots. A token-checked Redis lease
ensures only one worker replica consumes a given user's channel at a time.
This module does not place, modify, or cancel broker orders.
"""
import asyncio
import logging
import time
import inspect
from collections.abc import Awaitable, Callable
from uuid import UUID, uuid4

from redis.asyncio import Redis, from_url

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.broker_connection import BrokerConnection
from app.models.market_data_subscription import MarketDataSubscription
from app.services.redis_market_quote_consumer import RedisMarketQuoteConsumer

logger = logging.getLogger(__name__)

_RENEW_LEASE = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('PEXPIRE', KEYS[1], ARGV[2])
end
return 0
"""
_RELEASE_LEASE = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""


class RedisMarketQuoteWorker:
    """Reconcile durable subscriptions into one leased consumer per user."""

    def __init__(
        self,
        *,
        redis_client: Redis | None = None,
        subscription_loader: Callable[[], dict[UUID, list[str]]] | None = None,
        consumer_factory: Callable[[Redis, UUID], RedisMarketQuoteConsumer] | None = None,
        on_quote: Callable[[UUID, dict], Awaitable[None] | None] | None = None,
        lease_seconds: int = 30,
        reconcile_seconds: float = 5.0,
    ) -> None:
        if lease_seconds < 3 or reconcile_seconds <= 0:
            raise ValueError("Lease must be at least 3 seconds and reconcile interval must be positive.")
        self.redis = redis_client if redis_client is not None else from_url(settings.REDIS_URL, decode_responses=True)
        self._owns_redis = redis_client is None
        self.subscription_loader = subscription_loader or self._load_subscriptions
        self.consumer_factory = consumer_factory or (
            lambda client, user_id: RedisMarketQuoteConsumer(client, user_id)
        )
        self.on_quote = on_quote
        self.lease_seconds = lease_seconds
        self.quote_max_age_seconds = 15.0
        self.reconcile_seconds = reconcile_seconds
        self._tasks: dict[UUID, tuple[tuple[str, ...], asyncio.Task]] = {}
        self._latest_quotes: dict[tuple[UUID, str], dict] = {}
        self._latest_quote_times: dict[tuple[UUID, str], float] = {}
        self._closed = False

    @staticmethod
    def _load_subscriptions() -> dict[UUID, list[str]]:
        db = SessionLocal()
        try:
            rows = (
                db.query(MarketDataSubscription)
                .join(
                    BrokerConnection,
                    MarketDataSubscription.broker_connection_id == BrokerConnection.id,
                )
                .filter(
                    MarketDataSubscription.is_active.is_(True),
                    BrokerConnection.broker == "upstox",
                    BrokerConnection.user_id == MarketDataSubscription.user_id,
                )
                .all()
            )
            grouped: dict[UUID, dict[str, set[str]]] = {}
            for row in rows:
                grouped.setdefault(row.user_id, {}).setdefault(row.feed_mode, set()).add(
                    row.instrument.instrument_key
                )
            desired: dict[UUID, list[str]] = {}
            for user_id, modes in grouped.items():
                owners: dict[str, str] = {}
                conflict = False
                for mode, keys in modes.items():
                    for key in keys:
                        previous = owners.get(key)
                        if previous is not None and previous != mode:
                            conflict = True
                            break
                        owners[key] = mode
                    if conflict:
                        break
                if conflict:
                    logger.error(
                        "Skipping quote consumption for user=%s: conflicting persisted feed-mode assignments",
                        user_id,
                    )
                    continue
                desired[user_id] = sorted(owners)
            return desired
        finally:
            db.close()

    @staticmethod
    def _lease_key(user_id: UUID) -> str:
        return f"tradepro:market:v1:consumer-lease:user:{user_id}"

    async def _acquire_lease(self, user_id: UUID, token: str) -> bool:
        return bool(await self.redis.set(
            self._lease_key(user_id), token, nx=True, px=self.lease_seconds * 1000
        ))

    async def _renew_lease(self, user_id: UUID, token: str) -> bool:
        result = await self.redis.eval(
            _RENEW_LEASE, 1, self._lease_key(user_id), token, self.lease_seconds * 1000
        )
        return bool(result)

    async def _release_lease(self, user_id: UUID, token: str) -> None:
        await self.redis.eval(_RELEASE_LEASE, 1, self._lease_key(user_id), token)

    async def _consume(self, user_id: UUID, instrument_keys: tuple[str, ...]) -> None:
        token = uuid4().hex
        try:
            acquired = await self._acquire_lease(user_id, token)
        except Exception:
            logger.warning("Could not acquire Redis quote consumer lease for user=%s", user_id)
            return
        if not acquired:
            logger.debug("Another worker owns Redis quote consumption for user=%s", user_id)
            return

        listener_task: asyncio.Task | None = None
        renewal_task: asyncio.Task | None = None
        lost_lease = asyncio.Event()
        consumer = None

        async def listen() -> None:
            async for quote in consumer.listen(list(instrument_keys)):
                key = quote.get("instrument_key")
                if not isinstance(key, str):
                    continue
                quote_key = (user_id, key)
                self._latest_quotes[quote_key] = quote
                self._latest_quote_times[quote_key] = time.monotonic()
                if self.on_quote is not None:
                    try:
                        result = self.on_quote(user_id, quote)
                        if inspect.isawaitable(result):
                            await result
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        # Downstream scanner/observer failures must not tear
                        # down the Redis listener or surrender its user lease.
                        logger.exception("Market quote callback failed for user=%s instrument=%s", user_id, key)

        async def renew() -> None:
            interval = self.lease_seconds / 3
            while True:
                await asyncio.sleep(interval)
                if not await self._renew_lease(user_id, token):
                    lost_lease.set()
                    return

        try:
            # Construct the consumer inside the lease-protected cleanup scope.
            # A factory/configuration error must not strand the user's lease
            # until its TTL expires and delay another healthy worker replica.
            consumer = self.consumer_factory(self.redis, user_id)
            listener_task = asyncio.create_task(listen(), name=f"market-quotes:{user_id}")
            renewal_task = asyncio.create_task(renew(), name=f"market-quote-lease:{user_id}")
            done, pending = await asyncio.wait(
                {listener_task, renewal_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                exception = task.exception()
                if exception is not None:
                    raise exception
            if lost_lease.is_set():
                logger.warning("Redis quote consumer lease lost for user=%s", user_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Redis quote consumer stopped for user=%s", user_id)
        finally:
            for task in (listener_task, renewal_task):
                if task is not None and not task.done():
                    task.cancel()
            await asyncio.gather(
                *(task for task in (listener_task, renewal_task) if task is not None),
                return_exceptions=True,
            )
            for key in instrument_keys:
                quote_key = (user_id, key)
                self._latest_quotes.pop(quote_key, None)
                self._latest_quote_times.pop(quote_key, None)
            try:
                await self._release_lease(user_id, token)
            except Exception:
                logger.warning("Could not release Redis quote consumer lease for user=%s", user_id)

    async def reconcile_once(self) -> None:
        if self._closed:
            return
        desired = self.subscription_loader()
        normalized = {
            user_id: tuple(sorted(set(keys)))
            for user_id, keys in desired.items()
            if keys
        }
        for user_id, (current_keys, task) in list(self._tasks.items()):
            if user_id not in normalized or normalized[user_id] != current_keys or task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                self._tasks.pop(user_id, None)
        for user_id, keys in normalized.items():
            if user_id not in self._tasks:
                task = asyncio.create_task(
                    self._consume(user_id, keys),
                    name=f"market-quote-user:{user_id}",
                )
                self._tasks[user_id] = (keys, task)

    async def run_forever(self) -> None:
        while not self._closed:
            try:
                await self.reconcile_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Market quote worker reconciliation failed; will retry")
            await asyncio.sleep(self.reconcile_seconds)

    def latest_quote(self, user_id: UUID, instrument_key: str) -> dict | None:
        """Return the latest validated in-process quote, if this worker owns it."""
        quote_key = (user_id, instrument_key)
        received_at = self._latest_quote_times.get(quote_key)
        if received_at is None or time.monotonic() - received_at > self.quote_max_age_seconds:
            self._latest_quotes.pop(quote_key, None)
            self._latest_quote_times.pop(quote_key, None)
            return None
        return self._latest_quotes.get(quote_key)

    async def close(self) -> None:
        self._closed = True
        tasks = [task for _, task in self._tasks.values()]
        self._tasks.clear()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._latest_quotes.clear()
        self._latest_quote_times.clear()
        if self._owns_redis:
            await self.redis.aclose()
