"""Token-fenced lifecycle operations for transactional PAPER stop events.

All operations participate in the caller's SQLAlchemy transaction. They never
commit, create orders, or call a broker. Conditional UPDATE statements provide
the concurrency boundary: a stale worker cannot advance an event after its
claim token has been replaced.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.paper_stop_event import PaperStopEvent


class PaperStopEventLifecycle:
    """Atomic, claim-token-owned PAPER stop-event state transitions."""

    ACTIVE_STATES = ("CLAIMED", "EXECUTING", "RETRYABLE")

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _now(value: datetime | None) -> datetime:
        current = value or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("Lifecycle time must be timezone-aware.")
        return current

    @staticmethod
    def _valid_token(token: UUID) -> None:
        if not isinstance(token, UUID):
            raise ValueError("A valid claim token is required.")

    def _transition(
        self, *, event_id: UUID, claim_token: UUID, expected_state: str,
        new_state: str, now: datetime | None = None,
        claimed_until: datetime | None = None,
        completed_at: datetime | None = None,
        last_error_code: str | None = None,
    ) -> PaperStopEvent | None:
        current = self._now(now)
        self._valid_token(claim_token)
        values = {"state": new_state}
        if claimed_until is not None:
            values["claimed_until"] = claimed_until
        if completed_at is not None:
            values["completed_at"] = completed_at
        if last_error_code is not None:
            values["last_error_code"] = last_error_code

        changed = (
            self.db.query(PaperStopEvent)
            .filter(
                PaperStopEvent.id == event_id,
                PaperStopEvent.claim_token == claim_token,
                PaperStopEvent.state == expected_state,
                PaperStopEvent.claimed_until > current,
            )
            .update(values, synchronize_session=False)
        )
        if changed != 1:
            return None
        self.db.flush()
        self.db.expire_all()
        return self.db.get(PaperStopEvent, event_id)

    def begin_execution(
        self, *, event_id: UUID, claim_token: UUID,
        now: datetime | None = None,
    ) -> PaperStopEvent | None:
        """CLAIMED -> EXECUTING, only for the current unexpired owner."""
        return self._transition(
            event_id=event_id, claim_token=claim_token,
            expected_state="CLAIMED", new_state="EXECUTING", now=now,
        )

    def complete(
        self, *, event_id: UUID, claim_token: UUID,
        now: datetime | None = None,
    ) -> PaperStopEvent | None:
        """EXECUTING -> COMPLETED, fenced by token and unexpired lease."""
        current = self._now(now)
        return self._transition(
            event_id=event_id, claim_token=claim_token,
            expected_state="EXECUTING", new_state="COMPLETED",
            now=current, completed_at=current,
        )

    def mark_retryable(
        self, *, event_id: UUID, claim_token: UUID,
        retry_after_seconds: int = 5, error_code: str = "PAPER_RETRYABLE",
        now: datetime | None = None,
    ) -> PaperStopEvent | None:
        """EXECUTING -> RETRYABLE with a bounded delay before reclamation."""
        current = self._now(now)
        if isinstance(retry_after_seconds, bool) or not isinstance(retry_after_seconds, int) or not 1 <= retry_after_seconds <= 300:
            raise ValueError("Retry delay must be between 1 and 300 seconds.")
        if not error_code or len(error_code) > 100:
            raise ValueError("A bounded error code is required.")
        return self._transition(
            event_id=event_id, claim_token=claim_token,
            expected_state="EXECUTING", new_state="RETRYABLE",
            now=current,
            claimed_until=current + timedelta(seconds=retry_after_seconds),
            last_error_code=error_code,
        )

    def fail(
        self, *, event_id: UUID, claim_token: UUID,
        error_code: str, now: datetime | None = None,
    ) -> PaperStopEvent | None:
        """EXECUTING -> FAILED; terminal failures cannot be reclaimed."""
        if not error_code or len(error_code) > 100:
            raise ValueError("A bounded error code is required.")
        return self._transition(
            event_id=event_id, claim_token=claim_token,
            expected_state="EXECUTING", new_state="FAILED",
            now=now, last_error_code=error_code,
        )

    def reclaim_expired(
        self, *, event_id: UUID, lease_seconds: int = 30,
        max_attempts: int = 5, now: datetime | None = None,
    ) -> PaperStopEvent | None:
        """Atomically rotate ownership of one expired, non-terminal claim.

        Concurrent reclaimers race on the same conditional UPDATE; at most one
        can replace the token. The previous worker's token becomes unusable.
        """
        current = self._now(now)
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int) or not 1 <= lease_seconds <= 300:
            raise ValueError("Claim lease must be between 1 and 300 seconds.")
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= 100:
            raise ValueError("Maximum attempts must be between 1 and 100.")

        replacement_token = uuid4()
        changed = (
            self.db.query(PaperStopEvent)
            .filter(
                PaperStopEvent.id == event_id,
                PaperStopEvent.state.in_(self.ACTIVE_STATES),
                PaperStopEvent.claimed_until <= current,
                PaperStopEvent.attempt_count < max_attempts,
            )
            .update(
                {
                    "state": "CLAIMED",
                    "claim_token": replacement_token,
                    "claimed_until": current + timedelta(seconds=lease_seconds),
                    "attempt_count": PaperStopEvent.attempt_count + 1,
                    "last_error_code": None,
                },
                synchronize_session=False,
            )
        )
        if changed == 1:
            self.db.flush()
            self.db.expire_all()
            return self.db.get(PaperStopEvent, event_id)

        # An expired event that exhausted its retry budget is terminalized.
        self.db.query(PaperStopEvent).filter(
            PaperStopEvent.id == event_id,
            PaperStopEvent.state.in_(self.ACTIVE_STATES),
            PaperStopEvent.claimed_until <= current,
            PaperStopEvent.attempt_count >= max_attempts,
        ).update(
            {"state": "FAILED", "last_error_code": "MAX_ATTEMPTS_EXCEEDED"},
            synchronize_session=False,
        )
        self.db.flush()
        return None
