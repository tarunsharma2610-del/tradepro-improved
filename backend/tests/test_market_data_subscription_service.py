from app.models.broker_connection import BrokerConnection
from app.models.instrument import Instrument
from app.models.market_data_subscription import MarketDataSubscription
from app.services.market_data_subscription_service import MarketDataSubscriptionService


def _setup(db_session, make_user):
    user = make_user()
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
    )
    first = Instrument(
        instrument_key="NSE_EQ|INE002A01018",
        exchange="NSE",
        segment="NSE_EQ",
        instrument_type="EQUITY",
        trading_symbol="RELIANCE",
        name="Reliance Industries",
    )
    second = Instrument(
        instrument_key="NSE_EQ|INE009A01021",
        exchange="NSE",
        segment="NSE_EQ",
        instrument_type="EQUITY",
        trading_symbol="INFY",
        name="Infosys",
    )
    db_session.add_all([connection, first, second])
    db_session.commit()
    return user, first, second


def test_replace_persists_and_replaces_desired_instrument_set(db_session, make_user):
    user, first, second = _setup(db_session, make_user)
    service = MarketDataSubscriptionService(db_session)

    service.replace_for_user(
        user_id=user.id, broker="upstox",
        instrument_keys=[first.instrument_key], feed_mode="ltpc",
    )
    active = service.list_active(user_id=user.id)
    assert [row.instrument_id for row in active] == [first.id]

    service.replace_for_user(
        user_id=user.id, broker="upstox",
        instrument_keys=[second.instrument_key], feed_mode="ltpc",
    )
    active = service.list_active(user_id=user.id)
    assert [row.instrument_id for row in active] == [second.id]


def test_replace_can_reactivate_previous_feed_mode_identity(db_session, make_user):
    user, first, _ = _setup(db_session, make_user)
    service = MarketDataSubscriptionService(db_session)

    service.replace_for_user(
        user_id=user.id, broker="upstox",
        instrument_keys=[first.instrument_key], feed_mode="ltpc",
    )
    service.replace_for_user(
        user_id=user.id, broker="upstox",
        instrument_keys=[first.instrument_key], feed_mode="full",
    )
    service.replace_for_user(
        user_id=user.id, broker="upstox",
        instrument_keys=[first.instrument_key], feed_mode="ltpc",
    )

    rows = db_session.query(MarketDataSubscription).all()
    assert len(rows) == 2
    # Switching back to ltpc reactivates its identity without deactivating
    # the independently desired full-mode subscription.
    assert sum(row.is_active for row in rows) == 2
    assert all(row.is_active for row in rows)


def test_deactivate_clears_all_user_desired_subscriptions(db_session, make_user):
    user, first, _ = _setup(db_session, make_user)
    service = MarketDataSubscriptionService(db_session)
    service.replace_for_user(
        user_id=user.id, broker="upstox",
        instrument_keys=[first.instrument_key], feed_mode="ltpc",
    )

    assert service.deactivate_for_user(user_id=user.id, broker="upstox") == 1
    assert service.list_active(user_id=user.id) == []

def test_replacing_one_feed_mode_preserves_other_mode_subscriptions(db_session, make_user):
    user, first, second = _setup(db_session, make_user)
    service = MarketDataSubscriptionService(db_session)

    service.replace_for_user(
        user_id=user.id, broker="upstox",
        instrument_keys=[first.instrument_key], feed_mode="ltpc",
    )
    service.replace_for_user(
        user_id=user.id, broker="upstox",
        instrument_keys=[second.instrument_key], feed_mode="full",
    )

    active = service.list_active(user_id=user.id)
    active_pairs = {(row.instrument_id, row.feed_mode) for row in active}
    assert active_pairs == {(first.id, "ltpc"), (second.id, "full")}

    # Replacing the ltpc set affects ltpc only; full-mode intent stays active.
    service.replace_for_user(
        user_id=user.id, broker="upstox",
        instrument_keys=[second.instrument_key], feed_mode="ltpc",
    )
    active = service.list_active(user_id=user.id)
    active_pairs = {(row.instrument_id, row.feed_mode) for row in active}
    assert active_pairs == {(second.id, "ltpc"), (second.id, "full")}

