import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class PaperStopEvent(BaseModel):
    """Durable idempotency/claim record for a PAPER stop observation.

    This table is intentionally storage-only: no worker currently creates
    events and no state here can authorize broker order writes.
    """

    __tablename__ = "paper_stop_events"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    strategy_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    instrument_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False)

    event_type: Mapped[str] = mapped_column(String(32), nullable=False, default="TRAILING_STOP")
    quote_epoch: Mapped[str] = mapped_column(String(128), nullable=False)
    quote_version: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)

    state: Mapped[str] = mapped_column(String(20), nullable=False, default="CLAIMED")
    claim_token: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    claimed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "strategy_id", "event_type", "quote_epoch", "quote_version",
            name="uq_paper_stop_event_strategy_quote",
        ),
        CheckConstraint(
            "event_type IN ('TRAILING_STOP')",
            name="ck_paper_stop_event_type",
        ),
        CheckConstraint(
            "state IN ('CLAIMED', 'EXECUTING', 'COMPLETED', 'RETRYABLE', 'FAILED')",
            name="ck_paper_stop_event_state",
        ),
        CheckConstraint("quote_version > 0", name="ck_paper_stop_event_quote_version"),
        CheckConstraint("trigger_price > 0", name="ck_paper_stop_event_trigger_price"),
        CheckConstraint("attempt_count >= 0", name="ck_paper_stop_event_attempt_count"),
        Index("ix_paper_stop_events_user_state", "user_id", "state"),
        Index("ix_paper_stop_events_portfolio_instrument", "portfolio_id", "instrument_id"),
        Index("ix_paper_stop_events_claimed_until", "state", "claimed_until"),
    )
