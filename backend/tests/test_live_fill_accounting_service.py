from datetime import datetime, timezone
import hashlib
import json
from decimal import Decimal

import pytest

from app.models.broker_connection import BrokerConnection
from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.execution import Execution
from app.models.live_position import LivePosition
from app.models.order import Order
from app.models.position import Position
from app.models.user import User
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.instrument_service import InstrumentService
from app.services.broker_charge_allocation_service import METHOD_VERSION
from app.services.live_fill_accounting_service import (
    LiveFillAccountingService,
    LiveFillChargeBreakdown,
)


def _charges(**overrides):
    values = dict(
        brokerage=Decimal("20.00"),
        stt=Decimal("0.20"),
        exchange_charges=Decimal("0.01"),
        sebi_charges=Decimal("0.01"),
        stamp_duty=Decimal("0.03"),
        gst=Decimal("3.61"),
        total_charges=Decimal("23.86"),
        source="BROKER_REPORTED",
        reference="contract-note-2026-10-18-001",
    )
    values.update(overrides)
    return LiveFillChargeBreakdown(**values)


def _reviewed_charges(accounting_context, reference="contract-note-2026-10-18-001", trade_record_id=None):
    db, user, _portfolio, _instrument, connection, *_rest = accounting_context
    # Keep the synthetic source bytes and reviewer lookup local to this helper;
    # fixture-local variables are not visible in this function scope.
    if trade_record_id is not None:
        reference = f"{reference}-{str(trade_record_id)[:8]}"
    # Evidence has a per-connection unique source hash; distinct synthetic
    # contract-note references must therefore have distinct source bytes.
    synthetic_document = f"synthetic test contract note:{reference.strip()}".encode("utf-8")
    reviewer = db.query(User).filter_by(email="live-accounting-reviewer@example.com").one()
    evidence = db.query(BrokerChargeEvidence).filter_by(broker_connection_id=connection.id, broker_report_reference=reference).one_or_none()
    if evidence is None:
        from datetime import date
        from uuid import uuid4
        storage_key = uuid4().hex
        db._synthetic_charge_documents[storage_key] = synthetic_document
        evidence = BrokerChargeEvidence(broker_connection_id=connection.id, source_kind="CONTRACT_NOTE", broker_report_reference=reference.strip(), report_date=date(2026, 10, 18), segment="NSE", source_filename="reviewed-contract-note.pdf", storage_key=storage_key, source_sha256=hashlib.sha256(synthetic_document).hexdigest(), byte_size=len(synthetic_document), parser_version="phase3-test", status="REVIEWED", reviewed_at=datetime.now(timezone.utc), reviewed_by_user_id=reviewer.id)
        db.add(evidence)
        db.flush()
    else:
        evidence.broker_report_reference = reference.strip()
    record = db.get(BrokerTradeRecord, trade_record_id) if trade_record_id else db.query(BrokerTradeRecord).filter_by(broker_trade_id="trade-live-001").one()
    expected = {"brokerage": Decimal("20.00"), "stt": Decimal("0.20"), "exchange_charges": Decimal("0.01"), "sebi_charges": Decimal("0.01"), "stamp_duty": Decimal("0.03"), "gst": Decimal("3.61")}
    existing = db.query(BrokerChargeAllocation).filter_by(evidence_id=evidence.id, broker_trade_record_id=record.id).all()
    if not existing:
        manifest = json.dumps([str(record.id)], separators=(",", ":"))
        manifest_hash = hashlib.sha256(manifest.encode("utf-8")).hexdigest()
        for name, amount in expected.items():
            component = BrokerChargeSourceComponent(
                evidence_id=evidence.id, source_sha256=evidence.source_sha256, component_name=name,
                revision=1, source_amount=amount, currency="INR", extraction_method="MANUAL_TRANSCRIPTION",
                parser_version="phase3-test", source_locator="test fixture / page 1",
                eligible_fill_ids_json=manifest, eligible_fill_set_sha256=manifest_hash,
                rounding_policy=METHOD_VERSION, allocation_basis="EXPLICIT_REVIEWED",
                extracted_by_user_id=user.id, status="VERIFIED", reviewed_by_user_id=reviewer.id,
                reviewed_at=datetime.now(timezone.utc), review_note="Synthetic unit-test fixture",
            )
            db.add(component)
            db.flush()
            db.add(BrokerChargeAllocation(
                evidence_id=evidence.id, broker_connection_id=connection.id, broker_trade_record_id=record.id,
                charge_component=name, source_component_total=amount, allocated_amount=amount,
                currency="INR", allocation_basis="EXPLICIT_REVIEWED", method_version=METHOD_VERSION,
                status="RECONCILED", reconciliation_reference=f"charge-component:{component.id}:sha256:{evidence.source_sha256}:fills:{manifest_hash}",
            ))
    db.commit()
    return _charges(reference=reference, evidence_id=evidence.id, reviewer_user_id=reviewer.id)


