"""Regression coverage for additive broker-order schema migration."""

import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


BACKEND_DIR = Path(__file__).resolve().parents[1]


def _run_alembic(database_url: str, revision: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env["MASTER_ENCRYPTION_KEY"] = "HuszwzTH0J4Uzhmkxh7WgSPUoZMkwOZDHZFlAZA-u24="
    env["SECRET_KEY"] = "test-secret-key-not-for-production"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", revision],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, (
        f"Alembic upgrade to {revision} failed.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def _id() -> str:
    return uuid.uuid4().hex


def test_live_broker_schema_migration_preserves_existing_paper_data(tmp_path):
    database_path = tmp_path / "broker-schema.sqlite"
    database_url = f"sqlite:///{database_path.as_posix()}"
    _run_alembic(database_url, "202610170003")

    user_id, portfolio_id, instrument_id = _id(), _id(), _id()
    order_id, execution_id = _id(), _id()
    now = datetime.now(timezone.utc).isoformat()

    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO users (id, email, password_hash, full_name) VALUES (:id, :email, :password, :name)"),
            {"id": user_id, "email": "broker-schema@example.com", "password": "test-hash", "name": "Schema Test"},
        )
        connection.execute(
            text(
                "INSERT INTO portfolios (id, user_id, name, virtual_capital, cash_balance) "
                "VALUES (:id, :user_id, 'Paper portfolio', 100000, 95000)"
            ),
            {"id": portfolio_id, "user_id": user_id},
        )
        connection.execute(
            text(
                "INSERT INTO instruments "
                "(id, instrument_key, exchange, segment, instrument_type, trading_symbol, name) "
                "VALUES (:id, 'NSE_EQ|BROKER_SCHEMA_TEST', 'NSE', 'NSE_EQ', 'EQUITY', 'BRKTEST', 'Broker Schema Test')"
            ),
            {"id": instrument_id},
        )
        connection.execute(
            text(
                "INSERT INTO orders "
                "(id, portfolio_id, instrument_id, side, order_type, segment, quantity, status, trading_mode, "
                "execution_reason, placed_at, filled_at) "
                "VALUES (:id, :portfolio_id, :instrument_id, 'BUY', 'MARKET', 'EQUITY_DELIVERY', 2, "
                "'FILLED', 'PAPER', 'MANUAL', :placed_at, :filled_at)"
            ),
            {
                "id": order_id, "portfolio_id": portfolio_id, "instrument_id": instrument_id,
                "placed_at": now, "filled_at": now,
            },
        )
        connection.execute(
            text(
                "INSERT INTO executions "
                "(id, order_id, portfolio_id, instrument_id, side, quantity, price, gross_value, brokerage, stt, "
                "exchange_charges, sebi_charges, stamp_duty, gst, total_charges, realized_pnl, "
                "strategy_realized_pnl, executed_at) "
                "VALUES (:id, :order_id, :portfolio_id, :instrument_id, 'BUY', 2, 100, 200, 0, 0, 0, 0, 0, 0, 0, 0, 0, :executed_at)"
            ),
            {
                "id": execution_id, "order_id": order_id, "portfolio_id": portfolio_id,
                "instrument_id": instrument_id, "executed_at": now,
            },
        )

    _run_alembic(database_url, "head")

    broker_order_one_id, broker_order_two_id = _id(), _id()
    broker_tag = "tp" + order_id
    with engine.begin() as connection:
        existing_order = connection.execute(
            text("SELECT status, trading_mode, quantity, broker_tag FROM orders WHERE id = :id"),
            {"id": order_id},
        ).mappings().one()
        assert existing_order["status"] == "FILLED"
        assert existing_order["trading_mode"] == "PAPER"
        assert existing_order["quantity"] == 2
        assert existing_order["broker_tag"] is None

        existing_execution = connection.execute(
            text(
                "SELECT quantity, price, broker_name, broker_trade_id, broker_order_ref_id "
                "FROM executions WHERE id = :id"
            ),
            {"id": execution_id},
        ).mappings().one()
        assert existing_execution["quantity"] == 2
        assert Decimal(str(existing_execution["price"])) == Decimal("100.0000")
        assert existing_execution["broker_name"] is None
        assert existing_execution["broker_trade_id"] is None
        assert existing_execution["broker_order_ref_id"] is None

        # One conceptual local order can safely map to multiple broker child IDs.
        for child_id, broker_id in [
            (broker_order_one_id, "upstox-child-order-1"),
            (broker_order_two_id, "upstox-child-order-2"),
        ]:
            connection.execute(
                text(
                    "INSERT INTO broker_orders "
                    "(id, order_id, broker_name, broker_order_id, broker_tag, status, requested_quantity, filled_quantity) "
                    "VALUES (:id, :order_id, 'upstox', :broker_order_id, :tag, 'open', 1, 0)"
                ),
                {
                    "id": child_id, "order_id": order_id,
                    "broker_order_id": broker_id, "tag": broker_tag,
                },
            )

        child = connection.execute(
            text("SELECT id FROM broker_orders WHERE broker_order_id = 'upstox-child-order-1'")
        ).mappings().one()
        live_execution_id = _id()
        connection.execute(
            text(
                "INSERT INTO executions "
                "(id, order_id, portfolio_id, instrument_id, side, quantity, price, gross_value, brokerage, stt, "
                "exchange_charges, sebi_charges, stamp_duty, gst, total_charges, realized_pnl, executed_at, "
                "broker_order_ref_id, broker_name, broker_trade_id) "
                "VALUES (:id, :order_id, :portfolio_id, :instrument_id, 'BUY', 1, 101, 101, 0, 0, 0, 0, 0, 0, 0, 0, :executed_at, :broker_order_ref_id, 'upstox', 'trade-unique-1')"
            ),
            {
                "id": live_execution_id, "order_id": order_id, "portfolio_id": portfolio_id,
                "instrument_id": instrument_id, "executed_at": now,
                "broker_order_ref_id": child["id"],
            },
        )

        # The database constraint prevents a replayed broker trade from being
        # recorded as a second execution for the same broker.
        with pytest.raises(IntegrityError):
            with connection.begin_nested():
                connection.execute(
                    text(
                        "INSERT INTO executions "
                        "(id, order_id, portfolio_id, instrument_id, side, quantity, price, gross_value, brokerage, stt, "
                        "exchange_charges, sebi_charges, stamp_duty, gst, total_charges, realized_pnl, executed_at, "
                        "broker_order_ref_id, broker_name, broker_trade_id) "
                        "VALUES (:id, :order_id, :portfolio_id, :instrument_id, 'BUY', 1, 101, 101, 0, 0, 0, 0, 0, 0, 0, 0, :executed_at, :broker_order_ref_id, 'upstox', 'trade-unique-1')"
                    ),
                    {
                        "id": _id(), "order_id": order_id, "portfolio_id": portfolio_id,
                        "instrument_id": instrument_id, "executed_at": now,
                        "broker_order_ref_id": child["id"],
                    },
                )

        # The new status width must hold the explicit partial-fill state.
        connection.execute(
            text("UPDATE orders SET status = 'PARTIALLY_FILLED', broker_tag = :tag WHERE id = :id"),
            {"tag": broker_tag, "id": order_id},
        )
        row = connection.execute(
            text("SELECT status, broker_tag FROM orders WHERE id = :id"), {"id": order_id}
        ).mappings().one()
        assert row["status"] == "PARTIALLY_FILLED"
        assert row["broker_tag"] == broker_tag

        # Broker order IDs are unique per broker.
        with pytest.raises(IntegrityError):
            with connection.begin_nested():
                connection.execute(
                    text(
                        "INSERT INTO broker_orders "
                        "(id, order_id, broker_name, broker_order_id, broker_tag, status, requested_quantity, filled_quantity) "
                        "VALUES (:id, :order_id, 'upstox', 'upstox-child-order-1', :tag, 'open', 1, 0)"
                    ),
                    {"id": _id(), "order_id": order_id, "tag": broker_tag},
                )

    engine.dispose()
