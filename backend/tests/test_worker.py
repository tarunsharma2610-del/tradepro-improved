from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import pytest

from app.worker import IST, _is_market_hours


def _ist(y, m, d, h, mi):
    return datetime(y, m, d, h, mi, tzinfo=IST)


def test_market_hours_true_during_a_weekday_trading_session():
    assert _is_market_hours(_ist(2026, 8, 19, 11, 0)) is True  # a Wednesday, mid-session


def test_market_hours_false_before_open():
    assert _is_market_hours(_ist(2026, 8, 19, 9, 0)) is False


def test_market_hours_false_after_close():
    assert _is_market_hours(_ist(2026, 8, 19, 16, 0)) is False


def test_market_hours_false_on_saturday():
    assert _is_market_hours(_ist(2026, 8, 22, 11, 0)) is False


def test_market_hours_true_exactly_at_open_and_close_boundaries():
    assert _is_market_hours(_ist(2026, 8, 19, 9, 15)) is True
    assert _is_market_hours(_ist(2026, 8, 19, 15, 30)) is True


@pytest.mark.asyncio
async def test_run_once_isolates_a_failing_strategy_from_the_rest(db_session, monkeypatch):
    """One strategy's evaluate() raising must not prevent the others in
    the same pass from being evaluated."""
    from app.models.strategy import Strategy
    from app.repositories.portfolio_repository import PortfolioRepository
    from app.services.instrument_service import InstrumentService
    from app.repositories.instrument_repository import InstrumentRepository
    import app.worker as worker_module
    from sqlalchemy.orm import sessionmaker

    # run_once() opens its OWN sessions via SessionLocal(). Point that at a
    # sessionmaker bound to the SAME engine/connection the db_session
    # fixture already set up (StaticPool -> one shared in-memory SQLite
    # connection), so every session run_once() opens sees the same data —
    # without reusing a single Session object, which breaks after the
    # first .close() call inside run_once().
    monkeypatch.setattr(worker_module, "SessionLocal", sessionmaker(bind=db_session.get_bind()))

    InstrumentService(db_session).seed_defaults()
    instrument = InstrumentRepository(db_session).search("RELIANCE")[0]

    from app.repositories.user_repository import UserRepository
    from app.core.security import hash_password

    user = UserRepository(db_session).create(email="w@example.com", password_hash=hash_password("x"), full_name="W")
    portfolio = PortfolioRepository(db_session).create(user_id=user.id, name="P", virtual_capital=Decimal("100000"))

    strategies = []
    for i in range(3):
        s = Strategy(
            portfolio_id=portfolio.id, instrument_id=instrument.id, name=f"S{i}", segment="EQUITY_INTRADAY",
            quantity=1, is_active=True, rsi_weight=1, sma_crossover_weight=1, macd_weight=1,
            volume_spike_weight=1, momentum_weight=1, entry_score_threshold=Decimal("0.9"),
            exit_score_threshold=Decimal("-0.9"), trailing_stop_pct=Decimal("2"), max_daily_loss=Decimal("5000"),
        )
        db_session.add(s)
        strategies.append(s)
    db_session.commit()

    call_count = {"n": 0}

    async def fake_evaluate(self, strategy):
        call_count["n"] += 1
        if strategy.name == "S1":
            raise RuntimeError("simulated failure mid-batch")
        from app.services.strategy_execution_service import EvaluationResult

        return EvaluationResult(str(strategy.id), "HOLD", "ok")

    with patch("app.worker.StrategyExecutionService.evaluate", new=fake_evaluate):
        evaluated_count = await worker_module.run_once()

    # All three were attempted despite S1 raising midway.
    assert call_count["n"] == 3
    assert evaluated_count == 2  # S1's failure doesn't count as evaluated, but doesn't block S0/S2 either


@pytest.mark.asyncio
async def test_run_telegram_poll_returns_zero_and_does_not_raise_on_internal_failure():
    import app.worker as worker_module

    with patch("app.worker.TelegramService.process_updates", new=AsyncMock(side_effect=RuntimeError("boom"))):
        result = await worker_module.run_telegram_poll()

    assert result == 0  # failed cleanly, didn't propagate


@pytest.mark.asyncio
async def test_run_news_ingest_returns_empty_dict_and_does_not_raise_on_internal_failure():
    import app.worker as worker_module

    with patch("app.worker.NewsService.ingest_all_active", new=AsyncMock(side_effect=RuntimeError("boom"))):
        result = await worker_module.run_news_ingest()

    assert result == {}