@pytest.fixture()
def accounting_context(db_session, make_user, monkeypatch):
    user = make_user()
    reviewer = make_user(email="live-accounting-reviewer@example.com")
    reviewer.is_admin = True
    # Keep each synthetic document keyed by its opaque storage key so tests
    # can model distinct uploaded notes without violating the unique source hash.
    db_session._synthetic_charge_documents = {}
    monkeypatch.setattr(
        "app.services.broker_charge_source_reconciliation_service.read_verified_document",
        lambda **kwargs: db_session._synthetic_charge_documents[kwargs["storage_key"]],
    )
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id, name="Live accounting", virtual_capital=Decimal("100000")
    )
    InstrumentService(db_session).seed_defaults()
    instrument = InstrumentRepository(db_session).search("RELIANCE")[0]
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=True,
    )
    order = Order(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        side="BUY",
        order_type="MARKET",
        segment="EQUITY_DELIVERY",
        quantity=5,
        status="PENDING",
        trading_mode="LIVE",
        execution_reason="MANUAL",
        placed_at=datetime.now(timezone.utc),
    )
    db_session.add_all([connection, order])
    db_session.flush()
    child = BrokerOrder(
        broker_connection_id=connection.id,
        order_id=order.id,
        broker_name="upstox",
        broker_order_id="broker-child-1",
        requested_quantity=5,
        filled_quantity=2,
        status="PARTIALLY_FILLED",
    )
    db_session.add(child)
    db_session.flush()
    record = BrokerTradeRecord(
        broker_connection_id=connection.id,
        broker_order_ref_id=child.id,
        broker_trade_id="trade-live-001",
        quantity=2,
        price=Decimal("100.25"),
        side="BUY",
        instrument_token=instrument.instrument_key,
        exchange_timestamp="2026-10-18T09:20:00+05:30",
    )
    paper_position = Position(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        quantity=7,
        avg_price=Decimal("80"),
        realized_pnl=Decimal("12.00"),
    )
    db_session.add_all([record, paper_position])
    db_session.commit()
    return db_session, user, portfolio, instrument, connection, order, child, record, paper_position


def test_promote_live_trade_atomically_updates_live_position_and_execution_only(accounting_context):
    db, user, portfolio, instrument, connection, order, child, record, paper_position = accounting_context
    cash_before = Decimal(str(portfolio.cash_balance))
    service = LiveFillAccountingService(db)

    result = service.promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    db.refresh(portfolio)
    db.refresh(paper_position)
    live_position = db.query(LivePosition).filter(
        LivePosition.broker_connection_id == connection.id,
        LivePosition.instrument_id == instrument.id,
    ).one()
    execution = db.query(Execution).filter(
        Execution.broker_connection_id == connection.id,
        Execution.broker_trade_id == record.broker_trade_id,
    ).one()
    assert result.inserted is True
    assert result.live_position_quantity == 2
    assert result.live_position_average_price == Decimal("100.2500")
    assert execution.charge_source == "BROKER_REPORTED"
    assert execution.charge_reference == "contract-note-2026-10-18-001"
    assert execution.price == Decimal("100.2500")
    assert execution.gross_value == Decimal("200.50")
    assert live_position.quantity == 2
    assert paper_position.quantity == 7
    assert paper_position.avg_price == Decimal("80.0000")
    assert Decimal(str(portfolio.cash_balance)) == cash_before
    assert order.status == "PENDING"
    assert db.query(Execution).count() == 1


