"""Fail-closed Redis quote consumer for scanner and paper-evaluation workers."""
import json
import math
from datetime import datetime, timezone
from uuid import UUID


class RedisMarketQuoteConsumer:
    """Read authoritative snapshots; Pub/Sub messages only trigger snapshot reads."""

    def __init__(self, redis_client, user_id: UUID, *, max_age_seconds: int = 15):
        if max_age_seconds <= 0:
            raise ValueError("Quote maximum age must be positive.")
        self.redis = redis_client
        self.user_id = str(user_id)
        self.max_age_seconds = max_age_seconds
        self.key_prefix = f"tradepro:market:v1:user:{self.user_id}"
        self._versions: dict[str, int] = {}

    def snapshot_key(self, instrument_key: str) -> str:
        return f"{self.key_prefix}:quote:{instrument_key}"

    @property
    def channel(self) -> str:
        return f"{self.key_prefix}:updates"

    async def get_quote(self, instrument_key: str) -> dict | None:
        """Return a validated quote or None. Never trust Pub/Sub payload data."""
        if not instrument_key or "|" not in instrument_key:
            return None
        key = self.snapshot_key(instrument_key)
        try:
            raw, ttl = await self.redis.get(key), await self.redis.ttl(key)
            if raw is None or ttl <= 0 or ttl > self.max_age_seconds:
                return None
            snapshot = json.loads(raw)
            if not isinstance(snapshot, dict):
                return None
            if snapshot.get("schema_version") != 1:
                return None
            if snapshot.get("user_id") != self.user_id:
                return None
            if snapshot.get("instrument_key") != instrument_key:
                return None
            version = snapshot.get("version")
            if isinstance(version, bool) or not isinstance(version, int) or version <= 0:
                return None
            if version < self._versions.get(instrument_key, 0):
                return None
            ltp = snapshot.get("ltp")
            if isinstance(ltp, bool) or not isinstance(ltp, (int, float)) or not math.isfinite(ltp) or ltp <= 0:
                return None
            exchange_ms = snapshot.get("exchange_timestamp_ms")
            if isinstance(exchange_ms, bool) or not isinstance(exchange_ms, int) or exchange_ms <= 0:
                return None
            received = datetime.fromisoformat(snapshot["received_at"])
            if received.tzinfo is None:
                return None
            now = datetime.now(timezone.utc)
            received_age = (now - received.astimezone(timezone.utc)).total_seconds()
            exchange_age = now.timestamp() * 1000 - exchange_ms
            if not 0 <= received_age <= self.max_age_seconds:
                return None
            if not -60_000 <= exchange_age <= self.max_age_seconds * 1000:
                return None
            self._versions[instrument_key] = version
            return snapshot
        except (TypeError, ValueError, KeyError, json.JSONDecodeError):
            return None
        except Exception:
            # Redis failures are an unavailable quote, never a stale fallback.
            return None

    async def recover(self, instrument_keys: list[str]) -> dict[str, dict]:
        """Re-read latest snapshots after startup/reconnect; Pub/Sub is lossy."""
        recovered = {}
        for instrument_key in dict.fromkeys(instrument_keys):
            quote = await self.get_quote(instrument_key)
            if quote is not None:
                recovered[instrument_key] = quote
        return recovered

    async def listen(self, instrument_keys: list[str]):
        """Yield validated latest snapshots after subscription and each notification."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.channel)
        try:
            # Initial snapshot sweep closes the subscribe/startup race.
            for quote in (await self.recover(instrument_keys)).values():
                yield quote
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                try:
                    event = json.loads(message.get("data", "{}"))
                    if not isinstance(event, dict) or event.get("user_id") != self.user_id:
                        continue
                    instrument_key = event.get("instrument_key")
                    event_version = event.get("version")
                    if instrument_key not in instrument_keys:
                        continue
                    if isinstance(event_version, bool) or not isinstance(event_version, int) or event_version <= 0:
                        continue
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
                quote = await self.get_quote(instrument_key)
                if quote is not None and quote["version"] >= event_version:
                    yield quote
        finally:
            await pubsub.unsubscribe(self.channel)
            await pubsub.aclose()
