from datetime import datetime, timezone
from decimal import Decimal
import uuid

import pytest

from app.models.instrument import Instrument
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.services.market_scanner import MarketScanObservation
from app.services.paper_stop_event_intake_service import (
    PaperStopEventIntakeService,
    PaperStopObservationRejected,
)


def setup_stop_position(db_session, make_user, *, quantity=5, watermark=Decimal("100")):
    user = make_user(email=f"intake-{uuid.uuid4().hex[:8]}@example.com")
    portfolio = Portfolio(
        user_id=user.id, name="PAPER intake", virtual_capital=100000,
        cash_balance=100000, is_active=True,
    )
    instrument = Instrument(
        instrument_key=f"NSE_EQ|{uuid.uuid4().hex[:12]}",
        exchange="NSE", segment="NSE_EQ", instrument_type="EQUITY",
        trading_symbol="INTAKETEST", name="Intake Test",
    )
    db_session.add_all([portfolio, instrument])
    db_session.flush()
    strategy = Strategy(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        name="Intake trailing stop", segment="EQUITY_INTRADAY",
        quantity=1, is_active=True, max_daily_loss=1000,
        trailing_stop_pct=Decimal("2"), current_watermark=watermark,
    )
    position = Position(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        quantity=quantity, avg_price=Decimal("100"), realized_pnl=Decimal("0"),
    )
    db_session.add_all([strategy, position])
    db_session.commit()
    return user, portfolio, instrument, strategy, position


def observation(user, instrument, *, price=97.0, version=1, received_at=None):
    stamp = received_at or datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)
    return MarketScanObservation(
        user_id=str(user.id), instrument_key=instrument.instrument_key,
        epoch="intake-epoch", version=version, ltp=price,
        price_change_pct=None, volume_traded_today=None, open_interest=None,
        buy_sell_imbalance=None, option_greeks=None,
        exchange_timestamp_ms=int(stamp.timestamp() * 1000),
        received_at=stamp.isoformat(),
    )


def test_fresh_long_stop_observation_creates_durable_claim(db_session, make_user):
    user, portfolio, instrument, strategy, _ = setup_stop_position(db_session, make_user)
    now = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)

    events = PaperStopEventIntakeService(db_session).evaluate_and_claim(
        observation(user, instrument, price=97.0), now=now
    )

    assert len(events) == 1
    assert events[0].state == "CLAIMED"
    assert events[0].strategy_id == strategy.id
    assert events[0].trigger_price == Decimal("97.0000")
    db_session.commit()
    assert db_session.query(PaperStopEvent).count() == 1


def test_non_triggering_observation_only_advances_long_watermark(db_session, make_user):
    user, portfolio, instrument, strategy, _ = setup_stop_position(db_session, make_user)
    now = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)

    events = PaperStopEventIntakeService(db_session).evaluate_and_claim(
        observation(user, instrument, price=103.0), now=now
    )

    assert events == []
    db_session.refresh(strategy)
    assert strategy.current_watermark == Decimal("103.0000")
    assert db_session.query(PaperStopEvent).count() == 0


def test_duplicate_quote_cannot_create_second_durable_claim(db_session, make_user):
    user, portfolio, instrument, strategy, _ = setup_stop_position(db_session, make_user)
    now = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)
    service = PaperStopEventIntakeService(db_session)
    quote = observation(user, instrument, price=97.0)

    first = service.evaluate_and_claim(quote, now=now)
    second = service.evaluate_and_claim(quote, now=now)

    assert len(first) == 1
    assert second == []
    db_session.commit()
    assert db_session.query(PaperStopEvent).count() == 1


def test_stale_quote_fails_closed_without_mutating_watermark(db_session, make_user):
    user, portfolio, instrument, strategy, _ = setup_stop_position(db_session, make_user)
    now = datetime(2026, 10, 30, 12, 1, tzinfo=timezone.utc)
    old = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)

    with pytest.raises(PaperStopObservationRejected, match="stale"):
        PaperStopEventIntakeService(db_session).evaluate_and_claim(
            observation(user, instrument, price=97.0, received_at=old), now=now
        )

    db_session.refresh(strategy)
    assert strategy.current_watermark == Decimal("100")
    assert db_session.query(PaperStopEvent).count() == 0
