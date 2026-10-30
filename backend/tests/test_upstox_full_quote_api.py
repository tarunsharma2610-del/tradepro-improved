import pytest

from app.brokers.upstox.adapter import UpstoxAdapter


@pytest.mark.asyncio
async def test_full_quote_uses_documented_upstox_v3_endpoint(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {
                "status": "success",
                "data": {
                    "NSE_EQ:TEST": {
                        "instrument_token": "NSE_EQ|INE002A01018",
                        "last_price": 123.45,
                        "last_trade_time": "1793330400000",
                    }
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

    result = await UpstoxAdapter().get_full_quote(
        "test-token", ["NSE_EQ|INE002A01018"]
    )

    assert result.ok is True
    assert result.data["status"] == "success"
    assert "/v3/market-quote/quotes" in captured["url"]
    assert captured["headers"]["Authorization"] == "Bearer test-token"
    assert captured["params"] == {"instrument_key": "NSE_EQ|INE002A01018"}
