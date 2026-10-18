"""Single fail-closed choke point for future live broker order writes.

This is intentionally a deny-all boundary for this phase. It is not wired to
API routes or workers and does not call a broker adapter. A later change must
implement the complete persisted-intent, safety-state, pre-trade-risk, explicit
confirmation, and ambiguous-response recovery protocol here before writes can
be enabled. Do not remove the unconditional block as a configuration shortcut.
"""

from typing import Any

from app.services.live_execution_service import LiveExecutionBlocked


class LiveBrokerWriteService:
    """Deny live order mutations until the full lifecycle is reviewed.

    Keeping all three write verbs in one service creates an auditable boundary
    while deliberately preventing this foundation step from placing, modifying,
    or cancelling real orders. Read-only broker reconciliation remains separate.
    """

    @staticmethod
    def _blocked() -> None:
        raise LiveExecutionBlocked(
            "Live broker writes are not approved; no broker request was sent."
        )

    async def place_order(self, access_token: str, order: dict[str, Any]) -> None:
        """Fail closed; future implementation must validate persisted intent first."""
        self._blocked()

    async def modify_order(self, access_token: str, order: dict[str, Any]) -> None:
        """Fail closed; future implementation must verify ownership and broker state."""
        self._blocked()

    async def cancel_order(self, access_token: str, order_id: str) -> None:
        """Fail closed; future implementation must reconcile cancellation result."""
        self._blocked()

