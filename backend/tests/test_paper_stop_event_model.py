import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.instrument import Instrument
from app.models.strategy import Strategy


def _dependencies(db_session, make_user):
    user = make_user()
    portfolio = Portfolio(
        user_id=user.id, name="PAPER", virtual_capital=100000,
        cash_balance=100000, is_active=True,
    )
    instrument = Instrument(
        instrument_key=f"NSE_EQ|{uuid.uuid4().hex[:12]}",
        exchange="NSE", segment="NSE_EQ", instrument_type="EQUITY",
        trading_symbol="TEST", name="Test Instrument",
    )
    db_session.add_all([portfolio, instrument])
    db_session.commit()
    strategy = Strategy(
        portfolio_id=portfolio.id, instrument_id=instrument.id, name="Test strategy",
        segment="EQUITY_INTRADAY", quantity=1, is_active=True,
        max_daily_loss=1000,
    )
    db_session.add(strategy)
    db_session.commit()
    return user, portfolio, instrument, strategy


def _event(user, portfolio, instrument, strategy, **overrides):
    values = dict(
        user_id=user.id, portfolio_id=portfolio.id, instrument_id=instrument.id,
        strategy_id=strategy.id, event_type="TRAILING_STOP",
        quote_epoch="subscription-epoch-1", quote_version=7,
        trigger_price=98.25, state="CLAIMED", attempt_count=0,
    )
    values.update(overrides)
    return PaperStopEvent(**values)


def test_paper_stop_event_persists_scoped_quote_identity(db_session, make_user):
    user, portfolio, instrument, strategy = _dependencies(db_session, make_user)
    event = _event(user, portfolio, instrument, strategy)
    db_session.add(event)
    db_session.commit()

    loaded = db_session.get(PaperStopEvent, event.id)
    assert loaded.user_id == user.id
    assert loaded.portfolio_id == portfolio.id
    assert loaded.strategy_id == strategy.id
    assert loaded.instrument_id == instrument.id
    assert loaded.quote_epoch == "subscription-epoch-1"
    assert loaded.quote_version == 7
    assert loaded.state == "CLAIMED"


def test_paper_stop_event_rejects_duplicate_strategy_epoch_version(db_session, make_user):
    user, portfolio, instrument, strategy = _dependencies(db_session, make_user)
    db_session.add(_event(user, portfolio, instrument, strategy))
    db_session.commit()
    db_session.add(_event(user, portfolio, instrument, strategy, trigger_price=97.5))

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.parametrize(
    "overrides",
    [
        {"state": "UNKNOWN"},
        {"event_type": "MARKET_ORDER"},
        {"quote_version": 0},
        {"trigger_price": 0},
        {"attempt_count": -1},
    ],
)
def test_paper_stop_event_rejects_invalid_state_or_quote_identity(db_session, make_user, overrides):
    user, portfolio, instrument, strategy = _dependencies(db_session, make_user)
    db_session.add(_event(user, portfolio, instrument, strategy, **overrides))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
