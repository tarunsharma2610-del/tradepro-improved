"""Read-only Upstox reconciliation orchestration.

This worker reads broker orders/trades and persists validated evidence only.
It never receives the general write-capable BrokerAdapter and cannot submit,
modify, or cancel orders. It is not automatically scheduled by this module.
"""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.brokers.upstox.reconciliation_client import (
    ReadOnlyBrokerResult,
    UpstoxReadOnlyReconciliationClient,
)
from app.models.broker_connection import BrokerConnection
from app.models.live_order_records import BrokerFillIdentity, LiveOrderIntent
from app.repositories.live_order_repository import LiveOrderRepository
from app.repositories.live_reconciliation_lease_repository import LiveReconciliationLeaseRepository
from app.repositories.live_order_reconciliation_run_repository import LiveReconciliationRunRepository
from app.repositories.live_reconciliation_issue_repository import LiveReconciliationIssueRepository
from app.services.live_order_reconciliation import (
    BrokerOrderDataError,
    ReconciliationIntentCandidate,
    match_broker_order_to_intent,
    normalize_upstox_order,
    normalize_upstox_trade,
)


@dataclass
class ReconciliationRunResult:
    status: str
    error_code: str | None = None
    orders_seen: int = 0
    orders_matched: int = 0
    orders_unmatched: int = 0
    trades_seen: int = 0
    fills_inserted: int = 0
    duplicate_fills: int = 0
    conflicts: int = 0
    run_id: UUID | None = None

    def safe_summary(self) -> dict[str, int]:
        return {
            "orders_seen": self.orders_seen,
            "orders_matched": self.orders_matched,
            "orders_unmatched": self.orders_unmatched,
            "trades_seen": self.trades_seen,
            "fills_inserted": self.fills_inserted,
            "duplicate_fills": self.duplicate_fills,
            "conflicts": self.conflicts,
        }


_LEASE_RENEWAL_BATCH_SIZE = 5


