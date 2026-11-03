import uuid

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerPortfolioAllocation(BaseModel):
    """Exclusive, owner-scoped link between one broker account and one LIVE portfolio.

    This is an allocation boundary only. It does not itself verify broker funds,
    synchronize positions, or enable broker order writes.
    """

    __tablename__ = "broker_portfolio_allocations"
    __table_args__ = (
        UniqueConstraint("broker_connection_id", name="uq_broker_portfolio_allocation_connection"),
        UniqueConstraint("portfolio_id", name="uq_broker_portfolio_allocation_portfolio"),
        CheckConstraint("trading_mode = 'LIVE'", name="ck_broker_portfolio_allocation_live_only"),
        ForeignKeyConstraint(
            ["broker_connection_id", "user_id"],
            ["broker_connections.id", "broker_connections.user_id"],
            name="fk_broker_portfolio_allocation_connection_owner",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["portfolios.id", "portfolios.user_id"],
            name="fk_broker_portfolio_allocation_portfolio_owner",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["portfolio_id", "trading_mode"],
            ["portfolios.id", "portfolios.trading_mode"],
            name="fk_broker_portfolio_allocation_live_portfolio",
            ondelete="CASCADE",
        ),
    )

    broker_connection_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    trading_mode: Mapped[str] = mapped_column(default="LIVE", server_default="LIVE", nullable=False)
