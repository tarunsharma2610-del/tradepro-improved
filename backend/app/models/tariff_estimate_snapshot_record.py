"""Durable estimate-only tariff snapshots; never a broker actual charge."""
from sqlalchemy import CheckConstraint, String, Text, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TariffEstimateSnapshotRecord(BaseModel):
    __tablename__ = "tariff_estimate_snapshot_records"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_tariff_estimate_snapshot_idempotency_key"),
        CheckConstraint("length(idempotency_key) = 64", name="ck_tariff_estimate_snapshot_key_sha256"),
        CheckConstraint("length(snapshot_sha256) = 64", name="ck_tariff_estimate_snapshot_digest_sha256"),
        CheckConstraint("status = 'ESTIMATE_ONLY'", name="ck_tariff_estimate_snapshot_estimate_only"),
    )

    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ESTIMATE_ONLY", server_default="ESTIMATE_ONLY")


@event.listens_for(TariffEstimateSnapshotRecord, "before_update")
def _reject_tariff_estimate_snapshot_mutation(_mapper, _connection, _target) -> None:
    """Reject ORM updates; estimate snapshots are append-only records."""
    raise ValueError("Tariff estimate snapshots are immutable; create a new event revision.")
