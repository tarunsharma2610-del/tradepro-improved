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
    sent_requests = []

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

        async def send(self, payload):
            sent_requests.append(payload)

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
    assert sent_requests
    import json
    request = json.loads(sent_requests[0])
    assert request["method"] == "sub"
    assert request["data"]["mode"] == "full"
    assert request["data"]["instrumentKeys"] == ["NSE_EQ|INE002A01018"]


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


@pytest.mark.asyncio
async def test_authorization_accepts_official_upstox_v3_url_and_headers(monkeypatch):
    streamer = _streamer()
    authorized_url = (
        "wss://xyz.upstox.com/market-data-feeder/v3/"
        "upstox-developer-api/feeds?requestId=test-request&code=single-use-test"
    )
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "success", "data": {"authorized_redirect_uri": authorized_url}}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers):
            captured["url"] = url
            captured["headers"] = headers
            return FakeResponse()

    monkeypatch.setattr("app.services.upstox_market_data_streamer.httpx.AsyncClient", FakeClient)

    result = await streamer._authorized_url("test-access-token")

    assert result == authorized_url
    assert captured["url"] == "https://api.upstox.com/v3/feed/market-data-feed/authorize"
    assert captured["headers"]["Authorization"] == "Bearer test-access-token"
    assert captured["headers"]["Accept"] == "application/json"



@pytest.mark.asyncio
@pytest.mark.parametrize("ltp,ltt", [(float("nan"), 0), (float("inf"), 0), (123.45, 0)])
async def test_nonfinite_price_or_missing_exchange_trade_time_is_not_cached(ltp, ltt):
    streamer = _streamer()
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    response = market_data_pb.FeedResponse()
    response.currentTs = now_ms
    response.feeds["NSE_EQ|INE002A01018"].ltpc.ltp = ltp
    response.feeds["NSE_EQ|INE002A01018"].ltpc.ltt = ltt

    await streamer._consume(response.SerializeToString())

    assert streamer.latest_tick("NSE_EQ|INE002A01018") is None


def test_tick_with_missing_exchange_timestamp_is_rejected_even_if_just_received():
    streamer = _streamer()
    streamer._ticks["NSE_EQ|INE002A01018"] = MarketTick(
        instrument_key="NSE_EQ|INE002A01018",
        ltp=100,
        exchange_timestamp_ms=0,
        received_at=datetime.now(timezone.utc),
        received_monotonic=time.monotonic(),
    )
    assert streamer.latest_tick("NSE_EQ|INE002A01018") is None


@pytest.mark.asyncio
async def test_full_v3_feed_decodes_depth_greeks_oi_volume_and_ohlc():
    streamer = _streamer()
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    response = market_data_pb.FeedResponse()
    response.currentTs = now_ms
    market_ff = response.feeds["NSE_EQ|INE002A01018"].fullFeed.marketFF
    market_ff.ltpc.ltp = 123.45
    market_ff.ltpc.ltt = now_ms
    quote = market_ff.marketLevel.bidAskQuote.add()
    quote.bidQ = 10
    quote.bidP = 123.4
    quote.askQ = 12
    quote.askP = 123.5
    market_ff.optionGreeks.delta = 0.51
    market_ff.optionGreeks.theta = -2.1
    market_ff.optionGreeks.gamma = 0.02
    market_ff.optionGreeks.vega = 1.5
    market_ff.optionGreeks.rho = 0.1
    market_ff.oi = 15000
    market_ff.vtt = 25000
    market_ff.atp = 123.2
    market_ff.tbq = 500
    market_ff.tsq = 450
    candle = market_ff.marketOHLC.ohlc.add()
    candle.interval = "1d"
    candle.open = 120
    candle.high = 125
    candle.low = 119
    candle.close = 123.45
    candle.vol = 25000
    candle.ts = now_ms

    await streamer._consume(response.SerializeToString())

    tick = streamer.latest_tick("NSE_EQ|INE002A01018")
    assert tick is not None
    assert tick.depth == ({
        "bid_quantity": 10, "bid_price": 123.4,
        "ask_quantity": 12, "ask_price": 123.5,
    },)
    assert tick.option_greeks == {
        "delta": 0.51, "theta": -2.1, "gamma": 0.02, "vega": 1.5, "rho": 0.1,
    }
    assert tick.open_interest == 15000
    assert tick.volume_traded_today == 25000
    assert tick.average_traded_price == pytest.approx(123.2)
    assert tick.total_buy_quantity == 500
    assert tick.total_sell_quantity == 450
    assert tick.ohlc[0]["interval"] == "1d"
    assert tick.ohlc[0]["volume"] == 25000


def test_full_feed_is_default_and_subscription_limits_are_mode_specific():
    streamer = _streamer()
    assert streamer.mode == "full"
    with pytest.raises(ValueError, match="full_d30"):
        UpstoxMarketDataStreamer(_no_token, ["NSE_EQ|INE002A01018"], mode="full_d30")
    with pytest.raises(ValueError, match="2000"):
        UpstoxMarketDataStreamer(
            _no_token,
            [f"NSE_EQ|{index}" for index in range(2001)],
            mode="full",
        )


@pytest.mark.asyncio
async def test_full_feed_does_not_fabricate_missing_optional_fields_as_zero():
    streamer = _streamer()
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    response = market_data_pb.FeedResponse()
    response.currentTs = now_ms
    market_ff = response.feeds["NSE_EQ|INE002A01018"].fullFeed.marketFF
    market_ff.ltpc.ltp = 123.45
    market_ff.ltpc.ltt = now_ms

    await streamer._consume(response.SerializeToString())

    tick = streamer.latest_tick("NSE_EQ|INE002A01018")
    assert tick is not None
    assert tick.depth is None
    assert tick.option_greeks is None
    assert tick.open_interest is None
    assert tick.volume_traded_today is None
    assert tick.average_traded_price is None
    assert tick.ohlc is None
