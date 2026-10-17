import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.broker_connection import BrokerConnection
from app.models.live_order_records import BrokerFillIdentity, LiveOrderEvent, LiveOrderIntent, LiveOrderOutbox
from app.models.portfolio import Portfolio
from app.repositories.live_order_repository import IdempotencyConflict, LiveOrderRepository


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