class _WorkerFailure(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class LiveOrderReconciliationWorker:
    """Run one owner-scoped, leased, read-only reconciliation pass."""

    _RETRYABLE = {"RATE_LIMITED", "UPSTREAM_SERVER_ERROR", "TIMEOUT", "NETWORK_ERROR"}

    def __init__(
        self,
        db: Session,
        *,
        client: UpstoxReadOnlyReconciliationClient | None = None,
        token_provider: Callable[[UUID], str | None] | None = None,
        sleeper: Callable[[float], Awaitable[Any]] = asyncio.sleep,
        max_attempts: int = 3,
        base_delay_seconds: float = 0.5,
        max_delay_seconds: float = 10.0,
        lease_seconds: int = 300,
    ):
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= 5:
            raise ValueError("max_attempts must be between 1 and 5")
        if base_delay_seconds < 0 or max_delay_seconds < base_delay_seconds:
            raise ValueError("retry delay bounds are invalid")
        self.db = db
        self.client = client or UpstoxReadOnlyReconciliationClient()
        self.token_provider = token_provider
        self.sleeper = sleeper
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.lease_seconds = lease_seconds
        self.lease_repository = LiveReconciliationLeaseRepository(db)
        self.run_repository = LiveReconciliationRunRepository(db)
        self.issue_repository = LiveReconciliationIssueRepository(db)
        self.order_repository = LiveOrderRepository(db)

    async def run_for_connection(
        self, *, user_id: UUID, broker_connection_id: UUID
    ) -> ReconciliationRunResult:
        connection = self.db.query(BrokerConnection).filter(
            BrokerConnection.id == broker_connection_id,
            BrokerConnection.user_id == user_id,
        ).first()
        if connection is None:
            return ReconciliationRunResult(status="FAILED", error_code="CONNECTION_NOT_FOUND")
        if connection.broker.lower() != "upstox":
            return ReconciliationRunResult(status="FAILED", error_code="UNSUPPORTED_BROKER")
        if not connection.is_connected:
            return ReconciliationRunResult(status="FAILED", error_code="CONNECTION_NOT_READY")

        # Recover old RUNNING summaries before claiming a new lease. The
        # repository locks the existing lease row and refuses recovery while an
        # unexpired owner exists; doing this before claim avoids mistaking our
        # own newly claimed lease for an active orphan.
        recovery_now = datetime.now(timezone.utc)
        try:
            self.run_repository.fail_orphaned_runs(
                user_id=user_id,
                broker_connection_id=broker_connection_id,
                stale_before=recovery_now - timedelta(seconds=self.lease_seconds),
                now=recovery_now,
            )
        except Exception:
            self.db.rollback()
            return ReconciliationRunResult(
                status="FAILED", error_code="STALE_RUN_RECOVERY_FAILED"
            )

        lease_token = self.lease_repository.claim(
            user_id=user_id,
            broker_connection_id=broker_connection_id,
            lease_seconds=self.lease_seconds,
        )
        if lease_token is None:
            return ReconciliationRunResult(status="LEASE_BUSY", error_code="LEASE_BUSY")

        try:
            run = self.run_repository.start(
                user_id=user_id,
                broker_connection_id=broker_connection_id,
            )
        except Exception:
            self.lease_repository.complete(
                user_id=user_id,
                broker_connection_id=broker_connection_id,
                lease_token=lease_token,
                error_code="RUN_RECORD_CREATE_FAILED",
            )
            return ReconciliationRunResult(status="FAILED", error_code="RUN_RECORD_CREATE_FAILED")

        try:
            result = await self._run_claimed(user_id, broker_connection_id, lease_token, run_id=run.id)
        except _WorkerFailure as exc:
            result = ReconciliationRunResult(status="FAILED", error_code=exc.code)
        except Exception:
            # Do not surface exception text: it may include upstream details or credentials.
            result = ReconciliationRunResult(status="FAILED", error_code="INTERNAL_ERROR")

        completion_error = result.error_code
        if result.status == "COMPLETED_WITH_CONFLICTS" and completion_error is None:
            completion_error = "RECONCILIATION_CONFLICTS"
        result.run_id = run.id
        try:
            final_status = self.run_repository.finish_with_lease(
                run_id=run.id,
                user_id=user_id,
                broker_connection_id=broker_connection_id,
                lease_token=lease_token,
                status=result.status,
                error_code=result.error_code,
                lease_error_code=completion_error,
                summary=result.safe_summary(),
            )
            if final_status == "LEASE_LOST":
                result.status = "LEASE_LOST"
                result.error_code = "LEASE_LOST"
        except Exception:
            # Finalizing the run and releasing the lease share one transaction.
            # A failed summary write rolls back the lease release as well.
            self.db.rollback()
            result.status = "FAILED"
            result.error_code = "RUN_SUMMARY_PERSISTENCE_FAILED"
        return result

    def _get_access_token(self, user_id: UUID) -> str | None:
        if self.token_provider is not None:
            return self.token_provider(user_id)
        from app.services.broker_credentials_service import BrokerCredentialsService
        return BrokerCredentialsService(self.db).get_access_token(user_id, "upstox")

    async def _read_with_retry(
        self,
        method: Callable[..., Awaitable[ReadOnlyBrokerResult]],
        access_token: str,
    ) -> ReadOnlyBrokerResult:
        last: ReadOnlyBrokerResult | None = None
        for attempt in range(self.max_attempts):
            last = await method(access_token)
            if last.ok:
                return last
            if last.error_code not in self._RETRYABLE or attempt + 1 >= self.max_attempts:
                raise _WorkerFailure(last.error_code or "UPSTREAM_ERROR")
            retry_after = last.retry_after_seconds
            delay = retry_after if retry_after is not None else self.base_delay_seconds * (2 ** attempt)
            await self.sleeper(min(self.max_delay_seconds, max(0.0, delay)))
        raise _WorkerFailure(last.error_code if last and last.error_code else "UPSTREAM_ERROR")

    @staticmethod
    def _data_list(result: ReadOnlyBrokerResult) -> list[dict[str, Any]]:
        body = result.data
        if not isinstance(body, dict) or str(body.get("status", "")).lower() != "success":
            raise _WorkerFailure("INVALID_RESPONSE_ENVELOPE")
        data = body.get("data")
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise _WorkerFailure("INVALID_RESPONSE_DATA")
        return data

    def _renew_or_fail(self, user_id: UUID, connection_id: UUID, token: UUID) -> None:
        if not self.lease_repository.renew(
            user_id=user_id,
            broker_connection_id=connection_id,
            lease_token=token,
            lease_seconds=self.lease_seconds,
        ):
            raise _WorkerFailure("LEASE_LOST")

    def _fence_write(self, user_id: UUID, connection_id: UUID, lease_token: UUID) -> None:
        """Fail closed unless this worker can lock its live lease for this write."""
        if not self.lease_repository.fence_for_write(
            user_id=user_id,
            broker_connection_id=connection_id,
            lease_token=lease_token,
        ):
            raise _WorkerFailure("LEASE_LOST")
    async def _run_claimed(
        self, user_id: UUID, connection_id: UUID, lease_token: UUID, *, run_id: UUID
    ) -> ReconciliationRunResult:
        access_token = self._get_access_token(user_id)
        if not access_token:
            raise _WorkerFailure("TOKEN_UNAVAILABLE")

        # Fetch both snapshots before mutating local reconciliation state. If either
        # read fails, this pass performs no order/fill persistence.
        order_response = await self._read_with_retry(self.client.get_order_book, access_token)
        trade_response = await self._read_with_retry(self.client.get_trades_for_day, access_token)
        order_records = self._data_list(order_response)
        trade_records = self._data_list(trade_response)
        self._renew_or_fail(user_id, connection_id, lease_token)

        result = ReconciliationRunResult(status="COMPLETED")
        intents = self.db.query(LiveOrderIntent).filter(
            LiveOrderIntent.user_id == user_id,
            LiveOrderIntent.broker_connection_id == connection_id,
        ).all()
        candidates = [
            ReconciliationIntentCandidate(
                intent_id=str(intent.id),
                broker_connection_id=str(intent.broker_connection_id),
                broker_order_id=intent.broker_order_id,
                broker_tag=intent.broker_tag,
                order_snapshot=intent.order_snapshot or {},
            )
            for intent in intents
        ]

        # Persist daily trade identities as unmatched first. Linking is a separate,
        # validated step after an order has been matched to an intent.
        result.trades_seen = len(trade_records)
        for index, record in enumerate(trade_records):
            if index % _LEASE_RENEWAL_BATCH_SIZE == 0:
                self._renew_or_fail(user_id, connection_id, lease_token)
            try:
                trade = normalize_upstox_trade(record)
                if not trade.product or not trade.order_type:
                    raise BrokerOrderDataError("trade is missing product/order type")
            except BrokerOrderDataError:
                result.conflicts += 1
                self._fence_write(user_id, connection_id, lease_token)
                self.issue_repository.record(
                    user_id=user_id, broker_connection_id=connection_id, run_id=run_id,
                    issue_type="INVALID_TRADE_RECORD",
                    safe_details={"record_index": index, "reason_code": "TRADE_NORMALIZATION_FAILED"},
                )
                continue

            details = {
                key: value for key, value in {
                    "exchange": trade.exchange,
                    "trading_symbol": trade.trading_symbol,
                    "exchange_order_id": trade.exchange_order_id,
                    "order_ref_id": trade.order_ref_id,
                }.items() if value is not None
            }
            try:
                self._fence_write(user_id, connection_id, lease_token)
                _, inserted = self.order_repository.record_broker_fill(
                    user_id=user_id,
                    broker_connection_id=connection_id,
                    broker_trade_id=trade.broker_trade_id,
                    broker_order_id=trade.broker_order_id,
                    instrument_key=trade.instrument_key,
                    side=trade.side,
                    quantity=trade.quantity,
                    price=trade.price,
                    executed_at=trade.executed_at,
                    product=trade.product,
                    order_type=trade.order_type,
                    intent_id=None,
                    safe_details=details,
                    correlation_id=f"reconcile:{connection_id}",
                )
                if inserted:
                    result.fills_inserted += 1
                else:
                    result.duplicate_fills += 1
            except (ValueError, RuntimeError):
                result.conflicts += 1
                self._fence_write(user_id, connection_id, lease_token)
                self.issue_repository.record(
                    user_id=user_id, broker_connection_id=connection_id, run_id=run_id,
                    issue_type="TRADE_PERSISTENCE_CONFLICT",
                    broker_order_id=trade.broker_order_id, broker_trade_id=trade.broker_trade_id,
                    safe_details={"reason_code": "TRADE_RECORD_REJECTED"},
                )

        for index, record in enumerate(order_records):
            if index % _LEASE_RENEWAL_BATCH_SIZE == 0:
                self._renew_or_fail(user_id, connection_id, lease_token)
            result.orders_seen += 1
            try:
                order = normalize_upstox_order(record)
            except BrokerOrderDataError:
                result.conflicts += 1
                self._fence_write(user_id, connection_id, lease_token)
                self.issue_repository.record(
                    user_id=user_id, broker_connection_id=connection_id, run_id=run_id,
                    issue_type="INVALID_ORDER_RECORD",
                    safe_details={"record_index": index, "reason_code": "ORDER_NORMALIZATION_FAILED"},
                )
                continue
            match = match_broker_order_to_intent(
                order, candidates, broker_connection_id=str(connection_id)
            )
            if match.status != "MATCHED" or match.intent_id is None:
                result.orders_unmatched += 1
                if match.status != "NO_MATCH":
                    result.conflicts += 1
                self._fence_write(user_id, connection_id, lease_token)
                self.issue_repository.record(
                    user_id=user_id, broker_connection_id=connection_id, run_id=run_id,
                    issue_type="UNMATCHED_ORDER" if match.status == "NO_MATCH" else "ORDER_MATCH_REQUIRES_REVIEW",
                    broker_order_id=order.broker_order_id,
                    safe_details={"match_status": match.status, "reason_code": "ORDER_NOT_SAFELY_MATCHED"},
                )
                continue

            try:
                intent_id = UUID(match.intent_id)
            except (ValueError, TypeError):
                result.conflicts += 1
                continue
            intent = self.db.query(LiveOrderIntent).filter(
                LiveOrderIntent.id == intent_id,
                LiveOrderIntent.user_id == user_id,
                LiveOrderIntent.broker_connection_id == connection_id,
            ).first()
            if intent is None:
                result.conflicts += 1
                self._fence_write(user_id, connection_id, lease_token)
                self.issue_repository.record(
                    user_id=user_id, broker_connection_id=connection_id, run_id=run_id,
                    issue_type="MATCHED_INTENT_NOT_FOUND", broker_order_id=order.broker_order_id,
                    safe_details={"reason_code": "MATCHED_INTENT_NOT_FOUND"},
                )
                continue

            # Link the order ID first without treating status alone as fill evidence.
            execution_states = {"FILLED", "PARTIALLY_FILLED", "PARTIALLY_FILLED_CANCELLED"}
            if order.state in execution_states:
                initial_state = intent.state if intent.state in {
                    "CANCELLED", "REJECTED", "FILLED", "PARTIALLY_FILLED",
                    "PARTIALLY_FILLED_CANCELLED", "RECONCILIATION_REQUIRED",
                } else "OPEN"
            else:
                initial_state = order.state
            try:
                self._fence_write(user_id, connection_id, lease_token)
                current, _ = self.order_repository.apply_reconciliation_transition(
                    user_id=user_id,
                    intent_id=intent_id,
                    expected_version=intent.version,
                    new_state=initial_state,
                    broker_order_id=order.broker_order_id,
                    safe_details={
                        "raw_status": order.raw_status,
                        "filled_quantity_reported": order.filled_quantity,
                        "match_status": match.status,
                    },
                    correlation_id=f"reconcile:{connection_id}",
                )
            except (ValueError, RuntimeError):
                result.conflicts += 1
                self._fence_write(user_id, connection_id, lease_token)
                self.issue_repository.record(
                    user_id=user_id, broker_connection_id=connection_id, run_id=run_id,
                    intent_id=intent_id, broker_order_id=order.broker_order_id,
                    issue_type="ORDER_STATUS_TRANSITION_CONFLICT",
                    safe_details={"reason_code": "ORDER_LINK_OR_STATUS_TRANSITION_REJECTED"},
                )
                continue

            # Consume this candidate as soon as its broker order ID is durably linked;
            # a reused tag must not let a second broker order claim the same intent.
            candidates = [candidate for candidate in candidates if candidate.intent_id != match.intent_id]

            # Link only trade rows with this exact broker order ID. Economic checks,
            # quantity caps and limit-price protection run inside the repository.
            fills = self.db.query(BrokerFillIdentity).filter(
                BrokerFillIdentity.broker_connection_id == connection_id,
                BrokerFillIdentity.broker_order_id == order.broker_order_id,
            ).all()
            for fill in fills:
                if fill.intent_id is not None and fill.intent_id != intent_id:
                    result.conflicts += 1
                    continue
                try:
                    self._fence_write(user_id, connection_id, lease_token)
                    self.order_repository.link_existing_fill_to_intent(
                        user_id=user_id,
                        fill_id=fill.id,
                        intent_id=intent_id,
                        correlation_id=f"reconcile:{connection_id}",
                    )
                except (ValueError, RuntimeError):
                    result.conflicts += 1
                    self._fence_write(user_id, connection_id, lease_token)
                    self.issue_repository.record(
                        user_id=user_id, broker_connection_id=connection_id, run_id=run_id,
                        intent_id=intent_id, broker_order_id=order.broker_order_id,
                        broker_trade_id=fill.broker_trade_id, issue_type="FILL_LINK_CONFLICT",
                        safe_details={"reason_code": "FILL_FAILED_INTENT_VALIDATION"},
                    )

            refreshed = self.db.query(LiveOrderIntent).filter(
                LiveOrderIntent.id == intent_id,
                LiveOrderIntent.user_id == user_id,
            ).one()
            try:
                self._fence_write(user_id, connection_id, lease_token)
                resolved_intent, _ = self.order_repository.apply_reconciliation_transition(
                    user_id=user_id,
                    intent_id=intent_id,
                    expected_version=refreshed.version,
                    new_state=order.state,
                    broker_order_id=order.broker_order_id,
                    safe_details={
                        "raw_status": order.raw_status,
                        "filled_quantity_reported": order.filled_quantity,
                        "trade_evidence_checked": True,
                    },
                    correlation_id=f"reconcile:{connection_id}",
                )
                if order.state in execution_states and resolved_intent.state == "UNKNOWN":
                    result.conflicts += 1
                result.orders_matched += 1
            except (ValueError, RuntimeError):
                result.conflicts += 1
                self._fence_write(user_id, connection_id, lease_token)
                self.issue_repository.record(
                    user_id=user_id, broker_connection_id=connection_id, run_id=run_id,
                    intent_id=intent_id, broker_order_id=order.broker_order_id,
                    issue_type="ORDER_STATUS_TRANSITION_CONFLICT",
                    safe_details={"reason_code": "BROKER_STATUS_CONFLICTS_WITH_FILL_EVIDENCE"},
                )

        if result.conflicts:
            result.status = "COMPLETED_WITH_CONFLICTS"
            result.error_code = "RECONCILIATION_CONFLICTS"
        return result
