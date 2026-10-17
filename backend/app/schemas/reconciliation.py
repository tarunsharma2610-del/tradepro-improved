from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


RunStatus = Literal["RUNNING", "COMPLETED", "COMPLETED_WITH_CONFLICTS", "FAILED", "LEASE_LOST"]
IssueStatus = Literal["OPEN", "RESOLVED"]


class ReconciliationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    broker_connection_id: UUID
    status: RunStatus
    started_at: datetime
    completed_at: datetime | None
    error_code: str | None
    summary: dict[str, int] | None


class ReconciliationIssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    broker_connection_id: UUID
    run_id: UUID | None
    intent_id: UUID | None
    issue_type: str
    broker_order_id: str | None
    broker_trade_id: str | None
    status: IssueStatus
    safe_details: dict[str, str | int | float | bool | None] | None
    first_seen_at: datetime
    last_seen_at: datetime
    occurrence_count: int
    resolved_at: datetime | None
