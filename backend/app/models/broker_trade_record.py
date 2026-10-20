import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerTradeRecord(BaseModel):
    """Immutable-identity broker trade intake row awaiting accounting review."""

    __tablename__ = "broker_trade_records"
    __table_args__ = (
        UniqueConstraint(
            "broker_connection_id", "broker_trade_id",
            name="uq_broker_trade_connection_trade",
        ),
        CheckConstraint("quantity > 0", name="ck_broker_trade_quantity_positive"),
        CheckConstraint("price > 0", name="ck_broker_trade_price_positive"),
        CheckConstraint("side IN ('BUY', 'SELL')", name="ck_broker_trade_side"),
    )

    broker_connection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    broker_order_ref_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("broker_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    broker_trade_id: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    side: Mapped[str] = mapped_column(String(4), nullable=False)
    instrument_token: Mapped[str] = mapped_column(String(128), nullable=False)
    exchange_timestamp: Mapped[str] = mapped_column(String(100), nullable=False)
