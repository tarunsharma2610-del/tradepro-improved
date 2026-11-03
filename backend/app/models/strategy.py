import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Strategy(BaseModel):
    """The 'no-code strategy builder' is this row: every field here is
    something the frontend builder form sets through plain inputs, not
    something requiring the user to write code. `current_watermark` and
    `paused_until` are engine-managed state, not user-set config — see
    services/strategy_execution_service.py."""

    __tablename__ = "strategies"
    __table_args__ = (
        CheckConstraint(
            "((last_quote_epoch IS NULL AND last_quote_version IS NULL "
            "AND last_quote_received_at IS NULL AND last_quote_exchange_timestamp_ms IS NULL) "
            "OR (last_quote_epoch IS NOT NULL AND length(last_quote_epoch) BETWEEN 1 AND 128 "
            "AND last_quote_version IS NOT NULL AND last_quote_version > 0 "
            "AND last_quote_received_at IS NOT NULL "
            "AND last_quote_exchange_timestamp_ms IS NOT NULL "
            "AND last_quote_exchange_timestamp_ms > 0))",
            name="ck_strategies_quote_identity_complete",
        ),
    )

    portfolio_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    instrument_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("instruments.id"), index=True)
    instrument: Mapped["Instrument"] = relationship(lazy="joined")

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    segment: Mapped[str] = mapped_column(String(20), nullable=False)  # feeds the cost engine on every fill
    quantity: Mapped[int] = mapped_column(nullable=False)  # fixed size per entry — see README known limitations
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Indicator weights — 0 disables that indicator for this strategy.
    rsi_weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1, nullable=False)
    sma_crossover_weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1, nullable=False)
    macd_weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1, nullable=False)
    volume_spike_weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1, nullable=False)
    momentum_weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1, nullable=False)

    entry_score_threshold: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5, nullable=False)
    exit_score_threshold: Mapped[float] = mapped_column(Numeric(4, 2), default=-0.3, nullable=False)
    trailing_stop_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=2, nullable=False)

    # --- Risk management ---
    max_daily_loss: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    paused_until: Mapped[date | None] = mapped_column(Date, nullable=True)  # set when max_daily_loss is hit

    # --- Engine state (not user-configured) ---
    current_watermark: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_quote_epoch: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_quote_version: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_quote_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_quote_exchange_timestamp_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
