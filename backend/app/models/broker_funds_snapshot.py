import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, JSON, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerFundsSnapshot(BaseModel):
    """Immutable normalized copy of a broker funds response.

    Trading margin is deliberately not written into Portfolio.cash_balance:
    available margin is not equivalent to withdrawable cash or net liquidation value.
    """

    __tablename__ = "broker_funds_snapshots"

    broker_connection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    total_available_to_trade: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cash_available_to_trade: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    pledge_available_to_trade: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    unsettled_profit_today: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    unsettled_profit_previous_days: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    raw_response: Mapped[dict] = mapped_column(JSON, nullable=False)
