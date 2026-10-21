import uuid
from datetime import datetime, timedelta, timezone

from app.models.broker_connection import BrokerConnection
from app.models.live_order_records import LiveReconciliationLease, LiveReconciliationRun
from app.repositories.live_order_reconciliation_run_repository import LiveReconciliationRunRepository
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


def _run(db_session, user, connection, started_at):
    run = LiveReconciliationRun(
        user_id=user.id,
        broker_connection_id=connection.id,
        status="RUNNING",
        started_at=started_at,
        summary={
            "orders_seen": 0, "orders_matched": 0, "orders_unmatched": 0,
            "trades_seen": 0, "fills_inserted": 0, "duplicate_fills": 0,
            "conflicts": 0,
        },
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def test_orphaned_stale_run_is_failed_without_active_lease(db_session, make_user):
    user = make_user()
    connection = _connection(db_session, user)
    now = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    run = _run(db_session, user, connection, now - timedelta(hours=2))

    count = LiveReconciliationRunRepository(db_session).fail_orphaned_runs(
        user_id=user.id, broker_connection_id=connection.id,
        stale_before=now - timedelta(minutes=5), now=now,
    )

    assert count == 1
    db_session.refresh(run)
    assert run.status == "FAILED"
    assert run.error_code == "WORKER_INTERRUPTED"
    assert run.completed_at == now
    assert run.summary["orders_seen"] == 0


def test_orphan_recovery_does_not_fail_run_while_lease_is_active(db_session, make_user):
    user = make_user()
    connection = _connection(db_session, user)
    now = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    run = _run(db_session, user, connection, now - timedelta(hours=2))
    token = LiveReconciliationLeaseRepository(db_session).claim(
        user_id=user.id, broker_connection_id=connection.id,
        now=now - timedelta(seconds=30), lease_seconds=300,
    )
    assert token is not None

    count = LiveReconciliationRunRepository(db_session).fail_orphaned_runs(
        user_id=user.id, broker_connection_id=connection.id,
        stale_before=now - timedelta(minutes=5), now=now,
    )

    assert count == 0
    db_session.refresh(run)
    assert run.status == "RUNNING"


def test_orphan_recovery_only_changes_stale_runs_for_requested_connection(db_session, make_user):
    user = make_user()
    other_user = make_user(email="other@example.com")
    connection = _connection(db_session, user)
    other_connection = _connection(db_session, other_user)
    now = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    stale = _run(db_session, user, connection, now - timedelta(hours=2))
    recent = _run(db_session, user, connection, now - timedelta(minutes=1))
    other = _run(db_session, other_user, other_connection, now - timedelta(hours=2))

    count = LiveReconciliationRunRepository(db_session).fail_orphaned_runs(
        user_id=user.id, broker_connection_id=connection.id,
        stale_before=now - timedelta(minutes=5), now=now,
    )

    assert count == 1
    db_session.refresh(stale)
    db_session.refresh(recent)
    db_session.refresh(other)
    assert stale.status == "FAILED"
    assert recent.status == "RUNNING"
    assert other.status == "RUNNING"


def test_orphan_recovery_rejects_naive_or_future_cutoff(db_session, make_user):
    user = make_user()
    connection = _connection(db_session, user)
    repository = LiveReconciliationRunRepository(db_session)
    now = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)

    import pytest
    with pytest.raises(ValueError, match="timezone-aware"):
        repository.fail_orphaned_runs(
            user_id=user.id, broker_connection_id=connection.id,
            stale_before=now.replace(tzinfo=None), now=now,
        )
    with pytest.raises(ValueError, match="later than now"):
        repository.fail_orphaned_runs(
            user_id=user.id, broker_connection_id=connection.id,
            stale_before=now + timedelta(seconds=1), now=now,
        )
