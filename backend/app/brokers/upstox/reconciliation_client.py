"""Narrow, read-only Upstox client for reconciliation.

This class intentionally exposes only GET endpoints. Do not add order placement,
modification, or cancellation methods here. Error bodies are never returned/logged.
"""
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
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

    async def get_brokerage_estimate(
        self,
        access_token: str,
        *,
        instrument_token: str,
        quantity: int,
        product: str,
        transaction_type: str,
        price: Decimal | str | int | float,
    ) -> ReadOnlyBrokerResult:
        """Read the official order-specific charge estimate; never treat it as actuals."""
        instrument_token = self._required_id(instrument_token, "instrument_token")
        product = self._required_id(product, "product", max_length=16)
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        transaction_type = self._required_id(transaction_type, "transaction_type", max_length=4).upper()
        if transaction_type not in {"BUY", "SELL"}:
            raise ValueError("transaction_type must be BUY or SELL")
        try:
            parsed_price = price if isinstance(price, Decimal) else Decimal(str(price))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("price must be a finite positive decimal") from exc
        if not parsed_price.is_finite() or parsed_price <= 0:
            raise ValueError("price must be a finite positive decimal")
        return await self._get(
            "/charges/brokerage",
            access_token,
            {
                "instrument_token": instrument_token,
                "quantity": str(quantity),
                "product": product,
                "transaction_type": transaction_type,
                "price": format(parsed_price, "f"),
            },
        )

    async def get_trade_charges(
        self,
        access_token: str,
        *,
        segment: str,
        financial_year: str,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> ReadOnlyBrokerResult:
        """Read aggregate segment/FY charges; this is not per-fill evidence."""
        segment = self._required_id(segment, "segment", max_length=8).upper()
        if segment not in {"EQ", "FO", "COM", "CD"}:
            raise ValueError("segment must be EQ, FO, COM, or CD")
        financial_year = self._required_id(financial_year, "financial_year", max_length=4)
        if len(financial_year) != 4 or not financial_year.isdigit():
            raise ValueError("financial_year must use the four-digit YYZZ format")
        start_year = 2000 + int(financial_year[:2])
        end_year = 2000 + int(financial_year[2:])
        if end_year != start_year + 1:
            raise ValueError("financial_year must identify consecutive financial years")
        fy_start, fy_end = date(start_year, 4, 1), date(end_year, 3, 31)
        params: dict[str, str] = {"segment": segment, "financial_year": financial_year}
        parsed_dates: dict[str, date] = {}
        for field, value in (("from_date", from_date), ("to_date", to_date)):
            if value is None:
                continue
            try:
                parsed = datetime.strptime(value, "%d-%m-%Y").date()
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{field} must use dd-mm-yyyy format") from exc
            if not fy_start <= parsed <= fy_end:
                raise ValueError(f"{field} must fall within financial_year")
            parsed_dates[field] = parsed
            params[field] = value
        if (
            "from_date" in parsed_dates
            and "to_date" in parsed_dates
            and parsed_dates["to_date"] < parsed_dates["from_date"]
        ):
            raise ValueError("to_date must not precede from_date")
        return await self._get("/trade/profit-loss/charges", access_token, params)

    async def get_historical_trades(
        self,
        access_token: str,
        *,
        start_date: str,
        end_date: str,
        page_number: int,
        page_size: int,
        segment: str | None = None,
    ) -> ReadOnlyBrokerResult:
        """Read paginated broker trade references (Upstox documents a three-FY window)."""
        try:
            parsed_start = date.fromisoformat(start_date)
            parsed_end = date.fromisoformat(end_date)
        except (TypeError, ValueError) as exc:
            raise ValueError("start_date and end_date must use YYYY-MM-DD format") from exc
        if parsed_end < parsed_start:
            raise ValueError("end_date must not precede start_date")
        if isinstance(page_number, bool) or not isinstance(page_number, int) or page_number < 1:
            raise ValueError("page_number must be an integer greater than or equal to 1")
        if isinstance(page_size, bool) or not isinstance(page_size, int) or not 1 <= page_size <= 5000:
            raise ValueError("page_size must be between 1 and 5000")
        params = {
            "start_date": parsed_start.isoformat(),
            "end_date": parsed_end.isoformat(),
            "page_number": str(page_number),
            "page_size": str(page_size),
        }
        if segment is not None:
            segment = self._required_id(segment, "segment", max_length=8).upper()
            if segment not in {"EQ", "FO", "COM", "CD", "MF"}:
                raise ValueError("segment must be EQ, FO, COM, CD, or MF")
            params["segment"] = segment
        return await self._get("/charges/historical-trades", access_token, params)

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
