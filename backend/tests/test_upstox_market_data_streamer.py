import asyncio
import time
from datetime import datetime, timezone

import pytest

from app.brokers.upstox.proto import MarketDataFeedV3_pb2 as market_data_pb
from app.services.upstox_market_data_streamer import MarketTick, UpstoxMarketDataStreamer


async def _no_token():
    return None


def _streamer():
    return UpstoxMarketDataStreamer(
        _no_token,
        ["NSE_EQ|INE002A01018"],
        stale_after_seconds=15,
        silence_timeout_seconds=60,
    )


@pytest.mark.asyncio
async def test_protobuf_ltpc_message_is_cached_as_fresh_quote():
    received = []
    streamer = UpstoxMarketDataStreamer(_no_token, ["NSE_EQ|INE002A01018"], received.append)
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    response = market_data_pb.FeedResponse()
    response.currentTs = now_ms
    response.feeds["NSE_EQ|INE002A01018"].ltpc.ltp = 123.45
    response.feeds["NSE_EQ|INE002A01018"].ltpc.ltt = now_ms

    await streamer._consume(response.SerializeToString())

    tick = streamer.latest_tick("NSE_EQ|INE002A01018")
    assert tick is not None
    assert tick.ltp == pytest.approx(123.45)
    assert tick.exchange_timestamp_ms == now_ms
    assert received == [tick]


@pytest.mark.asyncio
async def test_old_exchange_timestamp_is_rejected_as_stale():
    streamer = _streamer()
    old_ms = int(datetime.now(timezone.utc).timestamp() * 1000) - 60_000
    response = market_data_pb.FeedResponse()
    response.currentTs = old_ms
    response.feeds["NSE_EQ|INE002A01018"].ltpc.ltp = 100
    response.feeds["NSE_EQ|INE002A01018"].ltpc.ltt = old_ms

    await streamer._consume(response.SerializeToString())

    assert streamer.latest_tick("NSE_EQ|INE002A01018") is None


@pytest.mark.asyncio
async def test_unrequested_instrument_keys_are_ignored():
    streamer = _streamer()
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    response = market_data_pb.FeedResponse()
    response.currentTs = now_ms
    response.feeds["NSE_EQ|NOT_SUBSCRIBED"].ltpc.ltp = 999
    response.feeds["NSE_EQ|NOT_SUBSCRIBED"].ltpc.ltt = now_ms

    await streamer._consume(response.SerializeToString())

    assert streamer.latest_tick("NSE_EQ|NOT_SUBSCRIBED") is None


def test_missing_or_received_stale_tick_fails_closed():
    streamer = _streamer()
    assert streamer.latest_tick("NSE_EQ|INE002A01018") is None
    streamer._ticks["NSE_EQ|INE002A01018"] = MarketTick(
        instrument_key="NSE_EQ|INE002A01018",
        ltp=100,
        exchange_timestamp_ms=0,
        received_at=datetime.now(timezone.utc),
        received_monotonic=time.monotonic() - 30,
    )
    assert streamer.latest_tick("NSE_EQ|INE002A01018") is None


def test_stream_rejects_invalid_keys_and_unsafe_staleness_configuration():
    with pytest.raises(ValueError, match="segment-prefixed"):
        UpstoxMarketDataStreamer(_no_token, ["NOT_A_KEY"])
    with pytest.raises(ValueError, match="Silence timeout"):
        UpstoxMarketDataStreamer(_no_token, ["NSE_EQ|ABC"], stale_after_seconds=20, silence_timeout_seconds=10)


@pytest.mark.asyncio
async def test_stream_reconnects_after_silence_timeout(monkeypatch):
    streamer = _streamer()
    connects = 0

    async def token_provider():
        return "test-access-token"

    async def authorized_url(_token):
        return "wss://feed.upstox.com/test"

    streamer.token_provider = token_provider
    streamer._authorized_url = authorized_url

    class FakeSocket:
        async def __aenter__(self):
            if connects >= 2:
                streamer._stop.set()
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def send(self, _payload):
            return None

        async def recv(self):
            raise asyncio.TimeoutError()

    def fake_connect(*_args, **_kwargs):
        nonlocal connects
        connects += 1
        return FakeSocket()

    async def no_wait(_seconds):
        return None

    monkeypatch.setattr("app.services.upstox_market_data_streamer.websockets.connect", fake_connect)
    monkeypatch.setattr(streamer, "_sleep_or_stop", no_wait)

    await streamer._run()

    assert connects == 2
    assert streamer.connected is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "authorized_url",
    [
        "http://feed.upstox.com/unsafe",
        "wss://evil.example/unsafe",
        "wss://upstox.com.evil.example/unsafe",
    ],
)
async def test_authorization_rejects_non_tls_or_non_upstox_hosts(monkeypatch, authorized_url):
    streamer = _streamer()

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"data": {"authorized_redirect_uri": authorized_url}}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("app.services.upstox_market_data_streamer.httpx.AsyncClient", FakeClient)

    with pytest.raises(ValueError, match="invalid WebSocket authorization URL"):
        await streamer._authorized_url("test-access-token")
