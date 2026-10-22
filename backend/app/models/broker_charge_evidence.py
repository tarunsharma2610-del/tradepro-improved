import uuid
from datetime import datetime, date

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerChargeEvidence(BaseModel):
    """Metadata for an imported broker charge document; not proof of authenticity by itself.

    The original document is kept outside this table. Its SHA-256 fingerprint lets
    the application detect byte-level changes when the same file is reprocessed.
    Review status is a workflow marker, not cryptographic broker verification.
    """

    __tablename__ = "broker_charge_evidence"
    __table_args__ = (
        UniqueConstraint(
            "broker_connection_id", "source_sha256",
            name="uq_charge_evidence_connection_sha256",
        ),
        CheckConstraint("byte_size > 0", name="ck_charge_evidence_byte_size_positive"),
        CheckConstraint("length(source_sha256) = 64", name="ck_charge_evidence_sha256_length"),
        CheckConstraint(
            "status IN ('RECEIVED', 'REVIEWED', 'REJECTED')",
            name="ck_charge_evidence_status",
        ),
    )

    broker_connection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("broker_connections.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    source_kind: Mapped[str] = mapped_column(
        String(30), nullable=False, default="CONTRACT_NOTE", server_default="CONTRACT_NOTE"
    )
    broker_report_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    report_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    segment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # Relative opaque key only; never store user-controlled filesystem paths.
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    parser_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="RECEIVED", server_default="RECEIVED", index=True
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
