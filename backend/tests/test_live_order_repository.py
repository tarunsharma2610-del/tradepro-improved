import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.broker_connection import BrokerConnection
from app.models.live_order_records import BrokerFillIdentity, LiveOrderEvent, LiveOrderIntent, LiveOrderOutbox
from app.models.portfolio import Portfolio
from app.repositories.live_order_repository import (
    IdempotencyConflict, LiveOrderRepository, LiveOrderVersionConflict, InvalidLiveOrderTransition,
)


def _account(db_session, user):
    portfolio = Portfolio(
        user_id=user.id,
        name="Test portfolio",
        virtual_capital=100000,
        cash_balance=100000,
        is_active=True,
    )
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="test-encrypted-key",
        api_secret_encrypted="test-encrypted-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=False,
    )
    db_session.add_all([portfolio, connection])
    db_session.commit()
    return portfolio, connection


def _intent_args(user, portfolio, connection, *, key="request-123", snapshot=None):
    snapshot = snapshot or {
        "instrument_key": "NSE_EQ|TEST",
        "side": "BUY",
        "order_type": "LIMIT",
        "quantity": 1,
        "limit_price": "100.00",
        "product": "D",
    }
    return {
        "user_id": user.id,
        "portfolio_id": portfolio.id,
        "broker_connection_id": connection.id,
        "client_idempotency_key": key,
        "order_snapshot": snapshot,
        "correlation_id": "test-correlation",
    }


def test_create_intent_atomically_persists_outbox_and_audit(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)

    intent, created = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )

    assert created is True
    assert intent.state == "CREATED"
    assert db_session.query(LiveOrderOutbox).filter_by(intent_id=intent.id).count() == 1
    event = db_session.query(LiveOrderEvent).filter_by(intent_id=intent.id).one()
    assert event.event_type == "INTENT_CREATED"
    assert event.safe_details == {"state": "CREATED", "outbox": "READY"}


