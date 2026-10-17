import uuid

from sqlalchemy import JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AuditLog(BaseModel):
    """Append-only. Never updated, never deleted by the app itself.
    Written for: login success/failure, MFA enable/disable, broker
    credentials added/updated/removed, platform settings changed,
    trading-mode-relevant actions. Extend `action` values as new modules
    land — don't repurpose existing ones."""

    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
