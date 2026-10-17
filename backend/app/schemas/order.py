from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.instrument import InstrumentBrief


class PlaceOrderRequest(BaseModel):
    instrument_id: UUID
    side: str = Field(pattern="^(BUY|SELL)$")
    order_type: str = Field(pattern="^(MARKET|LIMIT)$")
    segment: str = Field(pattern="^(EQUITY_DELIVERY|EQUITY_INTRADAY|FUTURES|OPTIONS)$")
    quantity: int = Field(gt=0)
    limit_price: Decimal | None = None

    @field_validator("limit_price")
    @classmethod
    def limit_price_required_for_limit_orders(cls, v, info):
        if info.data.get("order_type") == "LIMIT" and v is None:
            raise ValueError("limit_price is required for LIMIT orders")
        return v


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    instrument: InstrumentBrief
    side: str
    order_type: str
    segment: str
    quantity: int
    limit_price: Decimal | None
    status: str
    rejection_reason: str | None
    execution_reason: str
    placed_at: datetime
    filled_at: datetime | None


class PositionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    instrument: InstrumentBrief
    quantity: int
    avg_price: Decimal
    realized_pnl: Decimal


class ExecutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    instrument: InstrumentBrief
    side: str
    quantity: int
    price: Decimal
    gross_value: Decimal
    brokerage: Decimal
    stt: Decimal
    exchange_charges: Decimal
    sebi_charges: Decimal
    stamp_duty: Decimal
    gst: Decimal
    total_charges: Decimal
    realized_pnl: Decimal
    executed_at: datetime
