"""Per-user Upstox stream registry with Redis-backed cross-process tick delivery."""
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
        self._redis: Redis | None = None

    def _redis_client(self) -> Redis:
        if self._redis is None:
            self._redis = from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def start(self, user_id: UUID, instrument_keys: list[str], mode: str = "full") -> UpstoxMarketDataStreamer:
        current = self._streams.get(user_id)
        if current is not None and current.running:
            # A second start request adds/reconciles another feed-mode set on
            # the existing user socket instead of disrupting healthy feeds.
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
        await streamer.start()
        return streamer

    async def stop(self, user_id: UUID) -> bool:
        streamer = self._streams.pop(user_id, None)
        if streamer is None:
            return False
        await streamer.stop()
        return True

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
