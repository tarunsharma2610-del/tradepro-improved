from datetime import datetime, timedelta, timezone
import uuid

import pytest

from app.brokers.upstox.reconciliation_client import ReadOnlyBrokerResult
from app.models.broker_connection import BrokerConnection
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.execution import Execution
from app.models.live_position import LivePosition
from app.models.live_order_records import BrokerFillIdentity, LiveOrderIntent, LiveReconciliationIssue, LiveReconciliationLease, LiveReconciliationRun
from app.models.portfolio import Portfolio
from app.repositories.live_order_repository import LiveOrderRepository
from app.repositories.live_reconciliation_lease_repository import LiveReconciliationLeaseRepository
from app.services.live_order_reconciliation_worker import LiveOrderReconciliationWorker


class _FakeReadClient:
    def __init__(self, orders=None, trades=None, order_results=None, trade_results=None):
        self.orders = orders or []
        self.trades = trades or []
        self.order_results = list(order_results or [])
        self.trade_results = list(trade_results or [])
        self.calls = []

    async def get_order_book(self, access_token):
        self.calls.append(("orders", access_token))
        if self.order_results:
            return self.order_results.pop(0)
        return ReadOnlyBrokerResult(True, {"status": "success", "data": self.orders}, 200)

    async def get_trades_for_day(self, access_token):
        self.calls.append(("trades", access_token))
        if self.trade_results:
            return self.trade_results.pop(0)
        return ReadOnlyBrokerResult(True, {"status": "success", "data": self.trades}, 200)


def _setup(db_session, make_user, *, is_connected=True):
    user = make_user()
    portfolio = Portfolio(
        user_id=user.id, name="Worker test", virtual_capital=100000,
        cash_balance=100000, is_active=True,
    )
    connection = BrokerConnection(
        user_id=user.id, broker="upstox", api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret", redirect_uri="https://example.invalid/callback",
        is_connected=is_connected,
    )
    db_session.add_all([portfolio, connection])
    db_session.commit()
    return user, portfolio, connection


def _order(**overrides):
    record = {
        "order_id": "broker-order-1", "status": "complete",
        "instrument_token": "NSE_EQ|TEST", "transaction_type": "BUY",
        "order_type": "LIMIT", "quantity": 1, "filled_quantity": 1,
        "average_price": 99.25, "price": 100.0, "trigger_price": 0,
        "product": "D", "tag": "intent-tag-1",
    }
    record.update(overrides)
    return record


def _trade(**overrides):
    record = {
        "trade_id": "trade-1", "order_id": "broker-order-1",
        "instrument_token": "NSE_EQ|TEST", "transaction_type": "BUY",
        "quantity": 1, "average_price": 99.25,
        "exchange_timestamp": "17-Oct-2026 10:15:30",
        "product": "D", "order_type": "LIMIT", "exchange": "NSE",
        "trading_symbol": "TEST-EQ", "exchange_order_id": "exchange-order-1",
        "order_ref_id": "ref-1",
    }
    record.update(overrides)
    return record


def _intent(db_session, user, portfolio, connection, *, tag="intent-tag-1", quantity=1):
    repository = LiveOrderRepository(db_session)
    intent, _ = repository.create_or_get_intent(
        user_id=user.id,
        portfolio_id=portfolio.id,
        broker_connection_id=connection.id,
        client_idempotency_key="worker-intent-1",
        order_snapshot={
            "instrument_key": "NSE_EQ|TEST", "side": "BUY", "order_type": "LIMIT",
            "quantity": quantity, "limit_price": "100.00", "product": "D",
        },
        correlation_id="worker-test",
    )
    intent.broker_tag = tag
    db_session.commit()
    db_session.refresh(intent)
    return intent


