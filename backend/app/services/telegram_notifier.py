"""
Thin wrapper over the Telegram Bot API — VERIFIED against current docs
(core.telegram.org/bots/api): base URL pattern, sendMessage, getUpdates,
getMe. This API has been stable for years; the shapes here are about as
low-risk as an external API integration gets.
"""

from dataclasses import dataclass
from typing import Any

import httpx

_BASE = "https://api.telegram.org/bot{token}"


@dataclass
class TelegramResult:
    ok: bool
    data: Any = None
    error: str | None = None


async def get_me(bot_token: str) -> TelegramResult:
    return await _get(bot_token, "getMe")


async def send_message(bot_token: str, chat_id: int, text: str) -> TelegramResult:
    return await _post(bot_token, "sendMessage", {"chat_id": chat_id, "text": text})


async def get_updates(bot_token: str, offset: int | None = None, timeout: int = 0) -> TelegramResult:
    """`offset` should be the last processed update_id + 1 — Telegram then
    only returns updates you haven't acknowledged yet. `timeout=0` (the
    default here) makes this a quick poll rather than long-polling, which
    suits a periodic worker tick better than holding a connection open."""
    params: dict[str, Any] = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    return await _get(bot_token, "getUpdates", params)


async def _get(bot_token: str, method: str, params: dict | None = None) -> TelegramResult:
    url = f"{_BASE.format(token=bot_token)}/{method}"
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, params=params)
        except httpx.HTTPError as exc:
            return TelegramResult(ok=False, error=f"Network error contacting Telegram: {exc}")
    return _to_result(resp)


async def _post(bot_token: str, method: str, json_body: dict) -> TelegramResult:
    url = f"{_BASE.format(token=bot_token)}/{method}"
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(url, json=json_body)
        except httpx.HTTPError as exc:
            return TelegramResult(ok=False, error=f"Network error contacting Telegram: {exc}")
    return _to_result(resp)


def _to_result(resp: httpx.Response) -> TelegramResult:
    try:
        body = resp.json()
    except ValueError:
        return TelegramResult(ok=False, error="Telegram returned a non-JSON response")

    if not body.get("ok"):
        return TelegramResult(ok=False, error=body.get("description", f"Telegram API error ({resp.status_code})"))
    return TelegramResult(ok=True, data=body.get("result"))
