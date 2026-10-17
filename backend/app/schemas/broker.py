from datetime import datetime
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
