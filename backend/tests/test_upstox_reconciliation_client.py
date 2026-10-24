import httpx
import pytest

from app.brokers.upstox.reconciliation_client import (
    API_V2,
    UpstoxReadOnlyReconciliationClient,
)


class _Response:
    def __init__(self, status_code=200, body=None, headers=None):
        self.status_code = status_code
        self.body = body if body is not None else {"status": "success", "data": []}
        self.headers = headers or {}

    def json(self):
        if self.body == "not-json":
            raise ValueError("not JSON")
        return self.body


class _AsyncClient:
    response = _Response()
    exception = None
    calls = []

    def __init__(self, *, timeout):
        self.timeout = timeout

    async def __aenter__(self):
        type(self).calls = []
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *, headers, params=None):
        type(self).calls.append({"url": url, "headers": headers, "params": params})
        if type(self).exception is not None:
            raise type(self).exception
        return type(self).response


@pytest.fixture
def fake_httpx(monkeypatch):
    _AsyncClient.response = _Response()
    _AsyncClient.exception = None
    _AsyncClient.calls = []
    monkeypatch.setattr(httpx, "AsyncClient", _AsyncClient)
    return _AsyncClient


@pytest.mark.asyncio
async def test_order_book_uses_only_fixed_read_endpoint(fake_httpx):
    client = UpstoxReadOnlyReconciliationClient()
    result = await client.get_order_book("test-token")

    assert result.ok is True
    assert result.data["status"] == "success"
    assert fake_httpx.calls[0]["url"] == f"{API_V2}/order/retrieve-all"
    assert fake_httpx.calls[0]["headers"]["Authorization"] == "Bearer test-token"
    assert fake_httpx.calls[0]["params"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "args", "path", "params"),
    [
        ("get_order_details", ("order-1",), "/order/details", {"order_id": "order-1"}),
        ("get_order_history", (), "/order/history", {"order_id": "order-1"}),
        ("get_order_history", (), "/order/history", {"tag": "correlation-1"}),
        ("get_order_trades", ("order-1",), "/order/trades", {"order_id": "order-1"}),
    ],
)
async def test_order_read_methods_use_documented_get_paths(fake_httpx, method, args, path, params):
    client = UpstoxReadOnlyReconciliationClient()
    if method == "get_order_history":
        result = await client.get_order_history("test-token", **params)
    else:
        result = await getattr(client, method)("test-token", *args)

    assert result.ok is True
    assert fake_httpx.calls[0]["url"] == f"{API_V2}{path}"
    assert fake_httpx.calls[0]["params"] == params


@pytest.mark.asyncio
async def test_order_history_requires_order_id_or_tag():
    client = UpstoxReadOnlyReconciliationClient()
    with pytest.raises(ValueError, match="order_id or tag is required"):
        await client.get_order_history("test-token")


@pytest.mark.asyncio
async def test_missing_token_is_classified_without_network_call(fake_httpx):
    result = await UpstoxReadOnlyReconciliationClient().get_order_book("")

    assert result.ok is False
    assert result.error_code == "MISSING_ACCESS_TOKEN"
    assert fake_httpx.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "category"),
    [
        (401, "TOKEN_EXPIRED_OR_UNAUTHORIZED"),
        (403, "FORBIDDEN"),
        (429, "RATE_LIMITED"),
        (503, "UPSTREAM_SERVER_ERROR"),
        (400, "UPSTREAM_CLIENT_ERROR"),
    ],
)
async def test_http_errors_are_sanitized_and_classified(fake_httpx, status, category):
    fake_httpx.response = _Response(status, body={"message": "secret response body"})
    result = await UpstoxReadOnlyReconciliationClient().get_order_book("test-token")

    assert result.ok is False
    assert result.status_code == status
    assert result.error_code == category
    assert not hasattr(result, "error")
    assert "secret response body" not in repr(result)


@pytest.mark.asyncio
async def test_timeout_and_network_errors_do_not_leak_exception_text(fake_httpx):
    fake_httpx.exception = httpx.TimeoutException("Bearer token should not leak")
    result = await UpstoxReadOnlyReconciliationClient().get_order_book("test-token")
    assert result.error_code == "TIMEOUT"
    assert "Bearer token" not in repr(result)

    fake_httpx.exception = httpx.ConnectError("Bearer token should not leak")
    result = await UpstoxReadOnlyReconciliationClient().get_order_book("test-token")
    assert result.error_code == "NETWORK_ERROR"
    assert "Bearer token" not in repr(result)


