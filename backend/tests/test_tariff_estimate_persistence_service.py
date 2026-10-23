from datetime import date
from decimal import Decimal

import pytest

from app.services.broker_tariff_rules import TariffRule
from app.services.tariff_estimate_persistence_service import persist_tariff_estimate_snapshot
from app.services.tariff_estimate_snapshot import build_tariff_estimate_snapshot


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
