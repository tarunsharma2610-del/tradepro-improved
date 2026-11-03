import pytest

from app.brokers.upstox.adapter import UpstoxAdapter


@pytest.mark.asyncio
async def test_funds_v3_uses_documented_endpoint_and_version_header(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {"status": "success", "data": {"available_to_trade": {}, "unavailable_to_trade": {}}}

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
    result = await UpstoxAdapter().get_funds_and_margin("oauth-access-token")

    assert result.ok is True
    assert captured["url"] == "https://api.upstox.com/v3/user/get-funds-and-margin"
    assert captured["headers"]["Authorization"] == "Bearer oauth-access-token"
    assert captured["headers"]["Api-Version"] == "3.0"
    assert captured["params"] is None


@pytest.mark.asyncio
async def test_funds_v3_provider_error_is_not_replaced_with_simulated_data(monkeypatch):
    class FakeResponse:
        status_code = 423
        text = "funds service maintenance"

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
    result = await UpstoxAdapter().get_funds_and_margin("oauth-access-token")
    assert result.ok is False
    assert "423" in result.error
    assert result.data is None
