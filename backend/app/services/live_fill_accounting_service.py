"""Atomic promotion of a broker-confirmed trade into live accounting.

The service is deliberately unregistered. It writes only broker-scoped
LivePosition and Execution rows; it never changes paper Position rows or
Portfolio.cash_balance. Actual broker-reported charges with an audit reference
are mandatory; estimated paper costs are rejected for live promotion.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.broker_connection import BrokerConnection
from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.models.broker_charge_canonical_component import BrokerChargeCanonicalComponent
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.live_position import LivePosition
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.user import User
from app.services.broker_charge_evidence_service import require_reviewed_charge_evidence
from app.services.broker_charge_component_set_contract import (
    LIVE_FILL_ACCOUNTING_COMPONENTS,
    LIVE_FILL_COMPONENT_SET_VERSION,
    validate_live_fill_component_set,
)
from app.services.broker_charge_canonical_allocation_reconciliation_service import verify_canonical_component_allocation_ledger
from app.services.position_math import apply_fill
from app.services.transaction_costs import Side


CENT = Decimal("0.01")


@dataclass(frozen=True)
class LiveFillChargeBreakdown:
    brokerage: Decimal
    stt: Decimal
    exchange_charges: Decimal
    sebi_charges: Decimal
    stamp_duty: Decimal
    gst: Decimal
    total_charges: Decimal
    source: str
    reference: str
    evidence_id: UUID | None = None
    reviewer_user_id: UUID | None = None
    demat_transaction_charges: Decimal | None = None


@dataclass(frozen=True)
class LiveFillAccountingResult:
    execution_id: UUID
    broker_trade_id: str
    inserted: bool
    live_position_quantity: int
    live_position_average_price: Decimal
    realized_pnl: Decimal


class LiveFillAccountingService:
    """Promote one staged broker trade exactly once, atomically."""

    def __init__(self, db: Session):
        self.db = db

    def promote_trade(
        self,
        user_id: UUID,
        broker_trade_record_id: UUID,
        charges: LiveFillChargeBreakdown,
    ) -> LiveFillAccountingResult:
        try:
            fee_values = self._validate_charges(charges)
            # Use unlocked reads only to discover the parent ID, then acquire row
            # locks in the shared Order -> BrokerOrder -> BrokerTradeRecord order.
            # Ingestion and child reconciliation take the same parent/child locks;
            # locking the trade record first can deadlock against reconciliation.
            record_hint = (
                self.db.query(BrokerTradeRecord)
                .filter(BrokerTradeRecord.id == broker_trade_record_id)
                .first()
            )
            if record_hint is None:
                raise ValueError("Broker trade intake record not found.")

            child_hint = (
                self.db.query(BrokerOrder)
                .filter(BrokerOrder.id == record_hint.broker_order_ref_id)
                .first()
            )
            if child_hint is None or child_hint.broker_connection_id != record_hint.broker_connection_id:
                raise ValueError("Broker trade is not bound to a valid child-order/connection mapping.")

            row = (
                self.db.query(Order, Portfolio.user_id)
                .join(Portfolio, Portfolio.id == Order.portfolio_id)
                .filter(Order.id == child_hint.order_id, Portfolio.user_id == user_id)
                .with_for_update(of=Order)
                .populate_existing()
                .first()
            )
            if row is None:
                raise ValueError("Broker trade order not found.")
            order, owner_id = row
            if owner_id != user_id or order.trading_mode != "LIVE":
                raise ValueError("Live fill accounting is only allowed for an owned LIVE order.")
            if order.execution_reason != "MANUAL":
                raise ValueError("Only manual LIVE orders are supported by this accounting step.")
            if order.status == "REJECTED":
                raise ValueError("A rejected local order cannot accept broker fill accounting.")

            child = (
                self.db.query(BrokerOrder)
                .filter(BrokerOrder.id == child_hint.id, BrokerOrder.order_id == order.id)
                .with_for_update()
                .populate_existing()
                .first()
            )
            if (
                child is None
                or child.broker_connection_id != record_hint.broker_connection_id
            ):
                raise ValueError("Broker child-order mapping changed while acquiring accounting locks.")

            # Do not lock the trade row yet. Canonical charge verification locks
            # all canonical snapshots first, then evidence, source rows, allocations,
            # and finally the trade record. Taking the trade lock first would invert
            # that order and can deadlock against verification/promotion.
            record = (
                self.db.query(BrokerTradeRecord)
                .filter(
                    BrokerTradeRecord.id == broker_trade_record_id,
                    BrokerTradeRecord.broker_order_ref_id == child.id,
                    BrokerTradeRecord.broker_connection_id == child.broker_connection_id,
                )
                .populate_existing()
                .first()
            )
            if record is None:
                raise ValueError("Broker trade mapping changed while acquiring accounting locks.")
            if record.quantity > child.filled_quantity or record.quantity > child.requested_quantity:
                raise ValueError("Broker trade quantity exceeds the broker-confirmed child-order fill quantity.")
            if record.quantity > order.quantity:
                raise ValueError("Broker trade quantity exceeds the local order quantity.")
            connection = (
                self.db.query(BrokerConnection)
                .filter(
                    BrokerConnection.id == record.broker_connection_id,
                    BrokerConnection.user_id == user_id,
                    BrokerConnection.broker == child.broker_name,
                )
                .with_for_update()
                .populate_existing()
                .first()
            )
            if connection is None or child.broker_name != "upstox":
                raise ValueError("Broker trade connection is not owned by this user.")
            instrument: Instrument | None = self.db.get(Instrument, order.instrument_id)
            if instrument is None:
                raise ValueError("The order instrument no longer exists.")
            if record.instrument_token != instrument.instrument_key:
                raise ValueError("Broker trade instrument does not match the local order.")
            if record.side != order.side or record.side not in {"BUY", "SELL"}:
                raise ValueError("Broker trade side does not match the local order.")
            if type(record.quantity) is not int or record.quantity <= 0:
                raise ValueError("Broker trade quantity is invalid.")
            price = Decimal(str(record.price))
            if not price.is_finite() or price <= 0:
                raise ValueError("Broker trade price is invalid.")
            executed_at = self._parse_exchange_timestamp(record.exchange_timestamp)
            record_snapshot = (
                record.broker_connection_id,
                record.broker_order_ref_id,
                record.broker_trade_id,
                record.quantity,
                Decimal(str(record.price)),
                record.side,
                record.instrument_token,
                record.exchange_timestamp,
            )

            existing = (
                self.db.query(Execution)
                .filter(
                    Execution.broker_connection_id == connection.id,
                    Execution.broker_trade_id == record.broker_trade_id,
                )
                .first()
            )
            if existing is not None:
                # Exact replay exits before charge-evidence locks, so it may safely
                # lock/refresh the trade row here without reversing the ledger lock
                # order used by source verification.
                record = (
                    self.db.query(BrokerTradeRecord)
                    .filter(
                        BrokerTradeRecord.id == broker_trade_record_id,
                        BrokerTradeRecord.broker_order_ref_id == child.id,
                        BrokerTradeRecord.broker_connection_id == child.broker_connection_id,
                    )
                    .with_for_update()
                    .populate_existing()
                    .first()
                )
                if record is None or (
                    record.broker_connection_id,
                    record.broker_order_ref_id,
                    record.broker_trade_id,
                    record.quantity,
                    Decimal(str(record.price)),
                    record.side,
                    record.instrument_token,
                    record.exchange_timestamp,
                ) != record_snapshot:
                    raise ValueError("Broker trade changed during existing-execution replay; review required.")
                if not self._same_execution(existing, record, order, fee_values, charges):
                    raise ValueError("Broker trade already has a conflicting accounted execution.")
                position = self._get_live_position(connection.id, instrument.id)
                if position is None:
                    raise ValueError("Accounted execution exists but its live position row is missing.")
                self.db.rollback()
                return self._result(existing, record, position, inserted=False)

            # Replay/conflict checks precede evidence checks: an already-accounted
            # trade must return idempotently or fail on changed accounting details,
            # without requiring callers to resubmit evidence metadata on every retry.
            if charges.evidence_id is None or charges.reviewer_user_id is None:
                raise ValueError("A persisted reviewed contract-note evidence record is required for live-fill accounting.")
            require_reviewed_charge_evidence(
                self.db,
                evidence_id=charges.evidence_id,
                broker_connection_id=connection.id,
                broker_report_reference=charges.reference,
                reviewer_user_id=charges.reviewer_user_id,
                lock=False,
            )

            staged_child_quantity = (
                self.db.query(func.coalesce(func.sum(BrokerTradeRecord.quantity), 0))
                .filter(
                    BrokerTradeRecord.broker_connection_id == connection.id,
                    BrokerTradeRecord.broker_order_ref_id == child.id,
                )
                .scalar()
            )
            if int(staged_child_quantity or 0) != int(child.filled_quantity or 0):
                raise ValueError(
                    "Durable broker trade quantity does not match broker-confirmed child fill quantity; reconciliation required."
                )

            self._ensure_exchange_order(record, connection.id, instrument.instrument_key, executed_at)

            # A child order's filled_quantity is an aggregate cap, not a per-trade
            # cap. The child row is locked above so concurrent promotions for the
            # same child are serialized on PostgreSQL.
            accounted_quantity = (
                self.db.query(func.coalesce(func.sum(Execution.quantity), 0))
                .filter(
                    Execution.broker_order_ref_id == child.id,
                    Execution.broker_connection_id == connection.id,
                )
                .scalar()
            )
            if int(accounted_quantity or 0) + record.quantity > child.filled_quantity:
                raise ValueError(
                    "Cumulative accounted trade quantity exceeds the broker-confirmed child-order fill quantity."
                )
            accounted_order_quantity = (
                self.db.query(func.coalesce(func.sum(Execution.quantity), 0))
                .filter(
                    Execution.order_id == order.id,
                    Execution.broker_connection_id == connection.id,
                )
                .scalar()
            )
            if int(accounted_order_quantity or 0) + record.quantity > order.quantity:
                raise ValueError(
                    "Cumulative accounted trade quantity exceeds the local order quantity."
                )

            # Validate the allocation ledger after structural quantity/order checks,
            # but before creating or mutating any accounting rows. Caller-supplied
            # amounts are only a consistency assertion against the persisted ledger.
            fee_values = self._load_reconciled_allocation_fees(
                evidence_id=charges.evidence_id,
                broker_connection_id=connection.id,
                broker_trade_record_id=record.id,
                reviewer_user_id=charges.reviewer_user_id,
                supplied_fees=fee_values,
                broker_report_reference=charges.reference,
                require_demat=(order.segment == "EQUITY_DELIVERY" and record.side == "SELL"),
            )

            # The verification path now owns the evidence -> component ->
            # allocation -> trade lock order. Refresh the trade after those locks
            # are acquired and fail closed if any intake fields changed meanwhile.
            locked_record = (
                self.db.query(BrokerTradeRecord)
                .filter(
                    BrokerTradeRecord.id == broker_trade_record_id,
                    BrokerTradeRecord.broker_order_ref_id == child.id,
                    BrokerTradeRecord.broker_connection_id == child.broker_connection_id,
                )
                .with_for_update()
                .populate_existing()
                .first()
            )
            if locked_record is None:
                raise ValueError("Broker trade mapping changed during charge verification.")
            locked_snapshot = (
                locked_record.broker_connection_id,
                locked_record.broker_order_ref_id,
                locked_record.broker_trade_id,
                locked_record.quantity,
                Decimal(str(locked_record.price)),
                locked_record.side,
                locked_record.instrument_token,
                locked_record.exchange_timestamp,
            )
            if locked_snapshot != record_snapshot:
                raise ValueError("Broker trade changed during charge verification; manual reconciliation required.")
            record = locked_record

            portfolio = (
                self.db.query(Portfolio)
                .filter(Portfolio.id == order.portfolio_id, Portfolio.user_id == user_id)
                .with_for_update()
                .first()
            )
            if portfolio is None or not portfolio.is_active:
                raise ValueError("Order portfolio is missing or inactive.")

            position = self._get_live_position(connection.id, instrument.id, lock=True)
            if position is None:
                position = LivePosition(
                    broker_connection_id=connection.id,
                    instrument_id=instrument.id,
                    quantity=0,
                    avg_price=Decimal("0"),
                    realized_pnl=Decimal("0"),
                )
                self.db.add(position)
                self.db.flush()

            side = Side(record.side)
            update = apply_fill(
                position_quantity=position.quantity,
                position_avg_price=Decimal(str(position.avg_price)),
                side=side,
                fill_quantity=record.quantity,
                fill_price=price,
            )
            position.quantity = update.new_quantity
            position.avg_price = update.new_avg_price
            position.realized_pnl = Decimal(str(position.realized_pnl)) + update.realized_pnl

            gross_value = (price * Decimal(record.quantity)).quantize(CENT, rounding=ROUND_HALF_UP)
            execution = Execution(
                order_id=order.id,
                portfolio_id=portfolio.id,
                instrument_id=instrument.id,
                side=record.side,
                quantity=record.quantity,
                price=price,
                gross_value=gross_value,
                brokerage=fee_values["brokerage"],
                stt=fee_values["stt"],
                exchange_charges=fee_values["exchange_charges"],
                sebi_charges=fee_values["sebi_charges"],
                stamp_duty=fee_values["stamp_duty"],
                gst=fee_values["gst"],
                total_charges=fee_values["total_charges"],
                demat_transaction_charges=fee_values.get("demat_transaction_charges"),
                demat_charge_status=(
                    "KNOWN" if fee_values.get("demat_transaction_charges") is not None
                    else "NOT_APPLICABLE"
                ),
                charge_source=charges.source,
                charge_reference=charges.reference.strip(),
                charge_evidence_id=charges.evidence_id,
                realized_pnl=update.realized_pnl,
                strategy_realized_pnl=None,
                broker_order_ref_id=child.id,
                broker_name=child.broker_name,
                broker_connection_id=connection.id,
                broker_trade_id=record.broker_trade_id,
                executed_at=executed_at,
            )
            self.db.add_all([position, execution])
            self.db.commit()
            self.db.refresh(execution)
            self.db.refresh(position)
            return self._result(execution, record, position, inserted=True)
        except IntegrityError:
            self.db.rollback()
            # A concurrent promotion may have won the unique trade-ID race.
            record = self.db.get(BrokerTradeRecord, broker_trade_record_id)
            if record is not None:
                existing = (
                    self.db.query(Execution)
                    .filter(
                        Execution.broker_connection_id == record.broker_connection_id,
                        Execution.broker_trade_id == record.broker_trade_id,
                    )
                    .first()
                )
                if existing is not None:
                    position = self._get_live_position(
                        record.broker_connection_id,
                        existing.instrument_id,
                    )
                    order = self.db.get(Order, existing.order_id)
                    fee_values = self._validate_charges(charges)
                    if (
                        position is not None
                        and order is not None
                        and self._same_execution(existing, record, order, fee_values, charges)
                    ):
                        return self._result(existing, record, position, inserted=False)
            raise ValueError("Concurrent live fill promotion conflict; review required.") from None
        except Exception:
            self.db.rollback()
            raise

    def _load_reconciled_allocation_fees(
        self,
        *,
        evidence_id: UUID,
        broker_connection_id: UUID,
        broker_trade_record_id: UUID,
        reviewer_user_id: UUID,
        supplied_fees: dict[str, Decimal],
        broker_report_reference: str,
        require_demat: bool = False,
    ) -> dict[str, Decimal]:
        """Load actual fees from the six core snapshots and optional DP snapshot.

        Lock order is canonical snapshots (sorted by component) -> evidence ->
        source rows -> allocation rows -> reviewer/trade rows. All six snapshots
        are locked before any verifier locks the shared evidence row, preventing
        cross-component verification deadlocks. Legacy raw-component allocations
        are not an accounting fallback.
        """
        names = LIVE_FILL_ACCOUNTING_COMPONENTS
        demat_name = "demat_transaction_charges"
        snapshots = (
            self.db.query(BrokerChargeCanonicalComponent)
            .filter(BrokerChargeCanonicalComponent.evidence_id == evidence_id)
            .order_by(BrokerChargeCanonicalComponent.canonical_component)
            .with_for_update()
            .populate_existing()
            .all()
        )
        by_name = {row.canonical_component: row for row in snapshots}
        allowed_names = set(names) | {demat_name}
        required_names = set(names) | ({demat_name} if require_demat else set())
        if (
            len(snapshots) != len(by_name)
            or not required_names.issubset(set(by_name))
            or not set(by_name).issubset(allowed_names)
        ):
            raise ValueError(
                "Live accounting requires six core canonical snapshots and a reviewed DP snapshot for eligible delivery sells."
            )
        if any(
            snapshot.status != "VERIFIED"
            or snapshot.reviewed_by_user_id is None
            or snapshot.reviewed_at is None
            or snapshot.component_set_version != LIVE_FILL_COMPONENT_SET_VERSION
            for snapshot in snapshots
        ):
            raise ValueError("Every canonical charge snapshot must be independently verified.")

        # The complete snapshot set is locked first. The verifier rechecks source
        # bytes, source links, representation mapping, snapshot fingerprint,
        # exact fill manifest, explicit weights, deterministic amounts and
        # durable reconciliation references inside this transaction.
        verifications: dict[str, dict[str, object]] = {}
        for name in sorted(by_name):
            snapshot = by_name[name]
            verification = verify_canonical_component_allocation_ledger(
                self.db, snapshot_id=snapshot.id
            )
            if (
                verification.get("status") != "ALREADY_RECONCILED"
                or verification.get("canonical_component") != name
                or verification.get("evidence_id") != str(evidence_id)
            ):
                raise ValueError(
                    "Every canonical charge component must be fully verified and reconciled before accounting."
                )
            verifications[name] = verification
            if name == demat_name:
                self._validate_demat_manifest_eligibility(
                    snapshot, broker_connection_id=broker_connection_id
                )

        # The canonical verifier has locked and refreshed the evidence row.
        evidence = (
            self.db.query(BrokerChargeEvidence)
            .filter(BrokerChargeEvidence.id == evidence_id)
            .with_for_update()
            .populate_existing()
            .one_or_none()
        )
        if (
            evidence is None
            or evidence.broker_connection_id != broker_connection_id
            or evidence.source_kind != "CONTRACT_NOTE"
            or evidence.status != "REVIEWED"
            or evidence.reviewed_by_user_id is None
            or evidence.reviewed_by_user_id != reviewer_user_id
            or not evidence.broker_report_reference
            or evidence.broker_report_reference.strip() != broker_report_reference.strip()
        ):
            raise ValueError("Canonical charge evidence no longer matches the reviewed broker connection.")
        # Reference comparison is repeated after the evidence row is locked.
        if evidence.broker_report_reference.strip() == "":
            raise ValueError("Reviewed broker contract-note reference is required.")

        # Include every allocation row for this fill, not only canonical-linked
        # rows, so an extra legacy/IPFT/unmapped row cannot be silently ignored.
        fill_rows = (
            self.db.query(BrokerChargeAllocation)
            .filter(
                BrokerChargeAllocation.evidence_id == evidence_id,
                BrokerChargeAllocation.broker_trade_record_id == broker_trade_record_id,
            )
            .order_by(BrokerChargeAllocation.charge_component, BrokerChargeAllocation.id)
            .with_for_update()
            .populate_existing()
            .all()
        )
        required_fill_names = set(names) | ({demat_name} if require_demat else set())
        if len(fill_rows) != len(required_fill_names) or {row.charge_component for row in fill_rows} != required_fill_names:
            raise ValueError(
                "Live accounting requires exactly the applicable canonical per-fill allocations; missing DP or extra/unmapped rows block promotion."
            )
        for row in fill_rows:
            snapshot = by_name.get(row.charge_component)
            if (
                snapshot is None
                or row.canonical_component_id != snapshot.id
                or row.broker_connection_id != broker_connection_id
                or row.status != "RECONCILED"
                or row.currency != "INR"
                or not row.reconciliation_reference
            ):
                raise ValueError(
                    "Every per-fill charge allocation must link to its verified canonical snapshot and durable reconciliation."
                )

        derived = {
            row.charge_component: Decimal(str(row.allocated_amount)).quantize(CENT)
            for row in fill_rows
        }
        for name in required_fill_names:
            verification = verifications[name]
            if not verification.get("allocation_ids"):
                raise ValueError("Canonical component verifier returned no reconciled allocation IDs.")
            if not any(
                str(row.id) in set(verification["allocation_ids"])
                and row.charge_component == name
                and row.canonical_component_id == by_name[name].id
                for row in fill_rows
            ):
                raise ValueError("Per-fill allocation does not match the verified canonical allocation ledger.")

        if any(supplied_fees[name] != derived[name] for name in names):
            raise ValueError("Caller-supplied charge amounts differ from the reconciled canonical per-fill allocation ledger.")
        if require_demat:
            if supplied_fees.get(demat_name) is None or supplied_fees[demat_name] != derived.get(demat_name):
                raise ValueError("Delivery-sell DP/demat amount differs from the reconciled canonical per-fill allocation ledger.")
        elif supplied_fees.get(demat_name) is not None or demat_name in derived:
            raise ValueError("DP/demat allocation is not applicable to this fill and cannot be silently included.")
        total = sum((derived[name] for name in names), Decimal("0"))
        if require_demat:
            total += derived[demat_name]
        total = total.quantize(CENT)
        if supplied_fees["total_charges"] != total:
            raise ValueError("Total charges do not equal the reconciled canonical per-fill allocation ledger.")

        reviewer = (
            self.db.query(User)
            .filter(User.id == reviewer_user_id)
            .with_for_update()
            .populate_existing()
            .one_or_none()
        )
        if reviewer is None or not reviewer.is_active or not reviewer.is_admin:
            raise ValueError("Only an active platform administrator may promote live-fill accounting.")
        return {**derived, "total_charges": total}


    def _validate_demat_manifest_eligibility(
        self,
        snapshot: BrokerChargeCanonicalComponent,
        *,
        broker_connection_id: UUID,
    ) -> None:
        """Require every DP-manifest fill to be a mapped equity-delivery SELL.

        A reviewer-provided manifest is not sufficient by itself: verify each
        fill against the staged broker trade, child order and local order so DP
        cannot be allocated to BUY or non-delivery executions.
        """
        try:
            manifest = json.loads(snapshot.eligible_fill_ids_json or "")
            if not isinstance(manifest, list) or not manifest:
                raise ValueError
            fill_ids = [UUID(value) for value in manifest]
        except (TypeError, ValueError, json.JSONDecodeError):
            raise ValueError("DP/demat manifest must contain valid persisted fill IDs.") from None

        if len(set(fill_ids)) != len(fill_ids):
            raise ValueError("DP/demat manifest cannot contain duplicate fill IDs.")
        rows = (
            self.db.query(
                BrokerTradeRecord.id,
                BrokerTradeRecord.broker_connection_id,
                BrokerTradeRecord.side,
                BrokerTradeRecord.instrument_token,
                BrokerOrder.broker_connection_id,
                BrokerOrder.broker_name,
                Order.segment,
                Order.side,
                Instrument.instrument_key,
                BrokerConnection.broker,
                BrokerConnection.user_id,
                Portfolio.user_id,
            )
            .join(BrokerOrder, BrokerOrder.id == BrokerTradeRecord.broker_order_ref_id)
            .join(Order, Order.id == BrokerOrder.order_id)
            .join(Instrument, Instrument.id == Order.instrument_id)
            .join(BrokerConnection, BrokerConnection.id == BrokerOrder.broker_connection_id)
            .join(Portfolio, Portfolio.id == Order.portfolio_id)
            .filter(BrokerTradeRecord.id.in_(fill_ids))
            .all()
        )
        if len(rows) != len(fill_ids) or any(
            trade_connection_id != broker_connection_id
            or child_connection_id != broker_connection_id
            or trade_side != "SELL"
            or segment != "EQUITY_DELIVERY"
            or order_side != "SELL"
            or trade_instrument_token != local_instrument_key
            or child_broker_name != connection_broker
            or portfolio_user_id != connection_user_id
            for (
                _fill_id,
                trade_connection_id,
                trade_side,
                trade_instrument_token,
                child_connection_id,
                child_broker_name,
                segment,
                order_side,
                local_instrument_key,
                connection_broker,
                connection_user_id,
                portfolio_user_id,
            ) in rows
        ):
            raise ValueError(
                "DP/demat manifest may include only mapped equity-delivery SELL fills for the reviewed broker connection."
            )

    def _ensure_exchange_order(
        self,
        current_record: BrokerTradeRecord,
        connection_id: UUID,
        instrument_token: str,
        current_time: datetime,
    ) -> None:
        """Fail closed if staged/accounted fills prove promotion would be out of exchange-time order.

        The broker-connection row is locked by the caller so trade ingestion and
        accounting promotion serialize on the same account boundary.
        """
        staged = (
            self.db.query(BrokerTradeRecord)
            .filter(
                BrokerTradeRecord.broker_connection_id == connection_id,
                BrokerTradeRecord.instrument_token == instrument_token,
            )
            .all()
        )
        if len(staged) < 2:
            return
        trade_ids = [item.broker_trade_id for item in staged]
        accounted = (
            self.db.query(Execution)
            .filter(
                Execution.broker_connection_id == connection_id,
                Execution.broker_trade_id.in_(trade_ids),
            )
            .all()
        )
        executions_by_trade_id = {item.broker_trade_id: item for item in accounted}

        for candidate in staged:
            if candidate.id == current_record.id:
                continue
            try:
                candidate_time = self._parse_exchange_timestamp(candidate.exchange_timestamp)
            except ValueError:
                raise ValueError(
                    "Another staged broker trade has an invalid exchange timestamp; manual review required."
                ) from None

            prior_execution = executions_by_trade_id.get(candidate.broker_trade_id)
            if prior_execution is not None:
                prior_time = prior_execution.executed_at
                if prior_time.tzinfo is None or prior_time.utcoffset() is None:
                    prior_time = prior_time.replace(tzinfo=timezone.utc)
                else:
                    prior_time = prior_time.astimezone(timezone.utc)
                if prior_time > current_time:
                    raise ValueError(
                        "An earlier broker trade cannot be promoted after a later trade was accounted; manual review required."
                    )
            elif candidate_time < current_time:
                raise ValueError(
                    "An earlier broker trade is still unaccounted; promote trades in exchange-time order."
                )

            if candidate_time == current_time and (
                candidate.side != current_record.side
                or Decimal(str(candidate.price)) != Decimal(str(current_record.price))
            ):
                raise ValueError(
                    "Trades for the same instrument have ambiguous exchange timestamps; manual review required."
                )

    @staticmethod
    def _validate_charges(charges: LiveFillChargeBreakdown) -> dict[str, Decimal]:
        if not isinstance(charges, LiveFillChargeBreakdown):
            raise ValueError("An explicit validated live-fill charge breakdown is required.")
        if charges.source != "BROKER_REPORTED":
            raise ValueError("Live fill promotion requires broker-reported charges, not estimates.")
        if not isinstance(charges.reference, str) or not charges.reference.strip():
            raise ValueError("Broker-reported charges require a non-empty audit reference.")
        if len(charges.reference.strip()) > 200:
            raise ValueError("Broker-reported charge audit reference must be at most 200 characters.")
        names = (
            "brokerage", "stt", "exchange_charges", "sebi_charges",
            "stamp_duty", "gst", "total_charges",
        )
        values: dict[str, Decimal] = {}
        for name in names:
            raw = getattr(charges, name)
            try:
                amount = Decimal(str(raw))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError(f"Live-fill charge {name} is invalid.") from None
            if not amount.is_finite() or amount < 0:
                raise ValueError(f"Live-fill charge {name} must be finite and non-negative.")
            if amount != amount.quantize(CENT):
                raise ValueError(f"Live-fill charge {name} must be expressed to paise precision.")
            values[name] = amount
        raw_demat = charges.demat_transaction_charges
        if raw_demat is not None:
            try:
                demat = Decimal(str(raw_demat))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError("Live-fill DP/demat charge is invalid.") from None
            if not demat.is_finite() or demat < 0 or demat != demat.quantize(CENT):
                raise ValueError("Live-fill DP/demat charge must be finite, non-negative and paise-exact.")
            values["demat_transaction_charges"] = demat
        else:
            values["demat_transaction_charges"] = None
        component_sum = sum(values[name] for name in names[:-1])
        if raw_demat is not None:
            component_sum += values["demat_transaction_charges"]
        if values["total_charges"] != component_sum:
            raise ValueError("Live-fill total_charges must equal the sum of the six core components and any applicable DP/demat charge.")
        return values

    @staticmethod
    def _parse_exchange_timestamp(value: str | None) -> datetime:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Broker trade exchange timestamp is required for live accounting.")
        try:
            parsed = datetime.fromisoformat(value.strip())
        except ValueError:
            raise ValueError("Broker trade exchange timestamp is not valid ISO-8601.") from None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("Broker trade exchange timestamp must include a timezone offset.")
        return parsed.astimezone(timezone.utc)

    def _get_live_position(self, connection_id: UUID, instrument_id: UUID, lock: bool = False) -> LivePosition | None:
        query = self.db.query(LivePosition).filter(
            LivePosition.broker_connection_id == connection_id,
            LivePosition.instrument_id == instrument_id,
        )
        if lock:
            query = query.with_for_update().populate_existing()
        return query.first()

    @staticmethod
    def _same_execution(
        execution: Execution,
        record: BrokerTradeRecord,
        order: Order,
        fees: dict[str, Decimal],
        charges: LiveFillChargeBreakdown,
    ) -> bool:
        return (
            execution.order_id == order.id
            and execution.portfolio_id == order.portfolio_id
            and execution.instrument_id == order.instrument_id
            and execution.broker_order_ref_id == record.broker_order_ref_id
            and execution.broker_trade_id == record.broker_trade_id
            and execution.broker_name == "upstox"
            and execution.quantity == record.quantity
            and Decimal(str(execution.price)) == Decimal(str(record.price))
            and Decimal(str(execution.gross_value)) == (
                Decimal(str(record.price)) * Decimal(record.quantity)
            ).quantize(CENT, rounding=ROUND_HALF_UP)
            and execution.side == record.side
            and execution.executed_at.replace(tzinfo=timezone.utc) == (
                LiveFillAccountingService._parse_exchange_timestamp(record.exchange_timestamp)
                .replace(tzinfo=timezone.utc)
            )
            and execution.charge_source == charges.source
            and execution.charge_reference == charges.reference.strip()
            # A replay may omit evidence metadata; if supplied, its identity must
            # match. New promotions separately require reviewed evidence below.
            and (charges.evidence_id is None or execution.charge_evidence_id == charges.evidence_id)
            and Decimal(str(execution.brokerage)) == fees["brokerage"]
            and Decimal(str(execution.stt)) == fees["stt"]
            and Decimal(str(execution.exchange_charges)) == fees["exchange_charges"]
            and Decimal(str(execution.sebi_charges)) == fees["sebi_charges"]
            and Decimal(str(execution.stamp_duty)) == fees["stamp_duty"]
            and Decimal(str(execution.gst)) == fees["gst"]
            and (
                Decimal(str(execution.demat_transaction_charges)) == fees["demat_transaction_charges"]
                if fees.get("demat_transaction_charges") is not None
                else execution.demat_transaction_charges is None
            )
            and execution.demat_charge_status == (
                "KNOWN" if fees.get("demat_transaction_charges") is not None else "NOT_APPLICABLE"
            )
            and Decimal(str(execution.total_charges)) == fees["total_charges"]
        )

    @staticmethod
    def _result(
        execution: Execution,
        record: BrokerTradeRecord,
        position: LivePosition,
        *,
        inserted: bool,
    ) -> LiveFillAccountingResult:
        return LiveFillAccountingResult(
            execution_id=execution.id,
            broker_trade_id=record.broker_trade_id,
            inserted=inserted,
            live_position_quantity=position.quantity,
            live_position_average_price=Decimal(str(position.avg_price)),
            realized_pnl=Decimal(str(execution.realized_pnl)),
        )
