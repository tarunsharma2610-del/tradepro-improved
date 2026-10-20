import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerOrder(BaseModel):
    """Broker-specific child order observed during read-only reconciliation.

    This record is intake/reconciliation state only. It does not submit or
    modify broker orders.
    """

    __tablename__ = "broker_orders"
    __table_args__ = (
        UniqueConstraint(
            "broker_connection_id", "broker_order_id",
            name="uq_broker_order_connection_order",
        ),
        CheckConstraint("requested_quantity > 0", name="ck_broker_order_requested_quantity_positive"),
        CheckConstraint(
            "filled_quantity >= 0 AND filled_quantity <= requested_quantity",
            name="ck_broker_order_filled_quantity_bounds",
        ),
    )

    broker_connection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    broker_name: Mapped[str] = mapped_column(String(50), nullable=False)
    broker_order_id: Mapped[str] = mapped_column(String(128), nullable=False)
    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    filled_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(32), nullable=False)
