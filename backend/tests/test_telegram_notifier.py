from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services import telegram_notifier


def _mock_httpx(json_body: dict, status: int = 200, method: str = "get"):
    mock_resp = type("R", (), {"status_code": status, "json": lambda self: json_body})()
    target = f"httpx.AsyncClient.{method}"
    return patch(target, new=AsyncMock(return_value=mock_resp))


@pytest.mark.asyncio
async def test_get_me_returns_bot_info_on_success():
    with _mock_httpx({"ok": True, "result": {"id": 123, "username": "my_trading_bot"}}):
        result = await telegram_notifier.get_me("fake-token")
    assert result.ok
    assert result.data["username"] == "my_trading_bot"


@pytest.mark.asyncio
async def test_get_me_reports_telegrams_own_error_description():
    with _mock_httpx({"ok": False, "description": "Unauthorized"}, status=401):
        result = await telegram_notifier.get_me("bad-token")
    assert not result.ok
    assert "Unauthorized" in result.error


@pytest.mark.asyncio
async def test_send_message_posts_chat_id_and_text():
    captured = {}

    async def fake_post(self, url, json=None, **kwargs):
        captured["url"] = url
        captured["json"] = json
        return type("R", (), {"status_code": 200, "json": lambda s: {"ok": True, "result": {}}})()

    with patch("httpx.AsyncClient.post", new=fake_post):
        result = await telegram_notifier.send_message("tok123", 555, "Hello trader")

    assert result.ok
    assert "tok123" in captured["url"]
    assert captured["json"] == {"chat_id": 555, "text": "Hello trader"}


@pytest.mark.asyncio
async def test_get_updates_passes_offset_for_pagination():
    captured = {}

    async def fake_get(self, url, params=None, **kwargs):
        captured["params"] = params
        return type("R", (), {"status_code": 200, "json": lambda s: {"ok": True, "result": []}})()

    with patch("httpx.AsyncClient.get", new=fake_get):
        await telegram_notifier.get_updates("tok", offset=42)

    assert captured["params"]["offset"] == 42


@pytest.mark.asyncio
async def test_network_error_returns_a_result_not_an_exception():
    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=httpx.ConnectError("boom"))):
        result = await telegram_notifier.get_me("tok")
    assert not result.ok
    assert "network error" in result.error.lower()
