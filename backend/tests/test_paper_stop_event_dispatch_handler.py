from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.orm import sessionmaker
import pytest

from app.models.instrument import Instrument
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.services.market_quote_dispatcher import DispatchedMarketObservation
from app.services.market_scanner import MarketScanObservation
from app.services.paper_stop_event_claim_service import PaperStopEventClaimService


def _setup(db_session, make_user):
    user = make_user(email=f"dispatch-stop-{uuid4().hex}@example.invalid")
    portfolio = Portfolio(
        user_id=user.id, name="PAPER dispatch", virtual_capital=100000,
        cash_balance=100000, is_active=True,
    )
    instrument = Instrument(
        instrument_key=f"NSE_EQ|{uuid4().hex[:12]}", exchange="NSE",
        segment="NSE_EQ", instrument_type="EQUITY",
        trading_symbol="DISPATCHTEST", name="Dispatch Test",
    )
    db_session.add_all([portfolio, instrument])
    db_session.flush()
    strategy = Strategy(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        name="Dispatch stop", segment="EQUITY_INTRADAY", quantity=1,
        is_active=True, max_daily_loss=1000, trailing_stop_pct=Decimal("2"),
        current_watermark=Decimal("100"),
    )
    position = Position(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        quantity=2, avg_price=Decimal("100"), realized_pnl=Decimal("0"),
    )
    db_session.add_all([strategy, position])
    db_session.commit()
    return user, portfolio, instrument, strategy


def _item(user, instrument, *, version=1, price=97.0, now=None):
    now = now or datetime.now(timezone.utc)
    observation = MarketScanObservation(
        user_id=str(user.id), instrument_key=instrument.instrument_key,
        epoch="dispatch-epoch", version=version, ltp=price,
        price_change_pct=None, volume_traded_today=None, open_interest=None,
        buy_sell_imbalance=None, option_greeks=None,
        exchange_timestamp_ms=int(now.timestamp() * 1000),
        received_at=now.isoformat(),
    )
    return DispatchedMarketObservation(
        user_id=str(user.id), instrument_key=instrument.instrument_key,
        epoch="dispatch-epoch", version=version, observation=observation,
    )


@pytest.mark.asyncio
async def test_handler_commits_new_stop_claim_before_invoking_execution(
    db_session, make_user, monkeypatch
):
    import app.services.paper_stop_event_dispatch_handler as handler

    user, portfolio, instrument, strategy = _setup(db_session, make_user)
    monkeypatch.setattr(handler, "SessionLocal", sessionmaker(bind=db_session.get_bind()))
    calls = []

    async def fake_execute(self, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(
        handler.PaperStopEventExecutionService, "execute_claimed", fake_execute
    )

    await handler.handle_paper_market_observation(_item(user, instrument))

    event = db_session.query(PaperStopEvent).filter(
        PaperStopEvent.strategy_id == strategy.id
    ).one()
    assert event.state == "CLAIMED"
    assert event.quote_epoch == "dispatch-epoch"
    assert event.quote_version == 1
    assert len(calls) == 1
    assert calls[0]["user_id"] == user.id
    assert calls[0]["event_id"] == event.id
    assert calls[0]["claim_token"] == event.claim_token


@pytest.mark.asyncio
async def test_handler_rotates_expired_claim_token_before_execution(
    db_session, make_user, monkeypatch
):
    import app.services.paper_stop_event_dispatch_handler as handler

    user, portfolio, instrument, strategy = _setup(db_session, make_user)
    old_now = datetime.now(timezone.utc) - timedelta(minutes=2)
    event = PaperStopEventClaimService(db_session).claim_trailing_stop(
        user_id=user.id, portfolio_id=portfolio.id, strategy_id=strategy.id,
        instrument_id=instrument.id, quote_epoch="dispatch-epoch",
        quote_version=2, trigger_price=Decimal("97"),
        lease_seconds=1, now=old_now,
    )
    assert event is not None
    old_token = event.claim_token
    db_session.commit()

    monkeypatch.setattr(handler, "SessionLocal", sessionmaker(bind=db_session.get_bind()))
    calls = []

    async def fake_execute(self, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(
        handler.PaperStopEventExecutionService, "execute_claimed", fake_execute
    )

    await handler.handle_paper_market_observation(
        _item(user, instrument, version=2, now=datetime.now(timezone.utc))
    )

    db_session.expire_all()
    recovered = db_session.query(PaperStopEvent).filter(
        PaperStopEvent.id == event.id
    ).one()
    assert recovered.state == "CLAIMED"
    assert recovered.claim_token != old_token
    assert recovered.attempt_count == 2
    assert len(calls) == 1
    assert calls[0]["claim_token"] == recovered.claim_token
