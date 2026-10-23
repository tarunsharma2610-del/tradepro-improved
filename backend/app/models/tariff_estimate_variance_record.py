"""Append-only variance-only comparisons between estimates and reviewed actuals."""
from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TariffEstimateVarianceRecord(BaseModel):
    """Snapshot an estimate-versus-actual variance without changing accounting.

    This table is a comparison/audit record only. It is not an actual charge
    source and must never be consumed by the per-fill allocation ledger.
    """

    __tablename__ = "tariff_estimate_variance_records"
    __table_args__ = (
        UniqueConstraint(
            "estimate_snapshot_id", "source_component_id",
            name="uq_tariff_estimate_variance_snapshot_component",
        ),
        CheckConstraint("currency = 'INR'", name="ck_tariff_estimate_variance_currency_inr"),
        CheckConstraint("estimated_amount >= 0", name="ck_tariff_estimate_variance_estimated_nonnegative"),
        CheckConstraint("actual_amount >= 0", name="ck_tariff_estimate_variance_actual_nonnegative"),
        CheckConstraint("status = 'VARIANCE_ONLY'", name="ck_tariff_estimate_variance_status"),
    )

    estimate_snapshot_id: Mapped[object] = mapped_column(
        Uuid, ForeignKey("tariff_estimate_snapshot_records.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    source_component_id: Mapped[object] = mapped_column(
        Uuid, ForeignKey("broker_charge_source_components.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    evidence_id: Mapped[object] = mapped_column(
        Uuid, ForeignKey("broker_charge_evidence.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    component_name: Mapped[str] = mapped_column(String(30), nullable=False)
    estimate_snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    estimated_amount: Mapped[object] = mapped_column(Numeric(18, 2), nullable=False)
    actual_amount: Mapped[object] = mapped_column(Numeric(18, 2), nullable=False)
    variance_amount: Mapped[object] = mapped_column(Numeric(18, 2), nullable=False)
    variance_percent: Mapped[object | None] = mapped_column(Numeric(18, 6), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="VARIANCE_ONLY", server_default="VARIANCE_ONLY"
    )
