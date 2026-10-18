"""Central fail-closed boundary for future live broker order mutations.

The only enabled operation in this foundation is safety-aware preflight plus
durable intent persistence. It does not submit orders. Place/modify/cancel stay
unconditionally denied until a separately reviewed submission lifecycle covers
explicit confirmation, safety state, fresh risk, idempotency and ambiguous
broker outcomes. Do not weaken the deny-all methods as a configuration shortcut.
"""
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.live_execution_service import LiveExecutionBlocked, LiveOrderIntent
from app.services.live_order_recovery_service import LiveOrderRecoveryService
from app.services.live_preflight_coordinator import LivePreflightCoordinator


class LiveBrokerWriteService:
    """Single planned boundary; currently persists a plan but never writes to broker."""

    def __init__(
        self,
        db: Session | None = None,
        *,
        preflight_coordinator: LivePreflightCoordinator | Any | None = None,
        recovery_service: LiveOrderRecoveryService | Any | None = None,
    ):
        self.preflight = preflight_coordinator
        self.recovery = recovery_service
        if db is not None:
            self.preflight = self.preflight or LivePreflightCoordinator(db)
            self.recovery = self.recovery or LiveOrderRecoveryService(db)

    async def prepare_order_intent(
        self,
        user_id: UUID,
        intent: LiveOrderIntent,
        *,
        idempotency_key: str,
        user_confirmed: bool,
    ):
        """Run full safety-aware read-only preflight and persist a stable intent.

        This method may read market/account snapshots and write the local intent
        row. It never calls a broker order endpoint. A successful result is not
        an instruction or authorization to submit the order.
        """
        if self.preflight is None or self.recovery is None:
            raise LiveExecutionBlocked(
                "Safety-aware preflight and intent persistence dependencies are required."
            )
        plan = await self.preflight.preflight(
            user_id, intent, user_confirmed=user_confirmed
        )
        return self.recovery.persist_preflighted_intent(
            user_id,
            intent,
            plan,
            idempotency_key=idempotency_key,
        )

    @staticmethod
    def _blocked() -> None:
        raise LiveExecutionBlocked(
            "Live broker writes are not approved; no broker request was sent."
        )

    async def place_order(self, access_token: str, order: dict[str, Any]) -> None:
        """Fail closed; intent persistence is not authorization to submit."""
        self._blocked()

    async def modify_order(self, access_token: str, order: dict[str, Any]) -> None:
        """Fail closed until ownership and broker-state reconciliation are reviewed."""
        self._blocked()

    async def cancel_order(self, access_token: str, order_id: str) -> None:
        """Fail closed until broker-confirmed cancellation handling is reviewed."""
        self._blocked()
