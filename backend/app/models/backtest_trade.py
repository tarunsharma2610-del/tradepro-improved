import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BacktestTrade(BaseModel):
    """One row per simulated fill. Deliberately shaped like Execution
    (same cost components, same realized_pnl field) rather than a
    collapsed summary row — a backtest's trade log should be exactly as
    auditable as a real one, not a lesser version of it."""

    __tablename__ = "backtest_trades"

    backtest_run_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("backtest_runs.id", ondelete="CASCADE"), index=True)

    side: Mapped[str] = mapped_column(String(4), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)  # after simulated slippage
    gross_value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    brokerage: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    stt: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    exchange_charges: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    sebi_charges: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    stamp_duty: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    gst: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    total_charges: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    realized_pnl: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    candle_index: Mapped[int] = mapped_column(nullable=False)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
