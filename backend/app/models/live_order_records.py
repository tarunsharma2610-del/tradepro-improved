import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LiveOrderIntent(BaseModel):
    """Durable, broker-scoped live order request. This table does not submit orders."""

    __tablename__ = "live_order_intents"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "broker_connection_id", "client_idempotency_key",
            name="uq_live_intent_user_connection_key",
        ),
        UniqueConstraint(
            "broker_connection_id", "broker_order_id",
            name="uq_live_intent_connection_broker_order",
        ),
        CheckConstraint("submit_attempt_count >= 0", name="ck_live_intent_attempt_count_nonnegative"),
        CheckConstraint("version >= 1", name="ck_live_intent_version_positive"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    broker_connection_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False, index=True)

    client_idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    # Immutable, normalized economic order fields only; never credentials or authorization headers.
    order_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)

    state: Mapped[str] = mapped_column(String(32), nullable=False, default="CREATED", server_default="CREATED", index=True)
    broker_order_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    broker_tag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submit_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_submit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")


class LiveOrderEvent(BaseModel):
    """Append-only-by-policy audit event for a live-order intent; secrets must never be recorded."""

    __tablename__ = "live_order_events"

    intent_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("live_order_intents.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    safe_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class LiveOrderOutbox(BaseModel):
    """Transactional dispatch record. No worker or broker POST is implemented in Phase 1."""

    __tablename__ = "live_order_submit_outbox"
    __table_args__ = (
        UniqueConstraint("intent_id", name="uq_live_outbox_intent"),
        CheckConstraint("attempt_count >= 0", name="ck_live_outbox_attempt_count_nonnegative"),
    )

    intent_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("live_order_intents.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="READY", server_default="READY", index=True)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    claim_token: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    claimed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)


class BrokerFillIdentity(BaseModel):
    """Stable broker fill identity used for future idempotent fill ingestion; no ingestion runs yet."""

    __tablename__ = "broker_fill_identities"
    __table_args__ = (
        UniqueConstraint("broker_connection_id", "broker_trade_id", name="uq_broker_fill_connection_trade"),
        CheckConstraint("quantity > 0", name="ck_broker_fill_quantity_positive"),
        CheckConstraint("price > 0", name="ck_broker_fill_price_positive"),
    )

    broker_connection_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    intent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("live_order_intents.id", ondelete="SET NULL"), nullable=True, index=True)
    broker_order_id: Mapped[str] = mapped_column(String(128), nullable=False)
    broker_trade_id: Mapped[str] = mapped_column(String(128), nullable=False)
    instrument_key: Mapped[str] = mapped_column(String(128), nullable=False)
    side: Mapped[str] = mapped_column(String(4), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    safe_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
