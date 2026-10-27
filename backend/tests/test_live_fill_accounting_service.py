from datetime import datetime, timezone
import hashlib
import json
from decimal import Decimal

import pytest

from app.models.broker_connection import BrokerConnection
from app.models.broker_charge_allocation import BrokerChargeAllocation
from app.models.broker_charge_canonical_component import BrokerChargeCanonicalComponent
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
from app.services.broker_charge_component_set_contract import LIVE_FILL_COMPONENT_SET_VERSION
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


def _reviewed_charges(accounting_context, reference="contract-note-2026-10-18-001", trade_record_id=None, representation="DIRECT", with_demat=False):
    db, user, _portfolio, _instrument, connection, *_rest = accounting_context
    if trade_record_id is not None:
        reference = f"{reference}-{str(trade_record_id)[:8]}"
    synthetic_document = f"synthetic test contract note:{reference.strip()}".encode("utf-8")
    reviewer = db.query(User).filter_by(email="live-accounting-reviewer@example.com").one()
    snapshot_creator = db.query(User).filter_by(email="canonical-snapshot-creator@example.com").one()
    canonical_reviewer = db.query(User).filter_by(email="canonical-snapshot-reviewer@example.com").one()
    evidence = db.query(BrokerChargeEvidence).filter_by(
        broker_connection_id=connection.id, broker_report_reference=reference
    ).one_or_none()
    if evidence is None:
        from datetime import date
        from uuid import uuid4
        storage_key = uuid4().hex
        db._synthetic_charge_documents[storage_key] = synthetic_document
        evidence = BrokerChargeEvidence(
            broker_connection_id=connection.id,
            source_kind="CONTRACT_NOTE",
            broker_report_reference=reference.strip(),
            report_date=date(2026, 10, 18),
            segment="NSE",
            source_filename="reviewed-contract-note.pdf",
            storage_key=storage_key,
            source_sha256=hashlib.sha256(synthetic_document).hexdigest(),
            byte_size=len(synthetic_document),
            parser_version="phase3-test",
            status="REVIEWED",
            reviewed_at=datetime.now(timezone.utc),
            reviewed_by_user_id=reviewer.id,
        )
        db.add(evidence)
        db.flush()
    else:
        evidence.broker_report_reference = reference.strip()
    record = (
        db.get(BrokerTradeRecord, trade_record_id)
        if trade_record_id
        else db.query(BrokerTradeRecord).filter_by(broker_trade_id="trade-live-001").one()
    )
    expected = {
        "brokerage": Decimal("20.00"),
        "stt": Decimal("0.20"),
        "exchange_charges": Decimal("0.01"),
        "sebi_charges": Decimal("0.01"),
        "stamp_duty": Decimal("0.03"),
        "gst": Decimal("3.61"),
    }
    snapshots = db.query(BrokerChargeCanonicalComponent).filter_by(evidence_id=evidence.id).all()
    if not snapshots:
        source_components = db.query(BrokerChargeSourceComponent).filter_by(evidence_id=evidence.id).all()
        if not source_components:
            manifest = json.dumps([str(record.id)], separators=(",", ":"))
            manifest_hash = hashlib.sha256(manifest.encode("utf-8")).hexdigest()
            from app.services.broker_charge_representation_contract import CONTRACT_VERSION
            raw_rows = []
            for name, amount in expected.items():
                if name != "exchange_charges" or representation == "DIRECT":
                    raw_rows.append({
                        "component_name": name, "source_amount": amount,
                        "source_label": name, "representation_mode": None,
                        "representation_contract_version": None,
                    })
                elif representation == "COMBINED":
                    raw_rows.append({
                        "component_name": "transaction_charges", "source_amount": amount,
                        "source_label": "Transaction Charges (includes IPFT)",
                        "representation_mode": "COMBINED_TRANSACTION_AND_IPFT",
                        "representation_contract_version": CONTRACT_VERSION,
                    })
                elif representation == "SPLIT":
                    raw_rows.extend([
                        {
                            "component_name": "transaction_charges", "source_amount": Decimal("0.00"),
                            "source_label": "Transaction Charges (excluding IPFT)",
                            "representation_mode": "SPLIT_TRANSACTION_AND_IPFT",
                            "representation_contract_version": CONTRACT_VERSION,
                        },
                        {
                            "component_name": "ipft", "source_amount": amount,
                            "source_label": "IPFT",
                            "representation_mode": "SPLIT_TRANSACTION_AND_IPFT",
                            "representation_contract_version": CONTRACT_VERSION,
                        },
                    ])
                else:
                    raise ValueError(f"Unsupported test source representation: {representation}")
            if with_demat:
                raw_rows.append({
                    "component_name": "demat_transaction_charges",
                    "source_amount": Decimal("20.00"),
                    "source_label": "Demat Transaction Charges",
                    "representation_mode": None,
                    "representation_contract_version": None,
                })
            for raw in raw_rows:
                db.add(BrokerChargeSourceComponent(
                    evidence_id=evidence.id,
                    source_sha256=evidence.source_sha256,
                    component_name=raw["component_name"],
                    source_label=raw["source_label"],
                    representation_mode=raw["representation_mode"],
                    representation_contract_version=raw["representation_contract_version"],
                    revision=1,
                    source_amount=raw["source_amount"],
                    currency="INR",
                    extraction_method="MANUAL_TRANSCRIPTION",
                    component_set_version=LIVE_FILL_COMPONENT_SET_VERSION,
                    parser_version="phase3-test",
                    source_locator="test fixture / page 1",
                    eligible_fill_ids_json=manifest,
                    eligible_fill_set_sha256=manifest_hash,
                    eligible_fill_weights_json=json.dumps(
                        [{"fill_record_id": str(record.id), "weight": "1"}],
                        separators=(",", ":"),
                    ),
                    rounding_policy=METHOD_VERSION,
                    allocation_basis="EXPLICIT_REVIEWED",
                    extracted_by_user_id=user.id,
                    status="VERIFIED",
                    reviewed_by_user_id=reviewer.id,
                    reviewed_at=datetime.now(timezone.utc),
                    review_note="Synthetic unit-test fixture",
                ))
            db.flush()

        from app.services.broker_charge_canonical_component_snapshot_service import (
            materialize_canonical_charge_component_snapshots,
        )
        snapshots = materialize_canonical_charge_component_snapshots(
            db, evidence_id=evidence.id, requested_by_user_id=snapshot_creator.id
        )
        db.commit()

        from app.services.broker_charge_canonical_component_review_service import (
            review_canonical_charge_component_snapshot,
        )
        for snapshot in snapshots:
            review_canonical_charge_component_snapshot(
                db,
                snapshot_id=snapshot.id,
                reviewer_user_id=canonical_reviewer.id,
                decision="VERIFIED",
                review_note="Independent synthetic canonical-snapshot review",
            )
            db.commit()

        from app.services.broker_charge_canonical_allocation_persistence_service import (
            allocate_and_persist_canonical_snapshot,
        )
        for snapshot in snapshots:
            allocate_and_persist_canonical_snapshot(
                db,
                snapshot_id=snapshot.id,
                broker_connection_id=connection.id,
                broker_report_reference=reference.strip(),
            )
            db.commit()

        from app.services.broker_charge_canonical_allocation_reconciliation_service import (
            promote_verified_canonical_component_allocations,
        )
        for snapshot in snapshots:
            promote_verified_canonical_component_allocations(
                db, snapshot_id=snapshot.id, reviewer_user_id=canonical_reviewer.id
            )
            db.commit()

    if with_demat:
        return _charges(
            reference=reference, evidence_id=evidence.id, reviewer_user_id=reviewer.id,
            demat_transaction_charges=Decimal("20.00"), total_charges=Decimal("43.86"),
        )
    return _charges(reference=reference, evidence_id=evidence.id, reviewer_user_id=reviewer.id)


