import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Order(BaseModel):
    """One conceptual order model for manual trading, auto/strategy
    trading, backtesting, and (later) live trading — see the "critical
    trading architecture rule" in ARCHITECTURE.md. `execution_reason` and
    `strategy_id` exist now, unused by anything but manual trading in
    Phase 2, specifically so Phase 3's strategy engine is additive rather
    than a schema migration plus a rewrite of this table."""

    __tablename__ = "orders"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    instrument_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("instruments.id"), index=True)
    instrument: Mapped["Instrument"] = relationship(lazy="joined")

    side: Mapped[str] = mapped_column(String(4), nullable=False)  # BUY, SELL
    order_type: Mapped[str] = mapped_column(String(10), nullable=False)  # MARKET, LIMIT
    segment: Mapped[str] = mapped_column(String(20), nullable=False)  # EQUITY_DELIVERY, EQUITY_INTRADAY, FUTURES, OPTIONS — drives the cost engine
    quantity: Mapped[int] = mapped_column(nullable=False)
    limit_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)

    status: Mapped[str] = mapped_column(String(15), nullable=False, default="PENDING")  # PENDING, FILLED, REJECTED, CANCELLED
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    trading_mode: Mapped[str] = mapped_column(String(5), nullable=False, default="PAPER")  # PAPER, LIVE — see app/core/config.py
    execution_reason: Mapped[str] = mapped_column(String(20), nullable=False, default="MANUAL")  # MANUAL today; STRATEGY/BACKTEST in later phases
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)  # populated starting Phase 3

    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