def test_replaying_same_broker_trade_does_not_double_count_position(accounting_context):
    db, user, portfolio, instrument, connection, order, child, record, paper_position = accounting_context
    service = LiveFillAccountingService(db)

    first = service.promote_trade(user.id, record.id, _reviewed_charges(accounting_context))
    second = service.promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    assert first.inserted is True
    assert second.inserted is False
    assert first.execution_id == second.execution_id
    live_position = db.query(LivePosition).filter(
        LivePosition.broker_connection_id == connection.id,
        LivePosition.instrument_id == instrument.id,
    ).one()
    assert live_position.quantity == 2
    assert db.query(Execution).count() == 1


def test_replay_with_same_trade_id_but_changed_fill_details_is_rejected(accounting_context):
    db, user, _portfolio, _instrument, _connection, _order, _child, record, _paper_position = accounting_context
    service = LiveFillAccountingService(db)
    first = service.promote_trade(user.id, record.id, _reviewed_charges(accounting_context))
    assert first.inserted is True

    record.price = Decimal("101.25")
    db.commit()

    with pytest.raises(ValueError, match="conflicting accounted execution"):
        service.promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    assert db.query(Execution).count() == 1
    live_position = db.query(LivePosition).one()
    assert live_position.quantity == 2
    assert live_position.avg_price == Decimal("100.2500")


@pytest.mark.parametrize(
    ("charges", "message"),
    [
        (_charges(source="ESTIMATED"), "broker-reported charges"),
        # Period/segment aggregate charges and estimates are not per-fill evidence.
        (_charges(source="AGGREGATE_CHARGES"), "broker-reported charges"),
        (_charges(source="TRADE_CHARGES_API"), "broker-reported charges"),
        (_charges(source="BROKER_ESTIMATE"), "broker-reported charges"),
        (_charges(source="BROKER_REPORTED "), "broker-reported charges"),
        (_charges(source=" BROKER_REPORTED"), "broker-reported charges"),
        (_charges(reference=" "), "audit reference"),
        (_charges(reference="x" * 201), "at most 200 characters"),
        (_charges(total_charges=Decimal("99.00")), "sum of its six components"),
        (_charges(brokerage=Decimal("-1.00"), total_charges=Decimal("2.86")), "non-negative"),
        (_charges(stt=Decimal("0.201"), total_charges=Decimal("23.861")), "paise precision"),
    ],
)
def test_invalid_or_estimated_charges_block_live_promotion(accounting_context, charges, message):
    db, user, portfolio, instrument, connection, order, child, record, paper_position = accounting_context

    with pytest.raises(ValueError, match=message):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, charges)

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    db.refresh(paper_position)
    assert paper_position.quantity == 7


@pytest.mark.parametrize("status", ["PENDING_RECONCILIATION", "REJECTED"])
def test_non_reconciled_charge_allocations_block_live_accounting(accounting_context, status):
    db, user, _portfolio, _instrument, _connection, _order, _child, record, paper_position = accounting_context
    charges = _reviewed_charges(accounting_context)
    allocation = db.query(BrokerChargeAllocation).filter_by(
        evidence_id=charges.evidence_id, broker_trade_record_id=record.id
    ).first()
    allocation.status = status
    db.commit()

    with pytest.raises(ValueError, match="Pending, rejected, or unreferenced"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, charges)
    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    db.refresh(paper_position)
    assert paper_position.quantity == 7


def test_missing_component_allocation_blocks_live_accounting(accounting_context):
    db, user, _portfolio, _instrument, _connection, _order, _child, record, paper_position = accounting_context
    charges = _reviewed_charges(accounting_context)
    allocation = db.query(BrokerChargeAllocation).filter_by(
        evidence_id=charges.evidence_id, broker_trade_record_id=record.id
    ).first()
    db.delete(allocation)
    db.commit()

    with pytest.raises(ValueError, match="exactly six reconciled per-fill"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, charges)
    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    db.refresh(paper_position)
    assert paper_position.quantity == 7


def test_caller_charge_amounts_must_match_reconciled_ledger(accounting_context):
    db, user, _portfolio, _instrument, _connection, _order, _child, record, paper_position = accounting_context
    charges = _reviewed_charges(accounting_context)
    mismatched = _charges(
        brokerage=Decimal("21.00"), total_charges=Decimal("24.86"),
        evidence_id=charges.evidence_id, reviewer_user_id=charges.reviewer_user_id,
    )
    with pytest.raises(ValueError, match="differ from the reconciled per-fill"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, mismatched)
    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    db.refresh(paper_position)
    assert paper_position.quantity == 7


