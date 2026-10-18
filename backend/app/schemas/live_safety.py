from datetime import datetime
from pydantic import BaseModel, Field


class SafetyControlRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    expected_version: int | None = Field(default=None, ge=1)


class SafetyStatusOut(BaseModel):
    state_exists: bool
    broker: str
    allowed: bool
    decision_reason: str
    kill_switch_tripped: bool
    kill_switch_reason: str | None = None
    kill_switch_tripped_at: datetime | None = None
    circuit_state: str
    circuit_reason: str | None = None
    consecutive_broker_errors: int
    last_broker_error_at: datetime | None = None
    last_broker_error_code: str | None = None
    last_health_check_at: datetime | None = None
    version: int | None = None
