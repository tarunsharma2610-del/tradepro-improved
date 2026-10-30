"""Fail-closed Redis quote consumer for scanner and paper-evaluation workers."""
import asyncio
import json
import logging
import math
from datetime import datetime, timezone
from uuid import UUID

logger = logging.getLogger(__name__)


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
        self._epochs: dict[str, str] = {}

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
            if snapshot.get("schema_version") != 1 or snapshot.get("user_id") != self.user_id:
                return None
            if snapshot.get("instrument_key") != instrument_key:
                return None
            epoch = snapshot.get("epoch")
            if not isinstance(epoch, str) or not epoch:
                return None
            version = snapshot.get("version")
            if isinstance(version, bool) or not isinstance(version, int) or version <= 0:
                return None
            previous_epoch = self._epochs.get(instrument_key)
            if previous_epoch == epoch and version < self._versions.get(instrument_key, 0):
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
            self._epochs[instrument_key] = epoch
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

    async def listen(
        self,
        instrument_keys: list[str],
        *,
        max_reconnect_attempts: int | None = None,
        min_backoff_seconds: float = 0.25,
        max_backoff_seconds: float = 5.0,
    ):
        """Continuously resubscribe after Redis failures and sweep snapshots.

        Production callers leave max_reconnect_attempts unset for indefinite
        recovery. The limit and backoff bounds also make failure tests bounded.
        """
        if max_reconnect_attempts is not None and max_reconnect_attempts < 0:
            raise ValueError("Maximum reconnect attempts cannot be negative.")
        if min_backoff_seconds < 0 or max_backoff_seconds < min_backoff_seconds:
            raise ValueError("Invalid Redis reconnect backoff bounds.")

        reconnect_attempts = 0
        backoff = min_backoff_seconds
        while True:
            pubsub = self.redis.pubsub()
            try:
                await pubsub.subscribe(self.channel)
                # Close the startup/reconnect race using authoritative snapshots.
                for quote in (await self.recover(instrument_keys)).values():
                    yield quote

                while True:
                    # A blocking listen() can remain suspended on a dead TCP
                    # socket indefinitely when Redis is restarted without
                    # another message. Poll with a bounded timeout and use a
                    # Pub/Sub PING/PONG heartbeat to detect dead connections.
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=False,
                        timeout=1.0,
                    )
                    if message is None:
                        # PING is sent on the Pub/Sub connection itself. Read
                        # its PONG explicitly; do not use the general Redis
                        # connection pool as a proxy for Pub/Sub health.
                        await pubsub.ping()
                        pong = await pubsub.get_message(
                            ignore_subscribe_messages=False,
                            timeout=2.0,
                        )
                        if pong is None or pong.get("type") != "pong":
                            raise ConnectionError("Redis Pub/Sub heartbeat was not acknowledged")
                        continue
                    if message.get("type") != "message":
                        # Subscription acknowledgements and heartbeat replies
                        # are control frames, never market-data notifications.
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
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                reconnect_attempts += 1
                # Redis may have restarted with volatile data and INCR keys
                # reset. Local version high-water marks belong to the old
                # Redis process; clear them before reading the new epoch.
                self._versions.clear()
                self._epochs.clear()
                logger.warning(
                    "Redis quote consumer disconnected; reconnect attempt %s (%s).",
                    reconnect_attempts, type(exc).__name__,
                )
                if max_reconnect_attempts is not None and reconnect_attempts > max_reconnect_attempts:
                    return
                if max_backoff_seconds:
                    await asyncio.sleep(backoff)
                backoff = min(max(backoff * 2, min_backoff_seconds), max_backoff_seconds)
            finally:
                try:
                    await pubsub.unsubscribe(self.channel)
                except Exception:
                    pass
                try:
                    await pubsub.aclose()
                except Exception:
                    pass
