from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.instrument import InstrumentBrief


class StrategyCreate(BaseModel):
    instrument_id: UUID
    name: str = Field(min_length=1, max_length=100)
    segment: str = Field(pattern="^(EQUITY_DELIVERY|EQUITY_INTRADAY|FUTURES|OPTIONS)$")
    quantity: int = Field(gt=0)

    rsi_weight: Decimal = Decimal("1")
    sma_crossover_weight: Decimal = Decimal("1")
    macd_weight: Decimal = Decimal("1")
    volume_spike_weight: Decimal = Decimal("1")
    momentum_weight: Decimal = Decimal("1")

    entry_score_threshold: Decimal = Field(default=Decimal("0.5"), ge=-1, le=1)
    exit_score_threshold: Decimal = Field(default=Decimal("-0.3"), ge=-1, le=1)
    trailing_stop_pct: Decimal = Field(default=Decimal("2"), gt=0, le=50)
    max_daily_loss: Decimal = Field(gt=0)


class StrategyUpdate(BaseModel):
    """Same fields as create, all optional — PATCH-style partial update.
    is_active is deliberately separate (see the activate/deactivate
    endpoints) so flipping a strategy on/off is one obvious action, not
    buried in a general-purpose update payload."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    quantity: int | None = Field(default=None, gt=0)
    rsi_weight: Decimal | None = None
    sma_crossover_weight: Decimal | None = None
    macd_weight: Decimal | None = None
    volume_spike_weight: Decimal | None = None
    momentum_weight: Decimal | None = None
    entry_score_threshold: Decimal | None = Field(default=None, ge=-1, le=1)
    exit_score_threshold: Decimal | None = Field(default=None, ge=-1, le=1)
    trailing_stop_pct: Decimal | None = Field(default=None, gt=0, le=50)
    max_daily_loss: Decimal | None = Field(default=None, gt=0)


class StrategyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    instrument: InstrumentBrief
    name: str
    segment: str
    quantity: int
    is_active: bool
    rsi_weight: Decimal
    sma_crossover_weight: Decimal
    macd_weight: Decimal
    volume_spike_weight: Decimal
    momentum_weight: Decimal
    entry_score_threshold: Decimal
    exit_score_threshold: Decimal
    trailing_stop_pct: Decimal
    max_daily_loss: Decimal
    paused_until: date | None
    current_watermark: Decimal | None
    last_evaluated_at: datetime | None
    created_at: datetime


class StrategyEvaluationOut(BaseModel):
    strategy_id: str
    signal: str
    reason: str
    order_id: str | None
