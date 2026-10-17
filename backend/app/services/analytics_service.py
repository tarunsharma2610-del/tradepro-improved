"""
Deliberately honest about what it can and can't compute without a live
price: the equity curve here tracks realized cash balance over time
(every execution's net cash impact, replayed in order), not total mark-
to-market portfolio value -- that would need a historical price at every
point in time, which this phase doesn't have. Labeled as such in the
response, not silently presented as more complete than it is.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.models.order import Order
from app.models.strategy import Strategy


@dataclass
class EquityPoint:
    timestamp: datetime
    cash_balance: Decimal


@dataclass
class PortfolioAnalytics:
    total_realized_pnl: Decimal
    total_trades: int
    win_count: int
    loss_count: int
    win_rate_pct: Decimal | None
    best_trade_pnl: Decimal | None
    worst_trade_pnl: Decimal | None
    total_costs_paid: Decimal
    equity_curve: list[EquityPoint]


@dataclass
class StrategyAnalytics:
    strategy_id: UUID
    strategy_name: str
    is_active: bool
    total_trades: int
    win_count: int
    loss_count: int
    total_realized_pnl: Decimal


def portfolio_analytics(db: Session, portfolio_id: UUID, initial_capital: Decimal) -> PortfolioAnalytics:
    executions = (
        db.query(Execution)
        .filter(Execution.portfolio_id == portfolio_id)
        .order_by(Execution.executed_at)
        .all()
    )

    closing = [e for e in executions if e.realized_pnl != 0]
    wins = [e for e in closing if e.realized_pnl > 0]
    losses = [e for e in closing if e.realized_pnl < 0]

    running_cash = initial_capital
    equity_curve = []
    total_costs = Decimal("0")
    for e in executions:
        # Reconstruct the same signed cash effect ExecutionService applied at
        # the time -- net_cash_impact isn't stored directly, but it's fully
        # derivable from gross_value/total_charges/side, which are.
        signed_gross = Decimal(str(e.gross_value)) if e.side == "SELL" else -Decimal(str(e.gross_value))
        signed_charges = -Decimal(str(e.total_charges))  # charges always reduce cash, regardless of side
        running_cash += signed_gross + signed_charges
        equity_curve.append(EquityPoint(timestamp=e.executed_at, cash_balance=running_cash))
        total_costs += Decimal(str(e.total_charges))

    return PortfolioAnalytics(
        total_realized_pnl=sum((Decimal(str(e.realized_pnl)) for e in closing), Decimal("0")),
        total_trades=len(closing),
        win_count=len(wins),
        loss_count=len(losses),
        win_rate_pct=(Decimal(len(wins)) / Decimal(len(closing)) * 100) if closing else None,
        best_trade_pnl=max((Decimal(str(e.realized_pnl)) for e in closing), default=None),
        worst_trade_pnl=min((Decimal(str(e.realized_pnl)) for e in closing), default=None),
        total_costs_paid=total_costs,
        equity_curve=equity_curve,
    )


def strategy_analytics(db: Session, portfolio_id: UUID) -> list[StrategyAnalytics]:
    strategies = db.query(Strategy).filter(Strategy.portfolio_id == portfolio_id).all()
    results = []
    for strategy in strategies:
        executions = (
            db.query(Execution)
            .join(Order, Order.id == Execution.order_id)
            .filter(Order.strategy_id == strategy.id)
            .all()
        )
        closing = [e for e in executions if e.realized_pnl != 0]
        results.append(
            StrategyAnalytics(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                is_active=strategy.is_active,
                total_trades=len(closing),
                win_count=sum(1 for e in closing if e.realized_pnl > 0),
                loss_count=sum(1 for e in closing if e.realized_pnl < 0),
                total_realized_pnl=sum((Decimal(str(e.realized_pnl)) for e in closing), Decimal("0")),
            )
        )
    return results
