"""Portfolio-level risk checks shared by manual and strategy order entry.

Limits are configured by each portfolio owner. Unset limits do not apply;
the entire control set is inactive until explicitly enabled. Exposure is a
conservative mark-to-cost estimate (absolute quantity × average entry price),
not broker margin or liquidation value.
"""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.position import Position


def check_portfolio_order(
    db: Session,
    portfolio: Portfolio,
    instrument: Instrument,
    *,
    side: str,
    quantity: int,
    estimated_price: Decimal,
    reducing_position: bool = False,
    check_order_count: bool = True,
) -> str | None:
    """Return a human-readable rejection reason, or None when allowed."""
    if not portfolio.risk_controls_enabled:
        return None

    order_value = Decimal(quantity) * estimated_price
    if not order_value.is_finite() or order_value <= 0:
        return "Portfolio risk check could not validate the estimated order value."

    # Always permit orders that reduce an existing position so a risk limit
    # cannot trap a user in a position or prevent a strategy exit.
    if reducing_position:
        return None

    if portfolio.max_order_value is not None and order_value > Decimal(str(portfolio.max_order_value)):
        return f"Portfolio risk limit: estimated order value ₹{order_value:.2f} exceeds per-order cap ₹{portfolio.max_order_value}."

    now = datetime.now(timezone.utc)
    today = now.date()

    if portfolio.max_daily_loss is not None:
        realized_pnl = (
            db.query(func.coalesce(func.sum(Execution.realized_pnl), 0))
            .filter(Execution.portfolio_id == portfolio.id)
            .filter(func.date(Execution.executed_at) == today)
            .scalar()
        )
        realized_pnl = Decimal(str(realized_pnl))
        loss = max(Decimal("0"), -realized_pnl)
        if loss >= Decimal(str(portfolio.max_daily_loss)):
            return f"Portfolio risk limit: daily realized loss ₹{loss:.2f} has reached cap ₹{portfolio.max_daily_loss}."

    if check_order_count and portfolio.max_orders_per_day is not None:
        orders_today = (
            db.query(func.count(Order.id))
            .filter(Order.portfolio_id == portfolio.id)
            .filter(func.date(Order.placed_at) == today)
            .filter(Order.status != "CANCELLED")
            .scalar()
        )
        if int(orders_today or 0) >= portfolio.max_orders_per_day:
            return f"Portfolio risk limit: daily order cap of {portfolio.max_orders_per_day} has been reached."

    positions = (
        db.query(Position)
        .filter(Position.portfolio_id == portfolio.id, Position.quantity != 0)
        .all()
    )
    open_positions = len(positions)
    existing_exposure = sum(
        (abs(Decimal(str(p.quantity))) * abs(Decimal(str(p.avg_price))) for p in positions),
        Decimal("0"),
    )
    current_position = next((p for p in positions if p.instrument_id == instrument.id), None)
    if (
        portfolio.max_open_positions is not None
        and current_position is None
        and open_positions >= portfolio.max_open_positions
    ):
        return f"Portfolio risk limit: maximum {portfolio.max_open_positions} open positions reached."

    if portfolio.max_open_exposure is not None:
        projected_exposure = existing_exposure + order_value
        if projected_exposure > Decimal(str(portfolio.max_open_exposure)):
            return (
                f"Portfolio risk limit: estimated exposure ₹{projected_exposure:.2f} "
                f"would exceed cap ₹{portfolio.max_open_exposure}."
            )

    return None
