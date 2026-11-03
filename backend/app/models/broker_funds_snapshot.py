import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, JSON, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerFundsSnapshot(BaseModel):
    """Immutable normalized copy of a broker funds response.

    Trading margin is deliberately not written into Portfolio.cash_balance:
    available margin is not equivalent to withdrawable cash or net liquidation value.
    """

    __tablename__ = "broker_funds_snapshots"
    __table_args__ = (
        CheckConstraint("trading_mode = 'LIVE'", name="ck_broker_funds_snapshot_live_only"),
        ForeignKeyConstraint(
            ["broker_connection_id", "user_id"],
            ["broker_connections.id", "broker_connections.user_id"],
            name="fk_broker_funds_snapshot_connection_owner",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["portfolios.id", "portfolios.user_id"],
            name="fk_broker_funds_snapshot_portfolio_owner",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["portfolio_id", "trading_mode"],
            ["portfolios.id", "portfolios.trading_mode"],
            name="fk_broker_funds_snapshot_live_portfolio",
            ondelete="CASCADE",
        ),
    )

    broker_connection_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    trading_mode: Mapped[str] = mapped_column(default="LIVE", server_default="LIVE", nullable=False)
    total_available_to_trade: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cash_available_to_trade: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    pledge_available_to_trade: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    unsettled_profit_today: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    unsettled_profit_previous_days: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    raw_response: Mapped[dict] = mapped_column(JSON, nullable=False)
