from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BrokerConnectionCreate(BaseModel):
    """Body for POST /settings/broker — this is what replaces pasting keys
    into a .env file. broker is a string key ("upstox" today)."""

    broker: str = Field(default="upstox", max_length=50)
    api_key: str = Field(min_length=1, max_length=500)
    api_secret: str = Field(min_length=1, max_length=500)
    redirect_uri: str = Field(min_length=1, max_length=500)


class BrokerConnectionOut(BaseModel):
    """Never includes a decrypted secret — only a masked preview, exactly
    like a card-number field would. See core/encryption.py:mask_secret."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    broker: str
    api_key_masked: str
    is_connected: bool
    last_connected_at: datetime | None
    last_error: str | None
    created_at: datetime


class BrokerConnectionTestResult(BaseModel):
    success: bool
    message: str


class BrokerAuthorizeUrl(BaseModel):
    """Where to send the browser to complete the OAuth handshake with the
    broker (see app/brokers/upstox/adapter.py:get_authorize_url)."""

    authorize_url: str


class BrokerAnalyticsTokenSet(BaseModel):
    """Analytics Token copied by the user from Upstox Developer Apps; never returned."""

    analytics_token: str = Field(min_length=1, max_length=5000)


class BrokerAnalyticsTokenOut(BaseModel):
    configured: bool
    expires_at: datetime | None = None


class BrokerPortfolioAllocationCreate(BaseModel):
    broker_connection_id: UUID


class BrokerPortfolioAllocationOut(BaseModel):
    id: UUID
    portfolio_id: UUID
    broker_connection_id: UUID
    broker: str
    trading_mode: str
    created_at: datetime


class BrokerFundsSnapshotOut(BaseModel):
    id: UUID
    portfolio_id: UUID
    broker_connection_id: UUID
    total_available_to_trade: Decimal
    cash_available_to_trade: Decimal
    pledge_available_to_trade: Decimal
    unsettled_profit_today: Decimal
    unsettled_profit_previous_days: Decimal
    created_at: datetime
