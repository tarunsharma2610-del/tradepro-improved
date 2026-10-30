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
    token_calls = 0
    authorized_tokens = []
    sent_requests = []

    async def token_provider():
        nonlocal token_calls
        token_calls += 1
        return f"test-access-token-{token_calls}"

    async def authorized_url(token):
        authorized_tokens.append(token)
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
    assert token_calls == 2
    assert authorized_tokens == ["test-access-token-1", "test-access-token-2"]
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



@pytest.mark.asyncio
async def test_option_greeks_mode_decodes_first_level_depth_and_iv():
    streamer = UpstoxMarketDataStreamer(
        _no_token, ["NSE_FO|12345"], mode="option_greeks"
    )
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    response = market_data_pb.FeedResponse()
    response.currentTs = now_ms
    feed = response.feeds["NSE_FO|12345"].firstLevelWithGreeks
    feed.ltpc.ltp = 101.25
    feed.ltpc.ltt = now_ms
    feed.firstDepth.bidQ = 100
    feed.firstDepth.bidP = 101.2
    feed.firstDepth.askQ = 125
    feed.firstDepth.askP = 101.3
    feed.optionGreeks.delta = 0.52
    feed.optionGreeks.theta = -4.2
    feed.optionGreeks.gamma = 0.001
    feed.optionGreeks.vega = 8.1
    feed.optionGreeks.rho = 1.2
    feed.iv = 0.18
    feed.oi = 25000
    feed.vtt = 4000

    await streamer._consume(response.SerializeToString())

    tick = streamer.latest_tick("NSE_FO|12345")
    assert tick is not None
    assert tick.depth == ({
        "bid_quantity": 100, "bid_price": 101.2,
        "ask_quantity": 125, "ask_price": 101.3,
    },)
    assert tick.option_greeks["delta"] == pytest.approx(0.52)
    assert tick.option_greeks["iv"] == pytest.approx(0.18)
    assert tick.open_interest == 25000
    assert tick.volume_traded_today == 4000



@pytest.mark.asyncio
async def test_subscription_lifecycle_sends_binary_v3_sub_unsub_and_change_mode_requests():
    import json

    streamer = UpstoxMarketDataStreamer(
        _no_token, ["NSE_EQ|ONE"], mode="ltpc"
    )
    sent = []

    class FakeSocket:
        async def send(self, payload):
            assert isinstance(payload, bytes)
            sent.append(json.loads(payload.decode("utf-8")))

    streamer._socket = FakeSocket()
    streamer._connected = True

    assert await streamer.subscribe(["NSE_EQ|TWO"]) == "sent"
    assert streamer.instrument_keys == ["NSE_EQ|ONE", "NSE_EQ|TWO"]
    assert sent[-1]["method"] == "sub"
    assert sent[-1]["data"] == {
        "instrumentKeys": ["NSE_EQ|TWO"], "mode": "ltpc"
    }

    assert await streamer.unsubscribe(["NSE_EQ|ONE"]) == "sent"
    assert streamer.instrument_keys == ["NSE_EQ|TWO"]
    assert sent[-1]["method"] == "unsub"
    assert sent[-1]["data"] == {"instrumentKeys": ["NSE_EQ|ONE"]}

    streamer._ticks["NSE_EQ|TWO"] = MarketTick(
        instrument_key="NSE_EQ|TWO", ltp=100, exchange_timestamp_ms=1,
        received_at=datetime.now(timezone.utc), received_monotonic=time.monotonic(),
    )
    assert await streamer.change_mode(["NSE_EQ|TWO"], "full") == "sent"
    assert streamer.mode == "full"
    assert "NSE_EQ|TWO" not in streamer._ticks
    assert sent[-1]["method"] == "change_mode"
    assert sent[-1]["data"] == {
        "instrumentKeys": ["NSE_EQ|TWO"], "mode": "full"
    }


