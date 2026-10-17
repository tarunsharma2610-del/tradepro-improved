from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit_log(
    db: Session,
    *,
    action: str,
    user_id: UUID | None = None,
    request: Request | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=(request.client.host if request and request.client else None),
        event_metadata=metadata,
    )
    db.add(entry)
    db.commit()