def test_live_fill_promotion_requires_persisted_reviewed_evidence(accounting_context):
    db, user, _portfolio, _instrument, _connection, _order, _child, record, paper_position = accounting_context
    with pytest.raises(ValueError, match="persisted reviewed contract-note evidence"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, _charges())
    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    db.refresh(paper_position)
    assert paper_position.quantity == 7

def test_naive_exchange_timestamp_blocks_live_promotion(accounting_context):
    db, user, portfolio, instrument, connection, order, child, record, paper_position = accounting_context
    record.exchange_timestamp = "2026-10-18T09:20:00"
    db.commit()

    with pytest.raises(ValueError, match="timezone offset"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0


def test_sell_fill_realizes_pnl_on_live_position_without_changing_paper_position(accounting_context):
    db, user, portfolio, instrument, connection, order, child, record, paper_position = accounting_context
    order.side = "SELL"
    child.requested_quantity = 1
    child.filled_quantity = 1
    record.quantity = 1
    record.side = "SELL"
    record.price = Decimal("100.25")
    db.add(LivePosition(
        broker_connection_id=connection.id,
        instrument_id=instrument.id,
        quantity=3,
        avg_price=Decimal("90"),
        realized_pnl=Decimal("0"),
    ))
    db.commit()

    result = LiveFillAccountingService(db).promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    live_position = db.query(LivePosition).filter(
        LivePosition.broker_connection_id == connection.id,
        LivePosition.instrument_id == instrument.id,
    ).one()
    db.refresh(paper_position)
    assert result.realized_pnl == Decimal("10.25")
    assert live_position.quantity == 2
    assert live_position.avg_price == Decimal("90.0000")
    assert live_position.realized_pnl == Decimal("10.25")
    assert paper_position.quantity == 7


def test_replay_with_changed_charge_evidence_is_rejected(accounting_context):
    db, user, _portfolio, _instrument, _connection, _order, _child, record, _paper_position = accounting_context
    service = LiveFillAccountingService(db)
    first = service.promote_trade(user.id, record.id, _reviewed_charges(accounting_context))
    assert first.inserted is True

    with pytest.raises(ValueError, match="conflicting accounted execution"):
        service.promote_trade(
            user.id, record.id, _charges(reference="different-contract-note-2026-10-18")
        )

    assert db.query(Execution).count() == 1
    live_position = db.query(LivePosition).one()
    assert live_position.quantity == 2
    assert live_position.avg_price == Decimal("100.2500")


def test_charge_audit_reference_is_trimmed_and_replay_stays_idempotent(accounting_context):
    db, user, _portfolio, _instrument, _connection, _order, _child, record, _paper_position = accounting_context
    service = LiveFillAccountingService(db)

    first = service.promote_trade(
        user.id, record.id, _reviewed_charges(accounting_context, reference="  contract-note-2026-10-18-001  ")
    )
    second = service.promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    execution = db.query(Execution).one()
    assert first.inserted is True
    assert second.inserted is False
    assert execution.charge_reference == "contract-note-2026-10-18-001"
    assert first.execution_id == second.execution_id


def test_same_timestamp_different_prices_are_rejected_as_ambiguous(accounting_context):
    db, user, _portfolio, instrument, connection, _order, child, record, _paper_position = accounting_context
    child.filled_quantity = 3
    ambiguous = BrokerTradeRecord(
        broker_connection_id=connection.id,
        broker_order_ref_id=child.id,
        broker_trade_id="trade-live-ambiguous-time-001",
        quantity=1,
        price=Decimal("101.25"),
        side="BUY",
        instrument_token=instrument.instrument_key,
        exchange_timestamp=record.exchange_timestamp,
    )
    db.add(ambiguous)
    db.commit()

    with pytest.raises(ValueError, match="ambiguous exchange timestamps"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0


def test_later_fill_waits_for_earlier_staged_trade(accounting_context):
    db, user, _portfolio, instrument, connection, _order, child, record, _paper_position = accounting_context
    child.filled_quantity = 3
    record.exchange_timestamp = "2026-10-18T09:21:00+05:30"
    earlier = BrokerTradeRecord(
        broker_connection_id=connection.id,
        broker_order_ref_id=child.id,
        broker_trade_id="trade-live-earlier-001",
        quantity=1,
        price=Decimal("99.00"),
        side="BUY",
        instrument_token=instrument.instrument_key,
        exchange_timestamp="2026-10-18T09:20:00+05:30",
    )
    db.add(earlier)
    db.commit()

    with pytest.raises(ValueError, match="earlier broker trade is still unaccounted"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0


def test_earlier_fill_is_rejected_after_later_fill_was_accounted(accounting_context):
    db, user, _portfolio, instrument, connection, _order, child, later_record, _paper_position = accounting_context
    child.filled_quantity = 2
    later_record.exchange_timestamp = "2026-10-18T09:21:00+05:30"
    db.commit()
    later_result = LiveFillAccountingService(db).promote_trade(user.id, later_record.id, _reviewed_charges(accounting_context))
    assert later_result.inserted is True

    earlier = BrokerTradeRecord(
        broker_connection_id=connection.id,
        broker_order_ref_id=child.id,
        broker_trade_id="trade-live-late-arrival-001",
        quantity=1,
        price=Decimal("99.00"),
        side="BUY",
        instrument_token=instrument.instrument_key,
        exchange_timestamp="2026-10-18T09:20:00+05:30",
    )
    db.add(earlier)
    child.filled_quantity = 3
    db.commit()

    with pytest.raises(ValueError, match="earlier broker trade cannot be promoted after a later trade"):
        LiveFillAccountingService(db).promote_trade(user.id, earlier.id, _reviewed_charges(accounting_context, trade_record_id=earlier.id))

    assert db.query(Execution).count() == 1
    live_position = db.query(LivePosition).one()
    assert live_position.quantity == 2


def test_rejected_local_order_cannot_accept_broker_fill(accounting_context):
    db, user, _portfolio, _instrument, _connection, order, _child, record, _paper_position = accounting_context
    order.status = "REJECTED"
    db.commit()

    with pytest.raises(ValueError, match="rejected local order"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    assert order.status == "REJECTED"


def test_cancelled_local_order_can_account_a_confirmed_partial_fill(accounting_context):
    db, user, _portfolio, _instrument, _connection, order, child, record, _paper_position = accounting_context
    order.status = "CANCELLED"
    child.status = "CANCELLED"
    db.commit()

    result = LiveFillAccountingService(db).promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    db.refresh(order)
    assert result.inserted is True
    assert result.live_position_quantity == 2
    assert order.status == "CANCELLED"
    assert db.query(Execution).count() == 1


def test_broker_child_fill_cannot_exceed_local_order_quantity(accounting_context):
    db, user, _portfolio, _instrument, _connection, order, child, record, _paper_position = accounting_context
    order.quantity = 5
    child.requested_quantity = 6
    child.filled_quantity = 6
    record.quantity = 6
    db.commit()

    with pytest.raises(ValueError, match="exceeds the local order quantity"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0


def test_trade_quantity_cannot_exceed_broker_confirmed_child_fill(accounting_context):
    db, user, portfolio, instrument, connection, order, child, record, paper_position = accounting_context
    record.quantity = 3
    db.commit()

    with pytest.raises(ValueError, match="exceeds the broker-confirmed child-order fill quantity"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    db.refresh(paper_position)
    assert paper_position.quantity == 7




def test_promotion_waits_until_all_confirmed_child_fills_are_staged(accounting_context):
    db, user, _portfolio, _instrument, _connection, _order, child, record, paper_position = accounting_context
    child.filled_quantity = 3
    db.commit()

    with pytest.raises(ValueError, match="does not match broker-confirmed child fill quantity"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    db.refresh(paper_position)
    assert paper_position.quantity == 7


def test_staged_trade_quantity_must_match_broker_confirmed_child_fill(accounting_context):
    db, user, portfolio, instrument, connection, order, child, first_record, paper_position = accounting_context
    service = LiveFillAccountingService(db)

    first = service.promote_trade(user.id, first_record.id, _reviewed_charges(accounting_context))
    assert first.inserted is True

    second_record = BrokerTradeRecord(
        broker_connection_id=connection.id,
        broker_order_ref_id=child.id,
        broker_trade_id="trade-live-002",
        quantity=1,
        price=Decimal("100.25"),
        side="BUY",
        instrument_token=instrument.instrument_key,
        exchange_timestamp="2026-10-18T09:20:01+05:30",
    )
    db.add(second_record)
    db.commit()

    with pytest.raises(ValueError, match="does not match broker-confirmed child fill quantity"):
        service.promote_trade(user.id, second_record.id, _reviewed_charges(accounting_context, reference="contract-note-2026-10-18-002"))

    assert db.query(Execution).count() == 1
    live_position = db.query(LivePosition).filter_by(
        broker_connection_id=connection.id, instrument_id=instrument.id
    ).one()
    assert live_position.quantity == 2
    db.refresh(paper_position)
    assert paper_position.quantity == 7



def test_cumulative_fills_across_child_orders_cannot_exceed_local_order_quantity(accounting_context):
    db, user, _portfolio, instrument, connection, order, _child, record, _paper_position = accounting_context
    first = LiveFillAccountingService(db).promote_trade(user.id, record.id, _reviewed_charges(accounting_context))
    assert first.live_position_quantity == 2

    second_child = BrokerOrder(
        broker_connection_id=connection.id,
        order_id=order.id,
        broker_name="upstox",
        broker_order_id="broker-child-2",
        requested_quantity=4,
        filled_quantity=4,
        status="FILLED",
    )
    db.add(second_child)
    db.flush()
    second_record = BrokerTradeRecord(
        broker_connection_id=connection.id,
        broker_order_ref_id=second_child.id,
        broker_trade_id="trade-live-002",
        quantity=4,
        price=Decimal("101.00"),
        side="BUY",
        instrument_token=instrument.instrument_key,
        exchange_timestamp="2026-10-18T09:21:00+05:30",
    )
    db.add(second_record)
    db.commit()

    with pytest.raises(ValueError, match="Cumulative accounted trade quantity exceeds the local order quantity"):
        LiveFillAccountingService(db).promote_trade(user.id, second_record.id, _reviewed_charges(accounting_context))

    assert db.query(Execution).count() == 1
    live_position = db.query(LivePosition).one()
    assert live_position.quantity == 2


def test_live_fill_promotion_uses_consistent_charge_then_trade_lock_order(accounting_context, monkeypatch):
    from sqlalchemy.orm import Query

    db, user, _portfolio, _instrument, _connection, _order, _child, record, _paper_position = accounting_context
    locked_models = []
    original = Query.with_for_update

    def track_lock(query, *args, **kwargs):
        entities = [item.get("entity") for item in query.column_descriptions]
        for model, label in (
            (Order, "Order"),
            (BrokerOrder, "BrokerOrder"),
            (BrokerChargeEvidence, "BrokerChargeEvidence"),
            (BrokerChargeAllocation, "BrokerChargeAllocation"),
            (BrokerChargeSourceComponent, "BrokerChargeSourceComponent"),
            (BrokerTradeRecord, "BrokerTradeRecord"),
        ):
            if model in entities:
                locked_models.append(label)
                break
        return original(query, *args, **kwargs)

    monkeypatch.setattr(Query, "with_for_update", track_lock)

    LiveFillAccountingService(db).promote_trade(user.id, record.id, _reviewed_charges(accounting_context))

    # Charge verification locks evidence and its ledger before the staged trade.
    # The order/child locks serialize parent-order accounting before this sequence.
    assert locked_models[:6] == [
        "Order",
        "BrokerOrder",
        "BrokerChargeEvidence",
        "BrokerChargeAllocation",
        "BrokerChargeSourceComponent",
        "BrokerTradeRecord",
    ]


def test_failed_commit_rolls_back_execution_and_live_position(accounting_context, monkeypatch):
    """A persistence failure must not leave half-promoted live accounting."""
    db, user, _portfolio, instrument, connection, _order, _child, record, paper_position = accounting_context
    original_commit = db.commit

    def fail_commit():
        raise RuntimeError("simulated database commit failure")

    monkeypatch.setattr(db, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="simulated database commit failure"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, _reviewed_charges(accounting_context))
    monkeypatch.setattr(db, "commit", original_commit)

    db.rollback()
    assert db.query(Execution).filter_by(
        broker_connection_id=connection.id,
        broker_trade_id=record.broker_trade_id,
    ).count() == 0
    assert db.query(LivePosition).filter_by(
        broker_connection_id=connection.id,
        instrument_id=instrument.id,
    ).count() == 0
    db.refresh(paper_position)
    assert paper_position.quantity == 7
