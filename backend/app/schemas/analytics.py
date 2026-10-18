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


class LivePortfolioAnalyticsOut(BaseModel):
    total_gross_realized_pnl: Decimal
    total_net_realized_pnl: Decimal
    total_fills: int
    profitable_fills: int
    unprofitable_fills: int
    win_rate_pct: Decimal | None
    best_fill_net_pnl: Decimal | None
    worst_fill_net_pnl: Decimal | None
    total_effective_costs: Decimal
    accounting_note: str = (
        "Live-only metrics from broker-confirmed fills. Net P&L subtracts original "
        "execution charges and append-only charge adjustments. This is not broker cash "
        "or a mark-to-market equity curve; broker account balances remain authoritative."
    )
