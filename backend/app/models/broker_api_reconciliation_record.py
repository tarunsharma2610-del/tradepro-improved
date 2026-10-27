"""Immutable, owner-scoped aggregate broker API reconciliation snapshots."""
from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerApiReconciliationRecord(BaseModel):
    """Audit provenance for read-only aggregate API results; never per-fill actuals."""

    __tablename__ = "broker_api_reconciliation_records"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_broker_api_reconciliation_idempotency_key"),
        CheckConstraint("length(idempotency_key) = 64", name="ck_broker_api_reconciliation_key_sha256"),
        CheckConstraint("length(response_sha256) = 64", name="ck_broker_api_reconciliation_response_sha256"),
        CheckConstraint("evidence_kind = 'AGGREGATE_RECONCILIATION_ONLY'", name="ck_broker_api_reconciliation_kind"),
        CheckConstraint("per_fill_actual = false", name="ck_broker_api_reconciliation_not_per_fill_actual"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    broker_connection_id: Mapped[str] = mapped_column(ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    broker: Mapped[str] = mapped_column(String(32), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False)
    api_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v2", server_default="v2")
    request_scope_json: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[str] = mapped_column(String(40), nullable=False)
    fetch_status: Mapped[str] = mapped_column(String(32), nullable=False)
    http_status_code: Mapped[int | None] = mapped_column(nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evidence_kind: Mapped[str] = mapped_column(String(40), nullable=False, default="AGGREGATE_RECONCILIATION_ONLY", server_default="AGGREGATE_RECONCILIATION_ONLY")
    per_fill_actual: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="0")
    response_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    response_json: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)


@event.listens_for(BrokerApiReconciliationRecord, "before_update")
def _reject_api_reconciliation_mutation(_mapper, _connection, _target) -> None:
    raise ValueError("API reconciliation records are immutable; fetch a new snapshot.")