def test_same_key_and_same_hash_returns_existing_intent_without_duplicate_rows(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    repository = LiveOrderRepository(db_session)
    args = _intent_args(user, portfolio, connection)

    first, created_first = repository.create_or_get_intent(**args)
    second, created_second = repository.create_or_get_intent(**args)

    assert created_first is True
    assert created_second is False
    assert first.id == second.id
    assert db_session.query(LiveOrderIntent).count() == 1
    assert db_session.query(LiveOrderOutbox).count() == 1
    assert db_session.query(LiveOrderEvent).count() == 1


def test_same_key_with_different_request_hash_conflicts(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    repository = LiveOrderRepository(db_session)
    args = _intent_args(user, portfolio, connection)
    repository.create_or_get_intent(**args)

    changed = dict(args)
    changed["order_snapshot"] = {"instrument_key": "NSE_EQ|OTHER", "side": "BUY", "quantity": 1}

    with pytest.raises(IdempotencyConflict):
        repository.create_or_get_intent(**changed)

    assert db_session.query(LiveOrderIntent).count() == 1


def test_intent_rejects_portfolio_or_connection_owned_by_another_user(db_session, make_user):
    owner = make_user("owner@example.com")
    stranger = make_user("stranger@example.com")
    portfolio, connection = _account(db_session, owner)
    args = _intent_args(stranger, portfolio, connection)

    with pytest.raises(ValueError, match="must belong"):
        LiveOrderRepository(db_session).create_or_get_intent(**args)

    assert db_session.query(LiveOrderIntent).count() == 0
    assert db_session.query(LiveOrderOutbox).count() == 0


def test_repository_validates_key_and_hash(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    repository = LiveOrderRepository(db_session)
    args = _intent_args(user, portfolio, connection, key=" ")

    with pytest.raises(ValueError, match="idempotency_key"):
        repository.create_or_get_intent(**args)

    args = _intent_args(user, portfolio, connection)
    args["order_snapshot"] = {"limit_price": float("nan")}
    with pytest.raises(ValueError):
        repository.create_or_get_intent(**args)


def test_broker_fill_identity_rejects_duplicate_broker_trade_id(db_session, make_user):
    user = make_user()
    _, connection = _account(db_session, user)
    common = dict(
        broker_connection_id=connection.id,
        broker_order_id="broker-order-1",
        broker_trade_id="broker-trade-1",
        instrument_key="NSE_EQ|TEST",
        side="BUY",
        quantity=1,
        price=100,
        executed_at=__import__("datetime").datetime(2026, 10, 17),
    )
    db_session.add(BrokerFillIdentity(**common))
    db_session.commit()
    db_session.add(BrokerFillIdentity(**common))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    assert db_session.query(BrokerFillIdentity).count() == 1


def test_audit_event_requires_intent_owned_by_user(db_session, make_user):
    owner = make_user("audit-owner@example.com")
    stranger = make_user("audit-stranger@example.com")
    portfolio, connection = _account(db_session, owner)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(owner, portfolio, connection)
    )

    with pytest.raises(ValueError, match="not found"):
        LiveOrderRepository(db_session).append_event(
            user_id=stranger.id,
            intent_id=intent.id,
            event_type="TEST",
        )


def test_failed_commit_rolls_back_intent_event_and_outbox(db_session, make_user, monkeypatch):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    repository = LiveOrderRepository(db_session)

    def fail_commit():
        raise IntegrityError("forced test failure", {}, Exception("simulated"))

    monkeypatch.setattr(db_session, "commit", fail_commit)
    with pytest.raises(IntegrityError, match="forced test failure"):
        repository.create_or_get_intent(**_intent_args(user, portfolio, connection))

    monkeypatch.undo()
    assert db_session.query(LiveOrderIntent).count() == 0
    assert db_session.query(LiveOrderOutbox).count() == 0
    assert db_session.query(LiveOrderEvent).count() == 0


def test_unique_key_race_returns_committed_winner(db_session, make_user, monkeypatch):
    from sqlalchemy.orm import Session

    user = make_user()
    portfolio, connection = _account(db_session, user)
    args = _intent_args(user, portfolio, connection)
    repository = LiveOrderRepository(db_session)
    real_commit = db_session.commit
    injected = {"done": False}

    def simulate_competing_commit():
        if not injected["done"]:
            injected["done"] = True
            # Release this transaction before a second independent session commits the winner.
            db_session.rollback()
            other = Session(bind=db_session.get_bind())
            try:
                winner, created = LiveOrderRepository(other).create_or_get_intent(**args)
                assert created is True
                injected["winner_id"] = winner.id
            finally:
                other.close()
            raise IntegrityError("simulated unique-key race", {}, Exception("concurrent winner committed"))
        real_commit()

    monkeypatch.setattr(db_session, "commit", simulate_competing_commit)
    intent, created = repository.create_or_get_intent(**args)

    assert created is False
    assert str(intent.id) == str(injected["winner_id"])
    monkeypatch.undo()
    assert db_session.query(LiveOrderIntent).count() == 1
    assert db_session.query(LiveOrderOutbox).count() == 1
    assert db_session.query(LiveOrderEvent).count() == 1


def test_order_snapshot_rejects_nested_credential_fields(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    args = _intent_args(user, portfolio, connection)
    args["order_snapshot"] = {
        "instrument_key": "NSE_EQ|TEST",
        "metadata": [{"access_token": "must-not-persist"}],
    }

    with pytest.raises(ValueError, match="credential-like field"):
        LiveOrderRepository(db_session).create_or_get_intent(**args)

    assert db_session.query(LiveOrderIntent).count() == 0


def test_audit_details_reject_nested_secrets_and_non_object_values(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )
    repository = LiveOrderRepository(db_session)

    with pytest.raises(ValueError, match="credential-like field"):
        repository.append_event(
            user_id=user.id,
            intent_id=intent.id,
            event_type="TEST",
            safe_details={"request": {"Authorization": "Bearer must-not-persist"}},
        )
    with pytest.raises(ValueError, match="safe_details must be a JSON object"):
        repository.append_event(
            user_id=user.id,
            intent_id=intent.id,
            event_type="TEST",
            safe_details=["unexpected"],
        )

    assert db_session.query(LiveOrderEvent).filter_by(intent_id=intent.id).count() == 1



def test_reconciliation_transition_updates_intent_and_audit_atomically(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )
    repository = LiveOrderRepository(db_session)

    updated, changed = repository.apply_reconciliation_transition(
        user_id=user.id,
        intent_id=intent.id,
        expected_version=1,
        new_state="OPEN",
        broker_order_id="broker-order-987",
        safe_details={"raw_status": "open", "filled_quantity": 0},
        correlation_id="reconcile-test",
    )

    assert changed is True
    assert updated.state == "OPEN"
    assert updated.broker_order_id == "broker-order-987"
    assert updated.version == 2
    assert updated.last_reconciled_at is not None
    events = db_session.query(LiveOrderEvent).filter_by(intent_id=intent.id).order_by(LiveOrderEvent.created_at).all()
    assert [event.event_type for event in events] == ["INTENT_CREATED", "BROKER_STATUS_RECONCILED"]
    assert events[-1].safe_details["previous_state"] == "CREATED"
    assert events[-1].safe_details["new_state"] == "OPEN"
    assert events[-1].safe_details["new_version"] == 2


def test_repeated_same_observation_is_noop_without_duplicate_audit(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )
    repository = LiveOrderRepository(db_session)
    repository.apply_reconciliation_transition(
        user_id=user.id, intent_id=intent.id, expected_version=1,
        new_state="OPEN", broker_order_id="broker-order-repeat",
    )

    current, changed = repository.apply_reconciliation_transition(
        user_id=user.id, intent_id=intent.id, expected_version=2,
        new_state="OPEN", broker_order_id="broker-order-repeat",
    )
    assert changed is False
    assert current.version == 2
    assert db_session.query(LiveOrderEvent).filter_by(
        intent_id=intent.id, event_type="BROKER_STATUS_RECONCILED"
    ).count() == 1


def test_reconciliation_transition_rejects_stale_version(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )
    repository = LiveOrderRepository(db_session)
    repository.apply_reconciliation_transition(
        user_id=user.id, intent_id=intent.id, expected_version=1, new_state="OPEN"
    )

    with pytest.raises(LiveOrderVersionConflict, match="version changed"):
        repository.apply_reconciliation_transition(
            user_id=user.id, intent_id=intent.id, expected_version=1, new_state="FILLED"
        )
    db_session.refresh(intent)
    assert intent.state == "OPEN"
    assert intent.version == 2


def test_reconciliation_transition_rejects_terminal_state_regression(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )
    repository = LiveOrderRepository(db_session)
    filled, _ = repository.apply_reconciliation_transition(
        user_id=user.id, intent_id=intent.id, expected_version=1, new_state="FILLED",
        broker_order_id="broker-order-filled",
    )

    with pytest.raises(InvalidLiveOrderTransition, match="not allowed"):
        repository.apply_reconciliation_transition(
            user_id=user.id, intent_id=intent.id, expected_version=filled.version, new_state="OPEN"
        )


def test_cancelled_order_can_be_reconciled_to_filled_after_cancel_race(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )
    repository = LiveOrderRepository(db_session)
    cancelled, _ = repository.apply_reconciliation_transition(
        user_id=user.id, intent_id=intent.id, expected_version=1, new_state="CANCELLED",
        broker_order_id="broker-order-cancel-race",
    )
    filled, changed = repository.apply_reconciliation_transition(
        user_id=user.id, intent_id=intent.id, expected_version=cancelled.version, new_state="FILLED",
        broker_order_id="broker-order-cancel-race", safe_details={"trade_evidence": "test"},
    )
    assert changed is True
    assert filled.state == "FILLED"
    assert filled.version == 3


def test_reconciliation_transition_rejects_secret_fields(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )
    with pytest.raises(ValueError, match="credential-like field"):
        LiveOrderRepository(db_session).apply_reconciliation_transition(
            user_id=user.id, intent_id=intent.id, expected_version=1,
            new_state="OPEN", safe_details={"authorization_header": "secret"},
        )
    db_session.refresh(intent)
    assert intent.state == "CREATED"
    assert intent.version == 1
    assert db_session.query(LiveOrderEvent).filter_by(
        intent_id=intent.id, event_type="BROKER_STATUS_RECONCILED"
    ).count() == 0



def _record_fill(repository, user, connection, intent, **overrides):
    args = {
        "user_id": user.id,
        "broker_connection_id": connection.id,
        "broker_trade_id": "trade-stable-1",
        "broker_order_id": "broker-order-1",
        "instrument_key": "NSE_EQ|TEST",
        "side": "BUY",
        "quantity": 1,
        "price": "101.25",
        "executed_at": datetime(2026, 10, 17, 10, 15, tzinfo=timezone.utc),
        "product": "D",
        "order_type": "LIMIT",
        "intent_id": intent.id if intent else None,
        "safe_details": {"exchange": "NSE"},
        "correlation_id": "fill-test",
    }
    args.update(overrides)
    return repository.record_broker_fill(**args)


def test_record_broker_fill_is_idempotent_and_audited(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )
    repository = LiveOrderRepository(db_session)
    intent, _ = repository.apply_reconciliation_transition(
        user_id=user.id, intent_id=intent.id, expected_version=1,
        new_state="OPEN", broker_order_id="broker-order-1",
    )

    fill, created = _record_fill(repository, user, connection, intent)
    assert created is True
    assert fill.broker_trade_id == "trade-stable-1"
    assert fill.quantity == 2
    assert str(fill.price) == "101.2500"
    assert db_session.query(BrokerFillIdentity).filter_by(
        broker_connection_id=connection.id, broker_trade_id="trade-stable-1"
    ).count() == 1
    assert db_session.query(LiveOrderEvent).filter_by(
        intent_id=intent.id, event_type="BROKER_FILL_RECORDED"
    ).count() == 1

    duplicate, duplicate_created = _record_fill(repository, user, connection, intent)
    assert duplicate_created is False
    assert duplicate.id == fill.id
    assert db_session.query(BrokerFillIdentity).filter_by(
        broker_connection_id=connection.id, broker_trade_id="trade-stable-1"
    ).count() == 1
    assert db_session.query(LiveOrderEvent).filter_by(
        intent_id=intent.id, event_type="BROKER_FILL_RECORDED"
    ).count() == 1


def test_reused_trade_id_with_different_payload_is_conflict(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )
    repository = LiveOrderRepository(db_session)
    intent, _ = repository.apply_reconciliation_transition(
        user_id=user.id, intent_id=intent.id, expected_version=1,
        new_state="OPEN", broker_order_id="broker-order-1",
    )
    _record_fill(repository, user, connection, intent)

    with pytest.raises(LiveOrderVersionConflict, match="different fill details"):
        _record_fill(repository, user, connection, intent, price="102.25")

    assert db_session.query(BrokerFillIdentity).filter_by(
        broker_connection_id=connection.id, broker_trade_id="trade-stable-1"
    ).count() == 1


def test_fill_ingestion_rejects_intent_from_another_broker_connection(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    other_connection = BrokerConnection(
        user_id=user.id,
        broker="zerodha",
        api_key_encrypted="other-encrypted-key",
        api_secret_encrypted="other-encrypted-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=False,
    )
    db_session.add(other_connection)
    db_session.commit()
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )

    with pytest.raises(ValueError, match="matched intent not found"):
        _record_fill(
            LiveOrderRepository(db_session), user, other_connection, intent,
            broker_trade_id="trade-other-account",
        )
    assert db_session.query(BrokerFillIdentity).count() == 0


def test_fill_ingestion_rejects_credential_fields_in_safe_details(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )

    with pytest.raises(ValueError, match="credential-like field"):
        _record_fill(
            LiveOrderRepository(db_session), user, connection, intent,
            safe_details={"authorization_header": "do-not-store"},
        )
    assert db_session.query(BrokerFillIdentity).count() == 0



def test_fill_economic_mismatch_is_rejected_for_linked_intent(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )
    repository = LiveOrderRepository(db_session)
    intent, _ = repository.apply_reconciliation_transition(
        user_id=user.id, intent_id=intent.id, expected_version=1,
        new_state="OPEN", broker_order_id="broker-order-1",
    )

    with pytest.raises(LiveOrderVersionConflict, match="instrument differs"):
        _record_fill(repository, user, connection, intent, instrument_key="NSE_EQ|OTHER")
    assert db_session.query(BrokerFillIdentity).count() == 0


def test_fill_requires_intent_to_be_linked_to_broker_order_id(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection)
    )

    with pytest.raises(LiveOrderVersionConflict, match="already linked"):
        _record_fill(LiveOrderRepository(db_session), user, connection, intent)
    assert db_session.query(BrokerFillIdentity).count() == 0


def test_aggregate_partial_fills_cannot_exceed_intent_quantity(db_session, make_user):
    user = make_user()
    portfolio, connection = _account(db_session, user)
    snapshot = {
        "instrument_key": "NSE_EQ|TEST",
        "side": "BUY",
        "order_type": "LIMIT",
        "quantity": 3,
        "limit_price": "100.00",
        "product": "D",
    }
    intent, _ = LiveOrderRepository(db_session).create_or_get_intent(
        **_intent_args(user, portfolio, connection, snapshot=snapshot)
    )
    repository = LiveOrderRepository(db_session)
    intent, _ = repository.apply_reconciliation_transition(
        user_id=user.id, intent_id=intent.id, expected_version=1,
        new_state="OPEN", broker_order_id="broker-order-1",
    )
    _record_fill(repository, user, connection, intent, broker_trade_id="trade-partial-1", quantity=2)

    with pytest.raises(LiveOrderVersionConflict, match="aggregate fill quantity"):
        _record_fill(repository, user, connection, intent, broker_trade_id="trade-partial-2", quantity=2)
    assert db_session.query(BrokerFillIdentity).filter_by(intent_id=intent.id).count() == 1
