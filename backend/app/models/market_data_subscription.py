import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MarketDataSubscription(BaseModel):
    """Durable desired market-feed subscription, scoped to one user/broker/instrument.

    This records intent only. It does not start a broker stream and never
    authorizes order writes. A worker reconciler may consume active rows
    after validating that the broker connection belongs to the same user.
    """

    __tablename__ = "market_data_subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    broker_connection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False, index=True
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    feed_mode: Mapped[str] = mapped_column(String(24), nullable=False, default="ltpc")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    instrument = relationship("Instrument", lazy="joined")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "broker_connection_id", "instrument_id", "feed_mode",
            name="uq_market_subscription_user_broker_instrument_mode",
        ),
        ForeignKeyConstraint(
            ["broker_connection_id", "user_id"],
            ["broker_connections.id", "broker_connections.user_id"],
            ondelete="CASCADE",
            name="fk_market_subscription_broker_user",
        ),
        CheckConstraint(
            "feed_mode IN ('ltpc', 'option_greeks', 'full')",
            name="ck_market_subscription_feed_mode",
        ),
    )
