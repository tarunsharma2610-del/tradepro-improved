"""Regression test for the strategy-position migration's legacy-data backfill."""

import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, text


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
    # SQLite stores SQLAlchemy Uuid columns as 32-character hex strings.
    return uuid.uuid4().hex


def test_strategy_position_migration_backfills_populated_legacy_database(tmp_path):
    database_path = tmp_path / "legacy-tradepro.sqlite"
    database_url = f"sqlite:///{database_path.as_posix()}"

    # Build the exact schema immediately before the migration under test.
    _run_alembic(database_url, "202610170002")

    user_id, portfolio_id, instrument_id = _id(), _id(), _id()
    closed_strategy_id, open_strategy_id, oversell_strategy_id = _id(), _id(), _id()
    now = datetime.now(timezone.utc).isoformat()

    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO users (id, email, password_hash, full_name) VALUES (:id, :email, :password, :name)"),
            {"id": user_id, "email": "migration-test@example.com", "password": "test-hash", "name": "Migration Test"},
        )
        connection.execute(
            text(
                "INSERT INTO portfolios (id, user_id, name, virtual_capital, cash_balance) "
                "VALUES (:id, :user_id, 'Legacy portfolio', 100000, 95000)"
            ),
            {"id": portfolio_id, "user_id": user_id},
        )
        connection.execute(
            text(
                "INSERT INTO instruments "
                "(id, instrument_key, exchange, segment, instrument_type, trading_symbol, name) "
                "VALUES (:id, 'NSE_EQ|MIGRATION_TEST', 'NSE', 'NSE_EQ', 'EQUITY', 'MIGTEST', 'Migration Test Ltd')"
            ),
            {"id": instrument_id},
        )
        connection.execute(
            text(
                "INSERT INTO strategies "
                "(id, portfolio_id, instrument_id, name, segment, quantity, max_daily_loss) "
                "VALUES (:id, :portfolio_id, :instrument_id, :name, 'EQUITY_INTRADAY', 1, 1000)"
            ),
            [
                {"id": closed_strategy_id, "portfolio_id": portfolio_id, "instrument_id": instrument_id, "name": "Closed legacy strategy"},
                {"id": open_strategy_id, "portfolio_id": portfolio_id, "instrument_id": instrument_id, "name": "Open legacy strategy"},
                {"id": oversell_strategy_id, "portfolio_id": portfolio_id, "instrument_id": instrument_id, "name": "Legacy oversell strategy"},
            ],
        )

        # An aggregate/manual position exists already and must not be rewritten
        # by a strategy-attribution-only migration.
        aggregate_position_id = _id()
        connection.execute(
            text(
                "INSERT INTO positions (id, portfolio_id, instrument_id, quantity, avg_price, realized_pnl) "
                "VALUES (:id, :portfolio_id, :instrument_id, 17, 123.4500, 12.34)"
            ),
            {"id": aggregate_position_id, "portfolio_id": portfolio_id, "instrument_id": instrument_id},
        )

        trade_rows = [
            # Closed strategy: buy 10 @ 100, sell 4 @ 110, sell remaining 6 @ 90.
            (closed_strategy_id, "BUY", 10, "100.00", "2026-10-01T09:15:00+00:00"),
            (closed_strategy_id, "SELL", 4, "110.00", "2026-10-01T10:00:00+00:00"),
            (closed_strategy_id, "SELL", 6, "90.00", "2026-10-01T11:00:00+00:00"),
            # Open strategy: weighted average must be 210 for 10 shares.
            (open_strategy_id, "BUY", 5, "200.00", "2026-10-02T09:15:00+00:00"),
            (open_strategy_id, "BUY", 5, "220.00", "2026-10-02T10:00:00+00:00"),
            # Historical bug shape: only 2 strategy-owned shares, but a tagged
            # sell of 5. Attribution must close only 2, never go short.
            (oversell_strategy_id, "BUY", 2, "50.00", "2026-10-03T09:15:00+00:00"),
            (oversell_strategy_id, "SELL", 5, "60.00", "2026-10-03T10:00:00+00:00"),
        ]
        expected = []
        for strategy_id, side, quantity, price, executed_at in trade_rows:
            order_id, execution_id = _id(), _id()
            connection.execute(
                text(
                    "INSERT INTO orders "
                    "(id, portfolio_id, instrument_id, side, order_type, segment, quantity, status, "
                    "trading_mode, execution_reason, strategy_id, placed_at, filled_at) "
                    "VALUES (:id, :portfolio_id, :instrument_id, :side, 'MARKET', 'EQUITY_INTRADAY', "
                    ":quantity, 'FILLED', 'PAPER', 'STRATEGY', :strategy_id, :placed_at, :filled_at)"
                ),
                {
                    "id": order_id, "portfolio_id": portfolio_id, "instrument_id": instrument_id,
                    "side": side, "quantity": quantity, "strategy_id": strategy_id,
                    "placed_at": executed_at, "filled_at": executed_at,
                },
            )
            gross = Decimal(price) * quantity
            connection.execute(
                text(
                    "INSERT INTO executions "
                    "(id, order_id, portfolio_id, instrument_id, side, quantity, price, gross_value, "
                    "brokerage, stt, exchange_charges, sebi_charges, stamp_duty, gst, total_charges, "
                    "realized_pnl, executed_at) "
                    "VALUES (:id, :order_id, :portfolio_id, :instrument_id, :side, :quantity, :price, "
                    ":gross, 0, 0, 0, 0, 0, 0, 0, 0, :executed_at)"
                ),
                {
                    "id": execution_id, "order_id": order_id, "portfolio_id": portfolio_id,
                    "instrument_id": instrument_id, "side": side, "quantity": quantity,
                    "price": price, "gross": str(gross), "executed_at": executed_at,
                },
            )
            expected.append((execution_id, strategy_id, side, quantity, Decimal(price)))

    # Upgrade the populated database through the migration under test.
    _run_alembic(database_url, "head")

    with engine.connect() as connection:
        pnl_by_execution = {
            row["id"]: Decimal(str(row["strategy_realized_pnl"]))
            for row in connection.execute(
                text("SELECT id, strategy_realized_pnl FROM executions")
            ).mappings()
        }
        assert [pnl_by_execution[row[0]] for row in expected] == [
            Decimal("0.00"), Decimal("40.00"), Decimal("-60.00"),
            Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("20.00"),
        ]

        allocations = {
            row["strategy_id"]: row
            for row in connection.execute(
                text(
                    "SELECT strategy_id, portfolio_id, instrument_id, quantity, avg_price, realized_pnl "
                    "FROM strategy_positions"
                )
            ).mappings()
        }
        closed = allocations[closed_strategy_id]
        assert closed["quantity"] == 0
        assert Decimal(str(closed["avg_price"])) == Decimal("0.0000")
        assert Decimal(str(closed["realized_pnl"])) == Decimal("-20.00")

        opened = allocations[open_strategy_id]
        assert opened["quantity"] == 10
        assert Decimal(str(opened["avg_price"])) == Decimal("210.0000")
        assert Decimal(str(opened["realized_pnl"])) == Decimal("0.00")

        oversold = allocations[oversell_strategy_id]
        assert oversold["quantity"] == 0
        assert Decimal(str(oversold["avg_price"])) == Decimal("0.0000")
        assert Decimal(str(oversold["realized_pnl"])) == Decimal("20.00")

        aggregate = connection.execute(
            text("SELECT quantity, avg_price, realized_pnl FROM positions WHERE id = :id"),
            {"id": aggregate_position_id},
        ).mappings().one()
        assert aggregate["quantity"] == 17
        assert Decimal(str(aggregate["avg_price"])) == Decimal("123.4500")
        assert Decimal(str(aggregate["realized_pnl"])) == Decimal("12.34")

        portfolio = connection.execute(
            text("SELECT cash_balance FROM portfolios WHERE id = :id"),
            {"id": portfolio_id},
        ).mappings().one()
        assert Decimal(str(portfolio["cash_balance"])) == Decimal("95000.00")

    # Re-running at head should be a no-op rather than duplicate allocations.
    _run_alembic(database_url, "head")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM strategy_positions")).scalar_one() == 3
        assert connection.execute(text("SELECT COUNT(*) FROM executions WHERE strategy_realized_pnl IS NULL")).scalar_one() == 0
    engine.dispose()
