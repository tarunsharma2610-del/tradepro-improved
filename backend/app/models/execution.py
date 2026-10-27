import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Execution(BaseModel):
    """One row per fill. Orders can in principle have more than one fill
    (Phase 2 only ever produces exactly one, since it doesn't do partial
    fills yet — see ExecutionService) but the model doesn't assume that,
    so partial-fill support later is additive.

    Every cost component is stored individually, not just the total — the
    spec requires preserving gross P&L, transaction costs, and net P&L as
    distinct, auditable numbers, not a single collapsed figure."""

    __tablename__ = "executions"
    __table_args__ = (
        UniqueConstraint(
            "broker_connection_id", "broker_trade_id",
            name="uq_execution_connection_broker_trade",
        ),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    instrument_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("instruments.id"), index=True)
    instrument: Mapped["Instrument"] = relationship(lazy="joined")

    side: Mapped[str] = mapped_column(String(4), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    gross_value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    brokerage: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    stt: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    exchange_charges: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    sebi_charges: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    stamp_duty: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    gst: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    # A missing amount is not enough to distinguish unknown from not applicable.
    # Status is explicit so delivery-sell DP charges cannot be silently treated as zero.
    demat_transaction_charges: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    demat_charge_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="UNKNOWN", server_default="UNKNOWN"
    )
    total_charges: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    # Paper fills default to estimated charges; live promotion requires audited broker-reported charges.
    charge_source: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PAPER_ESTIMATE", server_default="PAPER_ESTIMATE"
    )
    charge_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Durable link to the reviewed source evidence for live-fill charge provenance.
    # Nullable to preserve existing paper executions and historical rows.
    charge_evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("broker_charge_evidence.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Optional strategy-attributed component, separate from position realized P&L.
    strategy_realized_pnl: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)

    # Broker provenance is null for paper executions and populated only for confirmed broker fills.
    broker_order_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("broker_orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    broker_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    broker_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("broker_connections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    broker_trade_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Realized P&L attributable to THIS fill specifically (0 for fills
    # open/add to a position rather than close one) — see position_math.py.
    realized_pnl: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)

    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
