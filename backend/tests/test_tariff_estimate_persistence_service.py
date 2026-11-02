from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.services.broker_tariff_rules import TariffRule
from app.services.tariff_estimate_persistence_service import persist_tariff_estimate_snapshot
from app.brokers.upstox.reconciliation_client import ReadOnlyBrokerResult
from app.services.tariff_estimate_snapshot import build_tariff_estimate_snapshot, build_upstox_brokerage_api_snapshots


def make_rule(rate="0.05"):
    return TariffRule(
        component="brokerage",
        broker="Upstox",
        exchange="NSE",
        segment="FO",
        product="FUTURES",
        transaction_side="SELL",
        calculation_basis="ORDER_NOTIONAL",
        rate=Decimal(rate),
        rate_unit="PERCENT",
        effective_from=date(2026, 4, 1),
        effective_to=None,
        source_url="https://upstox.com/brokerage-charges/",
        source_retrieved_on=date(2026, 10, 23),
        source_sha256="a" * 64,
        review_status="APPROVED",
    )


def make_snapshot(base="100000", rate="0.05"):
    return build_tariff_estimate_snapshot(
        make_rule(rate),
        trade_date=date(2026, 10, 23),
        calculation_base=base,
        source_identity="trade-event:123:brokerage",
    )


def test_persist_snapshot_and_exact_replay_is_idempotent(db_session):
    snapshot = make_snapshot()
    first, first_status = persist_tariff_estimate_snapshot(db_session, snapshot)
    db_session.commit()

    replay, replay_status = persist_tariff_estimate_snapshot(db_session, snapshot)
    assert first_status == "CREATED"
    assert replay_status == "EXACT_REPLAY"
    assert replay.id == first.id
    assert replay.status == "ESTIMATE_ONLY"
    assert db_session.query(type(first)).count() == 1


def test_same_event_with_changed_base_conflicts_without_overwrite(db_session):
    first, _ = persist_tariff_estimate_snapshot(db_session, make_snapshot(base="100000"))
    db_session.commit()
    original_json = first.snapshot_json

    with pytest.raises(ValueError, match="Conflicting tariff estimate replay"):
        persist_tariff_estimate_snapshot(db_session, make_snapshot(base="200000"))

    db_session.rollback()
    persisted = db_session.query(type(first)).filter_by(id=first.id).one()
    assert persisted.snapshot_json == original_json
    assert db_session.query(type(first)).count() == 1


def test_same_event_with_changed_rule_conflicts_without_second_row(db_session):
    first, _ = persist_tariff_estimate_snapshot(db_session, make_snapshot(rate="0.05"))
    db_session.commit()

    with pytest.raises(ValueError, match="Conflicting tariff estimate replay"):
        persist_tariff_estimate_snapshot(db_session, make_snapshot(rate="0.06"))

    db_session.rollback()
    assert db_session.query(type(first)).count() == 1


def test_record_is_not_promoted_to_actual_charge(db_session):
    record, _ = persist_tariff_estimate_snapshot(db_session, make_snapshot())
    with pytest.raises(Exception):
        record.status = "VERIFIED_ACTUAL"
        db_session.flush()
    db_session.rollback()


def test_persisted_snapshot_is_append_only(db_session):
    record, _ = persist_tariff_estimate_snapshot(db_session, make_snapshot())
    db_session.commit()

    record.snapshot_json = record.snapshot_json + " "
    with pytest.raises(ValueError, match="snapshots are immutable"):
        db_session.flush()
    db_session.rollback()

    persisted = db_session.query(type(record)).filter_by(id=record.id).one()
    assert persisted.snapshot_json == make_snapshot().canonical_json()



def test_database_rejects_direct_sql_snapshot_update(db_session):
    record, _ = persist_tariff_estimate_snapshot(db_session, make_snapshot())
    db_session.commit()

    with pytest.raises(IntegrityError, match="append-only"):
        db_session.execute(
            text("UPDATE tariff_estimate_snapshot_records SET snapshot_json = :payload WHERE id = :id"),
            {"payload": "tampered", "id": record.id.hex},
        )
    db_session.rollback()

    persisted = db_session.query(type(record)).filter_by(id=record.id).one()
    assert persisted.snapshot_json == make_snapshot().canonical_json()


def test_database_rejects_direct_sql_snapshot_delete(db_session):
    record, _ = persist_tariff_estimate_snapshot(db_session, make_snapshot())
    db_session.commit()

    with pytest.raises(IntegrityError, match="append-only"):
        db_session.execute(
            text("DELETE FROM tariff_estimate_snapshot_records WHERE id = :id"),
            {"id": record.id.hex},
        )
    db_session.rollback()

    assert db_session.query(type(record)).filter_by(id=record.id).one()

def make_api_snapshots():
    result = ReadOnlyBrokerResult(
        ok=True,
        status_code=200,
        data={
            "status": "success",
            "data": {
                "charges": {
                    "total": 12.34,
                    "brokerage": 10.0,
                    "taxes": {"gst": 1.02, "stt": 0.0, "stamp_duty": 0.0},
                    "other_charges": {
                        "transaction": 1.0,
                        "clearing": 0.0,
                        "ipft": 0.17,
                        "sebi_turnover": 0.15,
                    },
                    "dp_plan": {"name": "DP3A", "min_expense": 18.5},
                },
            },
        },
    )
    return build_upstox_brokerage_api_snapshots(
        result,
        request_parameters={
            "instrument_token": "NSE_EQ|INE669E01016",
            "quantity": 10,
            "product": "D",
            "transaction_type": "BUY",
            "price": "13.70",
        },
        trade_date=date(2026, 10, 24),
        source_identity="broker-order:123:api-estimate",
        exchange="NSE",
        segment="EQ",
        product="DELIVERY",
        retrieved_at=datetime(2026, 10, 24, 10, 15, tzinfo=timezone.utc),
    )


def test_persist_upstox_api_component_estimates_as_immutable_estimate_only_records(db_session):
    snapshots = make_api_snapshots()
    persisted = []
    for snapshot in snapshots:
        record, status = persist_tariff_estimate_snapshot(db_session, snapshot)
        assert status == "CREATED"
        assert record.status == "ESTIMATE_ONLY"
        assert record.snapshot_sha256 == snapshot.snapshot_sha256
        persisted.append(record)
    db_session.commit()

    for snapshot, original in zip(snapshots, persisted):
        replay, replay_status = persist_tariff_estimate_snapshot(db_session, snapshot)
        assert replay_status == "EXACT_REPLAY"
        assert replay.id == original.id
        payload = __import__("json").loads(replay.snapshot_json)
        assert payload["source_kind"] == "UPSTOX_BROKERAGE_API_ESTIMATE"
        assert payload["api_response_sha256"] == snapshot.api_response_sha256
        assert payload["api_response_json"] == snapshot.api_response_json
        assert payload["api_total_amount"] == "12.34"
        assert payload["dp_plan_min_expense"] == "18.50"

    assert db_session.query(type(persisted[0])).count() == len(snapshots)
