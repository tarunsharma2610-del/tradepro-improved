from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    virtual_capital: Decimal = Field(gt=0, le=Decimal("1000000000"))


class PortfolioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    virtual_capital: Decimal
    cash_balance: Decimal
    created_at: datetime
