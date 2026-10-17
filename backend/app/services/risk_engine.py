"""
Deliberately its own module, not a method buried in strategy_execution_service
— the architecture rules list risk management as a separate concern from
strategies/backtesting, and keeping it separable means Phase 4's
backtester and later live trading can both run orders through the same
risk checks rather than each re-implementing them.

Phase 3 scope: one rule — a strategy that has lost more than
max_daily_loss today (realized P&L across today's executions from that
strategy) is paused until the next calendar day. More rules (max
concurrent positions across strategies, portfolio-wide daily loss limits)
are natural additions here later, not a redesign.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.core.config import settings
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.strategy import Strategy


@dataclass
class RiskCheckResult:
    allowed: bool
    reason: str | None = None


def check_can_enter(db: Session, strategy: Strategy) -> RiskCheckResult:
    today = datetime.now(timezone.utc).date()

    if strategy.paused_until is not None and strategy.paused_until >= today:
        return RiskCheckResult(allowed=False, reason=f"Strategy paused until {strategy.paused_until} (daily loss limit hit).")

    todays_loss = _realized_loss_today(db, strategy.id, today)
    if todays_loss >= Decimal(str(strategy.max_daily_loss)):
        return RiskCheckResult(allowed=False, reason=f"Strategy daily loss limit reached (₹{todays_loss} of ₹{strategy.max_daily_loss}).")

    portfolio = db.get(Portfolio, strategy.portfolio_id)
    limit_pct = Decimal(str(settings.PORTFOLIO_DAILY_LOSS_LIMIT_PCT))
    if portfolio is not None and limit_pct > 0:
        portfolio_loss = _realized_loss_today_for_portfolio(db, strategy.portfolio_id, today)
        portfolio_limit = Decimal(str(portfolio.virtual_capital)) * limit_pct / Decimal("100")
        if portfolio_loss >= portfolio_limit:
            return RiskCheckResult(
                allowed=False,
                reason=(
                    f"Portfolio daily loss limit reached (₹{portfolio_loss} of "
                    f"₹{portfolio_limit}, {limit_pct}% of starting capital). "
                    "Automated entries are blocked for all strategies in this portfolio."
                ),
            )

    return RiskCheckResult(allowed=True)


def pause_if_daily_loss_exceeded(db: Session, strategy: Strategy) -> bool:
    """Call after every exit fill. Returns True if the strategy was just
    paused. Pausing is a DB write the caller must still commit/save."""
    today = datetime.now(timezone.utc).date()
    todays_loss = _realized_loss_today(db, strategy.id, today)
    if todays_loss >= Decimal(str(strategy.max_daily_loss)):
        strategy.paused_until = today
        strategy.is_active = False
        return True
    return False


def _realized_loss_today(db: Session, strategy_id, today: date) -> Decimal:
    """Sum of realized losses (positive number = how much was lost) from
    this strategy's own executions today. Profitable days return 0, not a
    negative number — this is a loss magnitude, not raw P&L."""
    total_pnl = (
        db.query(func.coalesce(func.sum(func.coalesce(Execution.strategy_realized_pnl, Execution.realized_pnl)), 0))
        .join(Order, Order.id == Execution.order_id)
        .filter(Order.strategy_id == strategy_id)
        .filter(func.date(Execution.executed_at) == today)
        .scalar()
    )
    total_pnl = Decimal(str(total_pnl))
    return -total_pnl if total_pnl < 0 else Decimal("0")



def _realized_loss_today_for_portfolio(db: Session, portfolio_id, today: date) -> Decimal:
    """Return portfolio-wide realized loss magnitude for UTC today.

    Includes fills from manual and strategy orders, so one strategy cannot
    continue opening positions after other activity exhausts the daily loss
    budget. This only gates automated entries, not manual/live submission.
    """
    total_pnl = (
        db.query(func.coalesce(func.sum(Execution.realized_pnl), 0))
        .filter(Execution.portfolio_id == portfolio_id)
        .filter(func.date(Execution.executed_at) == today)
        .scalar()
    )
    total_pnl = Decimal(str(total_pnl))
    return -total_pnl if total_pnl < 0 else Decimal("0")
