import pytest

from app.brokers.base import BrokerCallResult
from app.brokers.upstox.adapter import API_HFT_V2, UpstoxAdapter


@pytest.mark.asyncio
async def test_place_order_uses_current_upstox_hft_host_without_network(monkeypatch):
    """Verify the documented endpoint route without submitting a real order."""
    adapter = UpstoxAdapter()
    captured = {}

    async def fake_post(url, access_token, json_body):
        captured["url"] = url
        captured["access_token"] = access_token
        captured["json_body"] = json_body
        return BrokerCallResult(ok=True, data={"data": {"order_id": "sandbox-test-id"}})

    monkeypatch.setattr(adapter, "_post", fake_post)
    payload = {
        "quantity": 1,
        "product": "D",
        "validity": "DAY",
        "price": 0,
        "instrument_token": "NSE_EQ|INE669E01016",
        "order_type": "MARKET",
        "transaction_type": "BUY",
        "disclosed_quantity": 0,
        "trigger_price": 0,
    }

    result = await adapter.place_order("test-token", payload)

    assert result.ok
    assert captured["url"] == f"{API_HFT_V2}/order/place"
    assert captured["access_token"] == "test-token"
    assert captured["json_body"] == payload
    assert captured["url"] == "https://api-hft.upstox.com/v2/order/place"
