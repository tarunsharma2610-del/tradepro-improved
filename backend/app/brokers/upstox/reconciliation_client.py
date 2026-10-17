"""Narrow, read-only Upstox client for reconciliation.

This class intentionally exposes only GET endpoints. Do not add order placement,
modification, or cancellation methods here. Error bodies are never returned/logged.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx


API_V2 = "https://api.upstox.com/v2"


@dataclass(frozen=True)
class ReadOnlyBrokerResult:
    ok: bool
    data: Any = None
    status_code: int | None = None
    error_code: str | None = None
    retry_after_seconds: float | None = None


class UpstoxReadOnlyReconciliationClient:
    """Read-only façade with fixed endpoint paths and sanitized error categories."""

    def __init__(self, *, timeout_seconds: float = 15.0):
        if timeout_seconds <= 0 or timeout_seconds > 60:
            raise ValueError("timeout_seconds must be greater than 0 and at most 60")
        self.timeout_seconds = timeout_seconds

    async def get_order_book(self, access_token: str) -> ReadOnlyBrokerResult:
        return await self._get("/order/retrieve-all", access_token)

    async def get_order_details(self, access_token: str, order_id: str) -> ReadOnlyBrokerResult:
        order_id = self._required_id(order_id, "order_id")
        return await self._get("/order/details", access_token, {"order_id": order_id})

    async def get_order_history(
        self,
        access_token: str,
        *,
        order_id: str | None = None,
        tag: str | None = None,
    ) -> ReadOnlyBrokerResult:
        params: dict[str, str] = {}
        if order_id is not None:
            params["order_id"] = self._required_id(order_id, "order_id")
        if tag is not None:
            normalized_tag = self._required_id(tag, "tag", max_length=64)
            params["tag"] = normalized_tag
        if not params:
            raise ValueError("order_id or tag is required for order history")
        return await self._get("/order/history", access_token, params)

    async def get_order_trades(self, access_token: str, order_id: str) -> ReadOnlyBrokerResult:
        order_id = self._required_id(order_id, "order_id")
        return await self._get("/order/trades", access_token, {"order_id": order_id})

    async def get_trades_for_day(self, access_token: str) -> ReadOnlyBrokerResult:
        return await self._get("/order/trades/get-trades-for-day", access_token)

    @staticmethod
    def _required_id(value: str, field: str, *, max_length: int = 128) -> str:
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > max_length:
            raise ValueError(f"{field} must contain 1-{max_length} characters")
        return value.strip()

    @staticmethod
    def _retry_after_seconds(response: httpx.Response) -> float | None:
        raw = response.headers.get("Retry-After")
        if not raw:
            return None
        try:
            value = float(raw)
            return value if value >= 0 else None
        except (TypeError, ValueError):
            try:
                when = parsedate_to_datetime(raw)
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                return max(0.0, (when.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                return None

    async def _get(
        self,
        path: str,
        access_token: str,
        params: dict[str, str] | None = None,
    ) -> ReadOnlyBrokerResult:
        if not isinstance(access_token, str) or not access_token.strip():
            return ReadOnlyBrokerResult(ok=False, error_code="MISSING_ACCESS_TOKEN")
        # path is only supplied by the fixed methods above; callers cannot pass arbitrary URLs.
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(f"{API_V2}{path}", headers=headers, params=params)
        except httpx.TimeoutException:
            return ReadOnlyBrokerResult(ok=False, error_code="TIMEOUT")
        except httpx.HTTPError:
            return ReadOnlyBrokerResult(ok=False, error_code="NETWORK_ERROR")

        status = response.status_code
        if status >= 400:
            if status == 401:
                category = "TOKEN_EXPIRED_OR_UNAUTHORIZED"
            elif status == 403:
                category = "FORBIDDEN"
            elif status == 429:
                category = "RATE_LIMITED"
            elif status >= 500:
                category = "UPSTREAM_SERVER_ERROR"
            else:
                category = "UPSTREAM_CLIENT_ERROR"
            return ReadOnlyBrokerResult(
                ok=False,
                status_code=status,
                error_code=category,
                retry_after_seconds=self._retry_after_seconds(response),
            )
        try:
            body = response.json()
        except ValueError:
            return ReadOnlyBrokerResult(ok=False, status_code=status, error_code="NON_JSON_RESPONSE")
        return ReadOnlyBrokerResult(ok=True, data=body, status_code=status)
