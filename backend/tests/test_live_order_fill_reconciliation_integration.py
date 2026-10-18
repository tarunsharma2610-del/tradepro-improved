from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.brokers.base import BrokerCallResult
from app.core.config import settings
from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.execution import Execution
from app.models.live_position import LivePosition
from app.models.order import Order
from app.models.position import Position
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.instrument_service import InstrumentService
from app.services.live_order_fill_reconciliation_coordinator import (
    LiveOrderFillReconciliationCoordinator,
)
from app.services.live_fill_promotion_service import LiveFillPromotionService
from app.services.live_charge_estimate_service import LiveChargeEstimateService
from app.services.broker_child_order_reconciliation_service import (
    BrokerChildOrderReconciliationService,
)


class FakeReadOnlyUpstoxAdapter:
    """Only implements read endpoints needed for mocked reconciliation/promotion."""

    def __init__(self, instrument_key, *, fail_status=False, fail_estimate=False):
        self.instrument_key = instrument_key
        self.fail_status = fail_status
        self.fail_estimate = fail_estimate
        self.calls = []
        self.estimate_calls = 0

    async def get_order_trades(self, access_token, order_id):
        self.calls.append(("trades", order_id))
        return BrokerCallResult(ok=True, data={
            "status": "success",
            "data": [
                {
                    "order_id": order_id,
                    "trade_id": "trade-fill-001",
                    "quantity": 1,
                    "average_price": 100.0,
                    "transaction_type": "BUY",
                    "instrument_token": self.instrument_key,
                    "exchange_timestamp": "2026-10-19T10:30:00+05:30",
                },
                {
                    "order_id": order_id,
                    "trade_id": "trade-fill-002",
                    "quantity": 1,
                    "average_price": 101.0,
                    "transaction_type": "BUY",
                    "instrument_token": self.instrument_key,
                    "exchange_timestamp": "2026-10-19T10:30:01+05:30",
                },
            ],
        })

    async def get_order_status(self, access_token, order_id):
        self.calls.append(("status", order_id))
        if self.fail_status:
            return BrokerCallResult(ok=False, error="mock status unavailable")
        return BrokerCallResult(ok=True, data={
            "status": "success",
            "data": {
                "order_id": order_id,
                "status": "complete",
                "quantity": 2,
                "filled_quantity": 2,
                "average_price": 100.5,
                "instrument_token": self.instrument_key,
                "transaction_type": "BUY",
            },
        })

    async def get_brokerage_details(self, access_token, **params):
        self.calls.append(("brokerage", params["quantity"]))
        self.estimate_calls += 1
        if self.fail_estimate:
            return BrokerCallResult(ok=False, error="mock brokerage estimate unavailable")
        return BrokerCallResult(ok=True, data={
            "status": "success",
            "data": {
                "charges": {
                    "total": 2.63,
                    "brokerage": 2.00,
                    "taxes": {"gst": 0.37, "stt": 0.20, "stamp_duty": 0.02},
                    "other_charges": {
                        "transaction": 0.03,
                        "clearing": 0,
                        "ipft": 0,
                        "sebi_turnover": 0.01,
                    },
                    "dp_plan": {"name": "DP3A", "min_expense": 0},
                }
            },
        })


@pytest.fixture()
def live_order_context(db_session, make_user, monkeypatch):
    user = make_user()
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id, name="End-to-end fill reconcile", virtual_capital=Decimal("100000")
    )
    InstrumentService(db_session).seed_defaults()
    instrument = InstrumentRepository(db_session).search("RELIANCE")[0]
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="test-key",
        api_secret_encrypted="test-secret",
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted="test-token",
        access_token_expires_at=datetime(2026, 10, 20, 18, 0, tzinfo=timezone.utc),
        is_connected=True,
    )
    now = datetime(2026, 10, 19, 5, 0, tzinfo=timezone.utc)
    order = Order(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        side="BUY",
        order_type="MARKET",
        segment="EQUITY_DELIVERY",
        quantity=2,
        status="PENDING",
        trading_mode="LIVE",
        execution_reason="MANUAL",
        broker_order_id="broker-child-1",
        placed_at=now,
    )
    db_session.add_all([connection, order])
    db_session.flush()
    child = BrokerOrder(
        order_id=order.id,
        broker_connection_id=connection.id,
        broker_name="upstox",
        broker_order_id="broker-child-1",
        requested_quantity=2,
        filled_quantity=0,
        status="UNKNOWN",
    )
    db_session.add(child)
    db_session.commit()
    monkeypatch.setattr(
        BrokerCredentialsService, "get_access_token", lambda *_: "mock-access-token"
    )
    monkeypatch.setattr(settings, "AUTOMATED_ENTRIES_ENABLED", False)
    return db_session, user, portfolio, instrument, connection, order, child, now


