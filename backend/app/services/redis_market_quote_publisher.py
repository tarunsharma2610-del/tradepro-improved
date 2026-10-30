"""User-isolated Redis delivery for validated Upstox market ticks.

The latest snapshot is authoritative; Pub/Sub is only a wake-up signal.
Consumers must read and validate the snapshot rather than trust a Pub/Sub
message as the quote itself.
"""
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from redis.asyncio import Redis

from app.services.upstox_market_data_streamer import MarketTick

logger = logging.getLogger(__name__)


class RedisMarketQuotePublisher:
    """Publish fresh ticks into a per-user Redis cache and notification channel."""

    def __init__(self, redis_client: Redis, user_id: UUID, *, ttl_seconds: int = 15) -> None:
        if ttl_seconds <= 0:
            raise ValueError("Quote TTL must be positive.")
        self.redis = redis_client
        self.user_id = str(user_id)
        self.ttl_seconds = ttl_seconds
        self.key_prefix = f"tradepro:market:v1:user:{self.user_id}"

    def snapshot_key(self, instrument_key: str) -> str:
        return f"{self.key_prefix}:quote:{instrument_key}"

    @property
    def channel(self) -> str:
        return f"{self.key_prefix}:updates"

    def _fresh(self, tick: MarketTick, now: datetime) -> bool:
        if not tick.instrument_key or "|" not in tick.instrument_key:
            return False
        if tick.ltp <= 0 or tick.exchange_timestamp_ms <= 0:
            return False
        if now.tzinfo is None or tick.received_at.tzinfo is None:
            return False
        received_age = (now - tick.received_at.astimezone(timezone.utc)).total_seconds()
        exchange_age = now.timestamp() * 1000 - tick.exchange_timestamp_ms
        return 0 <= received_age <= self.ttl_seconds and -60_000 <= exchange_age <= self.ttl_seconds * 1000

    async def publish(self, tick: MarketTick) -> bool:
        """Atomically store a versioned snapshot and publish its key/version."""
        now = datetime.now(timezone.utc)
        if not self._fresh(tick, now):
            return False
        key = self.snapshot_key(tick.instrument_key)
        version_key = f"{key}:version"
        try:
            version = await self.redis.incr(version_key)
            snapshot = {
                "schema_version": 1, "user_id": self.user_id,
                "instrument_key": tick.instrument_key, "version": version,
                "ltp": tick.ltp, "exchange_timestamp_ms": tick.exchange_timestamp_ms,
                "received_at": tick.received_at.astimezone(timezone.utc).isoformat(),
                "published_at": now.isoformat(), "depth": tick.depth,
                "option_greeks": tick.option_greeks, "open_interest": tick.open_interest,
                "volume_traded_today": tick.volume_traded_today,
                "average_traded_price": tick.average_traded_price,
                "total_buy_quantity": tick.total_buy_quantity,
                "total_sell_quantity": tick.total_sell_quantity, "ohlc": tick.ohlc,
            }
            encoded = json.dumps(snapshot, separators=(",", ":"), allow_nan=False)
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.set(key, encoded, ex=self.ttl_seconds)
                pipe.publish(self.channel, json.dumps({
                    "schema_version": 1, "user_id": self.user_id,
                    "instrument_key": tick.instrument_key, "version": version,
                }, separators=(",", ":")))
                await pipe.execute()
            return True
        except Exception as exc:
            logger.warning("Redis market quote publish failed (%s); quote is unavailable to consumers.", type(exc).__name__)
            return False
