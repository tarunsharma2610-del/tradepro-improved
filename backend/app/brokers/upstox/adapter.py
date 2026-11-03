"""
Upstox implementation of BrokerAdapter.

Endpoints below marked VERIFIED were checked against api-documentation
directly. Endpoints marked BEST-EFFORT follow Upstox's consistent REST
pattern but weren't individually checked against their own docs page —
confirm the exact path/response shape there before the first real call in
Phase 2, rather than trusting this comment.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote, urlencode

import httpx

from app.brokers.base import BrokerAdapter, BrokerCallResult, BrokerTokenResult

AUTH_BASE = "https://api.upstox.com/v2"
API_V2 = "https://api.upstox.com/v2"
API_V3 = "https://api.upstox.com/v3"


class UpstoxAdapter(BrokerAdapter):
    broker_name = "upstox"

    # --- Authentication (VERIFIED: upstox.com/developer/api-documentation/authentication) ---
    def get_authorize_url(self, api_key: str, redirect_uri: str, state: str | None = None) -> str:
        params = {"response_type": "code", "client_id": api_key, "redirect_uri": redirect_uri}
        if state:
            params["state"] = state
        return f"{AUTH_BASE}/login/authorization/dialog?{urlencode(params)}"

    async def exchange_code_for_token(
        self, api_key: str, api_secret: str, redirect_uri: str, code: str
    ) -> BrokerCallResult:
        data = {
            "code": code,
            "client_id": api_key,
            "client_secret": api_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    f"{AUTH_BASE}/login/authorization/token",
                    data=data,
                    headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                )
            except httpx.HTTPError as exc:
                return BrokerCallResult(ok=False, error=f"Network error contacting Upstox: {exc}")

        if resp.status_code != 200:
            return BrokerCallResult(ok=False, error=f"Upstox token exchange failed ({resp.status_code}): {resp.text}")

        body = resp.json()
        access_token = body.get("access_token")
        if not access_token:
            return BrokerCallResult(ok=False, error="Upstox response did not include an access_token")

        # Upstox access tokens expire at 3:30 AM IST the following day
        # (per Access Token Request docs), not a fixed TTL from issuance.
        now_utc = datetime.now(timezone.utc)
        ist_offset = timedelta(hours=5, minutes=30)
        now_ist = now_utc + ist_offset
        expiry_ist = (now_ist + timedelta(days=1)).replace(hour=3, minute=30, second=0, microsecond=0)
        if expiry_ist <= now_ist:
            expiry_ist += timedelta(days=1)
        expires_at = expiry_ist - ist_offset  # back to UTC

        return BrokerCallResult(ok=True, data=BrokerTokenResult(access_token=access_token, expires_at=expires_at, raw=body))

    async def get_profile(self, access_token: str) -> BrokerCallResult:
        # BEST-EFFORT path — confirm against the "User" docs page.
        return await self._get(f"{API_V2}/user/profile", access_token)

    # --- Instruments ---
    async def sync_instruments(self) -> BrokerCallResult:
        # Catalog synchronization is intentionally handled by
        # app.services.instrument_service, which owns persistence and batch
        # upserts. This adapter method is not used by the admin sync endpoint.
        return BrokerCallResult(
            ok=False,
            error="Instrument catalog sync is provided by InstrumentService; this adapter method is not implemented.",
        )

    # --- Market data ---
    async def get_quote(self, access_token: str, instrument_keys: list[str]) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/ltp-v3
        params = {"instrument_key": ",".join(instrument_keys)}
        return await self._get(f"{API_V3}/market-quote/ltp", access_token, params=params)

    async def get_full_quote(self, access_token: str, instrument_keys: list[str]) -> BrokerCallResult:
        # VERIFIED: https://upstox.com/developer/api-documentation/get-full-market-quote-v3/
        params = {"instrument_key": ",".join(instrument_keys)}
        return await self._get(f"{API_V3}/market-quote/quotes", access_token, params=params)

    async def get_historical_data(
        self, access_token: str, instrument_key: str, unit: str, interval: str, from_date: date, to_date: date
    ) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/v3/get-historical-candle-data/
        # Path shape: /v3/historical-candle/{instrument_key}/{unit}/{interval}/{to_date}/{from_date}
        # unit: "minutes" | "hours" | "days" | "weeks" | "months"; to_date comes BEFORE from_date.
        path = f"{API_V3}/historical-candle/{instrument_key}/{unit}/{interval}/{to_date.isoformat()}/{from_date.isoformat()}"
        return await self._get(path, access_token)

    async def get_option_chain(
        self, access_token: str, instrument_key: str, expiry_date: str
    ) -> BrokerCallResult:
        """Fetch the official option-chain snapshot using the Analytics Token."""
        return await self._get(
            f"{API_V2}/option/chain",
            access_token,
            params={"instrument_key": instrument_key, "expiry_date": expiry_date},
        )

    async def get_intraday_data(
        self, access_token: str, instrument_key: str, unit: str, interval: str
    ) -> BrokerCallResult:
        """Fetch current-session candles using Upstox's supported V3 endpoint."""
        encoded_key = quote(instrument_key, safe="")
        path = f"{API_V3}/historical-candle/intraday/{encoded_key}/{unit}/{interval}"
        return await self._get(path, access_token)

    def get_market_data_stream_url(self, access_token: str) -> BrokerCallResult:
        return BrokerCallResult(
            ok=False,
            error="WebSocket streaming client lands in Phase 2 — see 'Websocket' and "
            "'Websocket implementation' pages in the Upstox docs for the authorized-URL handshake.",
        )

    # --- Orders (LIVE mode only) ---
    async def place_order(self, access_token: str, order: dict[str, Any]) -> BrokerCallResult:
        # VERIFIED path shape (sandbox example): upstox.com/developer/api-documentation/sandbox
        # Live trading is disabled at the application level (TRADING_MODE=PAPER) regardless of
        # whether this method works — see app/core/config.py.
        return await self._post(f"{API_V2}/order/place", access_token, json_body=order)

    async def get_order_status(self, access_token: str, order_id: str) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/get-order-details
        return await self._get(f"{API_V2}/order/details", access_token, params={"order_id": order_id})

    async def get_order_book(self, access_token: str) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/get-order-book
        return await self._get(f"{API_V2}/order/retrieve-all", access_token)

    # --- Positions & holdings ---
    async def get_positions(self, access_token: str) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/get-positions
        return await self._get(f"{API_V2}/portfolio/short-term-positions", access_token)

    async def get_holdings(self, access_token: str) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/get-holdings
        return await self._get(f"{API_V2}/portfolio/long-term-holdings", access_token)

    # --- internal helpers ---
    async def _get(self, url: str, access_token: str, params: dict[str, Any] | None = None) -> BrokerCallResult:
        headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
            except httpx.HTTPError as exc:
                return BrokerCallResult(ok=False, error=f"Network error contacting Upstox: {exc}")
        return self._to_result(resp)

    async def _post(self, url: str, access_token: str, json_body: dict[str, Any]) -> BrokerCallResult:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(url, headers=headers, json=json_body)
            except httpx.HTTPError as exc:
                return BrokerCallResult(ok=False, error=f"Network error contacting Upstox: {exc}")
        return self._to_result(resp)

    @staticmethod
    def _to_result(resp: httpx.Response) -> BrokerCallResult:
        if resp.status_code >= 400:
            return BrokerCallResult(ok=False, error=f"Upstox API error ({resp.status_code}): {resp.text}")
        try:
            return BrokerCallResult(ok=True, data=resp.json())
        except ValueError:
            return BrokerCallResult(ok=False, error="Upstox returned a non-JSON response")