@pytest.mark.asyncio
async def test_non_json_response_is_safe_failure(fake_httpx):
    fake_httpx.response = _Response(200, body="not-json")
    result = await UpstoxReadOnlyReconciliationClient().get_order_book("test-token")
    assert result.ok is False
    assert result.error_code == "NON_JSON_RESPONSE"


def test_read_only_client_exposes_no_order_write_methods():
    client = UpstoxReadOnlyReconciliationClient()
    assert not hasattr(client, "place_order")
    assert not hasattr(client, "modify_order")
    assert not hasattr(client, "cancel_order")



@pytest.mark.asyncio
async def test_daily_trade_history_uses_documented_get_endpoint(fake_httpx):
    client = UpstoxReadOnlyReconciliationClient()
    result = await client.get_trades_for_day("test-token")
    assert result.ok is True
    assert fake_httpx.calls[0]["url"] == f"{API_V2}/order/trades/get-trades-for-day"
    assert fake_httpx.calls[0]["params"] is None


@pytest.mark.asyncio
async def test_retry_after_metadata_is_exposed_without_response_body(fake_httpx):
    fake_httpx.response = _Response(
        429, body={"message": "private error body"}, headers={"Retry-After": "3"}
    )
    result = await UpstoxReadOnlyReconciliationClient().get_order_book("test-token")
    assert result.ok is False
    assert result.error_code == "RATE_LIMITED"
    assert result.retry_after_seconds == 3.0
    assert "private error body" not in repr(result)

@pytest.mark.asyncio
async def test_brokerage_estimate_uses_documented_read_only_endpoint_and_normalizes_inputs(fake_httpx):
    from decimal import Decimal

    fake_httpx.response = _Response(body={
        "status": "success",
        "data": {"charges": {"total": 12.34, "brokerage": 10.0, "dp_plan": {"min_expense": 18.5}}},
    })
    result = await UpstoxReadOnlyReconciliationClient().get_brokerage_estimate(
        "test-token",
        instrument_token="NSE_EQ|INE669E01016",
        quantity=10,
        product="I",
        transaction_type="buy",
        price=Decimal("13.70"),
    )
    assert result.ok is True
    assert fake_httpx.calls[0]["url"] == f"{API_V2}/charges/brokerage"
    assert fake_httpx.calls[0]["params"] == {
        "instrument_token": "NSE_EQ|INE669E01016",
        "quantity": "10",
        "product": "I",
        "transaction_type": "BUY",
        "price": "13.70",
    }
    # The daily DP-plan minimum is metadata, not included in the API total.
    assert result.data["data"]["charges"]["dp_plan"]["min_expense"] == 18.5


@pytest.mark.asyncio
async def test_brokerage_estimate_rejects_invalid_order_inputs_before_network(fake_httpx):
    client = UpstoxReadOnlyReconciliationClient()
    common = {
        "instrument_token": "NSE_EQ|INE669E01016",
        "quantity": 1,
        "product": "I",
        "transaction_type": "BUY",
        "price": "10.00",
    }
    for overrides, message in [
        ({"quantity": 0}, "positive integer"),
        ({"quantity": True}, "positive integer"),
        ({"transaction_type": "HOLD"}, "BUY or SELL"),
        ({"price": "NaN"}, "finite positive decimal"),
        ({"price": "0"}, "finite positive decimal"),
    ]:
        with pytest.raises(ValueError, match=message):
            await client.get_brokerage_estimate("test-token", **{**common, **overrides})
    assert fake_httpx.calls == []


@pytest.mark.asyncio
async def test_trade_charges_uses_documented_segment_and_financial_year_scope(fake_httpx):
    client = UpstoxReadOnlyReconciliationClient()
    result = await client.get_trade_charges(
        "test-token",
        segment="fo",
        financial_year="2627",
        from_date="01-04-2026",
        to_date="24-10-2026",
    )
    assert result.ok is True
    assert fake_httpx.calls[0]["url"] == f"{API_V2}/trade/profit-loss/charges"
    assert fake_httpx.calls[0]["params"] == {
        "segment": "FO",
        "financial_year": "2627",
        "from_date": "01-04-2026",
        "to_date": "24-10-2026",
    }


