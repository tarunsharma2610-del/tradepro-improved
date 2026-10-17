import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Execution(BaseModel):
    """One row per fill. Orders can in principle have more than one fill
    (Phase 2 only ever produces exactly one, since it doesn't do partial
    fills yet — see ExecutionService) but the model doesn't assume that,
    so partial-fill support later is additive.

    Every cost component is stored individually, not just the total — the
    spec requires preserving gross P&L, transaction costs, and net P&L as
    distinct, auditable numbers, not a single collapsed figure."""

    __tablename__ = "executions"

    order_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    instrument_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("instruments.id"), index=True)
    instrument: Mapped["Instrument"] = relationship(lazy="joined")

    side: Mapped[str] = mapped_column(String(4), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    gross_value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    brokerage: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    stt: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    exchange_charges: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    sebi_charges: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    stamp_duty: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    gst: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    total_charges: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    # Realized P&L attributable to THIS fill specifically (0 for fills that
    # open/add to a position rather than close one) — see position_math.py.
    realized_pnl: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    # Strategy-specific realized P&L uses the strategy allocation basis; NULL
    # on legacy/manual fills, with legacy strategy rows falling back to realized_pnl.
    strategy_realized_pnl: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)

    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
