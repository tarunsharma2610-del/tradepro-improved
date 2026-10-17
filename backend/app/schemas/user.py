from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    is_admin: bool
    mfa_enabled: bool
    created_at: datetime
