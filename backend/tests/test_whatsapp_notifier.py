from unittest.mock import patch

import pytest

from app.services import whatsapp_notifier


@pytest.mark.asyncio
async def test_send_message_posts_correct_shape_to_the_phone_number_id_endpoint():
    captured = {}

    async def fake_post(self, url, headers=None, json=None, **kwargs):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return type("R", (), {"status_code": 200, "json": lambda s: {"messages": [{"id": "wamid.abc"}]}})()

    with patch("httpx.AsyncClient.post", new=fake_post):
        result = await whatsapp_notifier.send_message("token123", "1234567890", "+919876543210", "Trade filled")

    assert result.ok
    assert "1234567890/messages" in captured["url"]
    assert captured["headers"]["Authorization"] == "Bearer token123"
    assert captured["json"]["to"] == "+919876543210"
    assert captured["json"]["text"]["body"] == "Trade filled"
    assert captured["json"]["messaging_product"] == "whatsapp"


@pytest.mark.asyncio
async def test_meta_error_response_surfaces_metas_own_error_message():
    """This is the shape a 24-hour-window violation actually returns as —
    the notifier surfaces it rather than swallowing it, since it's real,
    actionable information (see the module docstring's known limitation)."""

    async def fake_post(self, url, headers=None, json=None, **kwargs):
        return type(
            "R", (), {"status_code": 400, "json": lambda s: {"error": {"message": "Re-engagement message outside allowed window"}}}
        )()

    with patch("httpx.AsyncClient.post", new=fake_post):
        result = await whatsapp_notifier.send_message("token", "123", "+91999", "hi")

    assert not result.ok
    assert "window" in result.error.lower()