@pytest.mark.asyncio
async def test_worker_links_trade_and_resolves_full_fill_without_order_write_methods(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    intent = _intent(db_session, user, portfolio, connection)
    client = _FakeReadClient(orders=[_order()], trades=[_trade()])
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token",
        sleeper=lambda _delay: _no_sleep(),
    )

    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    db_session.refresh(intent)
    assert result.status == "COMPLETED"
    assert result.orders_seen == 1
    assert result.orders_matched == 1
    assert result.fills_inserted == 1
    assert intent.state == "FILLED"
    assert intent.broker_order_id == "broker-order-1"
    fill = db_session.query(BrokerFillIdentity).filter_by(broker_trade_id="trade-1").one()
    assert fill.intent_id == intent.id
    # Architectural boundary: the intent-based reconciliation worker stores
    # BrokerFillIdentity evidence only. It must never create manual-order staging
    # rows or promote evidence into live accounting as a side effect.
    assert db_session.query(BrokerTradeRecord).count() == 0
    assert db_session.query(Execution).count() == 0
    assert db_session.query(LivePosition).count() == 0
    db_session.refresh(portfolio)
    assert portfolio.cash_balance == 100000
    assert [call[0] for call in client.calls] == ["orders", "trades"]
    assert not hasattr(client, "place_order")
    row = db_session.query(LiveReconciliationLease).filter_by(
        broker_connection_id=connection.id
    ).one()
    assert row.lease_token is None
    assert row.last_error_code is None


async def _no_sleep():
    return None


@pytest.mark.asyncio
async def test_worker_repeat_run_deduplicates_fill_and_audit(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    intent = _intent(db_session, user, portfolio, connection)
    client = _FakeReadClient(orders=[_order()], trades=[_trade()])
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token",
        sleeper=_no_sleep,
    )

    first = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)
    second = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    assert first.status == "COMPLETED"
    assert second.status == "COMPLETED"
    assert second.duplicate_fills == 1
    assert db_session.query(BrokerFillIdentity).filter_by(broker_trade_id="trade-1").count() == 1
    # Replay must preserve the same workflow boundary as the initial pass.
    assert db_session.query(BrokerTradeRecord).count() == 0
    assert db_session.query(Execution).count() == 0
    assert db_session.query(LivePosition).count() == 0


@pytest.mark.asyncio
async def test_worker_does_not_mutate_when_trade_read_fails(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    intent = _intent(db_session, user, portfolio, connection)
    client = _FakeReadClient(
        orders=[_order()],
        trade_results=[ReadOnlyBrokerResult(False, status_code=429, error_code="RATE_LIMITED")],
    )
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token",
        max_attempts=1, sleeper=_no_sleep,
    )

    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    db_session.refresh(intent)
    assert result.status == "FAILED"
    assert result.error_code == "RATE_LIMITED"
    assert intent.state == "CREATED"
    assert intent.broker_order_id is None
    assert db_session.query(BrokerFillIdentity).count() == 0


@pytest.mark.asyncio
async def test_worker_retries_only_read_only_transient_errors_and_respects_retry_after(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    _intent(db_session, user, portfolio, connection)
    client = _FakeReadClient(
        orders=[_order()], trades=[_trade()],
        order_results=[
            ReadOnlyBrokerResult(False, status_code=429, error_code="RATE_LIMITED", retry_after_seconds=2.0),
            ReadOnlyBrokerResult(True, {"status": "success", "data": [_order()]}, 200),
        ],
    )
    delays = []

    async def sleep(delay):
        delays.append(delay)

    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token",
        sleeper=sleep, max_attempts=2, max_delay_seconds=5,
    )
    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    assert result.status == "COMPLETED"
    assert delays == [2.0]
    assert [call[0] for call in client.calls] == ["orders", "orders", "trades"]


