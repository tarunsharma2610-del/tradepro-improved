from unittest.mock import AsyncMock

import pytest

from app.brokers.upstox.adapter import UpstoxAdapter


@pytest.mark.asyncio
async def test_intraday_candle_call_uses_documented_v3_endpoint_and_bearer_auth(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {
                "status": "success",
                "data": {
                    "candles": [
                        ["2026-10-30T10:00:00+05:30", 100, 102, 99, 101, 500, 0]
                    ]
                },
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers, params=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["params"] = params
            return FakeResponse()

    monkeypatch.setattr("app.brokers.upstox.adapter.httpx.AsyncClient", FakeClient)

    result = await UpstoxAdapter().get_intraday_data(
        "test-token", "NSE_EQ|INE002A01018", "minutes", "5"
    )

    assert result.ok is True
    assert result.data["status"] == "success"
    assert "/v3/historical-candle/intraday/NSE_EQ%7CINE002A01018/minutes/5" in captured["url"]
    assert captured["headers"]["Authorization"] == "Bearer test-token"
    assert captured["headers"]["Accept"] == "application/json"
    assert captured["params"] is None
