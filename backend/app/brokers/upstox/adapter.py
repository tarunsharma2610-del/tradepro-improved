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
from urllib.parse import urlencode

import httpx

from app.brokers.base import BrokerAdapter, BrokerCallResult, BrokerTokenResult

AUTH_BASE = "https://api.upstox.com/v2"
API_V2 = "https://api.upstox.com/v2"
API_V3 = "https://api.upstox.com/v3"
API_V3 = "https://api.upstox.com/v3"
API_HFT_V2 = "https://api-hft.upstox.com/v2"
API_HFT_V3 = "https://api-hft.upstox.com/v3"


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
        return BrokerCallResult(
            ok=False,
            error="Instrument master sync is implemented in Phase 2 (needs local caching/storage, "
            "not just an HTTP call — see Upstox 'Instruments' docs for the gzipped JSON file URLs).",
        )

    # --- Market data ---
    async def get_quote(self, access_token: str, instrument_keys: list[str]) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/ltp-v3
        params = {"instrument_key": ",".join(instrument_keys)}
        return await self._get(f"{API_V3}/market-quote/ltp", access_token, params=params)

    async def get_historical_data(
        self, access_token: str, instrument_key: str, unit: str, interval: str, from_date: date, to_date: date
    ) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/v3/get-historical-candle-data/
        # Path shape: /v3/historical-candle/{instrument_key}/{unit}/{interval}/{to_date}/{from_date}
        # unit: "minutes" | "hours" | "days" | "weeks" | "months"; to_date comes BEFORE from_date.
        path = f"{API_V3}/historical-candle/{instrument_key}/{unit}/{interval}/{to_date.isoformat()}/{from_date.isoformat()}"
        return await self._get(path, access_token)

    def get_market_data_stream_url(self, access_token: str) -> BrokerCallResult:
        return BrokerCallResult(
            ok=False,
            error="WebSocket streaming client lands in Phase 2 — see 'Websocket' and "
            "'Websocket implementation' pages in the Upstox docs for the authorized-URL handshake.",
        )

    # --- Orders (LIVE mode only) ---
    async def place_order(self, access_token: str, order: dict[str, Any]) -> BrokerCallResult:
        # Current official Place Order V3 endpoint. The legacy V2 place-order
        # endpoint is marked deprecated in the current Upstox documentation.
        # V3 returns data.order_ids (a list, including when slicing is enabled).
        # This adapter method is not wired into paper ExecutionService; live execution
        # still requires a separately reviewed service and must remain disabled for now.
        return await self._post(f"{API_HFT_V3}/order/place", access_token, json_body=order)

    async def modify_order(self, access_token: str, order: dict[str, Any]) -> BrokerCallResult:
        # Official Upstox V3 Modify Order endpoint. This method is not wired
        # into local order management; callers must confirm broker status after the request.
        return await self._put(f"{API_HFT_V3}/order/modify", access_token, json_body=order)

    async def cancel_order(self, access_token: str, order_id: str) -> BrokerCallResult:
        # Official Upstox V3 Cancel Order endpoint. A successful request is
        # not proof that the broker order has reached CANCELLED state.
        return await self._delete(f"{API_HFT_V3}/order/cancel", access_token, params={"order_id": order_id})

    async def get_order_status(self, access_token: str, order_id: str) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/get-order-details
        return await self._get(f"{API_V2}/order/details", access_token, params={"order_id": order_id})

    async def get_order_trades(self, access_token: str, order_id: str) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/get-trades-by-order
        return await self._get(f"{API_V2}/order/trades", access_token, params={"order_id": order_id})

    async def get_order_history(
        self, access_token: str, order_id: str | None = None, tag: str | None = None
    ) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/get-order-history
        params: dict[str, str] = {}
        if order_id is not None:
            order_id = order_id.strip()
            if not order_id:
                raise ValueError("order_id must not be blank.")
            params["order_id"] = order_id
        if tag is not None:
            tag = tag.strip()
            if not tag:
                raise ValueError("tag must not be blank.")
            if len(tag) > 40:
                raise ValueError("tag must be 40 characters or fewer.")
            params["tag"] = tag
        if not params:
            raise ValueError("Provide order_id or tag to look up order history.")
        return await self._get(f"{API_V2}/order/history", access_token, params=params)

    async def get_order_book(self, access_token: str) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/get-order-book
        return await self._get(f"{API_V2}/order/retrieve-all", access_token)

    # --- Positions & holdings ---
    async def get_funds_and_margin(self, access_token: str) -> BrokerCallResult:
        # Official Funds & Margin V3; unified available/unavailable-to-trade
        # breakdown. This is read-only and is not yet used to approve orders.
        return await self._get_v3(f"{API_V3}/user/get-funds-and-margin", access_token)

    async def get_margin_details(
        self, access_token: str, instruments: list[dict[str, Any]]
    ) -> BrokerCallResult:
        # Official Margin Details API. Validate locally so malformed or
        # unsupported batches never make a broker request.
        normalized = _validate_margin_instruments(instruments)
        return await self._post(
            f"{API_V2}/charges/margin",
            access_token,
            json_body={"instruments": normalized},
        )

    async def get_positions(self, access_token: str) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/get-positions
        return await self._get(f"{API_V2}/portfolio/short-term-positions", access_token)

    async def get_holdings(self, access_token: str) -> BrokerCallResult:
        # VERIFIED: upstox.com/developer/api-documentation/get-holdings
        return await self._get(f"{API_V2}/portfolio/long-term-holdings", access_token)

    # --- internal helpers ---
    async def _get_v3(
        self, url: str, access_token: str, params: dict[str, Any] | None = None
    ) -> BrokerCallResult:
        headers = {
            "Accept": "application/json",
            "Api-Version": "3.0",
            "Authorization": f"Bearer {access_token}",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(url, headers=headers, params=params)
            except httpx.HTTPError as exc:
                return BrokerCallResult(ok=False, error=f"Network error contacting Upstox: {exc}")
        return self._to_result(resp)

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

    async def _put(self, url: str, access_token: str, json_body: dict[str, Any]) -> BrokerCallResult:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.put(url, headers=headers, json=json_body)
            except httpx.HTTPError as exc:
                return BrokerCallResult(ok=False, error=f"Network error contacting Upstox: {exc}")
        return self._to_result(resp)

    async def _delete(
        self, url: str, access_token: str, params: dict[str, Any] | None = None
    ) -> BrokerCallResult:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.delete(url, headers=headers, params=params)
            except httpx.HTTPError as exc:
                return BrokerCallResult(ok=False, error=f"Network error contacting Upstox: {exc}")
        return self._to_result(resp)

def _validate_margin_instruments(instruments: Any) -> list[dict[str, Any]]:
    if not isinstance(instruments, list) or not instruments:
        raise ValueError("instruments must be a non-empty list.")
    if len(instruments) > 20:
        raise ValueError("At most 20 instruments can be requested per margin calculation.")

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    allowed_products = {"I", "D", "CO", "MTF"}

    for index, item in enumerate(instruments):
        prefix = f"instruments[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{prefix} must be an object.")

        instrument_key = item.get("instrument_key")
        if not isinstance(instrument_key, str) or not instrument_key.strip():
            raise ValueError(f"{prefix}.instrument_key must be a non-empty string.")
        instrument_key = instrument_key.strip()
        if instrument_key in seen_keys:
            raise ValueError("Duplicate instrument_key values are not allowed in a margin request.")
        seen_keys.add(instrument_key)

        quantity = item.get("quantity")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError(f"{prefix}.quantity must be a positive integer.")

        transaction_type = item.get("transaction_type")
        if not isinstance(transaction_type, str) or transaction_type.upper() not in {"BUY", "SELL"}:
            raise ValueError(f"{prefix}.transaction_type must be BUY or SELL.")

        product = item.get("product")
        if not isinstance(product, str) or product.upper() not in allowed_products:
            raise ValueError(f"{prefix}.product must be one of I, D, CO, MTF.")

        normalized_item: dict[str, Any] = {
            "instrument_key": instrument_key,
            "quantity": quantity,
            "transaction_type": transaction_type.upper(),
            "product": product.upper(),
        }
        if "price" in item and item["price"] is not None:
            raw_price = item["price"]
            if isinstance(raw_price, bool):
                raise ValueError(f"{prefix}.price must be a finite positive number.")
            try:
                price = Decimal(str(raw_price))
            except (InvalidOperation, ValueError):
                raise ValueError(f"{prefix}.price must be a finite positive number.") from None
            if not price.is_finite() or price <= 0:
                raise ValueError(f"{prefix}.price must be a finite positive number.")
            normalized_item["price"] = float(price)

        normalized.append(normalized_item)

    return normalized


    @staticmethod
    def _to_result(resp: httpx.Response) -> BrokerCallResult:
        if resp.status_code >= 400:
            return BrokerCallResult(ok=False, error=f"Upstox API error ({resp.status_code}): {resp.text}")
        try:
            return BrokerCallResult(ok=True, data=resp.json())
        except ValueError:
            return BrokerCallResult(ok=False, error="Upstox returned a non-JSON response")
