from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import pytest

from app.brokers.base import BrokerCallResult
from app.services.strategy_execution_service import StrategyExecutionService

IST = ZoneInfo("Asia/Kolkata")


def _response(candles):
    return BrokerCallResult(
        ok=True,
        data={"status": "success", "data": {"candles": candles}},
    )


@pytest.mark.asyncio
async def test_strategy_fetch_combines_historical_and_current_session_candles():
    now = datetime.now(IST).replace(second=0, microsecond=0)
    historical_time = (now - timedelta(days=1)).replace(hour=15, minute=20)
    current_time = now.replace(hour=10, minute=0)
    historical = _response([
        [historical_time.isoformat(), 100, 102, 99, 101, 1000, 0],
    ])
    intraday = _response([
        [current_time.isoformat(), 101, 104, 100, 103, 500, 0],
    ])
    adapter = type(
        "FakeAdapter",
        (),
        {
            "get_historical_data": AsyncMock(return_value=historical),
            "get_intraday_data": AsyncMock(return_value=intraday),
        },
    )()
    service = object.__new__(StrategyExecutionService)

    with patch("app.services.strategy_execution_service.get_broker_adapter", return_value=adapter):
        candles = await service._fetch_candles("token", "NSE_EQ|INE002A01018")

    assert candles is not None
    assert len(candles) == 2
    assert candles[0].timestamp == historical_time
    assert candles[1].timestamp == current_time
    adapter.get_historical_data.assert_awaited_once()
    adapter.get_intraday_data.assert_awaited_once_with("token", "NSE_EQ|INE002A01018", "minutes", "5")


@pytest.mark.asyncio
async def test_strategy_fetch_fails_closed_if_either_provider_candle_source_fails():
    historical = _response([
        ["2026-10-29T15:20:00+05:30", 100, 102, 99, 101, 1000, 0],
    ])
    adapter = type(
        "FakeAdapter",
        (),
        {
            "get_historical_data": AsyncMock(return_value=historical),
            "get_intraday_data": AsyncMock(
                return_value=BrokerCallResult(ok=False, error="provider unavailable")
            ),
        },
    )()
    service = object.__new__(StrategyExecutionService)

    with patch("app.services.strategy_execution_service.get_broker_adapter", return_value=adapter):
        candles = await service._fetch_candles("token", "NSE_EQ|INE002A01018")

    assert candles is None
