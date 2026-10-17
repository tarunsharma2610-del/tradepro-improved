"""
Thin wrapper over Meta's WhatsApp Cloud API — VERIFIED against current
docs (developers.facebook.com/docs/whatsapp/cloud-api). Two things worth
knowing before relying on this:

1. It needs TWO credentials, not one: an access token AND a phone_number_id
   (identifying which of the business's registered numbers sends the
   message) — see KNOWN_PLATFORM_SETTING_KEYS in schemas/platform_setting.py.
2. Meta's "24-hour rule": a free-form text message like the one this
   sends only delivers if the recipient has messaged the business number
   within the last 24 hours. Outside that window, only pre-approved
   template messages work — this module doesn't implement template
   sending, so a notification to someone outside that window will fail.
   This is a real Meta platform policy, not a bug here — see README known
   limitations.
"""

from dataclasses import dataclass
from typing import Any

import httpx

API_VERSION = "v23.0"


@dataclass
class WhatsAppResult:
    ok: bool
    data: Any = None
    error: str | None = None


async def send_message(access_token: str, phone_number_id: str, to: str, text: str) -> WhatsAppResult:
    url = f"https://graph.facebook.com/{API_VERSION}/{phone_number_id}/messages"
    body = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text, "preview_url": False},
    }
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(url, headers={"Authorization": f"Bearer {access_token}"}, json=body)
        except httpx.HTTPError as exc:
            return WhatsAppResult(ok=False, error=f"Network error contacting WhatsApp: {exc}")

    try:
        response_body = resp.json()
    except ValueError:
        return WhatsAppResult(ok=False, error="WhatsApp returned a non-JSON response")

    if resp.status_code >= 400:
        error_message = response_body.get("error", {}).get("message", f"WhatsApp API error ({resp.status_code})")
        return WhatsAppResult(ok=False, error=error_message)

    return WhatsAppResult(ok=True, data=response_body)