@pytest.fixture()
def accounting_context(db_session, make_user, monkeypatch):
    user = make_user()
    reviewer = make_user(email="live-accounting-reviewer@example.com")
    reviewer.is_admin = True
    snapshot_creator = make_user(email="canonical-snapshot-creator@example.com")
    snapshot_creator.is_admin = True
    canonical_reviewer = make_user(email="canonical-snapshot-reviewer@example.com")
    canonical_reviewer.is_admin = True
    # Keep each synthetic document keyed by its opaque storage key so tests
    # can model distinct uploaded notes without violating the unique source hash.
    db_session._synthetic_charge_documents = {}
    monkeypatch.setattr(
        "app.services.broker_charge_source_reconciliation_service.read_verified_document",
        lambda **kwargs: db_session._synthetic_charge_documents[kwargs["storage_key"]],
    )
    monkeypatch.setattr(
        "app.services.broker_charge_canonical_component_snapshot_service.read_verified_document",
        lambda **kwargs: db_session._synthetic_charge_documents[kwargs["storage_key"]],
    )
    monkeypatch.setattr(
        "app.services.broker_charge_canonical_component_review_service.read_verified_document",
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


def test_equity_delivery_sell_rejects_missing_dp_snapshot(accounting_context):
    db, user, _portfolio, _instrument, _connection, order, _child, record, paper_position = accounting_context
    order.side = "SELL"
    record.side = "SELL"
    db.commit()
    charges = _reviewed_charges(accounting_context)

    with pytest.raises(ValueError, match="reviewed DP snapshot"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, charges)

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    db.refresh(paper_position)
    assert paper_position.quantity == 7



def test_equity_delivery_sell_promotes_only_with_reconciled_demat_allocation(accounting_context):
    db, user, _portfolio, instrument, connection, order, _child, record, paper_position = accounting_context
    order.segment = "EQUITY_DELIVERY"
    order.side = "SELL"
    record.side = "SELL"
    db.add(LivePosition(
        broker_connection_id=connection.id,
        instrument_id=instrument.id,
        quantity=3,
        avg_price=Decimal("90.00"),
        realized_pnl=Decimal("0.00"),
    ))
    db.commit()
    charges = _reviewed_charges(
        accounting_context, reference="delivery-dp-note-2026-10-18-001", with_demat=True
    )

    result = LiveFillAccountingService(db).promote_trade(user.id, record.id, charges)
    execution = db.query(Execution).filter_by(broker_trade_id=record.broker_trade_id).one()
    assert result.inserted is True
    assert execution.demat_charge_status == "KNOWN"
    assert execution.demat_transaction_charges == Decimal("20.00")
    assert execution.total_charges == Decimal("43.86")
    assert execution.total_charges_complete is True
    db.refresh(paper_position)
    assert paper_position.quantity == 7


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


@pytest.mark.parametrize("representation", ["COMBINED", "SPLIT"])
def test_live_fill_accounting_canonicalizes_exchange_ipft_once(accounting_context, representation):
    db, user, _portfolio, _instrument, connection, _order, _child, record, _paper_position = accounting_context
    charges = _reviewed_charges(
        accounting_context,
        reference=f"contract-note-canonical-{representation.lower()}",
        representation=representation,
    )

    result = LiveFillAccountingService(db).promote_trade(user.id, record.id, charges)

    execution = db.query(Execution).filter_by(
        broker_connection_id=connection.id, broker_trade_id=record.broker_trade_id
    ).one()
    assert result.inserted is True
    assert execution.exchange_charges == Decimal("0.01")
    assert execution.total_charges == Decimal("23.86")
    assert db.query(BrokerChargeAllocation).filter_by(
        evidence_id=charges.evidence_id, broker_trade_record_id=record.id
    ).count() == 6


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
        (_charges(total_charges=Decimal("99.00")), "sum of the six core components"),
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

    with pytest.raises(ValueError, match="Canonical allocation rows do not match|No allocations are linked|Pending canonical allocations"):
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

    with pytest.raises(ValueError, match="No allocations are linked|exactly six canonical per-fill charge allocations"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, charges)
    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    db.refresh(paper_position)
    assert paper_position.quantity == 7


def test_separately_reported_ipft_component_blocks_six_component_live_promotion(accounting_context):
    db, user, _portfolio, _instrument, connection, _order, _child, record, paper_position = accounting_context
    charges = _reviewed_charges(accounting_context)
    # The evidence vocabulary can preserve a separate IPFT source line, but
    # live-fill accounting must not silently ignore it or double-count it.
    db.add(BrokerChargeAllocation(
        evidence_id=charges.evidence_id,
        broker_connection_id=connection.id,
        broker_trade_record_id=record.id,
        charge_component="ipft",
        source_component_total=Decimal("0.01"),
        allocated_amount=Decimal("0.01"),
        currency="INR",
        allocation_basis="EXPLICIT_REVIEWED",
        method_version=METHOD_VERSION,
        status="RECONCILED",
        reconciliation_reference="test-separate-ipft-component",
    ))
    db.commit()

    with pytest.raises(ValueError, match="exactly the applicable canonical per-fill allocations"):
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
    with pytest.raises(ValueError, match="differ from the reconciled canonical per-fill"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, mismatched)
    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    db.refresh(paper_position)
    assert paper_position.quantity == 7



def test_demat_charge_is_included_in_total_and_requires_paise_precision():
    values = _charges(
        demat_transaction_charges=Decimal("1.50"),
        total_charges=Decimal("25.36"),
    )
    validated = LiveFillAccountingService._validate_charges(values)
    assert validated["demat_transaction_charges"] == Decimal("1.50")
    assert validated["total_charges"] == Decimal("25.36")


def test_demat_charge_cannot_be_negative_or_fractional_paise():
    with pytest.raises(ValueError, match="finite, non-negative and paise-exact"):
        LiveFillAccountingService._validate_charges(
            _charges(demat_transaction_charges=Decimal("-0.01"), total_charges=Decimal("23.85"))
        )
    with pytest.raises(ValueError, match="finite, non-negative and paise-exact"):
        LiveFillAccountingService._validate_charges(
            _charges(demat_transaction_charges=Decimal("1.501"), total_charges=Decimal("25.36"))
        )


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
    # This test exercises generic sell-side position math, not delivery DP.
    order.segment = "EQUITY_INTRADAY"
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


def test_exact_replay_without_resubmitted_evidence_metadata_is_idempotent(accounting_context):
    db, user, _portfolio, _instrument, _connection, _order, _child, record, _paper_position = accounting_context
    service = LiveFillAccountingService(db)
    first = service.promote_trade(user.id, record.id, _reviewed_charges(accounting_context))
    assert first.inserted is True

    # Evidence is mandatory for a new promotion, but an exact retry can safely
    # reuse the already-accounted execution when the caller omits evidence ID.
    replay = service.promote_trade(user.id, record.id, _charges())
    assert replay.inserted is False
    assert replay.execution_id == first.execution_id
    assert db.query(Execution).count() == 1
    assert db.query(LivePosition).one().quantity == 2


def test_replay_rejects_different_evidence_id_with_same_reference_and_charges(accounting_context):
    from uuid import uuid4

    db, user, _portfolio, _instrument, _connection, _order, _child, record, _paper_position = accounting_context
    service = LiveFillAccountingService(db)
    original = _reviewed_charges(accounting_context)
    first = service.promote_trade(user.id, record.id, original)
    assert first.inserted is True

    # Same visible reference and same charge amounts must not make a different
    # source-evidence identity look like an exact replay.
    conflicting = _charges(
        reference=original.reference,
        evidence_id=uuid4(),
        reviewer_user_id=original.reviewer_user_id,
    )
    with pytest.raises(ValueError, match="conflicting accounted execution"):
        service.promote_trade(user.id, record.id, conflicting)

    execution = db.query(Execution).one()
    assert execution.charge_evidence_id == original.evidence_id
    assert db.query(Execution).count() == 1
    assert db.query(LivePosition).one().quantity == 2


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
    charges = _reviewed_charges(accounting_context)
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

    LiveFillAccountingService(db).promote_trade(user.id, record.id, charges)

    # Order and child serialize parent-order accounting. Within charge
    # verification, source-component locks must precede allocation locks, and
    # the staged trade lock must come after the complete verified ledger.
    assert locked_models[:2] == ["Order", "BrokerOrder"]
    first_component = locked_models.index("BrokerChargeSourceComponent")
    first_allocation = locked_models.index("BrokerChargeAllocation")
    last_component = len(locked_models) - 1 - locked_models[::-1].index("BrokerChargeSourceComponent")
    last_allocation = len(locked_models) - 1 - locked_models[::-1].index("BrokerChargeAllocation")
    last_trade = len(locked_models) - 1 - locked_models[::-1].index("BrokerTradeRecord")
    assert first_component < first_allocation
    assert last_component < last_trade
    assert last_allocation < last_trade


@pytest.mark.parametrize("attribute,value", [("is_admin", False), ("is_active", False)])
def test_revoked_or_inactive_reviewer_cannot_promote_live_fill(accounting_context, attribute, value):
    db, user, _portfolio, instrument, connection, _order, _child, record, paper_position = accounting_context
    charges = _reviewed_charges(accounting_context)
    reviewer = db.get(User, charges.reviewer_user_id)
    setattr(reviewer, attribute, value)
    db.commit()

    with pytest.raises(ValueError, match="active platform administrator"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, charges)

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


def test_failure_after_accounting_rows_are_staged_rolls_back_everything(accounting_context, monkeypatch):
    """A failure after ORM rows are staged must roll back the position and execution together."""
    db, user, _portfolio, instrument, connection, _order, _child, record, paper_position = accounting_context
    original_add_all = db.add_all

    def stage_then_fail(instances):
        original_add_all(instances)
        raise RuntimeError("simulated failure after accounting rows were staged")

    monkeypatch.setattr(db, "add_all", stage_then_fail)
    with pytest.raises(RuntimeError, match="after accounting rows were staged"):
        LiveFillAccountingService(db).promote_trade(
            user.id, record.id, _reviewed_charges(accounting_context)
        )
    monkeypatch.setattr(db, "add_all", original_add_all)

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


def test_post_commit_refresh_failure_is_safe_to_retry_as_exact_replay(accounting_context, monkeypatch):
    """A response failure after commit must not double-apply the durable fill on retry."""
    db, user, _portfolio, instrument, connection, _order, _child, record, paper_position = accounting_context
    charges = _reviewed_charges(accounting_context)
    original_refresh = db.refresh

    def fail_execution_refresh(instance, *args, **kwargs):
        if isinstance(instance, Execution):
            raise RuntimeError("simulated response failure after commit")
        return original_refresh(instance, *args, **kwargs)

    monkeypatch.setattr(db, "refresh", fail_execution_refresh)
    with pytest.raises(RuntimeError, match="after commit"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, charges)

    # The commit already succeeded: rollback cannot erase it, so retry semantics
    # must safely recognize the exact persisted execution rather than reapply it.
    monkeypatch.setattr(db, "refresh", original_refresh)
    executions = db.query(Execution).filter_by(
        broker_connection_id=connection.id,
        broker_trade_id=record.broker_trade_id,
    ).all()
    assert len(executions) == 1
    live_position = db.query(LivePosition).filter_by(
        broker_connection_id=connection.id,
        instrument_id=instrument.id,
    ).one()
    assert live_position.quantity == record.quantity
    assert db.query(LivePosition).count() == 1

    replay = LiveFillAccountingService(db).promote_trade(user.id, record.id, charges)
    assert replay.inserted is False
    assert replay.execution_id == executions[0].id
    db.refresh(live_position)
    assert live_position.quantity == record.quantity
    db.refresh(paper_position)
    assert paper_position.quantity == 7


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


def test_flush_failure_after_accounting_rows_are_staged_rolls_back_everything(accounting_context, monkeypatch):
    """A flush failure after both accounting rows are staged must leave no partial ledger."""
    db, user, _portfolio, instrument, connection, _order, _child, record, paper_position = accounting_context
    original_flush = db.flush

    def fail_accounting_flush(*args, **kwargs):
        pending = list(db.new)
        if any(isinstance(item, (Execution, LivePosition)) for item in pending):
            raise RuntimeError("simulated flush failure with accounting rows pending")
        return original_flush(*args, **kwargs)

    monkeypatch.setattr(db, "flush", fail_accounting_flush)
    with pytest.raises(RuntimeError, match="flush failure with accounting rows pending"):
        LiveFillAccountingService(db).promote_trade(
            user.id, record.id, _reviewed_charges(accounting_context)
        )
    monkeypatch.setattr(db, "flush", original_flush)
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


@pytest.mark.parametrize(
    "status,demat_amount,expected",
    [
        ("INVALID", None, False),
        ("UNKNOWN", Decimal("0.00"), False),
        ("KNOWN", None, False),
        ("NOT_APPLICABLE", Decimal("1.00"), False),
        ("KNOWN", Decimal("0.00"), True),
        ("NOT_APPLICABLE", None, True),
    ],
)
def test_execution_completeness_property_fails_closed_on_inconsistent_demat_state(
    status, demat_amount, expected
):
    row = Execution(
        demat_charge_status=status,
        demat_transaction_charges=demat_amount,
    )
    assert row.total_charges_complete is expected


@pytest.mark.parametrize(
    "trade_side,order_side,segment",
    [
        ("BUY", "BUY", "EQUITY_DELIVERY"),
        ("SELL", "SELL", "EQUITY_INTRADAY"),
        ("SELL", "BUY", "EQUITY_DELIVERY"),
    ],
)
def test_demat_manifest_rejects_ineligible_fill_mapping(
    accounting_context, trade_side, order_side, segment
):
    db, _user, _portfolio, _instrument, connection, order, _child, record, _paper_position = accounting_context
    order.side = order_side
    order.segment = segment
    record.side = trade_side
    db.commit()
    snapshot = BrokerChargeCanonicalComponent(
        eligible_fill_ids_json=json.dumps([str(record.id)])
    )

    with pytest.raises(ValueError, match="only mapped equity-delivery SELL fills"):
        LiveFillAccountingService(db)._validate_demat_manifest_eligibility(
            snapshot, broker_connection_id=connection.id
        )


def test_demat_manifest_accepts_only_a_mapped_equity_delivery_sell(accounting_context):
    db, _user, _portfolio, _instrument, connection, order, _child, record, _paper_position = accounting_context
    order.side = "SELL"
    order.segment = "EQUITY_DELIVERY"
    record.side = "SELL"
    db.commit()
    snapshot = BrokerChargeCanonicalComponent(
        eligible_fill_ids_json=json.dumps([str(record.id)])
    )

    LiveFillAccountingService(db)._validate_demat_manifest_eligibility(
        snapshot, broker_connection_id=connection.id
    )
