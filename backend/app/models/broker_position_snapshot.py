import uuid

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerPositionSnapshot(BaseModel):
    """Immutable read-only broker position snapshot; never a paper Position row."""

    __tablename__ = "broker_position_snapshots"
    __table_args__ = (
        CheckConstraint("trading_mode = 'LIVE'", name="ck_broker_position_snapshot_live_only"),
        ForeignKeyConstraint(
            ["broker_connection_id", "user_id"],
            ["broker_connections.id", "broker_connections.user_id"],
            name="fk_broker_position_snapshot_connection_owner",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["portfolios.id", "portfolios.user_id"],
            name="fk_broker_position_snapshot_portfolio_owner",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["portfolio_id", "trading_mode"],
            ["portfolios.id", "portfolios.trading_mode"],
            name="fk_broker_position_snapshot_live_portfolio",
            ondelete="CASCADE",
        ),
    )

    broker_connection_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    trading_mode: Mapped[str] = mapped_column(default="LIVE", server_default="LIVE", nullable=False)
    positions: Mapped[list] = mapped_column(JSON, nullable=False)
    raw_response: Mapped[dict] = mapped_column(JSON, nullable=False)
