"""User-isolated Redis delivery for validated Upstox market ticks.

The latest snapshot is authoritative; Pub/Sub is only a wake-up signal.
Consumers must read and validate the snapshot rather than trust a Pub/Sub
message as the quote itself.
"""
import json
import logging
import math
from datetime import datetime, timezone
from uuid import UUID

from redis.asyncio import Redis

from app.services.upstox_market_data_streamer import MarketTick

logger = logging.getLogger(__name__)

_PUBLISH_ATOMIC = """
local version = redis.call('INCR', KEYS[2])
redis.call('EXPIRE', KEYS[2], ARGV[2])
local encoded = string.gsub(ARGV[1], '"version":0', '"version":' .. version, 1)
redis.call('SET', KEYS[1], encoded, 'EX', ARGV[2])
local event = cjson.encode({
    schema_version = 1,
    user_id = ARGV[3],
    instrument_key = ARGV[4],
    version = version
})
redis.call('PUBLISH', KEYS[3], event)
return version
"""


class RedisMarketQuotePublisher:
    """Publish fresh ticks with atomic version, snapshot and notification ordering."""

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
        if not math.isfinite(tick.ltp) or tick.ltp <= 0 or tick.exchange_timestamp_ms <= 0:
            return False
        if now.tzinfo is None or tick.received_at.tzinfo is None:
            return False
        received_age = (now - tick.received_at.astimezone(timezone.utc)).total_seconds()
        exchange_age = now.timestamp() * 1000 - tick.exchange_timestamp_ms
        return 0 <= received_age <= self.ttl_seconds and -60_000 <= exchange_age <= self.ttl_seconds * 1000

    async def publish(self, tick: MarketTick) -> bool:
        """Atomically allocate version, store expiring snapshot and publish event."""
        now = datetime.now(timezone.utc)
        if not self._fresh(tick, now):
            return False
        key = self.snapshot_key(tick.instrument_key)
        version_key = f"{key}:version"
        try:
            snapshot = {
                "schema_version": 1, "user_id": self.user_id,
                "instrument_key": tick.instrument_key, "version": 0,
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
            await self.redis.eval(
                _PUBLISH_ATOMIC, 3, key, version_key, self.channel,
                encoded, self.ttl_seconds, self.user_id, tick.instrument_key,
            )
            return True
        except Exception as exc:
            logger.warning("Redis market quote publish failed (%s); quote is unavailable to consumers.", type(exc).__name__)
            return False