@pytest.mark.asyncio
async def test_worker_missing_token_and_busy_lease_do_not_call_broker(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    client = _FakeReadClient()
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: None, sleeper=_no_sleep
    )
    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)
    assert result.error_code == "TOKEN_UNAVAILABLE"
    assert client.calls == []

    connection.is_connected = True
    db_session.commit()
    stale_started = datetime.now(timezone.utc) - timedelta(hours=1)
    stale_run = LiveReconciliationRun(
        user_id=user.id,
        broker_connection_id=connection.id,
        status="RUNNING",
        started_at=stale_started,
        summary={
            "orders_seen": 0, "orders_matched": 0, "orders_unmatched": 0,
            "trades_seen": 0, "fills_inserted": 0, "duplicate_fills": 0,
            "conflicts": 0,
        },
    )
    db_session.add(stale_run)
    db_session.commit()
    lease_token = LiveReconciliationLeaseRepository(db_session).claim(
        user_id=user.id, broker_connection_id=connection.id, lease_seconds=60
    )
    assert lease_token is not None
    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)
    assert result.status == "LEASE_BUSY"
    db_session.refresh(stale_run)
    assert stale_run.status == "RUNNING"
    assert client.calls == []


@pytest.mark.asyncio
async def test_worker_rejects_cross_user_connection_before_network(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    other = make_user(email="worker-other@example.com")
    client = _FakeReadClient()
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token", sleeper=_no_sleep
    )
    result = await worker.run_for_connection(user_id=other.id, broker_connection_id=connection.id)
    assert result.status == "FAILED"
    assert result.error_code == "CONNECTION_NOT_FOUND"
    assert client.calls == []


@pytest.mark.asyncio
async def test_worker_stores_unmatched_trade_without_linking_to_wrong_intent(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    _intent(db_session, user, portfolio, connection, tag="some-other-tag")
    client = _FakeReadClient(
        orders=[_order(tag="not-the-local-tag", order_id="manual-order-77")],
        trades=[_trade(order_id="manual-order-77", trade_id="manual-trade-77")],
    )
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token", sleeper=_no_sleep
    )
    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    assert result.status == "COMPLETED"
    assert result.orders_unmatched == 1
    fill = db_session.query(BrokerFillIdentity).filter_by(broker_trade_id="manual-trade-77").one()
    assert fill.intent_id is None



@pytest.mark.asyncio
async def test_execution_status_without_trade_evidence_is_unknown_then_recovers(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    intent = _intent(db_session, user, portfolio, connection)
    client = _FakeReadClient(orders=[_order()], trades=[])
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token", sleeper=_no_sleep
    )

    first = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)
    db_session.refresh(intent)
    assert first.status == "COMPLETED_WITH_CONFLICTS"
    assert intent.state == "UNKNOWN"
    assert intent.broker_order_id == "broker-order-1"
    assert db_session.query(BrokerFillIdentity).count() == 0

    # A later read supplies the actual trade. UNKNOWN is recoverable and can become FILLED.
    client.trades = [_trade()]
    second = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)
    db_session.refresh(intent)
    assert second.status == "COMPLETED"
    assert intent.state == "FILLED"
    assert db_session.query(BrokerFillIdentity).filter_by(intent_id=intent.id).count() == 1



@pytest.mark.asyncio
async def test_worker_does_not_retry_forbidden_response(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    intent = _intent(db_session, user, portfolio, connection)
    client = _FakeReadClient(
        order_results=[ReadOnlyBrokerResult(False, status_code=403, error_code="FORBIDDEN")],
    )
    delays = []

    async def sleep(delay):
        delays.append(delay)

    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token",
        sleeper=sleep, max_attempts=3,
    )
    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    db_session.refresh(intent)
    assert result.status == "FAILED"
    assert result.error_code == "FORBIDDEN"
    assert [call[0] for call in client.calls] == ["orders"]
    assert delays == []
    assert intent.state == "CREATED"
    assert db_session.query(BrokerFillIdentity).count() == 0


