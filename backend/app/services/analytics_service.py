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

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.models.live_charge_adjustment import LiveChargeAdjustment
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
    # This is the virtual portfolio view: live broker fills must never
    # change its cash curve or be mixed into paper performance statistics.
    executions = (
        db.query(Execution)
        .join(Order, Order.id == Execution.order_id)
        .filter(
            Execution.portfolio_id == portfolio_id,
            Order.trading_mode == "PAPER",
        )
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
            .filter(
                Order.strategy_id == strategy.id,
                Order.trading_mode == "PAPER",
            )
            .all()
        )
        strategy_pnls = [
            Decimal(str(e.strategy_realized_pnl if e.strategy_realized_pnl is not None else e.realized_pnl))
            for e in executions
        ]
        closing_pnls = [pnl for pnl in strategy_pnls if pnl != 0]
        results.append(
            StrategyAnalytics(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                is_active=strategy.is_active,
                total_trades=len(closing_pnls),
                win_count=sum(1 for pnl in closing_pnls if pnl > 0),
                loss_count=sum(1 for pnl in closing_pnls if pnl < 0),
                total_realized_pnl=sum(closing_pnls, Decimal("0")),
            )
        )
    return results


@dataclass
class LivePortfolioAnalytics:
    """Broker-confirmed live fill metrics; deliberately no synthetic cash curve."""

    total_gross_realized_pnl: Decimal
    total_net_realized_pnl: Decimal
    total_fills: int
    profitable_fills: int
    unprofitable_fills: int
    win_rate_pct: Decimal | None
    best_fill_net_pnl: Decimal | None
    worst_fill_net_pnl: Decimal | None
    total_effective_costs: Decimal


def live_portfolio_analytics(db: Session, portfolio_id: UUID) -> LivePortfolioAnalytics:
    """Calculate live-only net P&L using immutable executions plus charge deltas.

    The broker connection is authoritative for actual cash. This method
    intentionally does not reconstruct a cash/equity curve or include PAPER
    executions. Each fill's effective costs equal original execution charges
    plus all append-only adjustment deltas for that execution.
    """
    executions = (
        db.query(Execution)
        .join(Order, Order.id == Execution.order_id)
        .filter(
            Execution.portfolio_id == portfolio_id,
            Order.trading_mode == "LIVE",
            Execution.broker_connection_id.isnot(None),
            Execution.broker_trade_id.isnot(None),
        )
        .order_by(Execution.executed_at)
        .all()
    )
    if not executions:
        return LivePortfolioAnalytics(
            total_gross_realized_pnl=Decimal("0.00"),
            total_net_realized_pnl=Decimal("0.00"),
            total_fills=0,
            profitable_fills=0,
            unprofitable_fills=0,
            win_rate_pct=None,
            best_fill_net_pnl=None,
            worst_fill_net_pnl=None,
            total_effective_costs=Decimal("0.00"),
        )

    execution_ids = [execution.id for execution in executions]
    adjustment_rows = (
        db.query(
            LiveChargeAdjustment.execution_id,
            func.coalesce(func.sum(LiveChargeAdjustment.charge_delta), 0),
        )
        .filter(LiveChargeAdjustment.execution_id.in_(execution_ids))
        .group_by(LiveChargeAdjustment.execution_id)
        .all()
    )
    charge_deltas = {
        execution_id: Decimal(str(delta or 0))
        for execution_id, delta in adjustment_rows
    }

    gross_pnl = Decimal("0.00")
    effective_costs = Decimal("0.00")
    net_by_fill: list[Decimal] = []
    for execution in executions:
        gross = Decimal(str(execution.realized_pnl))
        base_charges = Decimal(str(execution.total_charges))
        effective_charge_total = base_charges + charge_deltas.get(execution.id, Decimal("0.00"))
        if effective_charge_total < 0:
            # Corrupt ledger state must not be silently presented as profit.
            raise ValueError("Effective live execution charges cannot be negative.")
        gross_pnl += gross
        effective_costs += effective_charge_total
        net_by_fill.append((gross - effective_charge_total).quantize(Decimal("0.01")))

    wins = sum(1 for value in net_by_fill if value > 0)
    losses = sum(1 for value in net_by_fill if value < 0)
    decisive = wins + losses
    return LivePortfolioAnalytics(
        total_gross_realized_pnl=gross_pnl.quantize(Decimal("0.01")),
        total_net_realized_pnl=sum(net_by_fill, Decimal("0.00")).quantize(Decimal("0.01")),
        total_fills=len(executions),
        profitable_fills=wins,
        unprofitable_fills=losses,
        win_rate_pct=(Decimal(wins) / Decimal(decisive) * 100).quantize(Decimal("0.01")) if decisive else None,
        best_fill_net_pnl=max(net_by_fill, default=None),
        worst_fill_net_pnl=min(net_by_fill, default=None),
        total_effective_costs=effective_costs.quantize(Decimal("0.01")),
    )
