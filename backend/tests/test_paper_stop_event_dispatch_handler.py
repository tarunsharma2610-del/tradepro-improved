from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
import pytest

from app.models.instrument import Instrument
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.services.market_quote_dispatcher import DispatchedMarketObservation
from app.services.market_scanner import MarketScanObservation
from app.services.paper_stop_event_claim_service import PaperStopEventClaimService



class _SessionProxy:
    """Keep the fixture-owned SQLite session open across handler session scopes."""

    def __init__(self, session):
        self._session = session

    def __getattr__(self, name):
        return getattr(self._session, name)

    def close(self):
        # The pytest fixture owns the underlying session lifecycle.
        return None


def _fixture_session_factory(db_session):
    return lambda: _SessionProxy(db_session)

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
    monkeypatch.setattr(handler, "SessionLocal", _fixture_session_factory(db_session))
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

    monkeypatch.setattr(handler, "SessionLocal", _fixture_session_factory(db_session))
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


@pytest.mark.asyncio
async def test_recovery_sweeper_resumes_expired_claim_without_redis_redelivery(
    db_session, make_user, monkeypatch
):
    import app.services.paper_stop_event_dispatch_handler as handler

    user, portfolio, instrument, strategy = _setup(db_session, make_user)
    old_now = datetime.now(timezone.utc) - timedelta(minutes=2)
    event = PaperStopEventClaimService(db_session).claim_trailing_stop(
        user_id=user.id, portfolio_id=portfolio.id, strategy_id=strategy.id,
        instrument_id=instrument.id, quote_epoch="orphaned-dispatch-epoch",
        quote_version=3, trigger_price=Decimal("97"),
        lease_seconds=1, now=old_now,
    )
    assert event is not None
    old_token = event.claim_token
    db_session.commit()

    monkeypatch.setattr(handler, "SessionLocal", _fixture_session_factory(db_session))
    calls = []

    async def fake_execute(self, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(
        handler.PaperStopEventExecutionService, "execute_claimed", fake_execute
    )

    recovered_count = await handler.recover_expired_paper_stop_events_once()

    db_session.expire_all()
    recovered = db_session.query(PaperStopEvent).filter(
        PaperStopEvent.id == event.id
    ).one()
    assert recovered_count == 1
    assert recovered.claim_token != old_token
    assert recovered.attempt_count == 2
    assert len(calls) == 1
    assert calls[0]["event_id"] == event.id
    assert calls[0]["claim_token"] == recovered.claim_token


@pytest.mark.asyncio
async def test_recovery_sweeper_terminalizes_expired_claim_at_attempt_limit(
    db_session, make_user, monkeypatch
):
    import app.services.paper_stop_event_dispatch_handler as handler

    user, portfolio, instrument, strategy = _setup(db_session, make_user)
    old_now = datetime.now(timezone.utc) - timedelta(minutes=2)
    event = PaperStopEventClaimService(db_session).claim_trailing_stop(
        user_id=user.id, portfolio_id=portfolio.id, strategy_id=strategy.id,
        instrument_id=instrument.id, quote_epoch="exhausted-dispatch-epoch",
        quote_version=4, trigger_price=Decimal("97"),
        lease_seconds=1, now=old_now,
    )
    assert event is not None
    event.attempt_count = 5
    db_session.commit()

    monkeypatch.setattr(handler, "SessionLocal", _fixture_session_factory(db_session))
    calls = []

    async def fake_execute(self, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(
        handler.PaperStopEventExecutionService, "execute_claimed", fake_execute
    )

    recovered_count = await handler.recover_expired_paper_stop_events_once()

    db_session.expire_all()
    terminal = db_session.query(PaperStopEvent).filter(
        PaperStopEvent.id == event.id
    ).one()
    assert recovered_count == 1
    assert terminal.state == "FAILED"
    assert terminal.last_error_code == "MAX_ATTEMPTS_EXCEEDED"
    assert calls == []


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_process_crash_after_claim_commit_recovers_same_event_without_redis(
    db_session, make_user, monkeypatch
):
    """A committed claim survives worker death and is resumed by the DB sweeper."""
    import app.services.paper_stop_event_dispatch_handler as handler
    from app.services.paper_stop_event_lifecycle import PaperStopEventLifecycle

    user, portfolio, instrument, strategy = _setup(db_session, make_user)
    monkeypatch.setattr(handler, "SessionLocal", _fixture_session_factory(db_session))
    executions = []

    async def interrupted_then_complete(self, **kwargs):
        executions.append(kwargs.copy())
        if len(executions) == 1:
            # Simulate hard process loss after the intake transaction committed.
            raise RuntimeError("simulated process death after durable claim commit")

        event = db_session.get(PaperStopEvent, kwargs["event_id"])
        assert event is not None
        assert event.state == "CLAIMED"
        assert event.claim_token == kwargs["claim_token"]
        lifecycle = PaperStopEventLifecycle(db_session)
        started = lifecycle.begin_execution(
            event_id=event.id, claim_token=event.claim_token,
        )
        assert started is not None
        completed = lifecycle.complete(
            event_id=event.id, claim_token=event.claim_token,
        )
        assert completed is not None
        db_session.commit()

    monkeypatch.setattr(
        handler.PaperStopEventExecutionService,
        "execute_claimed",
        interrupted_then_complete,
    )

    with pytest.raises(RuntimeError, match="simulated process death"):
        await handler.handle_paper_market_observation(
            _item(user, instrument, version=9, price=97.0)
        )

    event = db_session.query(PaperStopEvent).filter(
        PaperStopEvent.strategy_id == strategy.id,
        PaperStopEvent.quote_epoch == "dispatch-epoch",
        PaperStopEvent.quote_version == 9,
    ).one()
    original_event_id = event.id
    original_token = event.claim_token
    assert event.state == "CLAIMED"
    assert original_token is not None

    # The recovery path must not need Redis or a second quote delivery.
    event.claimed_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    recovered_count = await handler.recover_expired_paper_stop_events_once()

    db_session.expire_all()
    saved = db_session.get(PaperStopEvent, original_event_id)
    assert recovered_count == 1
    assert saved is not None
    assert saved.state == "COMPLETED"
    assert saved.claim_token != original_token
    assert saved.attempt_count == 2
    assert len(executions) == 2
    assert executions[0]["event_id"] == executions[1]["event_id"] == original_event_id
    assert executions[0]["claim_token"] == original_token
    assert executions[1]["claim_token"] == saved.claim_token


async def test_dispatch_worker_retries_after_durable_claim_commit_without_duplicate_event(
    db_session, make_user
):
    """Worker retry reuses one committed PAPER claim after an uncertain failure."""
    import asyncio

    from app.services.market_quote_dispatcher import MarketQuoteDispatcher
    from app.services.market_quote_dispatch_worker import MarketQuoteDispatchWorker

    user, portfolio, instrument, strategy = _setup(db_session, make_user)
    dispatcher = MarketQuoteDispatcher(max_pending_keys=4)
    assert dispatcher.publish(_item(user, instrument, version=7, price=97.0))

    calls = []
    execution_recovered = asyncio.Event()

    async def durable_claim_handler(item):
        # Model the handler's durable intake boundary: commit the event before
        # execution, then look it up by its unique strategy/quote identity on
        # redelivery. This isolates worker retry/ack behavior from execution.
        event = db_session.query(PaperStopEvent).filter(
            PaperStopEvent.strategy_id == strategy.id,
            PaperStopEvent.event_type == "TRAILING_STOP",
            PaperStopEvent.quote_epoch == item.epoch,
            PaperStopEvent.quote_version == item.version,
        ).one_or_none()
        if event is None:
            event = PaperStopEventClaimService(db_session).claim_trailing_stop(
                user_id=user.id,
                portfolio_id=portfolio.id,
                strategy_id=strategy.id,
                instrument_id=instrument.id,
                quote_epoch=item.epoch,
                quote_version=item.version,
                trigger_price=Decimal("97"),
                lease_seconds=30,
            )
            assert event is not None
            db_session.commit()

        calls.append((event.id, event.claim_token))
        if len(calls) == 1:
            # Simulate a process interruption after the durable claim commit.
            raise RuntimeError("simulated interruption after durable claim commit")
        execution_recovered.set()

    worker = MarketQuoteDispatchWorker(
        dispatcher,
        durable_claim_handler,
        min_backoff_seconds=0,
        max_backoff_seconds=0,
        max_attempts=2,
    )
    task = asyncio.create_task(worker.run())
    try:
        await asyncio.wait_for(execution_recovered.wait(), timeout=2)
        for _ in range(100):
            if worker.processed_count == 1:
                break
            await asyncio.sleep(0)

        assert worker.processed_count == 1
        assert worker.failure_count == 1
        assert dispatcher.pending_keys == 0
        assert dispatcher.inflight_keys == 0

        events = db_session.query(PaperStopEvent).filter(
            PaperStopEvent.strategy_id == strategy.id,
            PaperStopEvent.event_type == "TRAILING_STOP",
            PaperStopEvent.quote_epoch == "dispatch-epoch",
            PaperStopEvent.quote_version == 7,
        ).all()
        assert len(events) == 1
        assert events[0].state == "CLAIMED"
        assert events[0].claim_token is not None
        assert len(calls) == 2
        assert calls[0] == calls[1] == (events[0].id, events[0].claim_token)
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
