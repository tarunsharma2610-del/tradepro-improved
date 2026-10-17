"""track strategy-owned position allocations and strategy-specific realized P&L

Revision ID: 202610170003
Revises: 202610170002
Create Date: 2026-10-17
"""
from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP


revision = "202610170003"
down_revision = "202610170002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("executions", sa.Column("strategy_realized_pnl", sa.Numeric(18, 2), nullable=True))
    op.create_table(
        "strategy_positions",
        sa.Column("strategy_id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("realized_pnl", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_id", name="uq_strategy_position_strategy_id"),
    )
    op.create_index("ix_strategy_positions_portfolio_id", "strategy_positions", ["portfolio_id"], unique=False)
    op.create_index("ix_strategy_positions_instrument_id", "strategy_positions", ["instrument_id"], unique=False)

    # Backfill strategy-specific P&L and any still-open strategy allocations
    # before the new execution service begins relying on this table.
    executions = sa.table(
        "executions",
        sa.column("id", sa.Uuid()),
        sa.column("order_id", sa.Uuid()),
        sa.column("side", sa.String()),
        sa.column("quantity", sa.Integer()),
        sa.column("price", sa.Numeric(18, 4)),
        sa.column("executed_at", sa.DateTime(timezone=True)),
        sa.column("strategy_realized_pnl", sa.Numeric(18, 2)),
    )
    orders = sa.table(
        "orders",
        sa.column("id", sa.Uuid()),
        sa.column("strategy_id", sa.Uuid()),
    )
    strategies = sa.table(
        "strategies",
        sa.column("id", sa.Uuid()),
        sa.column("portfolio_id", sa.Uuid()),
        sa.column("instrument_id", sa.Uuid()),
    )
    strategy_positions = sa.table(
        "strategy_positions",
        sa.column("id", sa.Uuid()),
        sa.column("strategy_id", sa.Uuid()),
        sa.column("portfolio_id", sa.Uuid()),
        sa.column("instrument_id", sa.Uuid()),
        sa.column("quantity", sa.Integer()),
        sa.column("avg_price", sa.Numeric(18, 4)),
        sa.column("realized_pnl", sa.Numeric(18, 2)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    bind = op.get_bind()
    rows = bind.execute(
        sa.select(
            orders.c.strategy_id,
            executions.c.id,
            executions.c.side,
            executions.c.quantity,
            executions.c.price,
        )
        .select_from(executions.join(orders, orders.c.id == executions.c.order_id))
        .where(orders.c.strategy_id.is_not(None))
        .order_by(orders.c.strategy_id, executions.c.executed_at, executions.c.id)
    ).mappings()

    states = {}
    for row in rows:
        strategy_id = row["strategy_id"]
        state = states.setdefault(
            strategy_id,
            {"quantity": 0, "avg_price": Decimal("0"), "realized_pnl": Decimal("0")},
        )
        quantity = int(row["quantity"])
        price = Decimal(str(row["price"]))
        side = row["side"]
        signed_fill = quantity if side == "BUY" else -quantity
        old_quantity = state["quantity"]
        new_quantity = old_quantity + signed_fill
        same_direction_or_flat = old_quantity == 0 or ((old_quantity > 0) == (signed_fill > 0))

        if same_direction_or_flat:
            total_cost = abs(old_quantity) * state["avg_price"] + quantity * price
            new_avg_price = total_cost / abs(new_quantity) if new_quantity else Decimal("0")
            realized_pnl = Decimal("0.00")
        else:
            closing_quantity = min(quantity, abs(old_quantity))
            if old_quantity > 0:
                pnl = (price - state["avg_price"]) * closing_quantity
            else:
                pnl = (state["avg_price"] - price) * closing_quantity
            realized_pnl = pnl.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if new_quantity == 0:
                new_avg_price = Decimal("0")
            elif (old_quantity > 0) != (new_quantity > 0):
                new_avg_price = price
            else:
                new_avg_price = state["avg_price"]

        state["quantity"] = new_quantity
        state["avg_price"] = new_avg_price
        state["realized_pnl"] += realized_pnl
        bind.execute(
            executions.update()
            .where(executions.c.id == row["id"])
            .values(strategy_realized_pnl=realized_pnl)
        )

    now = datetime.now(timezone.utc)
    for strategy_id, state in states.items():
        strategy = bind.execute(
            sa.select(strategies.c.portfolio_id, strategies.c.instrument_id)
            .where(strategies.c.id == strategy_id)
        ).first()
        if strategy is None:
            continue
        bind.execute(
            strategy_positions.insert().values(
                id=uuid.uuid4(),
                strategy_id=strategy_id,
                portfolio_id=strategy.portfolio_id,
                instrument_id=strategy.instrument_id,
                quantity=state["quantity"],
                avg_price=state["avg_price"],
                realized_pnl=state["realized_pnl"],
                created_at=now,
                updated_at=now,
            )
        )


def downgrade() -> None:
    op.drop_index("ix_strategy_positions_instrument_id", table_name="strategy_positions")
    op.drop_index("ix_strategy_positions_portfolio_id", table_name="strategy_positions")
    op.drop_table("strategy_positions")
    op.drop_column("executions", "strategy_realized_pnl")
