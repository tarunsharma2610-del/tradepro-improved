import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.broker_connection import BrokerConnection
from app.models.instrument import Instrument
from app.models.market_data_subscription import MarketDataSubscription


def _dependencies(db_session, make_user):
    user = make_user()
    broker = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="test-key",
        api_secret_encrypted="test-secret",
        redirect_uri="https://example.invalid/callback",
    )
    instrument = Instrument(
        instrument_key="NSE_EQ|INE002A01018",
        exchange="NSE",
        segment="NSE_EQ",
        instrument_type="EQUITY",
        trading_symbol="RELIANCE",
        name="Reliance Industries",
    )
    db_session.add_all([broker, instrument])
    db_session.commit()
    return user, broker, instrument


def test_market_subscription_persists_user_scoped_desired_state(db_session, make_user):
    user, broker, instrument = _dependencies(db_session, make_user)
    subscription = MarketDataSubscription(
        user_id=user.id,
        broker_connection_id=broker.id,
        instrument_id=instrument.id,
        feed_mode="ltpc",
        is_active=True,
    )
    db_session.add(subscription)
    db_session.commit()

    loaded = db_session.get(MarketDataSubscription, subscription.id)
    assert loaded is not None
    assert loaded.user_id == user.id
    assert loaded.broker_connection_id == broker.id
    assert loaded.instrument_id == instrument.id
    assert loaded.feed_mode == "ltpc"
    assert loaded.is_active is True


def test_market_subscription_rejects_unsupported_feed_mode(db_session, make_user):
    user, broker, instrument = _dependencies(db_session, make_user)
    db_session.add(MarketDataSubscription(
        user_id=user.id,
        broker_connection_id=broker.id,
        instrument_id=instrument.id,
        feed_mode="unknown",
    ))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_market_subscription_rejects_duplicate_desired_subscription(db_session, make_user):
    user, broker, instrument = _dependencies(db_session, make_user)
    values = dict(
        user_id=user.id,
        broker_connection_id=broker.id,
        instrument_id=instrument.id,
        feed_mode="ltpc",
    )
    db_session.add(MarketDataSubscription(**values))
    db_session.commit()
    db_session.add(MarketDataSubscription(**values))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


