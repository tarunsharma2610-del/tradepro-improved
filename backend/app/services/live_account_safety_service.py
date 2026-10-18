"""Persistent account-wide kill switch and broker-error circuit breaker.

This service is deliberately not wired into order submission. Callers must
explicitly check the persisted state before any future live order path. Missing
state, stale health checks, unknown circuit states, and database errors fail
closed. Scope is (user, broker), never a single portfolio.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.live_account_safety import LiveAccountSafetyEvent, LiveAccountSafetyState
from app.services.live_execution_service import LiveExecutionBlocked

DEFAULT_BROKER = "upstox"
ALLOWED_CIRCUIT_STATES = {"CLOSED", "OPEN"}
DEFAULT_ERROR_THRESHOLD = 3
DEFAULT_HEALTH_MAX_AGE = timedelta(minutes=5)


@dataclass(frozen=True)
class LiveAccountSafetyDecision:
    allowed: bool
    reason: str
    kill_switch_tripped: bool = True
    circuit_state: str = "UNKNOWN"
    consecutive_broker_errors: int = 0
    state_version: int | None = None


class LiveAccountSafetyService:
    """Manage a durable safety latch and append-only idempotent event history."""

    def __init__(
        self,
        db: Session,
        *,
        clock=None,
        health_max_age: timedelta = DEFAULT_HEALTH_MAX_AGE,
    ):
        self.db = db
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.health_max_age = health_max_age

    def check_allowed(self, user_id: UUID, broker: str = DEFAULT_BROKER) -> LiveAccountSafetyDecision:
        """Read-only fail-closed check. It never creates state or clears a latch."""
        try:
            state = (
                self.db.query(LiveAccountSafetyState)
                .filter(
                    LiveAccountSafetyState.user_id == user_id,
                    LiveAccountSafetyState.broker == self._broker(broker),
                )
                .one_or_none()
            )
            if state is None:
                return LiveAccountSafetyDecision(False, "Persistent live safety state is missing; trading blocked.")
            now = self._now()
            if state.kill_switch_tripped:
                return self._decision(state, False, state.kill_switch_reason or "Account live kill switch is tripped.")
            if state.circuit_state != "CLOSED":
                return self._decision(state, False, state.circuit_reason or "Broker-error circuit is not closed.")
            if state.consecutive_broker_errors != 0:
                return self._decision(state, False, "Broker error counter is not clear; trading blocked.")
            if state.last_health_check_at is None:
                return self._decision(state, False, "No successful safety health check exists; trading blocked.")
            checked_at = self._aware(state.last_health_check_at)
            if checked_at > now or now - checked_at > self.health_max_age:
                return self._decision(state, False, "Safety health check is stale; trading blocked.")
            return self._decision(state, True, "Persistent account safety checks passed.")
        except Exception:
            # A DB outage or malformed state must never authorize trading.
            return LiveAccountSafetyDecision(False, "Persistent live safety state unavailable; trading blocked.")

    def initialize(self, user_id: UUID, *, broker: str = DEFAULT_BROKER,
                   actor_user_id: UUID | None = None, idempotency_key: str) -> LiveAccountSafetyState:
        """Create a fail-safe initial state. Initialization never enables trading."""
        broker = self._broker(broker)
        key = self._key(idempotency_key)
        try:
            existing = self._get_state(user_id, broker, lock=True)
            if existing is not None:
                return existing
            now = self._now()
            state = LiveAccountSafetyState(
                user_id=user_id, broker=broker, kill_switch_tripped=True,
                kill_switch_reason="Initial safety state; explicit health check and manual reset required.",
                kill_switch_tripped_at=now, circuit_state="CLOSED",
                consecutive_broker_errors=0, version=1,
            )
            self.db.add(state)
            self.db.flush()
            self._event(state, actor_user_id, key, "INITIALIZED", state.kill_switch_reason)
            self.db.commit()
            self.db.refresh(state)
            return state
        except IntegrityError:
            self.db.rollback()
            existing = self._get_state(user_id, broker, lock=False)
            if existing is not None:
                return existing
            raise LiveExecutionBlocked("Could not initialize persistent safety state; trading remains blocked.")
        except Exception:
            self.db.rollback()
            raise

    def trip_kill_switch(self, user_id: UUID, reason: str, *, broker: str = DEFAULT_BROKER,
                         actor_user_id: UUID | None = None, idempotency_key: str) -> LiveAccountSafetyState:
        reason = self._reason(reason)
        return self._mutate(
            user_id, broker, actor_user_id, idempotency_key, "KILL_SWITCH_TRIPPED", reason,
            lambda state, now: self._trip(state, now, reason),
        )

    def record_broker_error(self, user_id: UUID, error_code: str, reason: str, *,
                            broker: str = DEFAULT_BROKER, threshold: int = DEFAULT_ERROR_THRESHOLD,
                            actor_user_id: UUID | None = None, idempotency_key: str) -> LiveAccountSafetyState:
        if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 1:
            raise LiveExecutionBlocked("Broker-error threshold must be a positive integer.")
        error_code = self._reason(error_code, "Broker error code")[:100]
        reason = self._reason(reason)
        def change(state, now):
            state.consecutive_broker_errors += 1
            state.last_broker_error_at = now
            state.last_broker_error_code = error_code
            event_type = "BROKER_ERROR"
            if state.consecutive_broker_errors >= threshold:
                state.circuit_state = "OPEN"
                state.circuit_opened_at = state.circuit_opened_at or now
                state.circuit_reason = f"Broker error threshold reached ({threshold}): {reason}"[:500]
                state.kill_switch_tripped = True
                state.kill_switch_reason = state.circuit_reason
                state.kill_switch_tripped_at = now
                event_type = "CIRCUIT_OPENED"
            state.version += 1
            return event_type
        return self._mutate(
            user_id, broker, actor_user_id, idempotency_key, "BROKER_ERROR", reason,
            lambda state, now: self._apply_broker_error(state, now, change),
            error_code=error_code,
        )

    def record_broker_success(self, user_id: UUID, *, broker: str = DEFAULT_BROKER,
                              actor_user_id: UUID | None = None, idempotency_key: str) -> LiveAccountSafetyState:
        """Reset consecutive-error count; an open circuit still requires manual reset."""
        def change(state, now):
            state.consecutive_broker_errors = 0
            state.version += 1
        return self._mutate(
            user_id, broker, actor_user_id, idempotency_key, "BROKER_SUCCESS",
            "Broker call succeeded; any open circuit remains latched until manual reset.",
            lambda state, now: change(state, now),
        )

    def record_health_check(self, user_id: UUID, *, passed: bool, reason: str,
                            broker: str = DEFAULT_BROKER, actor_user_id: UUID | None = None,
                            idempotency_key: str) -> LiveAccountSafetyState:
        if type(passed) is not bool:
            raise LiveExecutionBlocked("Health-check result must be an explicit boolean.")
        reason = self._reason(reason)
        def change(state, now):
            state.last_health_check_at = now
            if not passed:
                self._trip(state, now, f"Safety health check failed: {reason}")
            elif state.consecutive_broker_errors == 0:
                # Passing health checks do not silently clear kill switch/circuit.
                state.version += 1
            else:
                state.version += 1
        return self._mutate(
            user_id, broker, actor_user_id, idempotency_key,
            "HEALTH_CHECK_PASSED" if passed else "HEALTH_CHECK_FAILED",
            reason, lambda state, now: change(state, now),
        )

    def manual_reset(self, user_id: UUID, reason: str, *, broker: str = DEFAULT_BROKER,
                     actor_user_id: UUID, idempotency_key: str) -> LiveAccountSafetyState:
        reason = self._reason(reason, "Manual reset reason")
        if actor_user_id is None:
            raise LiveExecutionBlocked("An authenticated actor is required for manual safety reset.")
        def change(state, now):
            if state.last_health_check_at is None:
                raise LiveExecutionBlocked("Manual reset requires a successful health check.")
            checked_at = self._aware(state.last_health_check_at)
            if checked_at > now or now - checked_at > self.health_max_age:
                raise LiveExecutionBlocked("Manual reset requires a fresh health check.")
            if state.consecutive_broker_errors != 0:
                raise LiveExecutionBlocked("Manual reset requires a cleared broker-error counter.")
            # The caller must record an explicit passing health check; failure
            # events trip the latch and do not qualify for reset.
            latest = (
                self.db.query(LiveAccountSafetyEvent)
                .filter(LiveAccountSafetyEvent.state_id == state.id)
                .order_by(LiveAccountSafetyEvent.created_at.desc(), LiveAccountSafetyEvent.id.desc())
                .first()
            )
            if latest is None or latest.event_type != "HEALTH_CHECK_PASSED":
                raise LiveExecutionBlocked("Manual reset requires the latest safety event to be a passing health check.")
            state.kill_switch_tripped = False
            state.kill_switch_reason = None
            state.kill_switch_tripped_at = None
            state.circuit_state = "CLOSED"
            state.circuit_opened_at = None
            state.circuit_reason = None
            state.version += 1
        return self._mutate(
            user_id, broker, actor_user_id, idempotency_key, "MANUAL_RESET", reason,
            lambda state, now: change(state, now),
        )

    def _mutate(self, user_id, broker, actor_user_id, idempotency_key, event_type, reason, mutation, error_code=None):
        broker = self._broker(broker)
        key = self._key(idempotency_key)
        try:
            state = self._get_state(user_id, broker, lock=True)
            if state is None:
                raise LiveExecutionBlocked("Persistent safety state is missing; initialize it before recording events.")
            replay = self.db.query(LiveAccountSafetyEvent).filter(
                LiveAccountSafetyEvent.state_id == state.id,
                LiveAccountSafetyEvent.idempotency_key == key,
            ).one_or_none()
            if replay is not None:
                return state
            now = self._now()
            result = mutation(state, now)
            # mutation may return a specialized event type for threshold trips.
            if isinstance(result, str):
                event_type = result
            self._event(state, actor_user_id, key, event_type, reason, error_code=error_code)
            self.db.commit()
            self.db.refresh(state)
            return state
        except Exception:
            self.db.rollback()
            raise

    def _apply_broker_error(self, state, now, change):
        change(state, now)
        return "CIRCUIT_OPENED" if state.circuit_state == "OPEN" else "BROKER_ERROR"

    def _trip(self, state, now, reason):
        state.kill_switch_tripped = True
        state.kill_switch_reason = reason[:500]
        state.kill_switch_tripped_at = now
        state.version += 1

    def _event(self, state, actor_user_id, key, event_type, reason, error_code=None):
        self.db.add(LiveAccountSafetyEvent(
            state_id=state.id, actor_user_id=actor_user_id, idempotency_key=key,
            event_type=event_type, reason=(reason or "")[:500] or None,
            error_code=(error_code or "")[:100] or None,
            consecutive_broker_errors=state.consecutive_broker_errors,
            circuit_state=state.circuit_state,
            kill_switch_tripped=state.kill_switch_tripped,
            state_version=state.version,
        ))

    def _get_state(self, user_id, broker, *, lock):
        query = self.db.query(LiveAccountSafetyState).filter(
            LiveAccountSafetyState.user_id == user_id,
            LiveAccountSafetyState.broker == broker,
        )
        if lock:
            query = query.with_for_update()
        return query.one_or_none()

    def _decision(self, state, allowed, reason):
        return LiveAccountSafetyDecision(
            allowed=allowed, reason=reason,
            kill_switch_tripped=state.kill_switch_tripped,
            circuit_state=state.circuit_state,
            consecutive_broker_errors=state.consecutive_broker_errors,
            state_version=state.version,
        )

    def _now(self):
        now = self.clock()
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise LiveExecutionBlocked("Safety-service clock must return a timezone-aware timestamp.")
        return now.astimezone(timezone.utc)

    @staticmethod
    def _aware(value):
        # SQLite returns naive values for timezone-aware columns.
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _broker(value):
        if not isinstance(value, str) or not value.strip():
            raise LiveExecutionBlocked("Broker name is required for account safety state.")
        return value.strip().lower()

    @staticmethod
    def _key(value):
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 200:
            raise LiveExecutionBlocked("A non-empty idempotency key up to 200 characters is required.")
        return value.strip()

    @staticmethod
    def _reason(value, label="Reason"):
        if not isinstance(value, str) or not value.strip():
            raise LiveExecutionBlocked(f"{label} is required.")
        return value.strip()[:500]
