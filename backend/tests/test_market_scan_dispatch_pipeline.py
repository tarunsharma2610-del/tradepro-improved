import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.services.market_quote_dispatcher import MarketQuoteDispatcher
from app.services.market_scan_dispatch_pipeline import MarketScanDispatchPipeline
from app.services.market_scanner import MarketScanner


def quote(user_id, *, instrument="NSE_EQ|INE002A01018", version=1, ltp=110.0):
    now = datetime.now(timezone.utc)
    return {
        "schema_version": 1,
        "user_id": str(user_id),
        "instrument_key": instrument,
        "epoch": "epoch-1",
        "version": version,
        "ltp": ltp,
        "exchange_timestamp_ms": int(now.timestamp() * 1000),
        "received_at": now.isoformat(),
        "ohlc": [{"interval": "1d", "close": 100.0}],
        "volume_traded_today": 1000,
    }


@pytest.mark.asyncio
async def test_pipeline_validates_scans_and_dispatches_observation():
    user_id = uuid4()
    dispatcher = MarketQuoteDispatcher(max_pending_keys=4)
    pipeline = MarketScanDispatchPipeline(
        scanner=MarketScanner(), dispatcher=dispatcher
    )

    assert pipeline.on_quote(user_id, quote(user_id)) is True
    item = await dispatcher.get()
    assert item.user_id == str(user_id)
    assert item.instrument_key == "NSE_EQ|INE002A01018"
    assert item.version == 1
    assert item.observation.price_change_pct == 10.0
    dispatcher.task_done()

    assert pipeline.accepted_observations == 1
    assert pipeline.rejected_quotes == 0
    assert pipeline.rejected_dispatches == 0


def test_pipeline_rejects_cross_user_invalid_and_duplicate_quotes():
    user_id = uuid4()
    pipeline = MarketScanDispatchPipeline()

    assert not pipeline.on_quote(user_id, quote(uuid4()))
    assert not pipeline.on_quote(user_id, quote(user_id, ltp=0))
    assert pipeline.on_quote(user_id, quote(user_id, version=1))
    assert not pipeline.on_quote(user_id, quote(user_id, version=1))

    assert pipeline.accepted_observations == 1
    assert pipeline.rejected_quotes == 3
    assert pipeline.dispatcher.pending_keys == 1


def test_pipeline_keeps_user_and_instrument_keys_isolated():
    user_a, user_b = uuid4(), uuid4()
    pipeline = MarketScanDispatchPipeline()

    assert pipeline.on_quote(user_a, quote(user_a))
    assert pipeline.on_quote(user_b, quote(user_b))
    assert pipeline.dispatcher.pending_keys == 2


def test_pipeline_reports_bounded_dispatch_overflow():
    user_id = uuid4()
    dispatcher = MarketQuoteDispatcher(max_pending_keys=1)
    pipeline = MarketScanDispatchPipeline(dispatcher=dispatcher)

    assert pipeline.on_quote(user_id, quote(user_id))
    assert not pipeline.on_quote(
        user_id, quote(user_id, instrument="NSE_EQ|INE009A01021")
    )

    assert pipeline.accepted_observations == 1
    assert pipeline.rejected_dispatches == 1
    assert dispatcher.dropped_unique_keys == 1
