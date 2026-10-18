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


@pytest.mark.asyncio
async def test_get_funds_and_margin_uses_official_v3_endpoint_and_shape_without_network(monkeypatch):
    adapter = UpstoxAdapter()
    captured = {}
    payload = {
        "status": "success",
        "data": {
            "available_to_trade": {
                "total": 5379.03,
                "cash_available_to_trade": {"total": 5117.34},
                "pledge_available_to_trade": {"total": 261.69},
            },
            "unavailable_to_trade": {"cash_unavailable_to_trade": {"unsettled_profit": {"todays_profit": 0.0}}},
        },
    }

    async def fake_get_v3(url, access_token, params=None):
        captured.update(url=url, access_token=access_token, params=params)
        return BrokerCallResult(ok=True, data=payload)

    monkeypatch.setattr(adapter, "_get_v3", fake_get_v3)

    result = await adapter.get_funds_and_margin("test-token")

    assert result.ok
    assert captured["url"] == "https://api.upstox.com/v3/user/get-funds-and-margin"
    assert captured["access_token"] == "test-token"
    assert captured["params"] is None
    assert result.data["data"]["available_to_trade"]["total"] == 5379.03


@pytest.mark.asyncio
async def test_get_v3_sends_required_api_version_header_and_preserves_maintenance_error(monkeypatch):
    adapter = UpstoxAdapter()
    captured = {}
    payload = {"status": "success", "data": {"available_to_trade": {"total": 1000.0}}}

    class FakeResponse:
        def __init__(self, status_code, text, body):
            self.status_code = status_code
            self.text = text
            self._body = body

        def json(self):
            return self._body

    class FakeAsyncClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers, params=None):
            captured.update(url=url, headers=headers, params=params)
            return FakeResponse(200, "ok", payload)

    monkeypatch.setattr("app.brokers.upstox.adapter.httpx.AsyncClient", FakeAsyncClient)
    result = await adapter._get_v3(
        "https://api.upstox.com/v3/user/get-funds-and-margin", "test-token"
    )

    assert result.ok
    assert captured["headers"]["Api-Version"] == "3.0"
    assert captured["headers"]["Authorization"] == "Bearer test-token"
    assert captured["headers"]["Accept"] == "application/json"

    class MaintenanceAsyncClient(FakeAsyncClient):
        async def get(self, url, headers, params=None):
            captured.update(url=url, headers=headers, params=params)
            return FakeResponse(423, "Funds service maintenance window", {"status": "error"})

    monkeypatch.setattr("app.brokers.upstox.adapter.httpx.AsyncClient", MaintenanceAsyncClient)
    error = await adapter._get_v3(
        "https://api.upstox.com/v3/user/get-funds-and-margin", "test-token"
    )
    assert error.ok is False
    assert "423" in error.error
    assert "maintenance window" in error.error


@pytest.mark.asyncio
async def test_get_margin_details_uses_official_endpoint_and_normalizes_valid_inputs(monkeypatch):
    adapter = UpstoxAdapter()
    captured = {}
    response = {
        "status": "success",
        "data": {
            "margins": [{"equity_margin": 33.6, "total_margin": 33.6}],
            "required_margin": 33.6,
            "final_margin": 33.6,
        },
    }

    async def fake_post(url, access_token, json_body):
        captured.update(url=url, access_token=access_token, json_body=json_body)
        return BrokerCallResult(ok=True, data=response)

    monkeypatch.setattr(adapter, "_post", fake_post)
    result = await adapter.get_margin_details(
        "test-token",
        [{
            "instrument_key": " NSE_EQ|INE669E01016 ",
            "quantity": 2,
            "transaction_type": "buy",
            "product": "d",
            "price": "100.25",
        }],
    )

    assert result.ok
    assert captured["url"] == "https://api.upstox.com/v2/charges/margin"
    assert captured["access_token"] == "test-token"
    assert captured["json_body"] == {
        "instruments": [{
            "instrument_key": "NSE_EQ|INE669E01016",
            "quantity": 2,
            "transaction_type": "BUY",
            "product": "D",
            "price": 100.25,
        }]
    }
    assert result.data["data"]["required_margin"] == 33.6