@pytest.mark.asyncio
async def test_worker_bounds_server_error_retries_before_any_mutation(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    intent = _intent(db_session, user, portfolio, connection)
    client = _FakeReadClient(
        order_results=[
            ReadOnlyBrokerResult(False, status_code=503, error_code="UPSTREAM_SERVER_ERROR"),
            ReadOnlyBrokerResult(False, status_code=503, error_code="UPSTREAM_SERVER_ERROR"),
            ReadOnlyBrokerResult(False, status_code=503, error_code="UPSTREAM_SERVER_ERROR"),
        ],
    )
    delays = []

    async def sleep(delay):
        delays.append(delay)

    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token",
        sleeper=sleep, max_attempts=3, base_delay_seconds=0.25, max_delay_seconds=1,
    )
    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    db_session.refresh(intent)
    assert result.status == "FAILED"
    assert result.error_code == "UPSTREAM_SERVER_ERROR"
    assert [call[0] for call in client.calls] == ["orders", "orders", "orders"]
    assert delays == [0.25, 0.5]
    assert intent.state == "CREATED"
    assert intent.broker_order_id is None
    assert db_session.query(BrokerFillIdentity).count() == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [
    None,
    {},
    {"status": "error", "data": []},
    {"status": "success", "data": {"unexpected": "object"}},
    {"status": "success", "data": [None]},
])
async def test_worker_rejects_malformed_order_envelope_without_persisting_evidence(
    body, db_session, make_user
):
    user, portfolio, connection = _setup(db_session, make_user)
    intent = _intent(db_session, user, portfolio, connection)
    client = _FakeReadClient(
        order_results=[ReadOnlyBrokerResult(True, body, 200)],
        trade_results=[ReadOnlyBrokerResult(True, {"status": "success", "data": [_trade()]}, 200)],
    )
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token", sleeper=_no_sleep
    )
    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    db_session.refresh(intent)
    assert result.status == "FAILED"
    assert result.error_code in {"INVALID_RESPONSE_ENVELOPE", "INVALID_RESPONSE_DATA"}
    assert intent.state == "CREATED"
    assert intent.broker_order_id is None
    assert db_session.query(BrokerFillIdentity).count() == 0



@pytest.mark.asyncio
async def test_worker_persists_credential_safe_success_summary(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    _intent(db_session, user, portfolio, connection)
    client = _FakeReadClient(orders=[_order()], trades=[_trade()])
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "never-persist-this-token",
        sleeper=_no_sleep,
    )

    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    run = db_session.query(LiveReconciliationRun).filter_by(id=result.run_id).one()
    assert result.status == "COMPLETED"
    assert run.status == "COMPLETED"
    assert run.completed_at is not None
    assert run.error_code is None
    assert run.summary == {
        "orders_seen": 1, "orders_matched": 1, "orders_unmatched": 0,
        "trades_seen": 1, "fills_inserted": 1, "duplicate_fills": 0, "conflicts": 0,
    }
    assert "never-persist-this-token" not in str(run.summary)


@pytest.mark.asyncio
async def test_worker_persists_sanitized_failure_summary(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    client = _FakeReadClient(
        order_results=[ReadOnlyBrokerResult(False, status_code=403, error_code="FORBIDDEN")],
    )
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token", sleeper=_no_sleep,
    )

    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    run = db_session.query(LiveReconciliationRun).filter_by(id=result.run_id).one()
    assert run.status == "FAILED"
    assert run.error_code == "FORBIDDEN"
    assert run.summary == {
        "orders_seen": 0, "orders_matched": 0, "orders_unmatched": 0,
        "trades_seen": 0, "fills_inserted": 0, "duplicate_fills": 0, "conflicts": 0,
    }



