import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerConnection(BaseModel):
    """One row per (user, broker). This is deliberately per-user, not a
    single global credential set — in a multi-tenant SaaS, every user
    connects their own broker account. `broker` is a string key ("upstox",
    later "zerodha", "groww", ...) so adding a broker never touches this
    table's schema, only app/brokers/<name>/adapter.py.

    `is_connected` must only ever be flipped to True after a real,
    successful call to the broker's API — never just because credentials
    were saved. See services/broker_credentials_service.py:test_connection.
    """

    __tablename__ = "broker_connections"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    broker: Mapped[str] = mapped_column(String(50), nullable=False)  # "upstox", ...

    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    api_secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    redirect_uri: Mapped[str] = mapped_column(String(500), nullable=False)

    # One-time OAuth state nonce digest; the raw nonce exists only inside the signed state token.
    oauth_state_nonce_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    oauth_state_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Independently generated, read-only Upstox Analytics Token (1-year validity).
    analytics_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    analytics_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "broker", name="uq_broker_connection_user_broker"), UniqueConstraint("id", "user_id", name="uq_broker_connection_id_user"))
