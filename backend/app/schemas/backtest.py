from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.instrument import InstrumentBrief


class BacktestCreate(BaseModel):
    instrument_id: UUID
    name: str = Field(min_length=1, max_length=100)
    segment: str = Field(pattern="^(EQUITY_DELIVERY|EQUITY_INTRADAY|FUTURES|OPTIONS)$")
    from_date: date
    to_date: date
    initial_capital: Decimal = Field(gt=0)
    quantity: int = Field(gt=0)

    rsi_weight: Decimal = Decimal("1")
    sma_crossover_weight: Decimal = Decimal("1")
    macd_weight: Decimal = Decimal("1")
    volume_spike_weight: Decimal = Decimal("1")
    momentum_weight: Decimal = Decimal("1")

    entry_score_threshold: Decimal = Field(default=Decimal("0.5"), ge=-1, le=1)
    exit_score_threshold: Decimal = Field(default=Decimal("-0.3"), ge=-1, le=1)
    trailing_stop_pct: Decimal = Field(default=Decimal("2"), gt=0, le=50)
    slippage_bps: Decimal = Field(default=Decimal("5"), ge=0, le=200)


class BacktestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    instrument: InstrumentBrief
    name: str
    segment: str
    from_date: date
    to_date: date
    initial_capital: Decimal
    quantity: int
    entry_score_threshold: Decimal
    exit_score_threshold: Decimal
    trailing_stop_pct: Decimal
    slippage_bps: Decimal
    status: str
    error_message: str | None
    final_capital: Decimal | None
    net_pnl: Decimal | None
    max_drawdown_pct: Decimal | None
    total_trades: int
    win_count: int
    loss_count: int
    candles_evaluated: int
    created_at: datetime
    completed_at: datetime | None


class BacktestTradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    side: str
    quantity: int
    price: Decimal
    gross_value: Decimal
    total_charges: Decimal
    realized_pnl: Decimal
    candle_index: int
    executed_at: datetime | None
