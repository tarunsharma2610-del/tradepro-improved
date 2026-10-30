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
    assert sum(row.is_active for row in rows) == 1
    assert next(row for row in rows if row.feed_mode == "ltpc").is_active


def test_deactivate_clears_all_user_desired_subscriptions(db_session, make_user):
    user, first, _ = _setup(db_session, make_user)
    service = MarketDataSubscriptionService(db_session)
    service.replace_for_user(
        user_id=user.id, broker="upstox",
        instrument_keys=[first.instrument_key], feed_mode="ltpc",
    )

    assert service.deactivate_for_user(user_id=user.id, broker="upstox") == 1
    assert service.list_active(user_id=user.id) == []
