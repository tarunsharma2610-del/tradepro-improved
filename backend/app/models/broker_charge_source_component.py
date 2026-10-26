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


class BrokerChargeSourceComponent(BaseModel):
    """A source amount transcribed from a specific, integrity-checked contract note.

    Manual entries are never trusted on submission. A distinct reviewer must
    confirm the amount against the original document before the record becomes
    VERIFIED. This table is a provenance ledger, not an automated parser.
    """

    __tablename__ = "broker_charge_source_components"
    __table_args__ = (
        UniqueConstraint("evidence_id", "component_name", "revision", name="uq_charge_source_component_evidence_name_revision"),
        CheckConstraint(
            "component_name IN ('brokerage', 'stt', 'exchange_charges', 'transaction_charges', "
            "'clearing_charges', 'ipft', 'other_charges', 'demat_transaction_charges', "
            "'sebi_charges', 'stamp_duty', 'gst')",
            name="ck_charge_source_component_name",
        ),
        CheckConstraint("source_amount >= 0", name="ck_charge_source_component_amount_nonnegative"),
        CheckConstraint("revision > 0", name="ck_charge_source_component_revision_positive"),
        CheckConstraint("currency = 'INR'", name="ck_charge_source_component_currency_inr"),
        CheckConstraint(
            "extraction_method IN ('MANUAL_TRANSCRIPTION', 'PARSER')",
            name="ck_charge_source_component_extraction_method",
        ),
        CheckConstraint(
            "status IN ('PENDING_REVIEW', 'VERIFIED', 'REJECTED')",
            name="ck_charge_source_component_status",
        ),
    )

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("broker_charge_evidence.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    component_name: Mapped[str] = mapped_column(String(30), nullable=False)
    # Preserve the exact source wording separately from the normalized ledger name.
    source_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Null means legacy/undeclared; never infer combined vs split semantics.
    representation_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Persist the exact validator contract used for combined/split declarations.
    # Null is legacy/undeclared and must never be inferred during review.
    representation_contract_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # Version of the canonical live-accounting component set approved for this row.
    # Null means legacy or evidence-only; promotion must not infer membership.
    component_set_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    source_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    extraction_method: Mapped[str] = mapped_column(
        String(30), nullable=False, default="MANUAL_TRANSCRIPTION", server_default="MANUAL_TRANSCRIPTION"
    )
    parser_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="manual-transcription-v1", server_default="manual-transcription-v1"
    )
    source_locator: Mapped[str] = mapped_column(String(200), nullable=False)
    # Canonical JSON array of reviewed BrokerTradeRecord UUIDs, sorted lexically.
    eligible_fill_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Canonical reviewed per-fill weights for EXPLICIT_REVIEWED allocations.
    eligible_fill_weights_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    eligible_fill_set_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rounding_policy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    allocation_basis: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extracted_by_user_id: Mapped[uuid.UUID] = mapped_column(
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
