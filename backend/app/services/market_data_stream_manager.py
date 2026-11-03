"""Per-user Upstox stream registry with Redis-backed cross-process tick delivery."""
import asyncio
import logging
from uuid import UUID

from redis.asyncio import Redis, from_url

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.redis_market_quote_publisher import RedisMarketQuotePublisher
from app.services.upstox_market_data_streamer import MarketTick, UpstoxMarketDataStreamer

logger = logging.getLogger(__name__)


class MarketDataStreamManager:
    def __init__(self):
        self._streams: dict[UUID, UpstoxMarketDataStreamer] = {}
        self._user_locks: dict[UUID, asyncio.Lock] = {}
        self._redis: Redis | None = None

    def _user_lock(self, user_id: UUID) -> asyncio.Lock:
        # One lock per user serializes concurrent start/stop requests so only
        # one upstream socket can be created for that user in this process.
        return self._user_locks.setdefault(user_id, asyncio.Lock())

    def _redis_client(self) -> Redis:
        if self._redis is None:
            self._redis = from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def start(self, user_id: UUID, instrument_keys: list[str], mode: str = "full") -> UpstoxMarketDataStreamer:
        async with self._user_lock(user_id):
            current = self._streams.get(user_id)
            if current is not None and current.running:
                # A second start request adds/reconciles another feed-mode set
                # on the existing user socket instead of creating a duplicate.
                await current.subscribe(instrument_keys, mode)
                return current

            async def token_provider() -> str | None:
                db = SessionLocal()
                try:
                    return BrokerCredentialsService(db).get_analytics_token(user_id, "upstox")
                finally:
                    db.close()

            publisher = RedisMarketQuotePublisher(self._redis_client(), user_id)

            async def publish_tick(tick: MarketTick) -> None:
                # Redis outages must not tear down a healthy Upstox socket. The
                # publisher logs and fails closed; consumers see no usable quote.
                await publisher.publish(tick)

            streamer = UpstoxMarketDataStreamer(
                token_provider, instrument_keys, on_tick=publish_tick, mode=mode,
            )
            self._streams[user_id] = streamer
            try:
                await streamer.start()
            except BaseException:
                if self._streams.get(user_id) is streamer:
                    self._streams.pop(user_id, None)
                raise
            return streamer

    async def stop(self, user_id: UUID) -> bool:
        async with self._user_lock(user_id):
            streamer = self._streams.pop(user_id, None)
            if streamer is None:
                return False
            await streamer.stop()
            return True

    async def subscribe(self, user_id: UUID, instrument_keys: list[str], mode: str) -> tuple[UpstoxMarketDataStreamer, str]:
        async with self._user_lock(user_id):
            streamer = self._streams.get(user_id)
            if streamer is None or not streamer.running:
                raise ValueError("Start a market-data stream before adding subscriptions.")
            delivery = await streamer.subscribe(instrument_keys, mode)
            return streamer, delivery

    async def unsubscribe(self, user_id: UUID, instrument_keys: list[str]) -> tuple[UpstoxMarketDataStreamer, str]:
        async with self._user_lock(user_id):
            streamer = self._streams.get(user_id)
            if streamer is None or not streamer.running:
                raise ValueError("No running market-data stream exists.")
            delivery = await streamer.unsubscribe(instrument_keys)
            return streamer, delivery

    async def change_mode(self, user_id: UUID, instrument_keys: list[str], mode: str) -> tuple[UpstoxMarketDataStreamer, str]:
        async with self._user_lock(user_id):
            streamer = self._streams.get(user_id)
            if streamer is None or not streamer.running:
                raise ValueError("No running market-data stream exists.")
            delivery = await streamer.change_mode(instrument_keys, mode)
            return streamer, delivery

    def get(self, user_id: UUID) -> UpstoxMarketDataStreamer | None:
        return self._streams.get(user_id)

    async def shutdown(self) -> None:
        streams = list(self._streams.items())
        self._streams.clear()
        for _, streamer in streams:
            await streamer.stop()
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None


market_data_stream_manager = MarketDataStreamManager()
