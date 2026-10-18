"""Unregistered orchestration from staged trade -> estimate -> atomic accounting.

This coordinator is deliberately not wired into API routes, background workers,
or live order submission. It promotes only trades already staged by the
read-only broker-trade intake service.
"""
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.broker_trade_record import BrokerTradeRecord
from app.models.execution import Execution
from app.services.live_execution_service import LiveExecutionBlocked
from app.services.live_fill_accounting_service import (
    LiveChargeBreakdown,
    LiveFillAccountingResult,
    LiveFillAccountingService,
)
from app.services.live_charge_estimate_service import LiveChargeEstimateService


class LiveFillPromotionService:
    """Obtain an explicit estimate, then atomically account the staged fill."""

    def __init__(
        self,
        db: Session,
        *,
        charge_estimator: LiveChargeEstimateService | None = None,
        accounting: LiveFillAccountingService | None = None,
    ):
        self.db = db
        self.charge_estimator = charge_estimator or LiveChargeEstimateService(db)
        self.accounting = accounting or LiveFillAccountingService(db)

    async def promote_trade(
        self, user_id: UUID, broker_trade_record_id: UUID
    ) -> LiveFillAccountingResult:
        record = self.db.get(BrokerTradeRecord, broker_trade_record_id)
        if record is None:
            raise LiveExecutionBlocked("Staged broker trade record was not found.")

        # Replay path: reuse the already-persisted provenance, so a repeated
        # promotion doesn't depend on the estimator endpoint being available.
        existing = (
            self.db.query(Execution)
            .filter(
                Execution.broker_connection_id == record.broker_connection_id,
                Execution.broker_trade_id == record.broker_trade_id,
            )
            .first()
        )
        if existing is not None:
            prior_charges = LiveChargeBreakdown(
                brokerage=existing.brokerage,
                stt=existing.stt,
                exchange_charges=existing.exchange_charges,
                sebi_charges=existing.sebi_charges,
                stamp_duty=existing.stamp_duty,
                gst=existing.gst,
                dp_charges=existing.dp_charges,
                source=existing.charge_source,
                reference=existing.charge_reference or "",
            )
            # The accounting service rechecks ownership and exact trade/order
            # identity before treating this as a duplicate.
            return self.accounting.account_trade(
                user_id, broker_trade_record_id, prior_charges
            )

        estimate = await self.charge_estimator.estimate_for_trade(
            user_id, broker_trade_record_id
        )
        if (
            estimate.broker_trade_id != record.broker_trade_id
            or estimate.broker_connection_id != record.broker_connection_id
            or estimate.instrument_token != record.instrument_token
            or estimate.quantity != record.quantity
            or estimate.price != Decimal(str(record.price))
        ):
            raise LiveExecutionBlocked(
                "Charge estimate identity does not match the staged trade; promotion blocked."
            )
        # Re-fetch after the asynchronous network boundary. The staged trade
        # is immutable through the intake service; still reject a changed row.
        self.db.refresh(record)
        if estimate.broker_trade_id != record.broker_trade_id:
            raise LiveExecutionBlocked(
                "Staged trade changed during charge estimation; promotion blocked."
            )
        return self.accounting.account_trade(
            user_id, broker_trade_record_id, estimate.breakdown
        )
