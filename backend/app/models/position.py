import uuid

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Position(BaseModel):
    """One row per (portfolio, instrument). `quantity` is signed: positive
    is long, negative is short — this is what lets the same model handle
    intraday short-selling and, later, option writing, without a separate
    "short position" table. See services/position_math.py for the fill
    logic that updates this."""

    __tablename__ = "positions"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    instrument_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("instruments.id"), index=True)
    instrument: Mapped["Instrument"] = relationship(lazy="joined")

    quantity: Mapped[int] = mapped_column(default=0, nullable=False)
    avg_price: Mapped[float] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    realized_pnl: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    __table_args__ = (UniqueConstraint("portfolio_id", "instrument_id", name="uq_position_portfolio_instrument"),)
