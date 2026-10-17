from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class EquityPointOut(BaseModel):
    timestamp: datetime
    cash_balance: Decimal


class PortfolioAnalyticsOut(BaseModel):
    total_realized_pnl: Decimal
    total_trades: int
    win_count: int
    loss_count: int
    win_rate_pct: Decimal | None
    best_trade_pnl: Decimal | None
    worst_trade_pnl: Decimal | None
    total_costs_paid: Decimal
    equity_curve: list[EquityPointOut]
    equity_curve_note: str = (
        "Cash balance over time from realized trades only -- does not include "
        "unrealized gains or losses on positions still open."
    )


class StrategyAnalyticsOut(BaseModel):
    strategy_id: UUID
    strategy_name: str
    is_active: bool
    total_trades: int
    win_count: int
    loss_count: int
    total_realized_pnl: Decimal
