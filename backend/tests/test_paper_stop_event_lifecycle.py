from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

import pytest

from app.models.instrument import Instrument
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.services.paper_stop_event_claim_service import PaperStopEventClaimService
from app.services.paper_stop_event_lifecycle import PaperStopEventLifecycle


def _claim(db_session, make_user):
    user = make_user(email=f"lifecycle-{uuid.uuid4().hex}@example.invalid")
    portfolio = Portfolio(
        user_id=user.id, name="PAPER lifecycle", virtual_capital=100000,
        cash_balance=100000, is_active=True,
    )
    instrument = Instrument(
        instrument_key=f"NSE_EQ|{uuid.uuid4().hex[:12]}",
        exchange="NSE", segment="NSE_EQ", instrument_type="EQUITY",
        trading_symbol="LIFECYCLE", name="Lifecycle Test",
    )
    db_session.add_all([portfolio, instrument])
    db_session.flush()
    strategy = Strategy(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        name="Lifecycle strategy", segment="EQUITY_INTRADAY",
        quantity=1, is_active=True, max_daily_loss=1000,
    )
    position = Position(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        quantity=2, avg_price=Decimal("100"), realized_pnl=Decimal("0"),
    )
    db_session.add_all([strategy, position])
    db_session.commit()
    now = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)
    event = PaperStopEventClaimService(db_session).claim_trailing_stop(
        user_id=user.id, portfolio_id=portfolio.id, strategy_id=strategy.id,
        instrument_id=instrument.id, quote_epoch="lifecycle-epoch",
        quote_version=1, trigger_price=Decimal("98.25"),
        lease_seconds=30, now=now,
    )
    assert event is not None
    db_session.commit()
    return event.id, event.claim_token, now


def test_claimed_event_can_execute_and_complete(db_session, make_user):
    event_id, token, now = _claim(db_session, make_user)
    lifecycle = PaperStopEventLifecycle(db_session)

    executing = lifecycle.begin_execution(
        event_id=event_id, claim_token=token, now=now + timedelta(seconds=1)
    )
    assert executing is not None
    assert executing.state == "EXECUTING"

    completed = lifecycle.complete(
        event_id=event_id, claim_token=token, now=now + timedelta(seconds=2)
    )
    assert completed is not None
    assert completed.state == "COMPLETED"
    assert completed.completed_at == now + timedelta(seconds=2)
    db_session.commit()


def test_stale_token_cannot_advance_event_after_reclaim(db_session, make_user):
    event_id, old_token, now = _claim(db_session, make_user)
    lifecycle = PaperStopEventLifecycle(db_session)
    reclaimed = lifecycle.reclaim_expired(
        event_id=event_id, lease_seconds=30, max_attempts=5,
        now=now + timedelta(seconds=31),
    )
    assert reclaimed is not None
    assert reclaimed.state == "CLAIMED"
    assert reclaimed.claim_token != old_token
    assert reclaimed.attempt_count == 2

    stale = lifecycle.begin_execution(
        event_id=event_id, claim_token=old_token,
        now=now + timedelta(seconds=32),
    )
    assert stale is None

    current = lifecycle.begin_execution(
        event_id=event_id, claim_token=reclaimed.claim_token,
        now=now + timedelta(seconds=32),
    )
    assert current is not None
    assert current.state == "EXECUTING"
    db_session.commit()


def test_expired_lease_can_be_reclaimed_only_once(db_session, make_user):
    event_id, old_token, now = _claim(db_session, make_user)
    lifecycle = PaperStopEventLifecycle(db_session)
    at_expiry = now + timedelta(seconds=30)

    first = lifecycle.reclaim_expired(event_id=event_id, now=at_expiry)
    assert first is not None
    replacement = first.claim_token
    second = lifecycle.reclaim_expired(event_id=event_id, now=at_expiry)
    assert second is None
    db_session.commit()

    saved = db_session.get(PaperStopEvent, event_id)
    assert saved.claim_token == replacement
    assert saved.claim_token != old_token
    assert saved.attempt_count == 2


def test_retryable_event_waits_until_retry_lease_expires(db_session, make_user):
    event_id, token, now = _claim(db_session, make_user)
    lifecycle = PaperStopEventLifecycle(db_session)
    lifecycle.begin_execution(event_id=event_id, claim_token=token, now=now + timedelta(seconds=1))
    retryable = lifecycle.mark_retryable(
        event_id=event_id, claim_token=token, retry_after_seconds=10,
        error_code="TEMPORARY_FAILURE", now=now + timedelta(seconds=2),
    )
    assert retryable is not None
    assert retryable.state == "RETRYABLE"
    assert lifecycle.reclaim_expired(event_id=event_id, now=now + timedelta(seconds=11)) is None
    reclaimed = lifecycle.reclaim_expired(event_id=event_id, now=now + timedelta(seconds=12))
    assert reclaimed is not None
    assert reclaimed.attempt_count == 2
    db_session.commit()


def test_expired_claim_at_attempt_limit_becomes_failed(db_session, make_user):
    event_id, token, now = _claim(db_session, make_user)
    # The original claim counts as attempt one.
    db_session.query(PaperStopEvent).filter_by(id=event_id).update(
        {"attempt_count": 2}, synchronize_session=False
    )
    db_session.commit()
    lifecycle = PaperStopEventLifecycle(db_session)
    assert lifecycle.reclaim_expired(
        event_id=event_id, max_attempts=2, now=now + timedelta(seconds=31)
    ) is None
    db_session.commit()
    saved = db_session.get(PaperStopEvent, event_id)
    assert saved.state == "FAILED"
    assert saved.last_error_code == "MAX_ATTEMPTS_EXCEEDED"


def test_terminal_failure_cannot_be_reclaimed(db_session, make_user):
    event_id, token, now = _claim(db_session, make_user)
    lifecycle = PaperStopEventLifecycle(db_session)
    lifecycle.begin_execution(event_id=event_id, claim_token=token, now=now + timedelta(seconds=1))
    failed = lifecycle.fail(
        event_id=event_id, claim_token=token, error_code="PERMANENT_FAILURE",
        now=now + timedelta(seconds=2),
    )
    assert failed is not None
    assert failed.state == "FAILED"
    assert lifecycle.reclaim_expired(event_id=event_id, now=now + timedelta(days=1)) is None
    db_session.commit()


def test_expired_execution_lease_rejects_completion(db_session, make_user):
    event_id, token, now = _claim(db_session, make_user)
    lifecycle = PaperStopEventLifecycle(db_session)
    lifecycle.begin_execution(event_id=event_id, claim_token=token, now=now + timedelta(seconds=1))
    assert lifecycle.complete(
        event_id=event_id, claim_token=token, now=now + timedelta(seconds=31)
    ) is None
    db_session.rollback()