@pytest.mark.asyncio
async def test_worker_persists_and_deduplicates_unmatched_order_review_issue(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    _intent(db_session, user, portfolio, connection, tag="different-local-tag")
    client = _FakeReadClient(
        orders=[_order(tag="broker-tag-without-match", order_id="manual-order-88")],
        trades=[],
    )
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token", sleeper=_no_sleep
    )

    first = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)
    second = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    issues = db_session.query(LiveReconciliationIssue).filter_by(
        broker_connection_id=connection.id, broker_order_id="manual-order-88"
    ).all()
    assert first.status == second.status == "COMPLETED"
    assert len(issues) == 1
    assert issues[0].issue_type == "UNMATCHED_ORDER"
    assert issues[0].status == "OPEN"
    assert issues[0].occurrence_count == 2
    assert issues[0].safe_details == {
        "match_status": "NO_MATCH", "reason_code": "ORDER_NOT_SAFELY_MATCHED",
    }


@pytest.mark.asyncio
async def test_worker_persists_invalid_trade_as_safe_review_issue(db_session, make_user):
    user, portfolio, connection = _setup(db_session, make_user)
    client = _FakeReadClient(
        orders=[],
        trades=[_trade(average_price="NaN")],
    )
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token", sleeper=_no_sleep
    )

    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    issue = db_session.query(LiveReconciliationIssue).filter_by(
        broker_connection_id=connection.id, issue_type="INVALID_TRADE_RECORD"
    ).one()
    assert result.status == "COMPLETED_WITH_CONFLICTS"
    assert issue.status == "OPEN"
    assert issue.safe_details == {
        "record_index": 0, "reason_code": "TRADE_NORMALIZATION_FAILED",
    }
    assert "NaN" not in str(issue.safe_details)



@pytest.mark.asyncio
async def test_worker_recovers_expired_orphan_run_before_claiming_new_lease(db_session, make_user):
    user, _portfolio, connection = _setup(db_session, make_user)
    now = datetime.now(timezone.utc)
    stale_started = now - timedelta(hours=1)
    stale_run = LiveReconciliationRun(
        user_id=user.id,
        broker_connection_id=connection.id,
        status="RUNNING",
        started_at=stale_started,
        summary={
            "orders_seen": 0, "orders_matched": 0, "orders_unmatched": 0,
            "trades_seen": 0, "fills_inserted": 0, "duplicate_fills": 0,
            "conflicts": 0,
        },
    )
    db_session.add_all([
        stale_run,
        LiveReconciliationLease(
            user_id=user.id,
            broker_connection_id=connection.id,
            lease_token=uuid.uuid4(),
            claimed_until=now - timedelta(minutes=10),
            generation=1,
            last_started_at=stale_started,
            last_error_code=None,
        ),
    ])
    db_session.commit()

    client = _FakeReadClient()
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token",
        sleeper=_no_sleep,
    )
    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    db_session.refresh(stale_run)
    assert stale_run.status == "FAILED"
    assert stale_run.error_code == "WORKER_INTERRUPTED"
    assert result.status == "COMPLETED"
    assert result.run_id is not None and result.run_id != stale_run.id
    current_run = db_session.query(LiveReconciliationRun).filter_by(id=result.run_id).one()
    assert current_run.status == "COMPLETED"
    lease = db_session.query(LiveReconciliationLease).filter_by(
        broker_connection_id=connection.id
    ).one()
    assert lease.generation == 2
    assert lease.lease_token is None


@pytest.mark.asyncio
async def test_worker_fails_closed_if_stale_run_recovery_errors(db_session, make_user):
    user, _portfolio, connection = _setup(db_session, make_user)
    client = _FakeReadClient()
    worker = LiveOrderReconciliationWorker(
        db_session, client=client, token_provider=lambda _user_id: "test-token",
        sleeper=_no_sleep,
    )

    def fail_recovery(**_kwargs):
        raise RuntimeError("private database detail")

    worker.run_repository.fail_orphaned_runs = fail_recovery
    result = await worker.run_for_connection(user_id=user.id, broker_connection_id=connection.id)

    assert result.status == "FAILED"
    assert result.error_code == "STALE_RUN_RECOVERY_FAILED"
    assert client.calls == []
    assert db_session.query(LiveReconciliationLease).count() == 0