@pytest.mark.asyncio
async def test_subscription_changes_while_disconnected_are_replayed_on_reconnect():
    import json

    streamer = UpstoxMarketDataStreamer(_no_token, ["NSE_EQ|ONE"], mode="ltpc")
    assert await streamer.subscribe(["NSE_EQ|TWO"]) == "queued_for_reconnect"
    assert await streamer.change_mode(["NSE_EQ|ONE", "NSE_EQ|TWO"], "full") == "queued_for_reconnect"
    assert streamer.instrument_keys == ["NSE_EQ|ONE", "NSE_EQ|TWO"]
    assert streamer.mode == "full"

    sent = []

    class FakeSocket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def send(self, payload):
            sent.append(json.loads(payload.decode("utf-8")))

        async def recv(self):
            streamer._stop.set()
            raise asyncio.TimeoutError()

    async def token_provider():
        return "test-access-token"

    async def authorized_url(_token):
        return "wss://feed.upstox.com/test"

    streamer.token_provider = token_provider
    streamer._authorized_url = authorized_url
    streamer._stop.clear()
    import app.services.upstox_market_data_streamer as streamer_module
    original_connect = streamer_module.websockets.connect
    streamer_module.websockets.connect = lambda *_args, **_kwargs: FakeSocket()
    try:
        await streamer._run()
    finally:
        streamer_module.websockets.connect = original_connect

    assert sent[0]["method"] == "sub"
    assert sent[0]["data"]["mode"] == "full"
    assert sent[0]["data"]["instrumentKeys"] == ["NSE_EQ|ONE", "NSE_EQ|TWO"]


@pytest.mark.asyncio
async def test_subscription_lifecycle_enforces_limits_and_keeps_one_key():
    streamer = UpstoxMarketDataStreamer(_no_token, ["NSE_EQ|ONE"], mode="full")
    with pytest.raises(ValueError, match="final instruments"):
        await streamer.unsubscribe(["NSE_EQ|ONE"])
    with pytest.raises(ValueError, match="2000"):
        await streamer.subscribe([f"NSE_EQ|{index}" for index in range(2000)])
    await streamer.subscribe(["NSE_EQ|TWO"])
    assert await streamer.change_mode(["NSE_EQ|ONE"], "ltpc") == "queued_for_reconnect"


@pytest.mark.asyncio
async def test_official_v3_cas_fields_are_preserved_in_full_market_feed():
    streamer = _streamer()
    key = "NSE_EQ|INE002A01018"
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    response = market_data_pb.FeedResponse()
    response.currentTs = now_ms
    market = response.feeds[key].fullFeed.marketFF
    market.ltpc.ltp = 123.45
    market.ltpc.ltt = now_ms
    market.iep = 123.6
    market.rp = 123.4
    market.ieq = 1500
    market.iiqTotal = 2400
    market.iiqM = 900
    market.casEligible = True

    await streamer._consume(response.SerializeToString())

    tick = streamer.latest_tick(key)
    assert tick is not None
    assert tick.indicative_equilibrium_price == pytest.approx(123.6)
    assert tick.reference_price == pytest.approx(123.4)
    assert tick.indicative_equilibrium_quantity == 1500
    assert tick.indicative_interest_quantity_total == 2400
    assert tick.indicative_interest_quantity_market == 900
    assert tick.cas_eligible is True


@pytest.mark.asyncio
async def test_absent_cas_numeric_fields_remain_unavailable():
    streamer = _streamer()
    key = "NSE_EQ|INE002A01018"
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    response = market_data_pb.FeedResponse()
    response.currentTs = now_ms
    market = response.feeds[key].fullFeed.marketFF
    market.ltpc.ltp = 123.45
    market.ltpc.ltt = now_ms

    await streamer._consume(response.SerializeToString())

    tick = streamer.latest_tick(key)
    assert tick is not None
    assert tick.indicative_equilibrium_price is None
    assert tick.reference_price is None
    assert tick.indicative_equilibrium_quantity is None
    assert tick.indicative_interest_quantity_total is None
    assert tick.indicative_interest_quantity_market is None
    assert tick.cas_eligible is False


@pytest.mark.asyncio
async def test_ltpc_iep_is_preserved_during_preopen_or_closing_auction():
    streamer = _streamer()
    key = "NSE_EQ|INE002A01018"
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    response = market_data_pb.FeedResponse()
    response.currentTs = now_ms
    ltpc = response.feeds[key].ltpc
    ltpc.ltp = 123.45
    ltpc.ltt = now_ms
    ltpc.iep.value = 123.6

    await streamer._consume(response.SerializeToString())

    tick = streamer.latest_tick(key)
    assert tick is not None
    assert tick.indicative_equilibrium_price == pytest.approx(123.6)


@pytest.mark.asyncio
async def test_market_info_message_exposes_segment_cas_and_preopen_status():
    streamer = _streamer()
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    response = market_data_pb.FeedResponse()
    response.type = market_data_pb.market_info
    response.currentTs = now_ms
    response.marketInfo.segmentStatus["NSE_EQ"] = market_data_pb.NORMAL_OPEN
    cas = response.marketInfo.casMarketStatus["NSE_EQ"]
    cas.status = "CAS_LM_START"
    cas.updatedTime = now_ms
    preopen = response.marketInfo.preOpenSessionStatus["NSE_EQ"]
    preopen.status = "PRE_OPEN_START"
    preopen.updatedTime = now_ms

    await streamer._consume(response.SerializeToString())

    assert streamer.market_info == {
        "current_timestamp_ms": now_ms,
        "segment_status": {"NSE_EQ": "NORMAL_OPEN"},
        "cas_market_status": {"NSE_EQ": {"status": "CAS_LM_START", "updated_time_ms": now_ms}},
        "pre_open_session_status": {"NSE_EQ": {"status": "PRE_OPEN_START", "updated_time_ms": now_ms}},
    }

