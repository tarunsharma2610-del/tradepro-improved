import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class BacktestRun(BaseModel):
    """Deliberately user-scoped, not portfolio-scoped — a backtest is a
    standalone what-if analysis, not a live trading account, so it never
    touches a real Portfolio's cash_balance or Position rows. It reuses
    the same calculation engine (see services/backtest_engine.py) without
    reusing the same storage, which would let a simulation contaminate
    real trading history."""

    __tablename__ = "backtest_runs"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    instrument_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("instruments.id"), index=True)
    instrument: Mapped["Instrument"] = relationship(lazy="joined")

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    segment: Mapped[str] = mapped_column(String(20), nullable=False)
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)

    initial_capital: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)

    rsi_weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1, nullable=False)
    sma_crossover_weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1, nullable=False)
    macd_weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1, nullable=False)
    volume_spike_weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1, nullable=False)
    momentum_weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1, nullable=False)
    entry_score_threshold: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5, nullable=False)
    exit_score_threshold: Mapped[float] = mapped_column(Numeric(4, 2), default=-0.3, nullable=False)
    trailing_stop_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=2, nullable=False)
    slippage_bps: Mapped[float] = mapped_column(Numeric(6, 2), default=5, nullable=False)

    status: Mapped[str] = mapped_column(String(15), nullable=False, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    final_capital: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    net_pnl: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    win_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loss_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    candles_evaluated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
