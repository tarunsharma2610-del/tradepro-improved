from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    virtual_capital: Decimal = Field(gt=0, le=Decimal("1000000000"))


class PortfolioRiskSettings(BaseModel):
    risk_controls_enabled: bool = False
    max_daily_loss: Decimal | None = Field(default=None, gt=0, le=Decimal("1000000000"))
    max_open_exposure: Decimal | None = Field(default=None, gt=0, le=Decimal("1000000000"))
    max_order_value: Decimal | None = Field(default=None, gt=0, le=Decimal("1000000000"))
    max_open_positions: int | None = Field(default=None, ge=1, le=10000)
    max_orders_per_day: int | None = Field(default=None, ge=1, le=100000)

    @model_validator(mode="after")
    def require_a_limit_when_enabled(self):
        limits = (
            self.max_daily_loss, self.max_open_exposure, self.max_order_value,
            self.max_open_positions, self.max_orders_per_day,
        )
        if self.risk_controls_enabled and not any(value is not None for value in limits):
            raise ValueError("Enable at least one risk limit, or leave risk controls disabled.")
        return self


class PortfolioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    virtual_capital: Decimal
    cash_balance: Decimal
    risk_controls_enabled: bool = False
    max_daily_loss: Decimal | None = None
    max_open_exposure: Decimal | None = None
    max_order_value: Decimal | None = None
    max_open_positions: int | None = None
    max_orders_per_day: int | None = None
    created_at: datetime
