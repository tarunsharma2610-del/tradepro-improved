from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import uuid

import pytest

from app.brokers.base import BrokerCallResult
from app.core.encryption import encrypt_value
from app.models.broker_connection import BrokerConnection
from app.models.execution import Execution
from app.models.order import Order
from app.models.paper_stop_event import PaperStopEvent
from app.models.position import Position
from app.models.strategy import Strategy
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.instrument_service import InstrumentService
from app.services.paper_stop_event_claim_service import PaperStopEventClaimService
from app.services.paper_stop_event_execution_service import (
    PaperStopEventExecutionRejected,
    PaperStopEventExecutionService,
)


@pytest.fixture()
def instrument(db_session):
    InstrumentService(db_session).seed_defaults()
    from app.repositories.instrument_repository import InstrumentRepository

    return InstrumentRepository(db_session).search("RELIANCE")[0]


@pytest.fixture()
def portfolio(db_session, make_user):
    user = make_user(email=f"atomic-stop-{uuid.uuid4().hex}@example.invalid")
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id,
        name="Atomic stop PAPER",
        virtual_capital=Decimal("100000"),
    )
    return user, portfolio


def _connect_analytics_token(db_session, user_id):
    db_session.add(BrokerConnection(
        user_id=user_id, broker="upstox",
        api_key_encrypted=encrypt_value("test-key"),
        api_secret_encrypted=encrypt_value("test-secret"),
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted=encrypt_value("test-access"),
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        analytics_token_encrypted=encrypt_value("test-analytics"),
        analytics_token_expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        is_connected=True,
    ))
    db_session.commit()


def _quote_patch(instrument):
    now = datetime.now(timezone.utc).isoformat()
    level = {"price": "2500.00", "quantity": 100000, "orders": 10}
    quote = {
        "instrument_token": instrument.instrument_key,
        "last_price": "2500.00",
        "last_trade_time": "1600000000000",
        "timestamp": now,
        "depth": {"buy": [level], "sell": [level]},
    }
    adapter = type("FakeAdapter", (), {
        "get_full_quote": AsyncMock(return_value=BrokerCallResult(
            ok=True, data={"data": {instrument.instrument_key: quote}}
        ))
    })()
    return patch("app.services.execution_service.get_broker_adapter", return_value=adapter)


def _claimed_event(db_session, user, portfolio, instrument):
    strategy = Strategy(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        name="Atomic stop", segment="EQUITY_INTRADAY", quantity=1,
        is_active=True, max_daily_loss=1000, current_watermark=Decimal("2600"),
    )
    position = Position(
        portfolio_id=portfolio.id, instrument_id=instrument.id,
        quantity=2, avg_price=Decimal("2600"), realized_pnl=Decimal("0"),
    )
    db_session.add_all([strategy, position])
    db_session.commit()
    now = datetime.now(timezone.utc)
    event = PaperStopEventClaimService(db_session).claim_trailing_stop(
        user_id=user.id, portfolio_id=portfolio.id, strategy_id=strategy.id,
        instrument_id=instrument.id, quote_epoch=f"atomic-{uuid.uuid4()}",
        quote_version=1, trigger_price=Decimal("2548"),
        lease_seconds=120, now=now,
    )
    assert event is not None
    db_session.commit()
    return strategy, position, event.id, event.claim_token


@pytest.mark.asyncio
async def test_stop_event_fill_and_completion_commit_atomically(
    db_session, portfolio, instrument
):
    user, p = portfolio
    strategy, position, event_id, token = _claimed_event(db_session, user, p, instrument)
    _connect_analytics_token(db_session, user.id)

    with patch("app.services.execution_service.settings.UPSTOX_CHARGE_ESTIMATES_ENABLED", False), _quote_patch(instrument):
        order = await PaperStopEventExecutionService(db_session).execute_claimed(
            user_id=user.id, event_id=event_id, claim_token=token
        )

    event = db_session.get(PaperStopEvent, event_id)
    db_session.refresh(p)
    db_session.refresh(position)
    db_session.refresh(strategy)
    assert order.status == "FILLED"
    assert order.paper_stop_event_id == event_id
    assert event.state == "COMPLETED"
    assert event.completed_at is not None
    assert position.quantity == 0
    assert p.cash_balance > Decimal("100000")
    assert strategy.current_watermark is None
    assert db_session.query(Execution).filter(Execution.order_id == order.id).count() == 1