def _coordinator(db, adapter):
    child_reconciler = BrokerChildOrderReconciliationService(db, adapter=adapter)
    estimator = LiveChargeEstimateService(db, adapter=adapter)
    promoter = LiveFillPromotionService(db, charge_estimator=estimator)
    return LiveOrderFillReconciliationCoordinator(
        db, child_reconciler=child_reconciler, promotion_service=promoter
    )


@pytest.mark.asyncio
async def test_real_service_chain_reconciles_then_promotes_idempotently_without_paper_side_effects(
    live_order_context,
):
    db, user, portfolio, instrument, connection, order, child, now = live_order_context
    before_cash = Decimal(str(portfolio.cash_balance))
    adapter = FakeReadOnlyUpstoxAdapter(instrument.instrument_key)
    coordinator = _coordinator(db, adapter)

    first = await coordinator.reconcile_and_promote(user.id, order.id)

    assert first.reconciliation_complete
    assert first.promotion_complete
    assert first.total_staged_trades == 2
    assert first.total_promoted_trades == 2
    assert first.total_duplicate_trades == 0
    assert db.query(BrokerTradeRecord).count() == 2
    assert db.query(Execution).count() == 2
    assert db.query(LivePosition).one().quantity == 2
    assert db.query(LivePosition).one().avg_price == Decimal("100.5000")
    assert db.query(Position).count() == 0
    db.refresh(portfolio)
    assert Decimal(str(portfolio.cash_balance)) == before_cash
    db.refresh(order)
    assert order.status == "PENDING"
    db.refresh(child)
    assert child.status == "FILLED"
    assert child.filled_quantity == 2
    assert adapter.estimate_calls == 2
    assert not any(name == "place_order" for name, *_ in adapter.calls)

    second = await coordinator.reconcile_and_promote(user.id, order.id)

    assert second.reconciliation_complete
    assert second.promotion_complete
    assert second.total_staged_trades == 2
    assert second.total_promoted_trades == 0
    assert second.total_duplicate_trades == 2
    assert db.query(Execution).count() == 2
    assert db.query(LivePosition).one().quantity == 2
    db.refresh(portfolio)
    assert Decimal(str(portfolio.cash_balance)) == before_cash
    assert adapter.estimate_calls == 2  # duplicate promotion reuses stored charge provenance


@pytest.mark.asyncio
async def test_status_failure_leaves_staged_trades_unaccounted(live_order_context):
    db, user, portfolio, instrument, connection, order, child, now = live_order_context
    before_cash = Decimal(str(portfolio.cash_balance))
    adapter = FakeReadOnlyUpstoxAdapter(instrument.instrument_key, fail_status=True)
    result = await _coordinator(db, adapter).reconcile_and_promote(user.id, order.id)

    assert not result.reconciliation_complete
    assert not result.promotion_complete
    assert result.total_staged_trades == 2
    assert result.total_promoted_trades == 0
    assert result.blocked_reason and "No fills were promoted" in result.blocked_reason
    assert db.query(BrokerTradeRecord).count() == 2
    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    assert db.query(Position).count() == 0
    db.refresh(portfolio)
    assert Decimal(str(portfolio.cash_balance)) == before_cash
    db.refresh(child)
    assert child.status == "UNKNOWN"
    assert child.status_checked_at is None
    assert not any(name == "place_order" for name, *_ in adapter.calls)


@pytest.mark.asyncio
async def test_estimate_failure_after_reconciliation_writes_no_accounting_rows(live_order_context):
    db, user, portfolio, instrument, connection, order, child, now = live_order_context
    before_cash = Decimal(str(portfolio.cash_balance))
    adapter = FakeReadOnlyUpstoxAdapter(instrument.instrument_key, fail_estimate=True)
    result = await _coordinator(db, adapter).reconcile_and_promote(user.id, order.id)

    assert result.reconciliation_complete
    assert not result.promotion_complete
    assert result.total_staged_trades == 2
    assert result.total_promoted_trades == 0
    assert result.blocked_reason and "Promotion stopped" in result.blocked_reason
    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    db.refresh(portfolio)
    assert Decimal(str(portfolio.cash_balance)) == before_cash
    assert not any(name == "place_order" for name, *_ in adapter.calls)
