"""PostgreSQL 16 transaction rollback and exactly-once PAPER retry acceptance.

Injects a failure after _fill has flushed its order, position, portfolio cash,
and execution writes but before the caller commits. The transaction must leave
no partial ledger/accounting state; a fresh retry must then commit exactly once.
"""
import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models  # noqa: F401
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.user import User
from app.services.execution_service import ExecutionService, PlaceOrderRequest
from app.services.transaction_costs import Segment, Side, calculate_costs


TEST_POSTGRES_URL = os.getenv("TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not TEST_POSTGRES_URL,
    reason="requires PostgreSQL 16 integration database",
)


def test_postgres_paper_fill_flush_failure_rolls_back_then_retry_commits_once():
    engine = create_engine(TEST_POSTGRES_URL, pool_size=3, max_overflow=0, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    db = Session()
    original_flush = db.flush
    user_id = uuid4()
    suffix = uuid4().hex[:12]
    portfolio = instrument = position = None
    try:
        user = User(
            id=user_id,
            email=f"pool-rollback-{suffix}@example.invalid",
            password_hash="test-only-not-authenticated",
            full_name="PostgreSQL PAPER rollback acceptance",
            is_admin=False,
        )
        portfolio = Portfolio(
            user_id=user.id,
            name="Rollback PAPER portfolio",
            trading_mode="PAPER",
            virtual_capital=Decimal("100000"),
            cash_balance=Decimal("100000"),
            balance_source="SIMULATED",
            is_active=True,
        )
        instrument = Instrument(
            instrument_key=f"NSE_EQ|{suffix}",
            exchange="NSE",
            segment="NSE_EQ",
            instrument_type="EQUITY",
            trading_symbol=f"RB{suffix[:8].upper()}",
            name="Rollback acceptance instrument",
        )
        db.add_all([user, portfolio, instrument])
        db.flush()
        position = Position(
            portfolio_id=portfolio.id,
            instrument_id=instrument.id,
            quantity=0,
            avg_price=Decimal("0"),
            realized_pnl=Decimal("0"),
        )
        db.add(position)
        db.commit()

        req = PlaceOrderRequest(
            portfolio_id=portfolio.id,
            instrument_id=instrument.id,
            side=Side.BUY,
            order_type="MARKET",
            segment=Segment.EQUITY_INTRADAY,
            quantity=2,
        )
        costs = calculate_costs(Segment.EQUITY_INTRADAY, Side.BUY, 2, Decimal("100"))

        def new_order():
            return Order(
                portfolio_id=portfolio.id,
                instrument_id=instrument.id,
                side="BUY",
                order_type="MARKET",
                segment="EQUITY_INTRADAY",
                quantity=2,
                limit_price=None,
                status="PENDING",
                trading_mode="PAPER",
                execution_reason="MANUAL",
                strategy_id=None,
                placed_at=datetime.now(timezone.utc),
            )

        # _fill performs four flushes in this fixture: order insert, position
        # update, portfolio update, then execution insert/final flush. Raise
        # only after the final flush has reached PostgreSQL.
        flush_calls = 0

        def fail_after_all_fill_rows_are_flushed(*args, **kwargs):
            nonlocal flush_calls
            flush_calls += 1
            result = original_flush(*args, **kwargs)
            if flush_calls == 4:
                raise RuntimeError("injected failure after PAPER ledger flush, before commit")
            return result

        db.flush = fail_after_all_fill_rows_are_flushed
        with pytest.raises(RuntimeError, match="after PAPER ledger flush"):
            ExecutionService(db)._fill(
                new_order(), portfolio, instrument, req, Decimal("100"), costs,
                charge_source="TEST", commit=False,
            )
        assert flush_calls == 4
        db.flush = original_flush
        db.rollback()

        # A separate session proves PostgreSQL persisted none of the failed
        # transaction's order, execution, position or cash changes.
        with Session() as verify:
            assert verify.query(Order).filter(Order.portfolio_id == portfolio.id).count() == 0
            assert verify.query(Execution).filter(Execution.portfolio_id == portfolio.id).count() == 0
            saved_portfolio = verify.get(Portfolio, portfolio.id)
            saved_position = verify.query(Position).filter(
                Position.portfolio_id == portfolio.id,
                Position.instrument_id == instrument.id,
            ).one()
            assert Decimal(str(saved_portfolio.cash_balance)) == Decimal("100000")
            assert saved_position.quantity == 0
            assert Decimal(str(saved_position.avg_price)) == Decimal("0")

        # Retry with a fresh session and the same economic order intent.
        with Session() as retry:
            retry_portfolio = retry.get(Portfolio, portfolio.id)
            retry_instrument = retry.get(Instrument, instrument.id)
            retry_order = ExecutionService(retry)._fill(
                new_order(), retry_portfolio, retry_instrument, req,
                Decimal("100"), costs, charge_source="TEST", commit=True,
            )
            retry_order_id = retry_order.id
            retry.commit()

        with Session() as verify:
            saved_portfolio = verify.get(Portfolio, portfolio.id)
            saved_position = verify.query(Position).filter(
                Position.portfolio_id == portfolio.id,
                Position.instrument_id == instrument.id,
            ).one()
            executions = verify.query(Execution).filter(
                Execution.portfolio_id == portfolio.id
            ).all()
            orders = verify.query(Order).filter(Order.portfolio_id == portfolio.id).all()
            assert len(orders) == 1
            assert len(executions) == 1
            assert orders[0].id == retry_order_id
            assert orders[0].status == "FILLED"
            assert orders[0].trading_mode == "PAPER"
            assert saved_position.quantity == 2
            assert Decimal(str(saved_portfolio.cash_balance)) == Decimal("100000") + costs.net_cash_impact
    finally:
        db.flush = original_flush
        db.rollback()
        cleanup_ids = {
            "portfolio": str(portfolio.id) if portfolio is not None else None,
            "instrument": str(instrument.id) if instrument is not None else None,
            "user": str(user_id),
        }
        db.close()
        with engine.begin() as connection:
            if cleanup_ids["portfolio"]:
                for table in ("executions", "orders", "positions"):
                    connection.execute(
                        text(f"DELETE FROM {table} WHERE portfolio_id = :portfolio_id"),
                        {"portfolio_id": cleanup_ids["portfolio"]},
                    )
                connection.execute(
                    text("DELETE FROM portfolios WHERE id = :portfolio_id"),
                    {"portfolio_id": cleanup_ids["portfolio"]},
                )
            if cleanup_ids["instrument"]:
                connection.execute(
                    text("DELETE FROM instruments WHERE id = :instrument_id"),
                    {"instrument_id": cleanup_ids["instrument"]},
                )
            connection.execute(
                text("DELETE FROM users WHERE id = :user_id"),
                {"user_id": cleanup_ids["user"]},
            )
        engine.dispose()