@pytest.mark.asyncio
async def test_completed_event_redelivery_returns_same_order_without_second_fill(
    db_session, portfolio, instrument
):
    user, p = portfolio
    _, _, event_id, token = _claimed_event(db_session, user, p, instrument)
    _connect_analytics_token(db_session, user.id)

    with patch("app.services.execution_service.settings.UPSTOX_CHARGE_ESTIMATES_ENABLED", False), _quote_patch(instrument):
        first = await PaperStopEventExecutionService(db_session).execute_claimed(
            user_id=user.id, event_id=event_id, claim_token=token
        )

    cash_after_first = Decimal(str(p.cash_balance))
    second = await PaperStopEventExecutionService(db_session).execute_claimed(
        user_id=user.id, event_id=event_id, claim_token=token
    )
    db_session.refresh(p)
    assert second.id == first.id
    assert Decimal(str(p.cash_balance)) == cash_after_first
    assert db_session.query(Order).filter(Order.paper_stop_event_id == event_id).count() == 1
    assert db_session.query(Execution).filter(Execution.order_id == first.id).count() == 1


@pytest.mark.asyncio
async def test_failed_event_completion_rolls_back_order_and_all_accounting(
    db_session, portfolio, instrument, monkeypatch
):
    user, p = portfolio
    strategy, position, event_id, token = _claimed_event(db_session, user, p, instrument)
    _connect_analytics_token(db_session, user.id)
    cash_before = Decimal(str(p.cash_balance))
    quantity_before = position.quantity

    def reject_completion(self, **kwargs):
        return None

    monkeypatch.setattr(
        "app.services.paper_stop_event_execution_service.PaperStopEventLifecycle.complete",
        reject_completion,
    )
    with patch("app.services.execution_service.settings.UPSTOX_CHARGE_ESTIMATES_ENABLED", False), _quote_patch(instrument):
        with pytest.raises(PaperStopEventExecutionRejected, match="atomic completion"):
            await PaperStopEventExecutionService(db_session).execute_claimed(
                user_id=user.id, event_id=event_id, claim_token=token
            )

    db_session.expire_all()
    event = db_session.get(PaperStopEvent, event_id)
    db_session.refresh(p)
    db_session.refresh(position)
    assert event.state == "CLAIMED"
    assert db_session.query(Order).filter(Order.paper_stop_event_id == event_id).count() == 0
    assert db_session.query(Execution).count() == 0
    assert Decimal(str(p.cash_balance)) == cash_before
    assert position.quantity == quantity_before


@pytest.mark.asyncio
async def test_wrong_claim_token_cannot_create_order(db_session, portfolio, instrument):
    user, p = portfolio
    _, _, event_id, _ = _claimed_event(db_session, user, p, instrument)
    with pytest.raises(PaperStopEventExecutionRejected, match="claim"):
        await PaperStopEventExecutionService(db_session).execute_claimed(
            user_id=user.id, event_id=event_id, claim_token=uuid.uuid4()
        )
    assert db_session.query(Order).filter(Order.paper_stop_event_id == event_id).count() == 0


def test_database_naive_claim_lease_is_interpreted_as_utc():
    """SQLite strips tzinfo from timezone=True; persisted UTC must stay valid."""
    from app.services.paper_stop_event_execution_service import PaperStopEventExecutionService

    naive = datetime(2026, 11, 1, 8, 0, 0)
    normalized = PaperStopEventExecutionService._utc_datetime(naive)
    assert normalized.tzinfo == timezone.utc
    assert normalized == datetime(2026, 11, 1, 8, 0, 0, tzinfo=timezone.utc)


def test_aware_claim_lease_is_converted_to_utc():
    from app.services.paper_stop_event_execution_service import PaperStopEventExecutionService

    value = datetime(2026, 11, 1, 13, 30, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    normalized = PaperStopEventExecutionService._utc_datetime(value)
    assert normalized == datetime(2026, 11, 1, 8, 0, 0, tzinfo=timezone.utc)
