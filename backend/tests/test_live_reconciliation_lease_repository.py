import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.broker_connection import BrokerConnection
from app.models.live_order_records import LiveReconciliationLease
from app.repositories.live_reconciliation_lease_repository import LiveReconciliationLeaseRepository


def _connection(db_session, user):
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=False,
    )
    db_session.add(connection)
    db_session.commit()
    return connection


def test_claim_excludes_second_worker_until_lease_expires(db_session, make_user):
    user = make_user()
    connection = _connection(db_session, user)
    repository = LiveReconciliationLeaseRepository(db_session)
    now = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)

    first = repository.claim(
        user_id=user.id, broker_connection_id=connection.id, now=now, lease_seconds=60
    )
    second = repository.claim(
        user_id=user.id, broker_connection_id=connection.id,
        now=now + timedelta(seconds=10), lease_seconds=60,
    )

    assert first is not None
    assert second is None
    lease = db_session.query(LiveReconciliationLease).filter_by(
        broker_connection_id=connection.id
    ).one()
    assert lease.lease_token == first
    assert lease.generation == 1


def test_expired_lease_can_be_reclaimed_and_old_owner_cannot_complete(db_session, make_user):
    user = make_user()
    connection = _connection(db_session, user)
    repository = LiveReconciliationLeaseRepository(db_session)
    now = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
    first = repository.claim(
        user_id=user.id, broker_connection_id=connection.id, now=now, lease_seconds=30
    )
    second = repository.claim(
        user_id=user.id, broker_connection_id=connection.id,
        now=now + timedelta(seconds=31), lease_seconds=30,
    )

    assert first is not None and second is not None and first != second
    assert repository.complete(
        user_id=user.id, broker_connection_id=connection.id, lease_token=first,
        now=now + timedelta(seconds=32),
    ) is False
    assert repository.complete(
        user_id=user.id, broker_connection_id=connection.id, lease_token=second,
        error_code="READ_COMPLETE", now=now + timedelta(seconds=33),
    ) is True
    lease = db_session.query(LiveReconciliationLease).filter_by(
        broker_connection_id=connection.id
    ).one()
    assert lease.lease_token is None
    assert lease.last_error_code == "READ_COMPLETE"
    assert lease.generation == 2


def test_lease_renewal_requires_current_unexpired_token(db_session, make_user):
    user = make_user()
    connection = _connection(db_session, user)
    repository = LiveReconciliationLeaseRepository(db_session)
    now = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
    token = repository.claim(
        user_id=user.id, broker_connection_id=connection.id, now=now, lease_seconds=30
    )
    assert token is not None
    assert repository.renew(
        user_id=user.id, broker_connection_id=connection.id, lease_token=token,
        now=now + timedelta(seconds=10), lease_seconds=60,
    ) is True
    assert repository.renew(
        user_id=user.id, broker_connection_id=connection.id, lease_token=uuid.uuid4(),
        now=now + timedelta(seconds=11), lease_seconds=60,
    ) is False
    assert repository.renew(
        user_id=user.id, broker_connection_id=connection.id, lease_token=token,
        now=now + timedelta(seconds=71), lease_seconds=60,
    ) is False


def test_claim_requires_connection_owned_by_authenticated_user(db_session, make_user):
    owner = make_user()
    other = make_user(email="other@example.com")
    connection = _connection(db_session, owner)
    with pytest.raises(ValueError, match="not found for authenticated user"):
        LiveReconciliationLeaseRepository(db_session).claim(
            user_id=other.id, broker_connection_id=connection.id
        )


@pytest.mark.parametrize("lease_seconds", [0, -1, 3601, True, 1.5])
def test_lease_duration_is_bounded(lease_seconds, db_session, make_user):
    user = make_user()
    connection = _connection(db_session, user)
    with pytest.raises(ValueError, match="between 1 and 3600"):
        LiveReconciliationLeaseRepository(db_session).claim(
            user_id=user.id, broker_connection_id=connection.id, lease_seconds=lease_seconds
        )


@pytest.mark.parametrize("missing_token", [False, True])
def test_claim_fails_closed_on_inconsistent_lease_state(db_session, make_user, missing_token):
    user = make_user()
    connection = _connection(db_session, user)
    now = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    lease = LiveReconciliationLease(
        user_id=user.id,
        broker_connection_id=connection.id,
        lease_token=None if missing_token else uuid.uuid4(),
        claimed_until=now + timedelta(minutes=2) if missing_token else None,
        generation=1,
        last_started_at=now - timedelta(hours=1),
        last_error_code=None,
    )
    db_session.add(lease)
    db_session.commit()

    with pytest.raises(RuntimeError, match="inconsistent reconciliation lease state"):
        LiveReconciliationLeaseRepository(db_session).claim(
            user_id=user.id,
            broker_connection_id=connection.id,
            now=now,
        )

    db_session.refresh(lease)
    assert (lease.lease_token is None) == missing_token
    assert (lease.claimed_until is None) != missing_token
    assert lease.generation == 1


