"""Atomic lease claims for read-only broker reconciliation jobs."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.broker_connection import BrokerConnection
from app.models.live_order_records import LiveReconciliationLease


class LiveReconciliationLeaseRepository:
    """One lease per broker connection; a stale owner cannot complete a newer lease."""

    def __init__(self, db: Session):
        self.db = db

    def claim(
        self,
        *,
        user_id: uuid.UUID,
        broker_connection_id: uuid.UUID,
        now: datetime | None = None,
        lease_seconds: int = 300,
    ) -> uuid.UUID | None:
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int) or not 1 <= lease_seconds <= 3600:
            raise ValueError("lease_seconds must be an integer between 1 and 3600")
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        connection = self.db.query(BrokerConnection).filter(
            BrokerConnection.id == broker_connection_id,
            BrokerConnection.user_id == user_id,
        ).first()
        if connection is None:
            raise ValueError("broker connection not found for authenticated user")

        token = uuid.uuid4()
        until = now + timedelta(seconds=lease_seconds)
        existing = self.db.query(LiveReconciliationLease).filter(
            LiveReconciliationLease.broker_connection_id == broker_connection_id
        ).first()
        if existing is None:
            try:
                self.db.add(LiveReconciliationLease(
                    user_id=user_id,
                    broker_connection_id=broker_connection_id,
                    lease_token=token,
                    claimed_until=until,
                    generation=1,
                    last_started_at=now,
                    last_error_code=None,
                ))
                self.db.commit()
                return token
            except IntegrityError:
                # Another process may have inserted the one-per-connection row.
                self.db.rollback()

        result = self.db.query(LiveReconciliationLease).filter(
            LiveReconciliationLease.user_id == user_id,
            LiveReconciliationLease.broker_connection_id == broker_connection_id,
            or_(
                LiveReconciliationLease.lease_token.is_(None),
                LiveReconciliationLease.claimed_until.is_(None),
                LiveReconciliationLease.claimed_until <= now,
            ),
        ).update(
            {
                "lease_token": token,
                "claimed_until": until,
                "generation": LiveReconciliationLease.generation + 1,
                "last_started_at": now,
                "last_error_code": None,
            },
            synchronize_session=False,
        )
        if result != 1:
            self.db.rollback()
            return None
        self.db.commit()
        return token

    def renew(
        self,
        *,
        user_id: uuid.UUID,
        broker_connection_id: uuid.UUID,
        lease_token: uuid.UUID,
        now: datetime | None = None,
        lease_seconds: int = 300,
    ) -> bool:
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, int) or not 1 <= lease_seconds <= 3600:
            raise ValueError("lease_seconds must be an integer between 1 and 3600")
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        result = self.db.query(LiveReconciliationLease).filter(
            LiveReconciliationLease.user_id == user_id,
            LiveReconciliationLease.broker_connection_id == broker_connection_id,
            LiveReconciliationLease.lease_token == lease_token,
            LiveReconciliationLease.claimed_until > now,
        ).update(
            {"claimed_until": now + timedelta(seconds=lease_seconds)},
            synchronize_session=False,
        )
        if result != 1:
            self.db.rollback()
            return False
        self.db.commit()
        return True

    def complete(
        self,
        *,
        user_id: uuid.UUID,
        broker_connection_id: uuid.UUID,
        lease_token: uuid.UUID,
        error_code: str | None = None,
        now: datetime | None = None,
    ) -> bool:
        if error_code is not None:
            if not isinstance(error_code, str) or not error_code or len(error_code) > 100:
                raise ValueError("error_code must be a safe non-empty category of at most 100 characters")
            if not all(char.isupper() or char.isdigit() or char == "_" for char in error_code):
                raise ValueError("error_code must contain only uppercase letters, digits and underscores")
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        result = self.db.query(LiveReconciliationLease).filter(
            LiveReconciliationLease.user_id == user_id,
            LiveReconciliationLease.broker_connection_id == broker_connection_id,
            LiveReconciliationLease.lease_token == lease_token,
        ).update(
            {
                "lease_token": None,
                "claimed_until": None,
                "last_completed_at": now,
                "last_error_code": error_code,
            },
            synchronize_session=False,
        )
        if result != 1:
            self.db.rollback()
            return False
        self.db.commit()
        return True
