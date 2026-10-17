from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models.execution import Execution
from app.models.order import Order
from app.models.strategy import Strategy
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.analytics_service import portfolio_analytics, strategy_analytics
from app.services.instrument_service import InstrumentService


@pytest.fixture()
def portfolio(db_session, make_user):
    user = make_user()
    return PortfolioRepository(db_session).create(user_id=user.id, name="Analytics test", virtual_capital=Decimal("100000"))


@pytest.fixture()
def instrument(db_session):
    InstrumentService(db_session).seed_defaults()
    from app.repositories.instrument_repository import InstrumentRepository

    return InstrumentRepository(db_session).search("TCS")[0]


def _make_order_and_execution(db, portfolio_id, instrument_id, *, side, realized_pnl, gross_value, total_charges, when, strategy_id=None):
    order = Order(
        portfolio_id=portfolio_id, instrument_id=instrument_id, side=side, order_type="MARKET", segment="EQUITY_INTRADAY",
        quantity=10, status="FILLED", trading_mode="PAPER", execution_reason="STRATEGY" if strategy_id else "MANUAL",
        strategy_id=strategy_id, placed_at=when, filled_at=when,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    execution = Execution(
        order_id=order.id, portfolio_id=portfolio_id, instrument_id=instrument_id, side=side, quantity=10,
        price=Decimal("100"), gross_value=gross_value, brokerage=Decimal("20"), stt=Decimal("2"),
        exchange_charges=Decimal("0.5"), sebi_charges=Decimal("0.01"), stamp_duty=Decimal("0.5"),
        gst=Decimal("3"), total_charges=total_charges, realized_pnl=realized_pnl, executed_at=when,
    )
    db.add(execution)
    db.commit()
    return order, execution


def test_portfolio_analytics_with_no_trades_yet(db_session, portfolio):
    result = portfolio_analytics(db_session, portfolio.id, portfolio.virtual_capital)
    assert result.total_trades == 0
    assert result.win_rate_pct is None
    assert result.best_trade_pnl is None
    assert result.equity_curve == []


def test_portfolio_analytics_computes_correct_aggregates(db_session, portfolio, instrument):
    now = datetime.now(timezone.utc)
    # An opening buy (realized_pnl=0, not a "trade" in the win/loss sense) ...
    _make_order_and_execution(db_session, portfolio.id, instrument.id, side="BUY", realized_pnl=Decimal("0"), gross_value=Decimal("1000"), total_charges=Decimal("26"), when=now)
    # ... then two closing sells, one win one loss.
    _make_order_and_execution(db_session, portfolio.id, instrument.id, side="SELL", realized_pnl=Decimal("150"), gross_value=Decimal("1100"), total_charges=Decimal("26"), when=now + timedelta(minutes=5))
    _make_order_and_execution(db_session, portfolio.id, instrument.id, side="SELL", realized_pnl=Decimal("-50"), gross_value=Decimal("950"), total_charges=Decimal("26"), when=now + timedelta(minutes=10))

    result = portfolio_analytics(db_session, portfolio.id, portfolio.virtual_capital)

    assert result.total_trades == 2  # only the two closing fills count
    assert result.win_count == 1
    assert result.loss_count == 1
    assert result.win_rate_pct == Decimal("50")
    assert result.total_realized_pnl == Decimal("100")  # 150 - 50
    assert result.best_trade_pnl == Decimal("150")
    assert result.worst_trade_pnl == Decimal("-50")
    assert result.total_costs_paid == Decimal("78")  # 26 * 3 fills
    assert len(result.equity_curve) == 3


def test_equity_curve_is_chronologically_ordered(db_session, portfolio, instrument):
    now = datetime.now(timezone.utc)
    _make_order_and_execution(db_session, portfolio.id, instrument.id, side="BUY", realized_pnl=Decimal("0"), gross_value=Decimal("1000"), total_charges=Decimal("20"), when=now + timedelta(minutes=10))
    _make_order_and_execution(db_session, portfolio.id, instrument.id, side="BUY", realized_pnl=Decimal("0"), gross_value=Decimal("500"), total_charges=Decimal("10"), when=now)

    result = portfolio_analytics(db_session, portfolio.id, portfolio.virtual_capital)

    assert result.equity_curve[0].timestamp < result.equity_curve[1].timestamp


def test_strategy_analytics_separates_by_strategy(db_session, portfolio, instrument):
    strategy_a = Strategy(
        portfolio_id=portfolio.id, instrument_id=instrument.id, name="Strategy A", segment="EQUITY_INTRADAY",
        quantity=10, is_active=True, rsi_weight=1, sma_crossover_weight=1, macd_weight=1, volume_spike_weight=1,
        momentum_weight=1, entry_score_threshold=Decimal("0.5"), exit_score_threshold=Decimal("-0.3"),
        trailing_stop_pct=Decimal("2"), max_daily_loss=Decimal("5000"),
    )
    strategy_b = Strategy(
        portfolio_id=portfolio.id, instrument_id=instrument.id, name="Strategy B", segment="EQUITY_INTRADAY",
        quantity=10, is_active=False, rsi_weight=1, sma_crossover_weight=1, macd_weight=1, volume_spike_weight=1,
        momentum_weight=1, entry_score_threshold=Decimal("0.5"), exit_score_threshold=Decimal("-0.3"),
        trailing_stop_pct=Decimal("2"), max_daily_loss=Decimal("5000"),
    )
    db_session.add_all([strategy_a, strategy_b])
    db_session.commit()

    now = datetime.now(timezone.utc)
    _make_order_and_execution(db_session, portfolio.id, instrument.id, side="SELL", realized_pnl=Decimal("100"), gross_value=Decimal("1000"), total_charges=Decimal("20"), when=now, strategy_id=strategy_a.id)
    _make_order_and_execution(db_session, portfolio.id, instrument.id, side="SELL", realized_pnl=Decimal("-30"), gross_value=Decimal("1000"), total_charges=Decimal("20"), when=now, strategy_id=strategy_b.id)
    # A manual trade (no strategy_id) shouldn't show up under either strategy.
    _make_order_and_execution(db_session, portfolio.id, instrument.id, side="SELL", realized_pnl=Decimal("999"), gross_value=Decimal("1000"), total_charges=Decimal("20"), when=now, strategy_id=None)

    results = {r.strategy_name: r for r in strategy_analytics(db_session, portfolio.id)}

    assert results["Strategy A"].total_realized_pnl == Decimal("100")
    assert results["Strategy A"].win_count == 1
    assert results["Strategy B"].total_realized_pnl == Decimal("-30")
    assert results["Strategy B"].loss_count == 1
    assert results["Strategy B"].is_active is False
    # No third entry for the manual trade — confirms it wasn't misattributed.
    assert len(results) == 2
