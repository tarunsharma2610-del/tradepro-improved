import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerChargeAllocation(BaseModel):
    """Durable per-fill allocation of one contract-note charge component.

    This table records reviewed allocation decisions; it does not calculate a
    valid allocation basis or authenticate the source document. Those checks
    must be performed by the allocation service before rows are inserted.
    """

    __tablename__ = "broker_charge_allocations"
    __table_args__ = (
        UniqueConstraint(
            "evidence_id",
            "broker_trade_record_id",
            "charge_component",
            name="uq_charge_allocation_evidence_trade_component",
        ),
        CheckConstraint(
            "charge_component IN ('brokerage', 'stt', 'exchange_charges', "
            "'transaction_charges', 'clearing_charges', 'ipft', 'other_charges', "
            "'demat_transaction_charges', 'sebi_charges', 'stamp_duty', 'gst')",
            name="ck_charge_allocation_component",
        ),
        CheckConstraint(
            "source_component_total >= 0 AND allocated_amount >= 0",
            name="ck_charge_allocation_nonnegative_amounts",
        ),
        CheckConstraint(
            "length(currency) = 3",
            name="ck_charge_allocation_currency_length",
        ),
        CheckConstraint(
            "status IN ('PENDING_RECONCILIATION', 'RECONCILED', 'REJECTED')",
            name="ck_charge_allocation_status",
        ),
    )

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("broker_charge_evidence.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Non-null for allocations created from a separately reviewed canonical snapshot.
    # Null is retained only for legacy rows created before canonical snapshots.
    canonical_component_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("broker_charge_canonical_components.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    broker_connection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("broker_connections.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    broker_trade_record_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("broker_trade_records.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    charge_component: Mapped[str] = mapped_column(String(30), nullable=False)
    source_component_total: Mapped[float] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    allocated_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR", server_default="INR"
    )
    allocation_basis: Mapped[str] = mapped_column(String(50), nullable=False)
    method_version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING_RECONCILIATION",
        server_default="PENDING_RECONCILIATION",
        index=True,
    )
    reconciliation_reference: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
