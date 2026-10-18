from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class PlatformStatsOut(BaseModel):
    total_users: int
    total_portfolios: int
    total_active_strategies: int
    total_strategies: int
    total_news_items: int
    total_backtest_runs: int


class SafetyPermissionChange(BaseModel):
    permission: Literal[
        "safety.status.read",
        "safety.audit.read",
        "safety.kill_switch.trip",
        "safety.reset",
    ]
    action: Literal["grant", "revoke"]


class SafetyPermissionChangeOut(BaseModel):
    user_id: UUID
    safety_permissions: list[str]
