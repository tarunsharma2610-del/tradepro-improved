import pytest

from app.brokers.upstox.adapter import UpstoxAdapter


@pytest.mark.asyncio
async def test_option_chain_uses_documented_endpoint_and_query_parameters(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {"status": "success", "data": [{"strike_price": 25000}]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers, params=None):
            captured.update(url=url, headers=headers, params=params)
            return FakeResponse()

    monkeypatch.setattr("app.brokers.upstox.adapter.httpx.AsyncClient", FakeClient)
    result = await UpstoxAdapter().get_option_chain(
        "analytics-token", "NSE_INDEX|Nifty 50", "current_week"
    )

    assert result.ok is True
    assert result.data["data"][0]["strike_price"] == 25000
    assert captured["url"] == "https://api.upstox.com/v2/option/chain"
    assert captured["headers"]["Authorization"] == "Bearer analytics-token"
    assert captured["params"] == {
        "instrument_key": "NSE_INDEX|Nifty 50",
        "expiry_date": "current_week",
    }


@pytest.mark.asyncio
async def test_option_chain_propagates_provider_errors_without_fabricating_data(monkeypatch):
    class FakeResponse:
        status_code = 401
        text = "invalid token"

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("app.brokers.upstox.adapter.httpx.AsyncClient", FakeClient)
    result = await UpstoxAdapter().get_option_chain(
        "analytics-token", "NSE_INDEX|Nifty 50", "current_week"
    )
    assert result.ok is False
    assert "401" in result.error
    assert result.data is None
