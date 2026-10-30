"""Authenticated Upstox Market Data Feed V3 client.

Each connection gets a fresh one-time authorization URL. WebSocket protocol
ping/pong is enabled; silence, socket failures and decode errors trigger a
bounded exponential reconnect loop. Cached ticks are unusable once stale.
This module does not place or modify orders.
"""
import asyncio
import json
import logging
import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable, Literal
from urllib.parse import urlparse

import httpx
import websockets

from app.brokers.upstox.proto import MarketDataFeedV3_pb2 as market_data_pb

logger = logging.getLogger(__name__)
_AUTH_URL = "https://api.upstox.com/v3/feed/market-data-feed/authorize"
_MAX_LTPC_KEYS = 5000


@dataclass(frozen=True)
class MarketTick:
    instrument_key: str
    ltp: float
    exchange_timestamp_ms: int
    received_at: datetime
    received_monotonic: float
    # None means the provider omitted the field; it is not a zero-value reading.
    depth: tuple[dict, ...] | None = None
    option_greeks: dict | None = None
    open_interest: float | None = None
    volume_traded_today: int | None = None
    average_traded_price: float | None = None
    total_buy_quantity: float | None = None
    total_sell_quantity: float | None = None
    ohlc: tuple[dict, ...] | None = None


class UpstoxMarketDataStreamer:
    """One user-scoped streamer; token_provider is called on every reconnect."""

    def __init__(
        self,
        token_provider: Callable[[], Awaitable[str | None]],
        instrument_keys: list[str],
        on_tick: Callable[[MarketTick], object] | None = None,
        *,
        stale_after_seconds: float = 15.0,
        silence_timeout_seconds: float = 60.0,
        reconnect_max_seconds: float = 30.0,
        mode: Literal["ltpc", "full", "option_greeks"] = "full",
    ):
        keys = list(dict.fromkeys(key.strip() for key in instrument_keys if key.strip()))
        if not keys:
            raise ValueError("At least one instrument_key is required.")
        limits = {"ltpc": 5000, "option_greeks": 3000, "full": 2000}
        if mode not in limits:
            raise ValueError("Unsupported Upstox V3 mode; full_d30 requires an eligible Upstox Plus entitlement and is not enabled here.")
        if len(keys) > limits[mode]:
            raise ValueError(f"{mode} supports at most {limits[mode]} instrument keys per connection.")
        if any("|" not in key or len(key) > 100 for key in keys):
            raise ValueError("Every instrument_key must be a valid segment-prefixed key.")
        if stale_after_seconds <= 0 or silence_timeout_seconds <= stale_after_seconds:
            raise ValueError("Silence timeout must be greater than the positive stale-data timeout.")

        self.token_provider = token_provider
        self.instrument_keys = keys
        self.mode = mode
        self._instrument_key_set = set(keys)
        self.on_tick = on_tick
        self.stale_after_seconds = stale_after_seconds
        self.silence_timeout_seconds = silence_timeout_seconds
        self.reconnect_max_seconds = reconnect_max_seconds
        self._ticks: dict[str, MarketTick] = {}
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def latest_tick(self, instrument_key: str) -> MarketTick | None:
        """Return only fresh data; callers must fail closed when this is None."""
        tick = self._ticks.get(instrument_key)
        if tick is None:
            return None
        if time.monotonic() - tick.received_monotonic > self.stale_after_seconds:
            return None
        if tick.exchange_timestamp_ms <= 0:
            return None
        exchange_age = datetime.now(timezone.utc).timestamp() * 1000 - tick.exchange_timestamp_ms
        if exchange_age > self.stale_after_seconds * 1000 or exchange_age < -60_000:
            return None
        return tick

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run(), name="upstox-market-data-v3")

    async def stop(self) -> None:
        self._stop.set()
        task = self._task
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._task = None
        self._connected = False

    async def _authorized_url(self, access_token: str) -> str:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                _AUTH_URL,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            response.raise_for_status()
            body = response.json()
        url = body.get("data", {}).get("authorized_redirect_uri")
        parsed = urlparse(url or "")
        if parsed.scheme != "wss" or not parsed.hostname or not (
            parsed.hostname == "upstox.com" or parsed.hostname.endswith(".upstox.com")
        ):
            raise ValueError("Upstox returned an invalid WebSocket authorization URL.")
        return url

    async def _run(self) -> None:
        delay = 1.0
        while not self._stop.is_set():
            try:
                token = await self.token_provider()
                if not token:
                    logger.warning("Upstox market stream has no valid access token; retrying.")
                    await self._sleep_or_stop(delay)
                    delay = min(delay * 2, self.reconnect_max_seconds)
                    continue
                url = await self._authorized_url(token)
                # Default TLS certificate verification remains enabled.
                async with websockets.connect(
                    url,
                    open_timeout=15,
                    close_timeout=5,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=8 * 1024 * 1024,
                ) as socket:
                    self._connected = True
                    delay = 1.0
                    request = {
                        "guid": "tradepro-improved-market-data-v3",
                        "method": "sub",
                        "data": {"mode": self.mode, "instrumentKeys": self.instrument_keys},
                    }
                    await socket.send(json.dumps(request).encode("utf-8"))
                    while not self._stop.is_set():
                        # The websockets library handles ping/pong. A silent
                        # application stream is recycled so stale state is not trusted.
                        payload = await asyncio.wait_for(
                            socket.recv(), timeout=self.silence_timeout_seconds
                        )
                        if not isinstance(payload, (bytes, bytearray)):
                            raise ValueError("Expected a binary Upstox protobuf frame.")
                        await self._consume(bytes(payload))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._connected = False
                # Avoid logging URL, token, or response bodies that might contain credentials.
                logger.warning("Upstox market stream disconnected (%s); reconnecting.", type(exc).__name__)
            finally:
                self._connected = False
            if not self._stop.is_set():
                await self._sleep_or_stop(delay)
                delay = min(delay * 2, self.reconnect_max_seconds)

    async def _sleep_or_stop(self, seconds: float) -> None:
        try:
            await asyncio.wait_for(self._stop.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            pass

    async def _consume(self, payload: bytes) -> None:
        response = market_data_pb.FeedResponse()
        response.ParseFromString(payload)
        received_at = datetime.now(timezone.utc)
        received_monotonic = time.monotonic()
        for key, feed in response.feeds.items():
            if key not in self._instrument_key_set:
                continue
            union = feed.WhichOneof("FeedUnion")
            ltpc = None
            if union == "ltpc":
                ltpc = feed.ltpc
            elif union == "fullFeed":
                full_union = feed.fullFeed.WhichOneof("FullFeedUnion")
                if full_union == "marketFF":
                    ltpc = feed.fullFeed.marketFF.ltpc
                elif full_union == "indexFF":
                    ltpc = feed.fullFeed.indexFF.ltpc
            elif union == "firstLevelWithGreeks":
                ltpc = feed.firstLevelWithGreeks.ltpc

            market_ff = None
            if union == "fullFeed" and full_union == "marketFF":
                market_ff = feed.fullFeed.marketFF
            elif union == "firstLevelWithGreeks":
                market_ff = feed.firstLevelWithGreeks
            if ltpc is None or not math.isfinite(ltpc.ltp) or ltpc.ltp <= 0 or ltpc.ltt <= 0:
                continue
            depth = None
            greeks = None
            open_interest = volume = average_price = total_buy = total_sell = None
            ohlc = None
            if market_ff is not None:
                if union == "fullFeed" and full_union == "marketFF":
                    depth = tuple({
                        "bid_quantity": int(q.bidQ), "bid_price": float(q.bidP),
                        "ask_quantity": int(q.askQ), "ask_price": float(q.askP),
                    } for q in market_ff.marketLevel.bidAskQuote)
                    greeks_source = market_ff.optionGreeks
                    open_interest = float(market_ff.oi) if market_ff.HasField("oi") else None
                    volume = int(market_ff.vtt) if market_ff.HasField("vtt") else None
                    average_price = float(market_ff.atp) if market_ff.HasField("atp") else None
                    total_buy = float(market_ff.tbq) if market_ff.HasField("tbq") else None
                    total_sell = float(market_ff.tsq) if market_ff.HasField("tsq") else None
                    ohlc = tuple({
                        "interval": item.interval, "open": float(item.open),
                        "high": float(item.high), "low": float(item.low),
                        "close": float(item.close), "volume": int(item.vol),
                        "timestamp_ms": int(item.ts),
                    } for item in market_ff.marketOHLC.ohlc)
                else:
                    greeks_source = market_ff.optionGreeks
                    if market_ff.HasField("oi"):
                        open_interest = float(market_ff.oi)
                    if market_ff.HasField("vtt"):
                        volume = int(market_ff.vtt)
                greeks = {
                    "delta": float(greeks_source.delta), "theta": float(greeks_source.theta),
                    "gamma": float(greeks_source.gamma), "vega": float(greeks_source.vega),
                    "rho": float(greeks_source.rho),
                }
            tick = MarketTick(
                instrument_key=key,
                ltp=float(ltpc.ltp),
                exchange_timestamp_ms=int(ltpc.ltt),
                received_at=received_at,
                received_monotonic=received_monotonic,
                depth=depth,
                option_greeks=greeks,
                open_interest=open_interest,
                volume_traded_today=volume,
                average_traded_price=average_price,
                total_buy_quantity=total_buy,
                total_sell_quantity=total_sell,
                ohlc=ohlc,
            )
            self._ticks[key] = tick
            if self.on_tick is not None:
                result = self.on_tick(tick)
                if asyncio.iscoroutine(result):
                    await result
