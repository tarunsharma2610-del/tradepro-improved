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
