import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LiveAccountSafetyState(BaseModel):
    """Account-wide live safety state keyed by tenant and broker.

    Missing state is unsafe. New state starts with the kill switch tripped and
    no health timestamp, so a caller must explicitly health-check and manually
    reset before this state can report safe. Scope is independent of portfolios.
    """

    __tablename__ = "live_account_safety_states"
    __table_args__ = (
        UniqueConstraint("user_id", "broker", name="uq_live_account_safety_user_broker"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    broker: Mapped[str] = mapped_column(String(50), nullable=False)
    kill_switch_tripped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    kill_switch_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    kill_switch_tripped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    circuit_state: Mapped[str] = mapped_column(String(20), nullable=False, default="CLOSED")
    consecutive_broker_errors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    circuit_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    circuit_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_broker_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_broker_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_health_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class LiveAccountSafetyEvent(BaseModel):
    """Append-only audit and idempotency record for live safety state changes."""

    __tablename__ = "live_account_safety_events"
    __table_args__ = (
        UniqueConstraint(
            "state_id", "idempotency_key",
            name="uq_live_account_safety_event_idempotency",
        ),
    )

    state_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("live_account_safety_states.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    consecutive_broker_errors: Mapped[int] = mapped_column(Integer, nullable=False)
    circuit_state: Mapped[str] = mapped_column(String(20), nullable=False)
    kill_switch_tripped: Mapped[bool] = mapped_column(Boolean, nullable=False)
    state_version: Mapped[int] = mapped_column(Integer, nullable=False)
