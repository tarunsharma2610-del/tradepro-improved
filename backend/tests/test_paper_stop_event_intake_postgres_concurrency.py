"""PostgreSQL 16 races for durable PAPER quote ordering.

Uses independent SQLAlchemy sessions/connections. No broker write API is called.
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.database import Base
from app.models.instrument import Instrument
from app.models.paper_stop_event import PaperStopEvent
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.strategy import Strategy
from app.models.user import User
from app.services.market_scanner import MarketScanObservation
from app.services.paper_stop_event_intake_service import PaperStopEventIntakeService


pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_POSTGRES_URL"),
    reason="requires dedicated PostgreSQL 16 test database",
)


def _seed(Session, suffix, *, watermark=Decimal("100.0000")):
    user_id, portfolio_id, instrument_id, strategy_id, position_id = (
        uuid4() for _ in range(5)
    )
    with Session.begin() as db:
        db.add(User(
            id=user_id,
            email=f"quote-order-{suffix}@example.invalid",
            password_hash="test-only",
            full_name="PAPER Quote Ordering Concurrency Test",
            is_admin=False,
        ))
        db.flush()
        db.add(Portfolio(
            id=portfolio_id,
            user_id=user_id,
            name=f"quote-order-{suffix}",
            virtual_capital=Decimal("100000.00"),
            cash_balance=Decimal("100000.00"),
            is_active=True,
        ))
        db.add(Instrument(
            id=instrument_id,
            instrument_key=f"TEST|QUOTE-ORDER|{suffix}",
            exchange="NSE",
            segment="NSE_EQ",
            instrument_type="EQUITY",
            trading_symbol=f"QORD{suffix[:8]}",
            name="PAPER quote ordering concurrency test",
        ))
        db.add(Strategy(
            id=strategy_id,
            portfolio_id=portfolio_id,
            instrument_id=instrument_id,
            name=f"quote-order-strategy-{suffix}",
            segment="EQUITY_INTRADAY",
            quantity=1,
            is_active=True,
            max_daily_loss=Decimal("1000.00"),
            trailing_stop_pct=Decimal("2.00"),
            current_watermark=watermark,
        ))
        db.add(Position(
            id=position_id,
            portfolio_id=portfolio_id,
            instrument_id=instrument_id,
            quantity=5,
            avg_price=Decimal("100.0000"),
            realized_pnl=Decimal("0.00"),
        ))
    return user_id, portfolio_id, instrument_id, strategy_id


def _observation(user_id, instrument_key, *, epoch, version, price, received_at):
    return MarketScanObservation(
        user_id=str(user_id),
        instrument_key=instrument_key,
        epoch=epoch,
        version=version,
        ltp=float(price),
        price_change_pct=None,
        volume_traded_today=None,
        open_interest=None,
        buy_sell_imbalance=None,
        option_greeks=None,
        exchange_timestamp_ms=int(received_at.timestamp() * 1000),
        received_at=received_at.isoformat(),
    )


def _cleanup(Session, ids):
    user_id, portfolio_id, instrument_id, strategy_id = ids
    with Session.begin() as db:
        db.execute(text("DELETE FROM paper_stop_events WHERE strategy_id = :id"),
                   {"id": str(strategy_id)})
        db.execute(text("DELETE FROM positions WHERE portfolio_id = :id"),
                   {"id": str(portfolio_id)})
        db.execute(text("DELETE FROM strategies WHERE id = :id"),
                   {"id": str(strategy_id)})
        db.execute(text("DELETE FROM portfolios WHERE id = :id"),
                   {"id": str(portfolio_id)})
        db.execute(text("DELETE FROM instruments WHERE id = :id"),
                   {"id": str(instrument_id)})
        db.execute(text("DELETE FROM users WHERE id = :id"),
                   {"id": str(user_id)})


def _engine_and_session():
    engine = create_engine(
        os.environ["TEST_POSTGRES_URL"],
        pool_size=4,
        max_overflow=0,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def test_postgres_concurrent_versions_never_regress_durable_quote_state():
    """N and N+1 race; whichever obtains the row lock first, N+1 must win."""
    engine, Session = _engine_and_session()
    ids = _seed(Session, uuid4().hex[:12])
    user_id, _, instrument_id, strategy_id = ids
    with Session() as db:
        instrument_key = db.get(Instrument, instrument_id).instrument_key

    now = datetime.now(timezone.utc)
    epoch = f"concurrent-{uuid4()}"
    older = _observation(
        user_id, instrument_key, epoch=epoch, version=10,
        price=Decimal("103.00"), received_at=now - timedelta(milliseconds=2),
    )
    newer = _observation(
        user_id, instrument_key, epoch=epoch, version=11,
        price=Decimal("105.00"), received_at=now,
    )
    barrier = threading.Barrier(2)
    outcomes = []
    lock = threading.Lock()

    def evaluate(observation):
        with Session() as db:
            barrier.wait(timeout=10)
            try:
                PaperStopEventIntakeService(db).evaluate_and_claim(observation, now=now)
                db.commit()
                result = "committed"
            except Exception as exc:
                db.rollback()
                result = f"error:{type(exc).__name__}:{exc}"
            with lock:
                outcomes.append(result)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(evaluate, older), pool.submit(evaluate, newer)]
            for future in futures:
                future.result(timeout=45)
        assert outcomes == ["committed", "committed"] or sorted(outcomes) == ["committed", "committed"], outcomes

        # A fresh connection verifies committed database state, not identity-map state.
        with Session() as verify:
            saved = verify.get(Strategy, strategy_id)
            assert saved.last_quote_epoch == epoch
            assert saved.last_quote_version == 11
            assert saved.last_quote_received_at is not None
            assert saved.current_watermark == Decimal("105.0000")
            assert verify.query(PaperStopEvent).filter_by(strategy_id=strategy_id).count() == 0
    finally:
        _cleanup(Session, ids)
        engine.dispose()


def test_postgres_concurrent_duplicate_trigger_creates_one_stop_event():
    """Two workers evaluating one triggering quote persist at most one claim."""
    engine, Session = _engine_and_session()
    ids = _seed(Session, uuid4().hex[:12])
    user_id, _, instrument_id, strategy_id = ids
    with Session() as db:
        instrument_key = db.get(Instrument, instrument_id).instrument_key

    now = datetime.now(timezone.utc)
    quote = _observation(
        user_id, instrument_key, epoch=f"duplicate-{uuid4()}",
        version=1, price=Decimal("97.00"), received_at=now,
    )
    barrier = threading.Barrier(2)
    outcomes = []
    lock = threading.Lock()

    def evaluate():
        with Session() as db:
            barrier.wait(timeout=10)
            try:
                events = PaperStopEventIntakeService(db).evaluate_and_claim(quote, now=now)
                db.commit()
                result = ("committed", len(events))
            except Exception as exc:
                db.rollback()
                result = ("error", type(exc).__name__, str(exc))
            with lock:
                outcomes.append(result)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(evaluate), pool.submit(evaluate)]
            for future in futures:
                future.result(timeout=45)
        assert len(outcomes) == 2, outcomes
        assert all(item[0] == "committed" for item in outcomes), outcomes
        with Session() as verify:
            saved = verify.get(Strategy, strategy_id)
            events = verify.query(PaperStopEvent).filter_by(strategy_id=strategy_id).all()
            assert saved.last_quote_version == 1
            assert len(events) == 1
            assert events[0].state == "CLAIMED"
    finally:
        _cleanup(Session, ids)
        engine.dispose()
