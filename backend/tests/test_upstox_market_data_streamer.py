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