@pytest.mark.asyncio
async def test_get_margin_details_rejects_invalid_batches_before_network(monkeypatch):
    adapter = UpstoxAdapter()
    fake_post = AsyncMock()
    monkeypatch.setattr(adapter, "_post", fake_post)
    valid = {
        "instrument_key": "NSE_EQ|INE669E01016",
        "quantity": 1,
        "transaction_type": "BUY",
        "product": "D",
    }

    with pytest.raises(ValueError, match="non-empty list"):
        await adapter.get_margin_details("test-token", [])
    with pytest.raises(ValueError, match="At most 20"):
        await adapter.get_margin_details("test-token", [dict(valid, instrument_key=f"NSE_EQ|{i}") for i in range(21)])
    with pytest.raises(ValueError, match="Duplicate instrument_key"):
        await adapter.get_margin_details("test-token", [valid, dict(valid)])
    with pytest.raises(ValueError, match="positive integer"):
        await adapter.get_margin_details("test-token", [dict(valid, quantity=0)])
    with pytest.raises(ValueError, match="BUY or SELL"):
        await adapter.get_margin_details("test-token", [dict(valid, transaction_type="SHORT")])
    with pytest.raises(ValueError, match="product"):
        await adapter.get_margin_details("test-token", [dict(valid, product="INVALID")])
    with pytest.raises(ValueError, match="finite positive number"):
        await adapter.get_margin_details("test-token", [dict(valid, price=float("nan"))])

    fake_post.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_margin_details_preserves_broker_error_without_approving_order(monkeypatch):
    adapter = UpstoxAdapter()

    async def fake_post(url, access_token, json_body):
        return BrokerCallResult(ok=False, error="Upstox API error (400): invalid instrument")

    monkeypatch.setattr(adapter, "_post", fake_post)
    result = await adapter.get_margin_details(
        "test-token",
        [{
            "instrument_key": "NSE_EQ|INE669E01016",
            "quantity": 1,
            "transaction_type": "BUY",
            "product": "D",
        }],
    )

    assert result.ok is False
    assert "invalid instrument" in result.error


@pytest.mark.asyncio
async def test_get_brokerage_details_uses_read_only_official_estimate_endpoint(monkeypatch):
    adapter = UpstoxAdapter()
    captured = {}

    async def fake_get(url, access_token, params=None):
        captured.update(url=url, access_token=access_token, params=params)
        return BrokerCallResult(ok=True, data={"status": "success", "data": {"charges": {}}})

    monkeypatch.setattr(adapter, "_get", fake_get)
    result = await adapter.get_brokerage_details(
        "test-token",
        instrument_token="NSE_EQ|INE669E01016",
        quantity=10,
        product="D",
        transaction_type="BUY",
        price=123.45,
    )

    assert result.ok
    assert captured["url"] == "https://api.upstox.com/v2/charges/brokerage"
    assert captured["access_token"] == "test-token"
    assert captured["params"] == {
        "instrument_token": "NSE_EQ|INE669E01016",
        "quantity": 10,
        "product": "D",
        "transaction_type": "BUY",
        "price": 123.45,
    }


@pytest.mark.asyncio
async def test_get_brokerage_details_rejects_invalid_inputs_before_network(monkeypatch):
    adapter = UpstoxAdapter()
    fake_get = AsyncMock()
    monkeypatch.setattr(adapter, "_get", fake_get)
    valid = dict(
        instrument_token="NSE_EQ|INE669E01016",
        quantity=10,
        product="D",
        transaction_type="BUY",
        price=123.45,
    )
    for invalid, message in [
        (dict(instrument_token=" ",), "instrument_token"),
        (dict(quantity=0), "positive integer"),
        (dict(product="OPTIONS"), "product"),
        (dict(transaction_type="SHORT"), "BUY or SELL"),
        (dict(price=float("nan")), "finite positive number"),
    ]:
        with pytest.raises(ValueError, match=message):
            await adapter.get_brokerage_details("test-token", **(valid | invalid))
    fake_get.assert_not_awaited()
