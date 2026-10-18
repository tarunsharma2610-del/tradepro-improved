import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LiveChargeAdjustment(BaseModel):
    """Append-only broker-confirmed fee correction for one accounted live fill.

    The original Execution remains immutable. broker_connection_id is retained
    as an identity snapshot (not a FK) so audit/idempotency history survives
    broker-connection deletion. Net-P&L consumers apply net_realized_pnl_delta;
    this row never replays fill quantity or changes a LivePosition.
    """

    __tablename__ = "live_charge_adjustments"
    __table_args__ = (
        UniqueConstraint(
            "broker_connection_id",
            "broker_trade_id",
            "source_reference",
            name="uq_live_charge_adjustment_trade_reference",
        ),
        UniqueConstraint(
            "execution_id",
            "adjustment_number",
            name="uq_live_charge_adjustment_execution_number",
        ),
    )

    execution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("executions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    broker_connection_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    broker_trade_id: Mapped[str] = mapped_column(String(100), nullable=False)
    adjustment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="BROKER_REPORTED")
    source_reference: Mapped[str] = mapped_column(String(200), nullable=False)

    brokerage: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    stt: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    exchange_charges: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    sebi_charges: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    stamp_duty: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    gst: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    dp_charges: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    previous_effective_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    new_effective_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    charge_delta: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    net_realized_pnl_delta: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
