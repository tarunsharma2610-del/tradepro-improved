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

    async def get_full_quote(self, access_token: str, instrument_keys: list[str]) -> BrokerCallResult:
        """Optional full quote snapshot, including exchange timestamps when supported."""
        return BrokerCallResult(ok=False, error=f"{self.broker_name} adapter does not implement full quotes.")

    async def get_option_chain(
        self, access_token: str, instrument_key: str, expiry_date: str
    ) -> BrokerCallResult:
        """Optional option-chain snapshot capability."""
        return BrokerCallResult(ok=False, error=f"{self.broker_name} adapter does not implement option chains.")

    async def get_intraday_data(
        self, access_token: str, instrument_key: str, unit: str, interval: str
    ) -> BrokerCallResult:
        """Fetch current-session candles when the broker exposes a dedicated endpoint.

        Optional capability: adapters without a dedicated intraday endpoint
        return a typed unsupported result instead of inventing fallback data.
        """
        return BrokerCallResult(ok=False, error=f"{self.broker_name} adapter does not implement intraday candles.")

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
    async def get_order_status(self, access_token: str, order_id: str) -> BrokerCallResult:
        ...

    @abstractmethod
    async def get_order_book(self, access_token: str) -> BrokerCallResult:
        ...

    # --- Positions & holdings ---
    @abstractmethod
    async def get_positions(self, access_token: str) -> BrokerCallResult:
        ...

    @abstractmethod
    async def get_holdings(self, access_token: str) -> BrokerCallResult:
        ...
