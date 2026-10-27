from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

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
    def limit_price_must_be_positive_and_present_for_limit_orders(cls, v, info):
        if v is not None and v <= 0:
            raise ValueError("limit_price must be greater than zero")
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
    demat_transaction_charges: Decimal | None
    demat_charge_status: str
    total_charges: Decimal
    realized_pnl: Decimal
    executed_at: datetime

    @computed_field
    @property
    def total_charges_complete(self) -> bool:
        """Derive completeness from validated persisted charge values."""
        from app.services.execution_charge_totals import execution_charge_total_is_complete

        return execution_charge_total_is_complete(self)