@pytest.mark.asyncio
async def test_trade_charges_rejects_invalid_financial_year_dates_and_segment(fake_httpx):
    client = UpstoxReadOnlyReconciliationClient()
    with pytest.raises(ValueError, match="financial_year"):
        await client.get_trade_charges("test-token", segment="EQ", financial_year="2628")
    with pytest.raises(ValueError, match="within financial_year"):
        await client.get_trade_charges(
            "test-token", segment="EQ", financial_year="2627", from_date="31-03-2026"
        )
    with pytest.raises(ValueError, match="to_date must not precede"):
        await client.get_trade_charges(
            "test-token", segment="EQ", financial_year="2627",
            from_date="02-05-2026", to_date="01-05-2026",
        )
    with pytest.raises(ValueError, match="segment must be"):
        await client.get_trade_charges("test-token", segment="ALL", financial_year="2627")
    assert fake_httpx.calls == []


@pytest.mark.asyncio
async def test_historical_trades_uses_documented_pagination_and_date_scope(fake_httpx):
    client = UpstoxReadOnlyReconciliationClient()
    result = await client.get_historical_trades(
        "test-token",
        start_date="2026-04-01",
        end_date="2026-10-24",
        page_number=2,
        page_size=5000,
        segment="mf",
    )
    assert result.ok is True
    assert fake_httpx.calls[0]["url"] == f"{API_V2}/charges/historical-trades"
    assert fake_httpx.calls[0]["params"] == {
        "start_date": "2026-04-01",
        "end_date": "2026-10-24",
        "page_number": "2",
        "page_size": "5000",
        "segment": "MF",
    }


@pytest.mark.asyncio
async def test_historical_trades_rejects_invalid_dates_and_pagination(fake_httpx):
    client = UpstoxReadOnlyReconciliationClient()
    common = {
        "start_date": "2026-04-01",
        "end_date": "2026-10-24",
        "page_number": 1,
        "page_size": 100,
    }
    for overrides, message in [
        ({"start_date": "01-04-2026"}, "YYYY-MM-DD"),
        ({"end_date": "2026-03-31"}, "end_date must not precede"),
        ({"page_number": 0}, "page_number"),
        ({"page_size": 5001}, "page_size"),
        ({"segment": "INVALID"}, "segment must be"),
    ]:
        with pytest.raises(ValueError, match=message):
            await client.get_historical_trades("test-token", **{**common, **overrides})
    assert fake_httpx.calls == []

@pytest.mark.asyncio
async def test_profit_loss_report_uses_documented_paginated_trade_wise_endpoint(fake_httpx):
    client = UpstoxReadOnlyReconciliationClient()
    fake_httpx.response = _Response(body={
        "status": "success",
        "data": [{
            "quantity": 10,
            "trade_type": "EQ",
            "buy_amount": 1000.0,
            "sell_amount": 1100.0,
        }],
        "metadata": {"page": {"page_number": 2, "page_size": 500}},
    })
    result = await client.get_profit_loss_report(
        "test-token",
        segment="eq",
        financial_year="2627",
        from_date="01-04-2026",
        to_date="24-10-2026",
        page_number=2,
        page_size=500,
    )
    assert result.ok is True
    assert fake_httpx.calls[0]["url"] == f"{API_V2}/trade/profit-loss/data"
    assert fake_httpx.calls[0]["params"] == {
        "segment": "EQ",
        "financial_year": "2627",
        "from_date": "01-04-2026",
        "to_date": "24-10-2026",
        "page_number": "2",
        "page_size": "500",
    }
    # This endpoint provides trade-wise P&L rows, not per-fill charge components.
    assert "charges_breakdown" not in result.data["data"][0]


@pytest.mark.asyncio
async def test_profit_loss_report_rejects_invalid_scope_and_pagination(fake_httpx):
    client = UpstoxReadOnlyReconciliationClient()
    common = {
        "segment": "EQ",
        "financial_year": "2627",
        "page_number": 1,
        "page_size": 100,
    }
    for overrides, message in [
        ({"segment": "ALL"}, "segment must be"),
        ({"financial_year": "2628"}, "financial_year"),
        ({"page_number": 0}, "page_number"),
        ({"page_size": 5001}, "page_size"),
        ({"from_date": "31-03-2026"}, "within financial_year"),
        ({"from_date": "02-05-2026", "to_date": "01-05-2026"}, "to_date must not precede"),
    ]:
        with pytest.raises(ValueError, match=message):
            await client.get_profit_loss_report(
                "test-token", **{**common, **overrides}
            )
    assert fake_httpx.calls == []
