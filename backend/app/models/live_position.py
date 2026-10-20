import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LivePosition(BaseModel):
    """Position isolated to one broker connection and instrument.

    This is intentionally separate from paper portfolio positions and cash.
    """

    __tablename__ = "live_positions"
    __table_args__ = (
        UniqueConstraint(
            "broker_connection_id", "instrument_id",
            name="uq_live_position_connection_instrument",
        ),
        CheckConstraint("avg_price >= 0", name="ck_live_position_average_price_nonnegative"),
    )

    broker_connection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("instruments.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    avg_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"), server_default="0")
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"), server_default="0")
