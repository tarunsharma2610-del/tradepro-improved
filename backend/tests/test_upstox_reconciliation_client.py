import httpx
import pytest

from app.brokers.upstox.reconciliation_client import (
    API_V2,
    UpstoxReadOnlyReconciliationClient,
)


class _Response:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self.body = body if body is not None else {"status": "success", "data": []}

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
