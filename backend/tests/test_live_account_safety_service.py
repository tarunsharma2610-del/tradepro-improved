from datetime import datetime, timedelta, timezone

import pytest

from app.models.live_account_safety import LiveAccountSafetyEvent, LiveAccountSafetyState
from app.services.live_account_safety_service import LiveAccountSafetyService
from app.services.live_execution_service import LiveExecutionBlocked


@pytest.fixture()
def safety_context(db_session, make_user):
    user = make_user()
    now = datetime(2026, 10, 18, 10, 0, tzinfo=timezone.utc)
    service = LiveAccountSafetyService(db_session, clock=lambda: now)
    return db_session, user, service, now


def _initialize(user, service):
    return service.initialize(
        user.id, broker="upstox", actor_user_id=user.id, idempotency_key="initialize-1"
    )


def test_missing_state_fails_closed_without_creating_state(safety_context):
    db, user, service, _now = safety_context

    decision = service.check_allowed(user.id)

    assert not decision.allowed
    assert "missing" in decision.reason.lower()
    assert db.query(LiveAccountSafetyState).count() == 0


def test_initial_state_is_tripped_and_audited(safety_context):
    db, user, service, _now = safety_context

    state = _initialize(user, service)
    decision = service.check_allowed(user.id)

    assert state.kill_switch_tripped
    assert state.circuit_state == "CLOSED"
    assert not decision.allowed
    assert "initial safety state" in decision.reason.lower()
    event = db.query(LiveAccountSafetyEvent).one()
    assert event.event_type == "INITIALIZED"
    assert event.kill_switch_tripped is True
    assert event.state_version == state.version


def test_broker_error_threshold_opens_circuit_and_trips_kill_switch(safety_context):
    db, user, service, _now = safety_context
    _initialize(user, service)

    first = service.record_broker_error(
        user.id, "HTTP_502", "temporary upstream failure",
        threshold=2, idempotency_key="error-1",
    )
    replay = service.record_broker_error(
        user.id, "HTTP_502", "temporary upstream failure",
        threshold=2, idempotency_key="error-1",
    )
    assert replay.consecutive_broker_errors == first.consecutive_broker_errors == 1

    state = service.record_broker_error(
        user.id, "HTTP_503", "upstream unavailable",
        threshold=2, idempotency_key="error-2",
    )
    decision = service.check_allowed(user.id)

    assert state.consecutive_broker_errors == 2
    assert state.circuit_state == "OPEN"
    assert state.kill_switch_tripped
    assert state.circuit_opened_at is not None
    assert state.last_broker_error_code == "HTTP_503"
    assert not decision.allowed
    assert "threshold" in decision.reason.lower()
    assert db.query(LiveAccountSafetyEvent).filter(
        LiveAccountSafetyEvent.idempotency_key == "error-1"
    ).count() == 1
    assert db.query(LiveAccountSafetyEvent).filter(
        LiveAccountSafetyEvent.event_type == "CIRCUIT_OPENED"
    ).count() == 1


def test_broker_success_clears_counter_but_never_automatically_closes_circuit(safety_context):
    _db, user, service, _now = safety_context
    _initialize(user, service)
    service.record_broker_error(
        user.id, "TIMEOUT", "broker timeout", threshold=1, idempotency_key="error-1"
    )

    state = service.record_broker_success(user.id, idempotency_key="success-1")
    decision = service.check_allowed(user.id)

    assert state.consecutive_broker_errors == 0
    assert state.circuit_state == "OPEN"
    assert state.kill_switch_tripped
    assert not decision.allowed


def test_manual_reset_requires_health_check_and_cleared_error_counter(safety_context):
    _db, user, service, _now = safety_context
    _initialize(user, service)

    with pytest.raises(LiveExecutionBlocked, match="successful health check"):
        service.manual_reset(
            user.id, "operator confirmed recovery", actor_user_id=user.id,
            idempotency_key="reset-too-early",
        )

    service.record_broker_error(
        user.id, "TIMEOUT", "broker timeout", threshold=1, idempotency_key="error-1"
    )
    service.record_health_check(
        user.id, passed=True, reason="broker session responds but error counter remains",
        actor_user_id=user.id, idempotency_key="health-pass-before-counter-clear",
    )
    with pytest.raises(LiveExecutionBlocked, match="cleared broker-error counter"):
        service.manual_reset(
            user.id, "operator confirmed recovery", actor_user_id=user.id,
            idempotency_key="reset-counter-not-clear",
        )

    service.record_broker_success(user.id, idempotency_key="success-1")
    service.record_health_check(
        user.id, passed=True, reason="broker session and account snapshots verified",
        actor_user_id=user.id, idempotency_key="health-pass-1",
    )
    state = service.manual_reset(
        user.id, "operator reviewed account and approved reset",
        actor_user_id=user.id, idempotency_key="reset-1",
    )

    decision = service.check_allowed(user.id)
    assert not state.kill_switch_tripped
    assert state.circuit_state == "CLOSED"
    assert state.consecutive_broker_errors == 0
    assert decision.allowed
    assert "passed" in decision.reason.lower()


def test_failed_health_check_trips_latch_and_stale_health_check_blocks(safety_context):
    db, user, service, now = safety_context
    _initialize(user, service)
    service.record_broker_success(user.id, idempotency_key="success-1")
    state = service.record_health_check(
        user.id, passed=False, reason="account positions could not be verified",
        actor_user_id=user.id, idempotency_key="health-fail-1",
    )
    assert state.kill_switch_tripped
    assert not service.check_allowed(user.id).allowed

    # Simulate an explicit passing check and manual reset, then age that check.
    service.record_health_check(
        user.id, passed=True, reason="all required broker checks passed",
        actor_user_id=user.id, idempotency_key="health-pass-1",
    )
    service.manual_reset(
        user.id, "operator reviewed recovery", actor_user_id=user.id,
        idempotency_key="reset-1",
    )
    state.last_health_check_at = now - timedelta(minutes=6)
    db.commit()

    decision = service.check_allowed(user.id)
    assert not decision.allowed
    assert "stale" in decision.reason.lower()


def test_manual_kill_switch_trip_is_idempotent_and_account_scoped(safety_context):
    db, user, service, _now = safety_context
    state = _initialize(user, service)
    first = service.trip_kill_switch(
        user.id, "operator emergency stop", actor_user_id=user.id,
        idempotency_key="emergency-stop-1",
    )
    version = first.version
    replay = service.trip_kill_switch(
        user.id, "operator emergency stop", actor_user_id=user.id,
        idempotency_key="emergency-stop-1",
    )

    assert replay.version == version
    assert replay.kill_switch_tripped
    assert db.query(LiveAccountSafetyEvent).filter(
        LiveAccountSafetyEvent.idempotency_key == "emergency-stop-1"
    ).count() == 1
    # A different broker has independent state; the Upstox account latch remains
    # keyed to the user and broker, not to a portfolio.
    other_broker = service.initialize(
        user.id, broker="another-broker", actor_user_id=user.id,
        idempotency_key="initialize-other-broker",
    )
    assert other_broker.kill_switch_tripped
    assert not service.check_allowed(user.id, "another-broker").allowed
    assert not service.check_allowed(user.id, "upstox").allowed


def test_unknown_circuit_state_fails_closed(safety_context):
    db, user, service, _now = safety_context
    state = _initialize(user, service)
    state.kill_switch_tripped = False
    state.last_health_check_at = service.clock()
    state.circuit_state = "HALF_OPEN_UNKNOWN"
    db.commit()

    decision = service.check_allowed(user.id)

    assert not decision.allowed
    assert "circuit" in decision.reason.lower()
