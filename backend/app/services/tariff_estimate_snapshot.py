"""Canonical immutable tariff-estimate snapshots and idempotency fingerprints.

This module deliberately does not persist estimates or promote them to broker
actuals. Persistence must use a database uniqueness constraint and a transaction
around insert/replay comparison; these helpers provide canonical payloads for
that layer.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from app.services.broker_tariff_rules import TariffRule, calculate_order_brokerage, calculate_tariff_amount


SNAPSHOT_SCHEMA_VERSION = "tariff-estimate-snapshot-v4"


def _decimal_string(value: Decimal | str | int | float, field: str) -> str:
    try:
        parsed = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite nonnegative decimal.") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(f"{field} must be a finite nonnegative decimal.")
    return format(parsed, "f")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TariffEstimateSnapshot:
    schema_version: str
    idempotency_key: str
    source_trade_record_id: str | None
    rule_fingerprint: str
    component: str
    broker: str
    exchange: str
    segment: str
    product: str
    transaction_side: str
    calculation_basis: str
    trade_date: str
    rate: str
    rate_unit: str
    calculation_base: str
    calculated_amount: str
    currency: str
    rounding_policy: str
    effective_from: str
    effective_to: str | None
    source_url: str
    source_retrieved_on: str
    source_sha256: str
    review_status: str
    minimum_inr: str | None
    maximum_inr: str | None
    comparison_scope: str = "TRADE_FILL"
    source_fill_ids_json: str | None = None
    source_fill_set_sha256: str | None = None

    def canonical_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @property
    def snapshot_sha256(self) -> str:
        return _sha256(self.canonical_json())


def build_tariff_estimate_snapshot(
    rule: TariffRule,
    *,
    trade_date: date,
    calculation_base: Decimal | str | int | float,
    source_identity: str,
    source_trade_record_id: UUID | str | None = None,
    comparison_scope: str = "TRADE_FILL",
    source_fill_record_ids: list[UUID | str] | tuple[UUID | str, ...] | None = None,
) -> TariffEstimateSnapshot:
    """Build a stable snapshot; source_identity must identify the same trade/event on replay."""
    if not isinstance(rule, TariffRule):
        raise ValueError("A validated tariff rule is required.")
    if rule.review_status != "APPROVED":
        raise ValueError("Only an approved tariff rule can be snapshotted.")
    if not source_identity or not source_identity.strip():
        raise ValueError("Stable source_identity is required for idempotency.")
    if trade_date < rule.effective_from or (rule.effective_to and trade_date > rule.effective_to):
        raise ValueError("Tariff rule is not effective on the trade date.")

    if source_trade_record_id is not None:
        try:
            source_trade_record_id = str(UUID(str(source_trade_record_id)))
        except (TypeError, ValueError) as exc:
            raise ValueError("source_trade_record_id must be a valid UUID when provided.") from exc

    if comparison_scope not in {"TRADE_FILL", "ORDER_FILL_SET"}:
        raise ValueError("Unsupported tariff estimate comparison scope.")
    fill_ids: list[str] | None = None
    if comparison_scope == "TRADE_FILL":
        if source_fill_record_ids is not None:
            raise ValueError("TRADE_FILL scope uses source_trade_record_id, not a fill-set argument.")
        if source_trade_record_id is not None:
            fill_ids = [source_trade_record_id]
    else:
        if source_trade_record_id is not None:
            raise ValueError("ORDER_FILL_SET scope must not set a single source_trade_record_id.")
        if not source_fill_record_ids:
            raise ValueError("ORDER_FILL_SET scope requires a nonempty exact fill set.")
        try:
            fill_ids = sorted({str(UUID(str(value))) for value in source_fill_record_ids})
        except (TypeError, ValueError) as exc:
            raise ValueError("Order fill set must contain valid UUIDs.") from exc
        if len(fill_ids) != len(source_fill_record_ids):
            raise ValueError("Order fill set must not contain duplicate fill IDs.")
    fill_ids_json = json.dumps(fill_ids, separators=(",", ":")) if fill_ids is not None else None
    fill_set_sha256 = _sha256(fill_ids_json) if fill_ids_json is not None else None

    base = _decimal_string(calculation_base, "Calculation base")
    if rule.component.lower() == "brokerage" and rule.calculation_basis == "ORDER_NOTIONAL":
        amount = calculate_order_brokerage(rule, order_notional=Decimal(base))
    else:
        amount = calculate_tariff_amount(rule, calculation_base=Decimal(base))
    rule_payload: dict[str, Any] = {
        "component": rule.component,
        "broker": rule.broker,
        "exchange": rule.exchange,
        "segment": rule.segment,
        "product": rule.product,
        "transaction_side": rule.transaction_side,
        "calculation_basis": rule.calculation_basis,
        "rate": format(rule.rate, "f"),
        "rate_unit": rule.rate_unit,
        "minimum_inr": format(rule.minimum_inr, "f") if rule.minimum_inr is not None else None,
        "maximum_inr": format(rule.maximum_inr, "f") if rule.maximum_inr is not None else None,
        "effective_from": rule.effective_from.isoformat(),
        "effective_to": rule.effective_to.isoformat() if rule.effective_to else None,
        "source_url": rule.source_url,
        "source_retrieved_on": rule.source_retrieved_on.isoformat(),
        "source_sha256": rule.source_sha256.lower(),
        "review_status": rule.review_status,
    }
    rule_fingerprint = _sha256(json.dumps(rule_payload, sort_keys=True, separators=(",", ":")))
    # Keep event identity independent of mutable rule content and calculation inputs.
    # If a tariff rule/base changes for the same event, the same key must collide so
    # persistence can detect a conflicting replay rather than create a second estimate.
    idempotency_key = _sha256("|".join((source_identity.strip(), rule.component, trade_date.isoformat())))
    return TariffEstimateSnapshot(
        schema_version=SNAPSHOT_SCHEMA_VERSION,
        idempotency_key=idempotency_key,
        source_trade_record_id=source_trade_record_id,
        rule_fingerprint=rule_fingerprint,
        component=rule.component,
        broker=rule.broker,
        exchange=rule.exchange,
        segment=rule.segment,
        product=rule.product,
        transaction_side=rule.transaction_side,
        calculation_basis=rule.calculation_basis,
        trade_date=trade_date.isoformat(),
        rate=format(rule.rate, "f"),
        rate_unit=rule.rate_unit,
        calculation_base=base,
        calculated_amount=format(amount, ".2f"),
        currency="INR",
        rounding_policy="decimal-half-up-paise-v1",
        effective_from=rule.effective_from.isoformat(),
        effective_to=rule.effective_to.isoformat() if rule.effective_to else None,
        source_url=rule.source_url,
        source_retrieved_on=rule.source_retrieved_on.isoformat(),
        source_sha256=rule.source_sha256.lower(),
        review_status=rule.review_status,
        minimum_inr=format(rule.minimum_inr, "f") if rule.minimum_inr is not None else None,
        maximum_inr=format(rule.maximum_inr, "f") if rule.maximum_inr is not None else None,
        comparison_scope=comparison_scope,
        source_fill_ids_json=fill_ids_json,
        source_fill_set_sha256=fill_set_sha256,
    )


def compare_estimate_replay(
    existing: TariffEstimateSnapshot,
    incoming: TariffEstimateSnapshot,
) -> str:
    """Return EXACT_REPLAY or raise on a same-key, different-payload conflict."""
    if existing.idempotency_key != incoming.idempotency_key:
        raise ValueError("Tariff estimate idempotency keys do not match.")
    if existing.canonical_json() != incoming.canonical_json():
        raise ValueError("Conflicting tariff estimate replay; refusing silent overwrite.")
    return "EXACT_REPLAY"