@pytest.mark.asyncio
async def test_mixed_mode_subscriptions_are_tracked_independently_and_unsubscribed_safely():
    import json

    streamer = UpstoxMarketDataStreamer(_no_token, ["NSE_EQ|ONE"], mode="ltpc")
    sent = []

    class FakeSocket:
        async def send(self, payload):
            sent.append(json.loads(payload.decode("utf-8")))

    streamer._socket = FakeSocket()
    streamer._connected = True

    assert await streamer.subscribe(["NSE_FO|TWO"], "option_greeks") == "sent"
    assert streamer.subscriptions_by_mode == {
        "ltpc": ["NSE_EQ|ONE"],
        "option_greeks": ["NSE_FO|TWO"],
    }
    assert sent[-1]["data"] == {
        "instrumentKeys": ["NSE_FO|TWO"], "mode": "option_greeks"
    }

    assert await streamer.change_mode(["NSE_EQ|ONE"], "full") == "sent"
    assert streamer.subscriptions_by_mode == {
        "option_greeks": ["NSE_FO|TWO"],
        "full": ["NSE_EQ|ONE"],
    }
    assert sent[-1]["method"] == "change_mode"
    assert sent[-1]["data"] == {
        "instrumentKeys": ["NSE_EQ|ONE"], "mode": "full"
    }

    assert await streamer.unsubscribe(["NSE_FO|TWO"]) == "sent"
    assert streamer.subscriptions_by_mode == {"full": ["NSE_EQ|ONE"]}


@pytest.mark.asyncio
async def test_mixed_mode_reconnect_replays_each_mode_as_a_separate_binary_request():
    import json

    streamer = UpstoxMarketDataStreamer(_no_token, ["NSE_EQ|ONE"], mode="ltpc")
    await streamer.subscribe(["NSE_FO|TWO"], "option_greeks")
    await streamer.change_mode(["NSE_EQ|ONE"], "full")
    sent = []

    class FakeSocket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def send(self, payload):
            sent.append(json.loads(payload.decode("utf-8")))

        async def recv(self):
            streamer._stop.set()
            raise asyncio.TimeoutError()

    async def token_provider():
        return "test-access-token"

    async def authorized_url(_token):
        return "wss://feed.upstox.com/test"

    streamer.token_provider = token_provider
    streamer._authorized_url = authorized_url
    streamer._stop.clear()
    import app.services.upstox_market_data_streamer as streamer_module
    original_connect = streamer_module.websockets.connect
    streamer_module.websockets.connect = lambda *_args, **_kwargs: FakeSocket()
    try:
        await streamer._run()
    finally:
        streamer_module.websockets.connect = original_connect

    assert {(request["data"]["mode"], tuple(request["data"]["instrumentKeys"]))
            for request in sent} == {
        ("option_greeks", ("NSE_FO|TWO",)),
        ("full", ("NSE_EQ|ONE",)),
    }
    assert all(request["method"] == "sub" for request in sent)


@pytest.mark.asyncio
async def test_same_instrument_cannot_be_subscribed_in_two_modes_without_change_mode():
    streamer = UpstoxMarketDataStreamer(_no_token, ["NSE_EQ|ONE"], mode="ltpc")
    with pytest.raises(ValueError, match="already subscribed in another mode"):
        await streamer.subscribe(["NSE_EQ|ONE"], "full")

@pytest.mark.asyncio
async def test_combined_feed_mode_limits_are_applied_to_resulting_subscription_sets():
    streamer = UpstoxMarketDataStreamer(
        _no_token, [f"NSE_EQ|{index}" for index in range(1501)], mode="full"
    )
    with pytest.raises(ValueError, match="full mode supports at most 1500"):
        await streamer.subscribe(["NSE_INDEX|NIFTY50"], "ltpc")

    single_mode = UpstoxMarketDataStreamer(
        _no_token, [f"NSE_EQ|{index}" for index in range(2000)], mode="ltpc"
    )
    assert await single_mode.change_mode(single_mode.instrument_keys, "full") == "queued_for_reconnect"
    assert single_mode.subscriptions_by_mode == {
        "full": sorted([f"NSE_EQ|{index}" for index in range(2000)])
    }
