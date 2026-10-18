import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerTradeRecord(BaseModel):
    """Durable, normalized broker-trade intake record.

    These records are not yet accounted executions: ingestion deliberately
    does not change portfolio cash, positions, order status, or paper
    executions. A later, separately reviewed reconciliation step can promote
    broker-confirmed records into live accounting atomically.
    """

    __tablename__ = "broker_trade_records"
    __table_args__ = (
        UniqueConstraint(
            "broker_connection_id",
            "broker_trade_id",
            name="uq_broker_trade_connection_trade_id",
        ),
    )

    broker_connection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    broker_order_ref_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("broker_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    broker_trade_id: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    side: Mapped[str] = mapped_column(String(4), nullable=False)
    instrument_token: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Preserve the broker timestamp verbatim until its exact timezone/format
    # contract is verified; do not silently reinterpret it as local time.
    exchange_timestamp: Mapped[str | None] = mapped_column(String(100), nullable=True)
