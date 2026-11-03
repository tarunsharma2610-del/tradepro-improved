from datetime import datetime, timezone
from decimal import Decimal
import uuid

import pytest

from app.models.instrument import Instrument
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.services.paper_stop_event_claim_service import (
    PaperStopClaimRejected,
    PaperStopEventClaimService,
)


def setup_open_position(db_session, make_user, *, email="claim@example.com"):
    user = make_user(email=email)
    portfolio = Portfolio(
        user_id=user.id, name="PAPER", virtual_capital=100000,
        cash_balance=100000, is_active=True,
    )
    instrument = Instrument(
        instrument_key=f"NSE_EQ|{uuid.uuid4().hex[:12]}",
        exchange="NSE", segment="NSE_EQ", instrument_type="EQUITY",
        trading_symbol="CLAIMTEST", name="Claim Test",
    )
    db_session.add_all([portfolio, instrument])
    db_session.flush()
    strategy = Strategy(
        portfolio_id=portfolio.id, instrument_id=instrument.id, name="Stop strategy",
        segment="EQUITY_INTRADAY", quantity=1, is_active=True, max_daily_loss=1000,
    )
    position = Position(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        quantity=5, avg_price=Decimal("100"), realized_pnl=Decimal("0"),
    )
    db_session.add_all([strategy, position])
    db_session.commit()
    return user, portfolio, instrument, strategy, position


def claim_args(user, portfolio, instrument, strategy, **overrides):
    args = dict(
        user_id=user.id, portfolio_id=portfolio.id, strategy_id=strategy.id,
        instrument_id=instrument.id, quote_epoch="epoch-1", quote_version=1,
        trigger_price=Decimal("98.25"),
        now=datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc),
    )
    args.update(overrides)
    return args


def test_claim_service_persists_claim_and_lease_metadata(db_session, make_user):
    user, portfolio, instrument, strategy, _ = setup_open_position(db_session, make_user)
    event = PaperStopEventClaimService(db_session).claim_trailing_stop(
        **claim_args(user, portfolio, instrument, strategy)
    )
    assert event is not None
    assert event.state == "CLAIMED"
    assert event.claim_token is not None
    assert event.attempt_count == 1
    assert event.claimed_until == datetime(2026, 10, 30, 12, 0, 30, tzinfo=timezone.utc)
    db_session.commit()
    assert db_session.query(PaperStopEvent).count() == 1


def test_duplicate_quote_claim_returns_none_without_poisoning_transaction(db_session, make_user):
    user, portfolio, instrument, strategy, _ = setup_open_position(db_session, make_user)
    service = PaperStopEventClaimService(db_session)
    args = claim_args(user, portfolio, instrument, strategy)
    first = service.claim_trailing_stop(**args)
    assert first is not None
    db_session.flush()
    second = service.claim_trailing_stop(**args)
    assert second is None
    db_session.commit()
    assert db_session.query(PaperStopEvent).count() == 1


def test_claim_rejects_cross_user_portfolio_access(db_session, make_user):
    user, portfolio, instrument, strategy, _ = setup_open_position(db_session, make_user)
    other = make_user(email="other-claim@example.com")
    with pytest.raises(PaperStopClaimRejected, match="portfolio"):
        PaperStopEventClaimService(db_session).claim_trailing_stop(
            **claim_args(other, portfolio, instrument, strategy)
        )


def test_claim_rejects_strategy_instrument_mismatch(db_session, make_user):
    user, portfolio, instrument, strategy, _ = setup_open_position(db_session, make_user)
    other_instrument = Instrument(
        instrument_key=f"NSE_EQ|{uuid.uuid4().hex[:12]}",
        exchange="NSE", segment="NSE_EQ", instrument_type="EQUITY",
        trading_symbol="OTHER", name="Other Instrument",
    )
    db_session.add(other_instrument)
    db_session.commit()
    with pytest.raises(PaperStopClaimRejected, match="strategy ownership"):
        PaperStopEventClaimService(db_session).claim_trailing_stop(
            **claim_args(user, portfolio, other_instrument, strategy)
        )


def test_claim_fails_closed_when_multiple_strategies_share_position(db_session, make_user):
    user, portfolio, instrument, strategy, _ = setup_open_position(db_session, make_user)
    other = Strategy(
        portfolio_id=portfolio.id, instrument_id=instrument.id, name="Competing strategy",
        segment="EQUITY_INTRADAY", quantity=1, is_active=True, max_daily_loss=1000,
    )
    db_session.add(other)
    db_session.commit()
    with pytest.raises(PaperStopClaimRejected, match="ownership is ambiguous"):
        PaperStopEventClaimService(db_session).claim_trailing_stop(
            **claim_args(user, portfolio, instrument, strategy)
        )
    assert db_session.query(PaperStopEvent).count() == 0


def test_claim_rejects_position_missing_or_flat(db_session, make_user):
    user, portfolio, instrument, strategy, position = setup_open_position(db_session, make_user)
    position.quantity = 0
    db_session.commit()
    with pytest.raises(PaperStopClaimRejected, match="No open"):
        PaperStopEventClaimService(db_session).claim_trailing_stop(
            **claim_args(user, portfolio, instrument, strategy)
        )


@pytest.mark.parametrize("overrides", [
    {"quote_epoch": ""},
    {"quote_version": 0},
    {"quote_version": True},
    {"trigger_price": Decimal("NaN")},
    {"trigger_price": Decimal("0")},
    {"lease_seconds": 0},
    {"lease_seconds": 301},
    {"now": datetime(2026, 10, 30, 12, 0)},
])
def test_claim_rejects_invalid_claim_input(db_session, make_user, overrides):
    user, portfolio, instrument, strategy, _ = setup_open_position(db_session, make_user)
    with pytest.raises(PaperStopClaimRejected):
        PaperStopEventClaimService(db_session).claim_trailing_stop(
            **claim_args(user, portfolio, instrument, strategy, **overrides)
        )
