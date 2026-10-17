from unittest.mock import AsyncMock

import pytest

from app.brokers.base import BrokerCallResult
from app.brokers.upstox.adapter import API_HFT_V3, UpstoxAdapter


@pytest.mark.asyncio
async def test_place_order_uses_current_upstox_hft_host_without_network(monkeypatch):
    """Verify the documented endpoint route without submitting a real order."""
    adapter = UpstoxAdapter()
    captured = {}

    async def fake_post(url, access_token, json_body):
        captured["url"] = url
        captured["access_token"] = access_token
        captured["json_body"] = json_body
        return BrokerCallResult(ok=True, data={"status": "success", "data": {"order_ids": ["sandbox-test-id"]}})

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
    assert captured["url"] == f"{API_HFT_V3}/order/place"
    assert captured["access_token"] == "test-token"
    assert captured["json_body"] == payload
    assert result.data["data"]["order_ids"] == ["sandbox-test-id"]
    assert captured["url"] == "https://api-hft.upstox.com/v3/order/place"


@pytest.mark.asyncio
async def test_modify_order_uses_official_upstox_v3_endpoint_without_network(monkeypatch):
    adapter = UpstoxAdapter()
    captured = {}

    async def fake_put(url, access_token, json_body):
        captured.update(url=url, access_token=access_token, json_body=json_body)
        return BrokerCallResult(ok=True, data={"status": "success", "data": {"order_id": "sandbox-test-id"}})

    monkeypatch.setattr(adapter, "_put", fake_put)
    payload = {
        "quantity": 2,
        "validity": "DAY",
        "price": 120.01,
        "order_id": "sandbox-test-id",
        "order_type": "LIMIT",
        "disclosed_quantity": 0,
        "trigger_price": 0,
    }

    result = await adapter.modify_order("test-token", payload)

    assert result.ok
    assert captured["url"] == "https://api-hft.upstox.com/v3/order/modify"
    assert captured["access_token"] == "test-token"
    assert captured["json_body"] == payload


@pytest.mark.asyncio
async def test_cancel_order_uses_official_upstox_v3_endpoint_without_network(monkeypatch):
    adapter = UpstoxAdapter()
    captured = {}

    async def fake_delete(url, access_token, params=None):
        captured.update(url=url, access_token=access_token, params=params)
        return BrokerCallResult(ok=True, data={"status": "success", "data": {"order_id": "sandbox-test-id"}})

    monkeypatch.setattr(adapter, "_delete", fake_delete)

    result = await adapter.cancel_order("test-token", "sandbox-test-id")

    assert result.ok
    assert captured["url"] == "https://api-hft.upstox.com/v3/order/cancel"
    assert captured["access_token"] == "test-token"
    assert captured["params"] == {"order_id": "sandbox-test-id"}


@pytest.mark.asyncio
async def test_get_order_trades_uses_official_read_only_endpoint_without_network(monkeypatch):
    adapter = UpstoxAdapter()
    captured = {}
    response = {
        "status": "success",
        "data": [
            {
                "order_id": "sandbox-test-id",
                "trade_id": "sandbox-trade-id",
                "quantity": 1,
                "average_price": 123.45,
            }
        ],
    }

    async def fake_get(url, access_token, params=None):
        captured.update(url=url, access_token=access_token, params=params)
        return BrokerCallResult(ok=True, data=response)

    monkeypatch.setattr(adapter, "_get", fake_get)

    result = await adapter.get_order_trades("test-token", "sandbox-test-id")

    assert result.ok
    assert captured["url"] == "https://api.upstox.com/v2/order/trades"
    assert captured["access_token"] == "test-token"
    assert captured["params"] == {"order_id": "sandbox-test-id"}
    assert result.data["data"][0]["trade_id"] == "sandbox-trade-id"


@pytest.mark.asyncio
async def test_get_order_history_can_lookup_by_stable_tag_without_network(monkeypatch):
    adapter = UpstoxAdapter()
    captured = {}
    response = {
        "status": "success",
        "data": [
            {"order_id": "sandbox-test-id", "status": "complete", "tag": "tradepro-recovery-123"}
        ],
    }

    async def fake_get(url, access_token, params=None):
        captured.update(url=url, access_token=access_token, params=params)
        return BrokerCallResult(ok=True, data=response)

    monkeypatch.setattr(adapter, "_get", fake_get)

    result = await adapter.get_order_history("test-token", tag=" tradepro-recovery-123 ")

    assert result.ok
    assert captured["url"] == "https://api.upstox.com/v2/order/history"
    assert captured["access_token"] == "test-token"
    assert captured["params"] == {"tag": "tradepro-recovery-123"}
    assert result.data["data"][0]["order_id"] == "sandbox-test-id"


@pytest.mark.asyncio
async def test_get_order_history_can_lookup_by_order_id_without_network(monkeypatch):
    adapter = UpstoxAdapter()
    captured = {}

    async def fake_get(url, access_token, params=None):
        captured.update(url=url, access_token=access_token, params=params)
        return BrokerCallResult(ok=True, data={"status": "success", "data": []})

    monkeypatch.setattr(adapter, "_get", fake_get)

    result = await adapter.get_order_history("test-token", order_id="broker-order-123")

    assert result.ok
    assert captured["params"] == {"order_id": "broker-order-123"}


@pytest.mark.asyncio
async def test_get_order_history_rejects_empty_or_oversized_tag_before_network(monkeypatch):
    adapter = UpstoxAdapter()
    fake_get = AsyncMock()
    monkeypatch.setattr(adapter, "_get", fake_get)

    with pytest.raises(ValueError, match="Provide order_id or tag"):
        await adapter.get_order_history("test-token")
    with pytest.raises(ValueError, match="tag must not be blank"):
        await adapter.get_order_history("test-token", tag="   ")
    with pytest.raises(ValueError, match="40 characters or fewer"):
        await adapter.get_order_history("test-token", tag="x" * 41)

    fake_get.assert_not_awaited()
