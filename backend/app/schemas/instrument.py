from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InstrumentBrief(BaseModel):
    """Embedded in position/order/execution responses so the frontend
    never has to do a separate lookup per instrument_id."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trading_symbol: str
    exchange: str


class InstrumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    instrument_key: str
    exchange: str
    segment: str
    instrument_type: str
    trading_symbol: str
    name: str
    lot_size: int
    expiry: date | None = None
    strike_price: float | None = None
    option_type: str | None = None
