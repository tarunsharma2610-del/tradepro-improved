"""
BrokerAdapter: the one contract every broker integration implements.

Nothing outside app/brokers/<broker_name>/ should ever import a
broker-specific module directly. The trading engine (Phase 2+), the
Settings service, and everything else talk to brokers only through this
interface, so adding Zerodha or Groww later means writing
app/brokers/zerodha/adapter.py and nothing else — the engine doesn't change.

All methods are async because they're all network calls to a broker's API.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass
class BrokerTokenResult:
    access_token: str
    expires_at: datetime | None
    raw: dict[str, Any]


@dataclass
class BrokerCallResult:
    """Wraps every adapter call. `ok=False` means the caller should show
    the real error, not fall back to demo/mock data — see the project's
    'never present fake data as real' rule in ARCHITECTURE.md."""

    ok: bool
    data: Any = None
    error: str | None = None


class BrokerAdapter(ABC):
    broker_name: str

    # --- Authentication ---
    @abstractmethod
    def get_authorize_url(self, api_key: str, redirect_uri: str, state: str | None = None) -> str:
        """Build the URL the browser is sent to for the OAuth login step."""

    @abstractmethod
    async def exchange_code_for_token(
        self, api_key: str, api_secret: str, redirect_uri: str, code: str
    ) -> BrokerCallResult:
        """Server-to-server exchange of the OAuth `code` for an access token."""

    @abstractmethod
    async def get_profile(self, access_token: str) -> BrokerCallResult:
        """Cheapest possible authenticated call — used to verify a
        connection actually works before is_connected is set True."""

    # --- Instruments ---
    @abstractmethod
    async def sync_instruments(self) -> BrokerCallResult:
        """Download/refresh the tradable-instrument master list."""

    # --- Market data ---
    @abstractmethod
    async def get_quote(self, access_token: str, instrument_keys: list[str]) -> BrokerCallResult:
        ...

    @abstractmethod
    async def get_historical_data(
        self, access_token: str, instrument_key: str, unit: str, interval: str, from_date: date, to_date: date
    ) -> BrokerCallResult:
        ...

    @abstractmethod
    async def get_full_market_quote(self, access_token: str, instrument_keys: list[str]) -> BrokerCallResult:
        """Return exchange timestamped quote snapshots for risk checks."""
        ...

    @abstractmethod
    async def get_market_holidays(self, access_token: str) -> BrokerCallResult:
        """Return exchange holiday/special-session calendar metadata."""
        ...

    @abstractmethod
    async def get_market_timings(self, access_token: str, market_date: date) -> BrokerCallResult:
        """Return official exchange open/close times for one market date."""
        ...

    @abstractmethod
    def get_market_data_stream_url(self, access_token: str) -> BrokerCallResult:
        """Authenticated WebSocket URL for live market data. Full streaming
        client lands in Phase 2 alongside the rest of real-time market
        data — this method exists now so the interface is complete."""

    # --- Orders (LIVE mode only — PAPER mode never calls these; see
    # app/core/config.py:TRADING_MODE and services in the execution engine) ---
    @abstractmethod
    async def place_order(self, access_token: str, order: dict[str, Any]) -> BrokerCallResult:
        ...

    @abstractmethod
    async def modify_order(self, access_token: str, order: dict[str, Any]) -> BrokerCallResult:
        """Modify an open/pending broker order; callers must reconcile the result."""
        ...

    @abstractmethod
    async def cancel_order(self, access_token: str, order_id: str) -> BrokerCallResult:
        """Request broker cancellation; callers must verify the resulting state."""
        ...

    @abstractmethod
    async def get_order_status(self, access_token: str, order_id: str) -> BrokerCallResult:
        ...

    @abstractmethod
    async def get_order_trades(self, access_token: str, order_id: str) -> BrokerCallResult:
        """Return broker-reported fills/trades for one order; caller reconciles them safely."""
        ...

    @abstractmethod
    async def get_order_history(
        self, access_token: str, order_id: str | None = None, tag: str | None = None
    ) -> BrokerCallResult:
        """Read order status history by broker order ID and/or stable tag."""
        ...

    @abstractmethod
    async def get_order_book(self, access_token: str) -> BrokerCallResult:
        ...

    # --- Positions & holdings ---
    @abstractmethod
    async def get_funds_and_margin(self, access_token: str) -> BrokerCallResult:
        """Return the broker-reported funds and margin snapshot."""
        ...

    @abstractmethod
    async def get_margin_details(
        self, access_token: str, instruments: list[dict[str, Any]]
    ) -> BrokerCallResult:
        """Return estimated broker margin for one or more proposed instruments."""
        ...

    @abstractmethod
    async def get_brokerage_details(
        self, access_token: str, *, instrument_token: str, quantity: int,
        product: str, transaction_type: str, price: float
    ) -> BrokerCallResult:
        """Return an explicitly estimated charge breakdown for one trade."""
        ...

    @abstractmethod
    async def get_positions(self, access_token: str) -> BrokerCallResult:
        ...

    @abstractmethod
    async def get_holdings(self, access_token: str) -> BrokerCallResult:
        ...
