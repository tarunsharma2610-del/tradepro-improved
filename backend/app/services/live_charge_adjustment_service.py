"""Append-only reconciliation of final broker charges against accounted live fills.

The original Execution and LivePosition are never rewritten by this service.
The ledger records the delta between the previously effective charges and the
new broker-reported charges. Net realized P&L consumers apply the recorded
net_realized_pnl_delta; fill quantity and position math are never replayed.
"""
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.models.live_charge_adjustment import LiveChargeAdjustment
from app.models.portfolio import Portfolio
from app.services.live_execution_service import LiveExecutionBlocked
from app.services.live_fill_accounting_service import (
    LiveChargeBreakdown,
    LiveFillAccountingService,
)


@dataclass(frozen=True)
class LiveChargeAdjustmentResult:
    execution_id: UUID
    adjustment_id: UUID | None
    broker_connection_id: UUID
    broker_trade_id: str
    source_reference: str
    duplicate: bool
    previous_effective_total: Decimal
    new_effective_total: Decimal
    effective_charge_total: Decimal
    charge_delta: Decimal
    net_realized_pnl_delta: Decimal
    effective_net_realized_pnl: Decimal


class LiveChargeAdjustmentService:
    """Apply one idempotent, append-only broker-confirmed charge revision."""

    def __init__(self, db: Session):
        self.db = db

    def apply_broker_reported_charges(
        self,
        user_id: UUID,
        broker_connection_id: UUID,
        broker_trade_id: str,
        charges: LiveChargeBreakdown,
    ) -> LiveChargeAdjustmentResult:
        values, new_total = LiveFillAccountingService._validate_charges(charges)
        if values["charge_source"] != "BROKER_REPORTED":
            raise LiveExecutionBlocked(
                "Charge adjustment requires broker-reported final charges, not an estimate."
            )
        if not isinstance(broker_trade_id, str) or not broker_trade_id.strip():
            raise LiveExecutionBlocked("A broker trade ID is required for charge adjustment.")
        broker_trade_id = broker_trade_id.strip()

        try:
            execution = (
                self.db.query(Execution)
                .join(Portfolio, Portfolio.id == Execution.portfolio_id)
                .filter(
                    Execution.broker_connection_id == broker_connection_id,
                    Execution.broker_trade_id == broker_trade_id,
                    Portfolio.user_id == user_id,
                )
                .with_for_update(of=Execution)
                .first()
            )
            if execution is None:
                raise LiveExecutionBlocked(
                    "No accounted live execution for this user's broker trade was found."
                )

            key_filter = (
                LiveChargeAdjustment.broker_connection_id == broker_connection_id,
                LiveChargeAdjustment.broker_trade_id == broker_trade_id,
                LiveChargeAdjustment.source_reference == values["charge_reference"],
            )
            replay = self.db.query(LiveChargeAdjustment).filter(*key_filter).first()
            if replay is not None:
                if not self._same_breakdown(replay, values, new_total):
                    raise LiveExecutionBlocked(
                        "This charge-document reference already exists with different values."
                    )
                latest = (
                    self.db.query(LiveChargeAdjustment)
                    .filter(LiveChargeAdjustment.execution_id == execution.id)
                    .order_by(LiveChargeAdjustment.adjustment_number.desc())
                    .first()
                )
                return self._result(
                    execution,
                    replay,
                    duplicate=True,
                    effective_total=Decimal(str(latest.new_effective_total if latest else execution.total_charges)),
                )

            latest = (
                self.db.query(LiveChargeAdjustment)
                .filter(LiveChargeAdjustment.execution_id == execution.id)
                .order_by(LiveChargeAdjustment.adjustment_number.desc())
                .first()
            )
            previous_total = (
                Decimal(str(latest.new_effective_total))
                if latest is not None
                else Decimal(str(execution.total_charges))
            )
            adjustment_number = latest.adjustment_number + 1 if latest else 1
            charge_delta = (new_total - previous_total).quantize(Decimal("0.01"))
            pnl_delta = (-charge_delta).quantize(Decimal("0.01"))

            row = LiveChargeAdjustment(
                execution_id=execution.id,
                broker_connection_id=broker_connection_id,
                broker_trade_id=broker_trade_id,
                adjustment_number=adjustment_number,
                source="BROKER_REPORTED",
                source_reference=values["charge_reference"],
                brokerage=values["brokerage"],
                stt=values["stt"],
                exchange_charges=values["exchange_charges"],
                sebi_charges=values["sebi_charges"],
                stamp_duty=values["stamp_duty"],
                gst=values["gst"],
                dp_charges=values["dp_charges"],
                previous_effective_total=previous_total,
                new_effective_total=new_total,
                charge_delta=charge_delta,
                net_realized_pnl_delta=pnl_delta,
            )
            self.db.add(row)
            self.db.flush()
            self.db.commit()
            self.db.refresh(row)
            self.db.refresh(execution)
            return self._result(execution, row, duplicate=False, effective_total=new_total)
        except IntegrityError as exc:
            self.db.rollback()
            # Concurrent replay of the same contract-note reference is safe
            # only if the persisted content exactly matches this request.
            replay = (
                self.db.query(LiveChargeAdjustment)
                .filter(
                    LiveChargeAdjustment.broker_connection_id == broker_connection_id,
                    LiveChargeAdjustment.broker_trade_id == broker_trade_id,
                    LiveChargeAdjustment.source_reference == values["charge_reference"],
                )
                .first()
            )
            if replay is not None and self._same_breakdown(replay, values, new_total):
                execution = self.db.query(Execution).filter(Execution.id == replay.execution_id).first()
                if execution is not None:
                    latest = (
                        self.db.query(LiveChargeAdjustment)
                        .filter(LiveChargeAdjustment.execution_id == execution.id)
                        .order_by(LiveChargeAdjustment.adjustment_number.desc())
                        .first()
                    )
                    return self._result(
                        execution, replay, duplicate=True,
                        effective_total=Decimal(str(latest.new_effective_total if latest else execution.total_charges)),
                    )
            raise LiveExecutionBlocked(
                "Concurrent charge adjustment detected; reload the latest effective charges and retry."
            ) from exc
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _same_breakdown(row: LiveChargeAdjustment, values: dict, total: Decimal) -> bool:
        names = ("brokerage", "stt", "exchange_charges", "sebi_charges", "stamp_duty", "gst", "dp_charges")
        return (
            row.source == values["charge_source"]
            and row.source_reference == values["charge_reference"]
            and all(Decimal(str(getattr(row, name))) == Decimal(str(values[name])) for name in names)
            and Decimal(str(row.new_effective_total)) == total
        )

    @staticmethod
    def _result(
        execution: Execution,
        row: LiveChargeAdjustment,
        *,
        duplicate: bool,
        effective_total: Decimal,
    ) -> LiveChargeAdjustmentResult:
        previous = Decimal(str(row.previous_effective_total))
        new = Decimal(str(row.new_effective_total))
        current_effective = Decimal(str(effective_total))
        delta = Decimal(str(row.charge_delta)).quantize(Decimal("0.01"))
        return LiveChargeAdjustmentResult(
            execution_id=execution.id,
            adjustment_id=row.id,
            broker_connection_id=row.broker_connection_id,
            broker_trade_id=row.broker_trade_id,
            source_reference=row.source_reference,
            duplicate=duplicate,
            previous_effective_total=previous,
            new_effective_total=new,
            effective_charge_total=current_effective,
            charge_delta=delta,
            net_realized_pnl_delta=(-delta).quantize(Decimal("0.01")),
            effective_net_realized_pnl=(
                Decimal(str(execution.realized_pnl)) - current_effective
            ).quantize(Decimal("0.01")),
        )
