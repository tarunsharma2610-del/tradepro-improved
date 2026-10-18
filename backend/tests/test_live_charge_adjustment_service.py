from decimal import Decimal

import pytest

from app.models.execution import Execution
from app.models.live_charge_adjustment import LiveChargeAdjustment
from app.models.live_position import LivePosition
from app.services.live_execution_service import LiveExecutionBlocked
from app.services.live_fill_accounting_service import (
    LiveChargeBreakdown,
    LiveFillAccountingService,
)
from app.services.live_charge_adjustment_service import LiveChargeAdjustmentService


def _charges(**overrides):
    values = dict(
        brokerage=Decimal("2.00"),
        stt=Decimal("0.20"),
        exchange_charges=Decimal("0.03"),
        sebi_charges=Decimal("0.01"),
        stamp_duty=Decimal("0.02"),
        gst=Decimal("0.37"),
        dp_charges=Decimal("0"),
        source="BROKER_REPORTED",
        reference="contract-note:trade-001:v1",
    )
    values.update(overrides)
    return LiveChargeBreakdown(**values)


def _account_estimate(context):
    db, user, _portfolio, _instrument, connection, _order, _child, record = context
    estimate = LiveChargeBreakdown(
        brokerage=Decimal("2.00"),
        stt=Decimal("0.20"),
        exchange_charges=Decimal("0.03"),
        sebi_charges=Decimal("0.01"),
        stamp_duty=Decimal("0.02"),
        gst=Decimal("0.37"),
        dp_charges=Decimal("0"),
        source="APPROVED_ESTIMATE",
        reference="upstox-estimator-v1",
    )
    LiveFillAccountingService(db).account_trade(user.id, record.id, estimate)
    return db, user, connection, record


def test_broker_reported_charges_append_adjustment_without_replaying_fill(accounting_context):
    db, user, connection, record = _account_estimate(accounting_context)
    execution = db.query(Execution).one()
    original_execution_id = execution.id
    original_total = Decimal(str(execution.total_charges))
    original_quantity = db.query(LivePosition).one().quantity

    result = LiveChargeAdjustmentService(db).apply_broker_reported_charges(
        user.id,
        connection.id,
        record.broker_trade_id,
        _charges(brokerage=Decimal("2.25"), gst=Decimal("0.50")),
    )

    assert not result.duplicate
    assert result.previous_effective_total == original_total == Decimal("2.63")
    assert result.new_effective_total == Decimal("2.81")
    assert result.charge_delta == Decimal("0.18")
    assert result.net_realized_pnl_delta == Decimal("-0.18")
    assert result.effective_net_realized_pnl == Decimal("-2.81")
    assert db.query(LiveChargeAdjustment).count() == 1

    db.refresh(execution)
    assert execution.id == original_execution_id
    assert execution.charge_source == "APPROVED_ESTIMATE"
    assert execution.total_charges == original_total
    assert db.query(Execution).count() == 1
    assert db.query(LivePosition).one().quantity == original_quantity == 2


def test_same_contract_note_replay_is_idempotent(accounting_context):
    db, user, connection, record = _account_estimate(accounting_context)
    service = LiveChargeAdjustmentService(db)
    charges = _charges(brokerage=Decimal("2.25"), gst=Decimal("0.50"))

    first = service.apply_broker_reported_charges(
        user.id, connection.id, record.broker_trade_id, charges
    )
    second = service.apply_broker_reported_charges(
        user.id, connection.id, record.broker_trade_id, charges
    )

    assert not first.duplicate
    assert second.duplicate
    assert first.adjustment_id == second.adjustment_id
    assert first.charge_delta == second.charge_delta == Decimal("0.18")
    assert db.query(LiveChargeAdjustment).count() == 1
    assert db.query(Execution).count() == 1
    assert db.query(LivePosition).one().quantity == 2


def test_same_contract_note_reference_with_different_amounts_is_rejected(accounting_context):
    db, user, connection, record = _account_estimate(accounting_context)
    service = LiveChargeAdjustmentService(db)

    service.apply_broker_reported_charges(
        user.id, connection.id, record.broker_trade_id,
        _charges(brokerage=Decimal("2.25"), gst=Decimal("0.50")),
    )
    with pytest.raises(LiveExecutionBlocked, match="reference already exists with different values"):
        service.apply_broker_reported_charges(
            user.id, connection.id, record.broker_trade_id,
            _charges(brokerage=Decimal("9.00"), gst=Decimal("0.50")),
        )

    assert db.query(LiveChargeAdjustment).count() == 1
    assert db.query(Execution).count() == 1


def test_new_charge_revision_uses_prior_effective_total_not_original_estimate(accounting_context):
    db, user, connection, record = _account_estimate(accounting_context)
    service = LiveChargeAdjustmentService(db)
    first = service.apply_broker_reported_charges(
        user.id, connection.id, record.broker_trade_id,
        _charges(brokerage=Decimal("2.25"), gst=Decimal("0.50"), reference="contract-note:v1"),
    )
    second = service.apply_broker_reported_charges(
        user.id, connection.id, record.broker_trade_id,
        _charges(reference="contract-note:v2"),
    )

    assert first.new_effective_total == Decimal("2.81")
    assert second.previous_effective_total == Decimal("2.81")
    assert second.new_effective_total == Decimal("2.63")
    assert second.charge_delta == Decimal("-0.18")
    assert second.net_realized_pnl_delta == Decimal("0.18")
    rows = db.query(LiveChargeAdjustment).order_by(LiveChargeAdjustment.adjustment_number).all()
    assert [row.adjustment_number for row in rows] == [1, 2]
    assert rows[1].previous_effective_total == Decimal("2.81")
    assert db.query(Execution).one().total_charges == Decimal("2.63")
    assert db.query(LivePosition).one().quantity == 2


def test_charge_adjustment_rejects_estimate_source(accounting_context):
    db, user, connection, record = _account_estimate(accounting_context)
    with pytest.raises(LiveExecutionBlocked, match="requires broker-reported final charges"):
        LiveChargeAdjustmentService(db).apply_broker_reported_charges(
            user.id,
            connection.id,
            record.broker_trade_id,
            _charges(source="APPROVED_ESTIMATE"),
        )
    assert db.query(LiveChargeAdjustment).count() == 0


def test_foreign_user_cannot_adjust_another_users_trade(accounting_context, make_user):
    db, user, connection, record = _account_estimate(accounting_context)
    stranger = make_user(email="charge-adjustment-stranger@example.com")

    with pytest.raises(LiveExecutionBlocked, match="No accounted live execution"):
        LiveChargeAdjustmentService(db).apply_broker_reported_charges(
            stranger.id, connection.id, record.broker_trade_id, _charges()
        )

    assert db.query(LiveChargeAdjustment).count() == 0
