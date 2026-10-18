"""PostgreSQL-only locking/uniqueness integration test.

The GitHub Actions workflow provisions an ephemeral PostgreSQL service and
runs this module after applying the real Alembic migration chain. The normal
unit-test suite remains SQLite-backed.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
import os
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.models.user import User
from app.services.live_charge_adjustment_service import LiveChargeAdjustmentService
from app.services.live_fill_accounting_service import (
    LiveChargeBreakdown,
    LiveFillAccountingService,
)


DATABASE_URL = os.getenv("POSTGRES_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="POSTGRES_TEST_DATABASE_URL is only set in the PostgreSQL CI integration step",
)


def _charges(reference: str, total: str) -> LiveChargeBreakdown:
    amount = Decimal(total)
    return LiveChargeBreakdown(
        brokerage=amount,
        stt=Decimal("0"),
        exchange_charges=Decimal("0"),
        sebi_charges=Decimal("0"),
        stamp_duty=Decimal("0"),
        gst=Decimal("0"),
        dp_charges=Decimal("0"),
        source="BROKER_REPORTED",
        reference=reference,
    )


def test_postgres_serializes_charge_revisions_and_deduplicates_same_reference():
    engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=0, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid4().hex
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        user = User(
            email=f"pg-charge-{suffix}@example.test",
            password_hash="integration-test-only",
            full_name="PostgreSQL Integration",
            is_admin=False,
        )
        db.add(user)
        db.flush()
        portfolio = Portfolio(
            user_id=user.id,
            name=f"PostgreSQL charge test {suffix[:8]}",
            virtual_capital=Decimal("100000"),
            cash_balance=Decimal("100000"),
        )
        instrument = Instrument(
            instrument_key=f"NSE_EQ|{suffix[:20]}",
            exchange="NSE",
            segment="NSE_EQ",
            instrument_type="EQUITY",
            trading_symbol=f"PG{suffix[:8]}",
            name="PostgreSQL test instrument",
            lot_size=1,
            tick_size=Decimal("0.05"),
            is_active=True,
        )
        db.add_all([portfolio, instrument])
        db.flush()
        connection = BrokerConnection(
            user_id=user.id,
            broker="upstox",
            api_key_encrypted="integration-key",
            api_secret_encrypted="integration-secret",
            redirect_uri="https://example.invalid/callback",
            is_connected=True,
        )
        db.add(connection)
        db.flush()
        order = Order(
            portfolio_id=portfolio.id,
            instrument_id=instrument.id,
            side="SELL",
            order_type="MARKET",
            segment="EQUITY_DELIVERY",
            quantity=1,
            status="FILLED",
            trading_mode="LIVE",
            execution_reason="MANUAL",
            placed_at=now,
            filled_at=now,
        )
        db.add(order)
        db.flush()
        execution = Execution(
            order_id=order.id,
            portfolio_id=portfolio.id,
            instrument_id=instrument.id,
            side="SELL",
            quantity=1,
            price=Decimal("100"),
            gross_value=Decimal("100"),
            brokerage=Decimal("10"),
            stt=Decimal("0"),
            exchange_charges=Decimal("0"),
            sebi_charges=Decimal("0"),
            stamp_duty=Decimal("0"),
            gst=Decimal("0"),
            dp_charges=Decimal("0"),
            total_charges=Decimal("10"),
            charge_source="APPROVED_ESTIMATE",
            charge_reference="integration-estimate",
            realized_pnl=Decimal("50"),
            broker_name="upstox",
            broker_connection_id=connection.id,
            broker_trade_id=f"trade-{suffix}",
            executed_at=now,
        )
        db.add(execution)

        # Separate reconciled staged fill used to verify PostgreSQL row-lock
        # scoping and concurrent duplicate promotion.
        fill_order = Order(
            portfolio_id=portfolio.id,
            instrument_id=instrument.id,
            side="SELL",
            order_type="MARKET",
            segment="EQUITY_DELIVERY",
            quantity=1,
            status="PENDING",
            trading_mode="LIVE",
            execution_reason="MANUAL",
            placed_at=now,
        )
        db.add(fill_order)
        db.flush()
        child = BrokerOrder(
            order_id=fill_order.id,
            broker_connection_id=connection.id,
            broker_name="upstox",
            broker_order_id=f"child-{suffix}",
            requested_quantity=1,
            filled_quantity=1,
            status="FILLED",
            status_checked_at=now,
        )
        db.add(child)
        db.flush()
        staged_record = BrokerTradeRecord(
            broker_connection_id=connection.id,
            broker_order_ref_id=child.id,
            broker_trade_id=f"fill-{suffix}",
            quantity=1,
            price=Decimal("100"),
            side="SELL",
            instrument_token=instrument.instrument_key,
            exchange_timestamp=now.isoformat(),
        )
        db.add(staged_record)
        db.commit()
        user_id = user.id
        connection_id = connection.id
        trade_id = execution.broker_trade_id
        execution_id = execution.id
        staged_record_id = staged_record.id

    barrier = Barrier(2)

    def apply(reference: str, total: str):
        barrier.wait(timeout=10)
        with SessionLocal() as db:
            return LiveChargeAdjustmentService(db).apply_broker_reported_charges(
                user_id, connection_id, trade_id, _charges(reference, total)
            )

    # Distinct revisions may arrive concurrently, but execution-row locking
    # must serialize their adjustment_number / previous-effective-total chain.
    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(apply, "contract-note-A", "12.00")
        second_future = pool.submit(apply, "contract-note-B", "15.00")
        distinct_results = [first_future.result(timeout=20), second_future.result(timeout=20)]

    assert all(not result.duplicate for result in distinct_results)
    with SessionLocal() as db:
        from app.models.live_charge_adjustment import LiveChargeAdjustment

        rows = (
            db.query(LiveChargeAdjustment)
            .filter(LiveChargeAdjustment.execution_id == execution_id)
            .order_by(LiveChargeAdjustment.adjustment_number)
            .all()
        )
        assert [row.adjustment_number for row in rows] == [1, 2]
        assert rows[1].previous_effective_total == rows[0].new_effective_total

    # Concurrent replay of the same contract-note reference is idempotent:
    # exactly one request inserts the row, the other returns duplicate=True.
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(apply, "contract-note-final", "18.00")
        second_future = pool.submit(apply, "contract-note-final", "18.00")
        same_reference_results = [first_future.result(timeout=20), second_future.result(timeout=20)]

    assert sorted(result.duplicate for result in same_reference_results) == [False, True]
    with SessionLocal() as db:
        from app.models.live_charge_adjustment import LiveChargeAdjustment

        rows = (
            db.query(LiveChargeAdjustment)
            .filter(LiveChargeAdjustment.execution_id == execution_id)
            .order_by(LiveChargeAdjustment.adjustment_number)
            .all()
        )
        assert [row.adjustment_number for row in rows] == [1, 2, 3]
        assert rows[-1].new_effective_total == Decimal("18.00")

    # The same broker trade may be promoted concurrently, but must create one
    # Execution and mutate the LivePosition only once. This also exercises
    # PostgreSQL FOR UPDATE OF on models with joined Instrument relationships.
    barrier = Barrier(2)

    def promote():
        barrier.wait(timeout=10)
        with SessionLocal() as db:
            return LiveFillAccountingService(db).account_trade(
                user_id,
                staged_record_id,
                LiveChargeBreakdown(
                    brokerage=Decimal("1"),
                    stt=Decimal("0"),
                    exchange_charges=Decimal("0"),
                    sebi_charges=Decimal("0"),
                    stamp_duty=Decimal("0"),
                    gst=Decimal("0"),
                    dp_charges=Decimal("0"),
                    source="BROKER_REPORTED",
                    reference="contract-note:concurrent-fill",
                ),
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(promote)
        second_future = pool.submit(promote)
        promotion_results = [first_future.result(timeout=20), second_future.result(timeout=20)]

    assert sorted(result.duplicate for result in promotion_results) == [False, True]
    with SessionLocal() as db:
        from app.models.live_position import LivePosition

        fill_executions = (
            db.query(Execution)
            .filter(
                Execution.broker_connection_id == connection_id,
                Execution.broker_trade_id == f"fill-{suffix}",
            )
            .all()
        )
        assert len(fill_executions) == 1
        position = db.query(LivePosition).filter(
            LivePosition.broker_connection_id == connection_id,
            LivePosition.instrument_id == fill_executions[0].instrument_id,
        ).one()
        assert position.quantity == -1
    engine.dispose()
