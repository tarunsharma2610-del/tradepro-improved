import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerChargeCanonicalComponent(BaseModel):
    """Immutable, versioned snapshot mapping raw reviewed rows to one canonical charge.

    A snapshot is created PENDING_REVIEW. It does not authorize allocation or
    accounting until a separate review/promotion workflow verifies its source
    fingerprint, canonical amount, fill manifest and mapping contract.
    """

    __tablename__ = "broker_charge_canonical_components"
    __table_args__ = (
        UniqueConstraint(
            "evidence_id", "canonical_component", "revision",
            name="uq_charge_canonical_component_evidence_name_revision",
        ),
        UniqueConstraint(
            "evidence_id", "canonical_component", "source_snapshot_sha256",
            name="uq_charge_canonical_component_source_snapshot",
        ),
        CheckConstraint(
            "canonical_component IN ('brokerage', 'stt', 'exchange_charges', 'sebi_charges', 'stamp_duty', 'gst')",
            name="ck_charge_canonical_component_name",
        ),
        CheckConstraint("canonical_amount >= 0", name="ck_charge_canonical_amount_nonnegative"),
        CheckConstraint("revision > 0", name="ck_charge_canonical_revision_positive"),
        CheckConstraint("currency = 'INR'", name="ck_charge_canonical_currency_inr"),
        CheckConstraint(
            "status IN ('PENDING_REVIEW', 'VERIFIED', 'REJECTED')",
            name="ck_charge_canonical_status",
        ),
    )

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("broker_charge_evidence.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    canonical_component: Mapped[str] = mapped_column(String(30), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    # Canonical JSON array of the exact immutable source-component row UUIDs.
    source_component_ids_json: Mapped[str] = mapped_column(Text, nullable=False)
    # Fingerprint of source IDs, revisions, labels, amounts, hashes and mapping version.
    source_snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mapping_version: Mapped[str] = mapped_column(String(80), nullable=False)
    representation_contract_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    canonical_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    component_set_version: Mapped[str] = mapped_column(String(80), nullable=False)
    eligible_fill_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    eligible_fill_weights_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    eligible_fill_set_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rounding_policy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    allocation_basis: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING_REVIEW", server_default="PENDING_REVIEW", index=True
    )
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
