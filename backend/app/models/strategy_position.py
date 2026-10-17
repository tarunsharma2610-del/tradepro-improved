import uuid

from sqlalchemy import ForeignKey, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class StrategyPosition(BaseModel):
    """Position allocation owned by one strategy, separate from the
    portfolio-wide fungible Position used for cash and aggregate accounting."""

    __tablename__ = "strategy_positions"

    strategy_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("strategies.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("instruments.id"), index=True, nullable=False
    )

    quantity: Mapped[int] = mapped_column(default=0, nullable=False)
    avg_price: Mapped[float] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    realized_pnl: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
