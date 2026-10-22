from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import hashlib

import pytest

from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_connection import BrokerConnection
from app.models.broker_trade_record import BrokerTradeRecord
from app.services.broker_charge_allocation_persistence_service import (
    allocate_and_persist_component,
)


def _trade(db, connection_id, trade_id):
    trade = BrokerTradeRecord(
        broker_connection_id=connection_id,
        broker_order_ref_id=uuid4(),
        broker_trade_id=trade_id,
        quantity=1,
        price=Decimal("100.0000"),
        side="BUY",
        instrument_token="NSE_EQ|TEST",
        exchange_timestamp="2026-10-21T10:00:00+05:30",
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade


def _allocate(db, user, connection, evidence, trades, weights=None, total="1.00", basis="EXPLICIT_REVIEWED"):
    return allocate_and_persist_component(
        db,
        evidence_id=evidence.id,
        broker_connection_id=connection.id,
        broker_report_reference="CN-2026-10-21-001",
        reviewer_user_id=user.id,
        source_component_total=total,
        charge_component="brokerage",
        fill_weights=weights or {trade.id: 1 for trade in trades},
        allocation_basis=basis,
    )


def test_persists_allocations_and_reconciles_source_total(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [_trade(db, connection.id, "trade-success-a"), _trade(db, connection.id, "trade-success-b")]

    rows = _allocate(db, user, connection, evidence, trades)

    assert len(rows) == 2
    assert sum((Decimal(row.allocated_amount) for row in rows), Decimal("0")) == Decimal("1.00")
    # Arithmetic totals match, but no independent source-document parser or
    # component-total verifier ran, so this service must not claim reconciliation.
    assert {row.status for row in rows} == {"PENDING_RECONCILIATION"}
    assert {row.reconciliation_reference for row in rows} == {None}
    assert db.query(BrokerChargeAllocation).count() == 2


def test_identical_replay_returns_existing_rows_without_duplicates(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [_trade(db, connection.id, "trade-replay-a"), _trade(db, connection.id, "trade-replay-b")]

    first = _allocate(db, user, connection, evidence, trades)
    second = _allocate(db, user, connection, evidence, trades)

    assert {row.id for row in first} == {row.id for row in second}
    assert db.query(BrokerChargeAllocation).count() == 2


def test_conflicting_replay_with_changed_total_fails_closed(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [_trade(db, connection.id, "trade-conflict-a"), _trade(db, connection.id, "trade-conflict-b")]
    _allocate(db, user, connection, evidence, trades, total="1.00")

    with pytest.raises(ValueError, match="Conflicting replay"):
        _allocate(db, user, connection, evidence, trades, total="1.10")


def test_rejects_fill_from_different_broker_connection(reviewed_evidence, make_user):
    db, user, connection, evidence = reviewed_evidence
    other_user = make_user(email="other@example.com")
    other_connection = BrokerConnection(
        user_id=other_user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key-2",
        api_secret_encrypted="encrypted-secret-2",
        redirect_uri="https://example.invalid/callback",
        is_connected=True,
    )
    db.add(other_connection)
    db.commit()
    db.refresh(other_connection)
    other_trade = _trade(db, other_connection.id, "trade-other-connection")

    with pytest.raises(ValueError, match="evidence connection"):
        _allocate(
            db, user, connection, evidence, [other_trade],
            weights={other_trade.id: 1},
        )
    assert db.query(BrokerChargeAllocation).count() == 0


def test_conflicting_fill_set_is_rejected_without_partial_rows(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [_trade(db, connection.id, "trade-set-a"), _trade(db, connection.id, "trade-set-b")]
    _allocate(db, user, connection, evidence, trades)

    with pytest.raises(ValueError, match="different fill set"):
        _allocate(db, user, connection, evidence, trades[:1])

    assert db.query(BrokerChargeAllocation).count() == 2


@pytest.fixture
def reviewed_evidence(db_session, make_user):
    """Create a persisted, explicitly reviewed contract-note evidence record."""
    user = make_user()
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=True,
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)

    evidence = BrokerChargeEvidence(
        broker_connection_id=connection.id,
        source_kind="CONTRACT_NOTE",
        broker_report_reference="CN-2026-10-21-001",
        source_filename="contract-note.pdf",
        source_sha256=hashlib.sha256(b"test contract note").hexdigest(),
        byte_size=len(b"test contract note"),
        status="REVIEWED",
        reviewed_at=datetime.now(timezone.utc),
        reviewed_by_user_id=user.id,
        review_note="Reviewed in test fixture",
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)
    return db_session, user, connection, evidence


def test_outer_transaction_rollback_removes_all_new_allocations(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [
        _trade(db, connection.id, "trade-rollback-a"),
        _trade(db, connection.id, "trade-rollback-b"),
    ]

    # The shared fixture commits setup rows. Start a fresh, explicit outer
    # transaction before the service opens its nested savepoint; otherwise
    # SQLite can release a SAVEPOINT without a real outer BEGIN.
    db.rollback()
    outer = db.begin()
    try:
        rows = _allocate(db, user, connection, evidence, trades)
        assert len(rows) == 2
        assert db.query(BrokerChargeAllocation).count() == 2
        outer.rollback()
    finally:
        if outer.is_active:
            outer.rollback()
    db.expire_all()

    assert db.query(BrokerChargeAllocation).count() == 0


def test_conflicting_replay_with_changed_basis_fails_closed(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [_trade(db, connection.id, "trade-basis-a"), _trade(db, connection.id, "trade-basis-b")]
    _allocate(db, user, connection, evidence, trades)

    with pytest.raises(ValueError, match="Conflicting replay"):
        _allocate(
            db, user, connection, evidence, trades,
            weights={trade.id: 1 for trade in trades},
            basis="QUANTITY",
        )


def test_reconciled_rows_cannot_be_rewritten_through_allocation_persistence(reviewed_evidence):
    db, user, connection, evidence = reviewed_evidence
    trades = [_trade(db, connection.id, "trade-reconciled-a"), _trade(db, connection.id, "trade-reconciled-b")]
    rows = _allocate(db, user, connection, evidence, trades)
    for row in rows:
        row.status = "RECONCILED"
        row.reconciliation_reference = "verified-source-reference"
    db.commit()

    with pytest.raises(ValueError, match="already reconciled"):
        _allocate(db, user, connection, evidence, trades)

    db.refresh(rows[0])
    assert rows[0].status == "RECONCILED"
    assert rows[0].reconciliation_reference == "verified-source-reference"
    assert db.query(BrokerChargeAllocation).count() == 2
