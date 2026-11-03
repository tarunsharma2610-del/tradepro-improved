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
    indicative_equilibrium_price: float | None = None
    reference_price: float | None = None
    indicative_equilibrium_quantity: int | None = None
    indicative_interest_quantity_total: int | None = None
    indicative_interest_quantity_market: int | None = None
    cas_eligible: bool = False


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
        # Keep a mode-indexed desired-state registry, matching the official
        # Upstox V3 SDK's subscription model while retaining our async transport.
        self.mode = mode  # legacy/default mode for callers that omit mode
        self.subscriptions: dict[str, set[str]] = {
            "ltpc": set(), "option_greeks": set(), "full": set()
        }
        self.subscriptions[mode].update(keys)
        self._instrument_key_set = set(keys)
        self.on_tick = on_tick
        self.stale_after_seconds = stale_after_seconds
        self.silence_timeout_seconds = silence_timeout_seconds
        self.reconnect_max_seconds = reconnect_max_seconds
        self._ticks: dict[str, MarketTick] = {}
        self._market_info: dict | None = None
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._connected = False
        self._socket = None
        self._send_lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def market_info(self) -> dict | None:
        return self._market_info

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

    async def _send_message(self, socket, method: str, instrument_keys: list[str], mode: str | None = None) -> None:
        request = {
            "guid": f"tradepro-improved-{method}-{time.time_ns()}",
            "method": method,
            "data": {"instrumentKeys": instrument_keys},
        }
        if mode is not None:
            request["data"]["mode"] = mode
        async with self._send_lock:
            await socket.send(json.dumps(request).encode("utf-8"))

    async def _send_control(self, method: str, instrument_keys: list[str], mode: str | None = None) -> str:
        socket = self._socket
        if socket is None or not self._connected:
            return "queued_for_reconnect"
        await self._send_message(socket, method, instrument_keys, mode)
        return "sent"

    def _validate_key_list(self, instrument_keys: list[str]) -> list[str]:
        keys = list(dict.fromkeys(key.strip() for key in instrument_keys if key.strip()))
        if not keys or any("|" not in key or len(key) > 100 for key in keys):
            raise ValueError("Provide valid segment-prefixed instrument keys.")
        return keys

    @property
    def subscriptions_by_mode(self) -> dict[str, list[str]]:
        return {mode: sorted(keys) for mode, keys in self.subscriptions.items() if keys}

    def _refresh_instrument_index(self) -> None:
        self._instrument_key_set = set().union(*self.subscriptions.values())
        self.instrument_keys = sorted(self._instrument_key_set)

    def _validate_mode_limits(self, proposed: dict[str, set[str]]) -> None:
        individual = {"ltpc": 5000, "option_greeks": 3000, "full": 2000}
        combined = {"ltpc": 2000, "option_greeks": 2000, "full": 1500}
        active_modes = [name for name, keys in proposed.items() if keys]
        for feed_mode in active_modes:
            limit = individual[feed_mode] if len(active_modes) == 1 else combined[feed_mode]
            if len(proposed[feed_mode]) > limit:
                raise ValueError(
                    f"{feed_mode} mode supports at most {limit} instrument keys "
                    "in the current subscription combination."
                )

    async def subscribe(self, instrument_keys: list[str], mode: str | None = None) -> str:
        keys = self._validate_key_list(instrument_keys)
        target_mode = mode or self.mode
        if target_mode not in self.subscriptions:
            raise ValueError("Unsupported mode. Allowed: ltpc, option_greeks, full.")
        additions = [key for key in keys if key not in self._instrument_key_set]
        already_in_mode = set(keys) & self.subscriptions[target_mode]
        if not additions and len(already_in_mode) == len(keys):
            return "already_subscribed"
        # A key cannot be simultaneously assigned to two feed modes. Use
        # change_mode() for an existing key to avoid ambiguous provider state.
        conflicts = set(keys) & self._instrument_key_set - self.subscriptions[target_mode]
        if conflicts:
            raise ValueError("Instrument already subscribed in another mode; use change_mode().")
        proposed = {name: set(mode_keys) for name, mode_keys in self.subscriptions.items()}
        proposed[target_mode].update(additions)
        self._validate_mode_limits(proposed)
        self.subscriptions = proposed
        self._refresh_instrument_index()
        if not additions:
            return "already_subscribed"
        return await self._send_control("sub", additions, target_mode)

    async def unsubscribe(self, instrument_keys: list[str]) -> str:
        keys = self._validate_key_list(instrument_keys)
        removals = [key for key in keys if key in self._instrument_key_set]
        if not removals:
            return "not_subscribed"
        if len(removals) == len(self.instrument_keys):
            raise ValueError("Cannot remove the final instruments; use DELETE /market-data/stream to stop the stream.")
        for mode_keys in self.subscriptions.values():
            mode_keys.difference_update(removals)
        self._refresh_instrument_index()
        for key in removals:
            self._ticks.pop(key, None)
        return await self._send_control("unsub", removals)

    async def change_mode(self, instrument_keys: list[str], mode: str) -> str:
        keys = self._validate_key_list(instrument_keys)
        if mode not in self.subscriptions:
            raise ValueError("Unsupported mode. Allowed: ltpc, option_greeks, full.")
        missing = set(keys) - self._instrument_key_set
        if missing:
            raise ValueError("All instruments must already be subscribed before changing mode.")
        current_modes = {name for name, mode_keys in self.subscriptions.items() if set(keys) & mode_keys}
        if len(current_modes) == 1 and mode in current_modes:
            return "already_in_mode"
        proposed = {name: set(mode_keys) - set(keys) for name, mode_keys in self.subscriptions.items()}
        proposed[mode].update(keys)
        self._validate_mode_limits(proposed)
        self.subscriptions = proposed
        self._refresh_instrument_index()
        active_modes = [name for name, mode_keys in self.subscriptions.items() if mode_keys]
        if len(active_modes) == 1:
            self.mode = mode
        for key in keys:
            self._ticks.pop(key, None)
        return await self._send_control("change_mode", keys, mode)

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
                    self._socket = socket
                    self._connected = True
                    delay = 1.0
                    # Rehydrate each feed-mode set independently after every
                    # reconnect; never flatten mixed-mode intent into one mode.
                    for feed_mode, keys in self.subscriptions_by_mode.items():
                        await self._send_message(socket, "sub", keys, feed_mode)
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
                self._socket = None
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
        if response.HasField("marketInfo"):
            info = response.marketInfo
            self._market_info = {
                "current_timestamp_ms": int(response.currentTs),
                "segment_status": {
                    segment: market_data_pb.MarketStatus.Name(value)
                    for segment, value in info.segmentStatus.items()
                },
                "cas_market_status": {
                    segment: {"status": value.status, "updated_time_ms": int(value.updatedTime)}
                    for segment, value in info.casMarketStatus.items()
                },
                "pre_open_session_status": {
                    segment: {"status": value.status, "updated_time_ms": int(value.updatedTime)}
                    for segment, value in info.preOpenSessionStatus.items()
                },
            }
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
            indicative_equilibrium_price = (
                float(ltpc.iep.value) if ltpc is not None and ltpc.HasField("iep") else None
            )
            reference_price = None
            indicative_equilibrium_quantity = None
            indicative_interest_quantity_total = None
            indicative_interest_quantity_market = None
            cas_eligible = False
            if market_ff is not None:
                if union == "firstLevelWithGreeks":
                    first = market_ff.firstDepth
                    depth = ({
                        "bid_quantity": int(first.bidQ), "bid_price": float(first.bidP),
                        "ask_quantity": int(first.askQ), "ask_price": float(first.askP),
                    },) if market_ff.HasField("firstDepth") else None
                if union == "fullFeed" and full_union == "marketFF":
                    depth = tuple({
                        "bid_quantity": int(q.bidQ), "bid_price": float(q.bidP),
                        "ask_quantity": int(q.askQ), "ask_price": float(q.askP),
                    } for q in market_ff.marketLevel.bidAskQuote) if market_ff.HasField("marketLevel") else None
                    greeks_source = market_ff.optionGreeks if market_ff.HasField("optionGreeks") else None
                    # The provider's proto3 scalar fields have no presence bits.
                    # Treat their default zero as unavailable rather than inventing
                    # a confirmed zero when the wire payload omitted the field.
                    open_interest = float(market_ff.oi) if market_ff.oi != 0 else None
                    volume = int(market_ff.vtt) if market_ff.vtt != 0 else None
                    average_price = float(market_ff.atp) if market_ff.atp != 0 else None
                    total_buy = float(market_ff.tbq) if market_ff.tbq != 0 else None
                    total_sell = float(market_ff.tsq) if market_ff.tsq != 0 else None
                    ohlc = tuple({
                        "interval": item.interval, "open": float(item.open),
                        "high": float(item.high), "low": float(item.low),
                        "close": float(item.close), "volume": int(item.vol),
                        "timestamp_ms": int(item.ts),
                    } for item in market_ff.marketOHLC.ohlc) if market_ff.HasField("marketOHLC") else None
                    # These fields are part of Upstox's official V3 schema (CAS
                    # market-data additions). Proto3 scalar zero is treated as
                    # unavailable for numeric fields, consistent with the other
                    # optional quote fields in this decoder.
                    if market_ff.iep != 0:
                        indicative_equilibrium_price = float(market_ff.iep)
                    reference_price = float(market_ff.rp) if market_ff.rp != 0 else None
                    indicative_equilibrium_quantity = int(market_ff.ieq) if market_ff.ieq != 0 else None
                    indicative_interest_quantity_total = int(market_ff.iiqTotal) if market_ff.iiqTotal != 0 else None
                    indicative_interest_quantity_market = int(market_ff.iiqM) if market_ff.iiqM != 0 else None
                    cas_eligible = bool(market_ff.casEligible)
                else:
                    greeks_source = market_ff.optionGreeks if market_ff.HasField("optionGreeks") else None
                    open_interest = float(market_ff.oi) if market_ff.oi != 0 else None
                    volume = int(market_ff.vtt) if market_ff.vtt != 0 else None
                if greeks_source is not None:
                    greeks = {
                        "delta": float(greeks_source.delta), "theta": float(greeks_source.theta),
                        "gamma": float(greeks_source.gamma), "vega": float(greeks_source.vega),
                        "rho": float(greeks_source.rho),
                    }
                    implied_volatility = float(market_ff.iv) if market_ff.iv != 0 else None
                    if implied_volatility is not None:
                        greeks["iv"] = implied_volatility
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
                indicative_equilibrium_price=indicative_equilibrium_price,
                reference_price=reference_price,
                indicative_equilibrium_quantity=indicative_equilibrium_quantity,
                indicative_interest_quantity_total=indicative_interest_quantity_total,
                indicative_interest_quantity_market=indicative_interest_quantity_market,
                cas_eligible=cas_eligible,
            )
            self._ticks[key] = tick
            if self.on_tick is not None:
                result = self.on_tick(tick)
                if asyncio.iscoroutine(result):
                    await result