def test_deactivate_mode_preserves_other_active_modes(db_session, make_user):
    user, first, second = _setup(db_session, make_user)
    service = MarketDataSubscriptionService(db_session)
    service.replace_for_user(
        user_id=user.id, broker="upstox",
        instrument_keys=[first.instrument_key], feed_mode="ltpc",
    )
    service.replace_for_user(
        user_id=user.id, broker="upstox",
        instrument_keys=[second.instrument_key], feed_mode="full",
    )

    assert service.deactivate_mode_for_user(
        user_id=user.id, broker="upstox", feed_mode="ltpc"
    ) == 1

    active = service.list_active(user_id=user.id)
    assert [(row.instrument_id, row.feed_mode) for row in active] == [
        (second.id, "full")
    ]

def test_replace_modes_persists_complete_mixed_mode_state_atomically(db_session, make_user):
    user, first, second = _setup(db_session, make_user)
    service = MarketDataSubscriptionService(db_session)
    service.replace_modes_for_user(
        user_id=user.id,
        broker="upstox",
        subscriptions_by_mode={
            "ltpc": [first.instrument_key],
            "full": [second.instrument_key],
        },
    )
    active = service.list_active(user_id=user.id)
    assert {(row.instrument_id, row.feed_mode) for row in active} == {
        (first.id, "ltpc"),
        (second.id, "full"),
    }

    # A complete desired-state replacement deactivates only the omitted mode
    # identity and preserves the other mode's active identity.
    service.replace_modes_for_user(
        user_id=user.id,
        broker="upstox",
        subscriptions_by_mode={"full": [first.instrument_key]},
    )
    active = service.list_active(user_id=user.id)
    assert {(row.instrument_id, row.feed_mode) for row in active} == {
        (first.id, "full"),
    }
    rows = db_session.query(MarketDataSubscription).all()
    assert len(rows) == 3
    assert sum(row.is_active for row in rows) == 1

def test_replace_modes_rejects_same_instrument_assigned_to_multiple_modes(db_session, make_user):
    user, first, _ = _setup(db_session, make_user)
    service = MarketDataSubscriptionService(db_session)

    try:
        service.replace_modes_for_user(
            user_id=user.id,
            broker="upstox",
            subscriptions_by_mode={
                "ltpc": [first.instrument_key],
                "full": [first.instrument_key],
            },
        )
        assert False, "Expected cross-mode duplicate validation to fail"
    except ValueError as exc:
        assert "cannot be active in both" in str(exc)

    assert service.list_active(user_id=user.id) == []


def test_nifty500_ltpc_subscription_set_persists_all_500_active_instruments(db_session, make_user):
    user = make_user()
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
    )
    instruments = [
        Instrument(
            instrument_key=f"NSE_EQ|INE{index:09d}",
            exchange="NSE",
            segment="NSE_EQ",
            instrument_type="EQUITY",
            trading_symbol=f"TEST{index:04d}",
            name=f"Test Company {index}",
            lot_size=1,
            tick_size=0.05,
            is_active=True,
        )
        for index in range(1, 501)
    ]
    db_session.add(connection)
    db_session.add_all(instruments)
    db_session.commit()

    active = MarketDataSubscriptionService(db_session).replace_for_user(
        user_id=user.id,
        broker="upstox",
        instrument_keys=[item.instrument_key for item in instruments],
        feed_mode="ltpc",
    )

    assert len(active) == 500
    assert {row.instrument.instrument_key for row in active} == {
        item.instrument_key for item in instruments
    }
    assert all(row.feed_mode == "ltpc" and row.is_active for row in active)