def test_write_fence_requires_current_unexpired_lease_and_locks_owned_row(db_session, make_user):
    user = make_user()
    connection = _connection(db_session, user)
    repository = LiveReconciliationLeaseRepository(db_session)
    now = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    first = repository.claim(
        user_id=user.id, broker_connection_id=connection.id,
        now=now, lease_seconds=30,
    )
    assert first is not None

    assert repository.fence_for_write(
        user_id=user.id, broker_connection_id=connection.id,
        lease_token=first, now=now + timedelta(seconds=10),
    ) is True
    # The caller's write transaction owns the row lock until it commits/rolls back.
    db_session.rollback()

    second = repository.claim(
        user_id=user.id, broker_connection_id=connection.id,
        now=now + timedelta(seconds=31), lease_seconds=30,
    )
    assert second is not None and second != first
    assert repository.fence_for_write(
        user_id=user.id, broker_connection_id=connection.id,
        lease_token=first, now=now + timedelta(seconds=32),
    ) is False
    assert repository.fence_for_write(
        user_id=user.id, broker_connection_id=connection.id,
        lease_token=second, now=now + timedelta(seconds=32),
    ) is True
    db_session.rollback()


def test_postgres_write_fence_blocks_reclaim_until_persistence_transaction_finishes():
    import os
    import threading

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.database import Base
    from app.models.user import User
    import app.models  # noqa: F401

    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is not configured")

    engine = create_engine(url, pool_size=5)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    first_session = None
    claimant_thread = None
    try:
        # The CI PostgreSQL database is dedicated to this workflow. Leave it
        # clean for the subsequent Alembic migration cycle.
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        first_session = SessionLocal()
        user = User(
            email=f"lease-fence-{uuid.uuid4()}@example.invalid",
            password_hash="test-only-hash",
            full_name="Lease Fence Test",
        )
        first_session.add(user)
        first_session.flush()
        connection = BrokerConnection(
            user_id=user.id,
            broker="upstox",
            api_key_encrypted="test-key",
            api_secret_encrypted="test-secret",
            redirect_uri="https://example.invalid/callback",
            is_connected=False,
        )
        first_session.add(connection)
        first_session.commit()

        now = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
        leases = LiveReconciliationLeaseRepository(first_session)
        first_token = leases.claim(
            user_id=user.id,
            broker_connection_id=connection.id,
            now=now,
            lease_seconds=30,
        )
        assert first_token is not None

        # Model one slow persistence transaction: the lease is valid at the
        # fence check, then expires while this transaction still owns the row.
        assert leases.fence_for_write(
            user_id=user.id,
            broker_connection_id=connection.id,
            lease_token=first_token,
            now=now + timedelta(seconds=10),
        ) is True

        started = threading.Event()
        finished = threading.Event()
        outcome = {}

        def attempt_reclaim():
            session = SessionLocal()
            try:
                started.set()
                outcome["token"] = LiveReconciliationLeaseRepository(session).claim(
                    user_id=user.id,
                    broker_connection_id=connection.id,
                    now=now + timedelta(seconds=31),
                    lease_seconds=30,
                )
            except Exception as exc:
                outcome["error"] = exc
            finally:
                session.close()
                finished.set()

        claimant_thread = threading.Thread(target=attempt_reclaim, daemon=True)
        claimant_thread.start()
        assert started.wait(timeout=3)
        # Without the row lock, the expired lease would be reclaimable here.
        assert not finished.wait(timeout=0.25)

        first_session.commit()
        assert finished.wait(timeout=3)
        claimant_thread.join(timeout=3)
        assert not claimant_thread.is_alive()
        assert "error" not in outcome
        assert outcome.get("token") is not None
        assert outcome["token"] != first_token
    finally:
        if first_session is not None:
            if first_session.in_transaction():
                first_session.rollback()
            first_session.close()
        if claimant_thread is not None and claimant_thread.is_alive():
            claimant_thread.join(timeout=3)
        # Avoid leaving schema behind for the workflow's Alembic check.
        Base.metadata.drop_all(engine)
        engine.dispose()
