import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerOrder(BaseModel):
    """One broker-side order ID belonging to a conceptual local Order.

    Upstox Place Order V3 may return multiple order IDs (for example, when
    order slicing is enabled), so broker IDs are tracked as child rows rather
    than relying only on Order.broker_order_id.
    """

    __tablename__ = "broker_orders"
    __table_args__ = (
        UniqueConstraint("broker_connection_id", "broker_order_id", name="uq_broker_orders_connection_order_id"),
    )

    broker_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("broker_connections.id", ondelete="SET NULL", name="fk_broker_orders_broker_connection_id"),
        nullable=True, index=True,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    broker_name: Mapped[str] = mapped_column(String(20), nullable=False)
    broker_order_id: Mapped[str] = mapped_column(String(100), nullable=False)
    broker_tag: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="UNKNOWN")
    requested_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    filled_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_fill_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    status_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
