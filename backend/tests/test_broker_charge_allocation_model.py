from decimal import Decimal

import pytest

from app.models.broker_charge_allocation import BrokerChargeAllocation


def test_charge_allocation_table_has_replay_safe_identity():
    constraints = {
        constraint.name: constraint
        for constraint in BrokerChargeAllocation.__table__.constraints
    }
    unique = constraints["uq_charge_allocation_evidence_trade_component"]
    assert tuple(column.name for column in unique.columns) == (
        "evidence_id",
        "broker_trade_record_id",
        "charge_component",
    )


def test_charge_allocation_amount_columns_use_paise_precision():
    table = BrokerChargeAllocation.__table__
    assert table.c.source_component_total.type.precision == 18
    assert table.c.source_component_total.type.scale == 2
    assert table.c.allocated_amount.type.precision == 18
    assert table.c.allocated_amount.type.scale == 2


def test_charge_allocation_has_fail_closed_reconciliation_default():
    column = BrokerChargeAllocation.__table__.c.status
    assert column.default.arg == "PENDING_RECONCILIATION"
    assert column.server_default.arg == "PENDING_RECONCILIATION"


def test_charge_allocation_rejects_unsupported_components_in_schema():
    constraints = {
        constraint.name: constraint
        for constraint in BrokerChargeAllocation.__table__.constraints
    }
    assert "ck_charge_allocation_component" in constraints
    assert "ck_charge_allocation_nonnegative_amounts" in constraints
    assert "ck_charge_allocation_status" in constraints
