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
    source_kind: str = "REVIEWED_TARIFF_RULE"
    api_version: str | None = None
    api_endpoint: str | None = None
    api_request_json: str | None = None
    api_retrieved_at: str | None = None
    api_response_sha256: str | None = None
    api_response_json: str | None = None
    api_total_amount: str | None = None
    dp_plan_name: str | None = None
    dp_plan_min_expense: str | None = None

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



def build_upstox_brokerage_api_snapshots(
    result: Any,
    *,
    request_parameters: dict[str, Any],
    trade_date: date,
    source_identity: str,
    exchange: str,
    segment: str,
    product: str,
    retrieved_at: Any,
    source_trade_record_id: UUID | str | None = None,
    comparison_scope: str = "TRADE_FILL",
    source_fill_record_ids: list[UUID | str] | tuple[UUID | str, ...] | None = None,
) -> tuple[TariffEstimateSnapshot, ...]:
    """Normalize Upstox brokerage calculator output into immutable estimate-only component snapshots.

    This deliberately accepts a successful read-only client result rather than an
    access token/client. It never persists records or treats estimates as actuals.
    """
    from datetime import datetime, timezone

    if not getattr(result, "ok", False):
        raise ValueError("A successful Upstox brokerage estimate response is required.")
    if not isinstance(source_identity, str) or not source_identity.strip():
        raise ValueError("Stable source_identity is required for API estimate idempotency.")
    if not isinstance(request_parameters, dict):
        raise ValueError("Exact Upstox request parameters are required.")
    required_request_keys = {"instrument_token", "quantity", "product", "transaction_type", "price"}
    if set(request_parameters) != required_request_keys:
        raise ValueError("Request provenance must contain exactly the documented brokerage query parameters.")
    if any(not isinstance(request_parameters[k], (str, int, float, Decimal)) or isinstance(request_parameters[k], bool)
           for k in required_request_keys):
        raise ValueError("Upstox request parameters contain an invalid value.")
    if not str(request_parameters["instrument_token"]).strip():
        raise ValueError("instrument_token is required for API estimate provenance.")
    try:
        request_quantity = int(str(request_parameters["quantity"]))
        request_price = Decimal(str(request_parameters["price"]))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Upstox request quantity and price must be valid positive values.") from exc
    if (
        str(request_quantity) != str(request_parameters["quantity"])
        or request_quantity <= 0
        or not request_price.is_finite()
        or request_price <= 0
        or str(request_parameters["transaction_type"]).upper() not in {"BUY", "SELL"}
        or not str(request_parameters["product"]).strip()
    ):
        raise ValueError("Upstox request quantity, price, product, or side is invalid.")
    if isinstance(retrieved_at, str):
        try:
            retrieved_at = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("retrieved_at must be an ISO-8601 timestamp.") from exc
    if not isinstance(retrieved_at, datetime) or retrieved_at.tzinfo is None:
        raise ValueError("retrieved_at must be a timezone-aware datetime.")
    retrieved_at = retrieved_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    response = getattr(result, "data", None)
    if not isinstance(response, dict) or response.get("status") != "success":
        raise ValueError("Upstox brokerage estimate response is not a successful documented payload.")
    data = response.get("data")
    charges = data.get("charges") if isinstance(data, dict) else None
    if not isinstance(charges, dict):
        raise ValueError("Upstox brokerage response is missing data.charges.")
    taxes = charges.get("taxes")
    other = charges.get("other_charges")
    dp_plan = charges.get("dp_plan")
    if not isinstance(taxes, dict) or not isinstance(other, dict) or not isinstance(dp_plan, dict):
        raise ValueError("Upstox brokerage response is missing documented charge breakdown sections.")

    def amount(value: Any, field: str) -> Decimal:
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f"Upstox response {field} must be a finite nonnegative amount.") from exc
        if not parsed.is_finite() or parsed < 0:
            raise ValueError(f"Upstox response {field} must be a finite nonnegative amount.")
        return parsed.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    from decimal import ROUND_HALF_UP

    component_amounts = {
        "brokerage": amount(charges.get("brokerage"), "brokerage"),
        "stt": amount(taxes.get("stt"), "taxes.stt"),
        "stamp_duty": amount(taxes.get("stamp_duty"), "taxes.stamp_duty"),
        "gst": amount(taxes.get("gst"), "taxes.gst"),
        "exchange_charges": (
            amount(other.get("transaction"), "other_charges.transaction")
            + amount(other.get("clearing"), "other_charges.clearing")
            + amount(other.get("ipft"), "other_charges.ipft")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "sebi_charges": amount(other.get("sebi_turnover"), "other_charges.sebi_turnover"),
    }
    total = amount(charges.get("total"), "total")
    dp_plan_name = dp_plan.get("name")
    if dp_plan_name is not None and not isinstance(dp_plan_name, str):
        raise ValueError("Upstox response dp_plan.name must be a string when present.")
    dp_minimum = amount(dp_plan.get("min_expense"), "dp_plan.min_expense")
    if not isinstance(exchange, str) or not exchange.strip() or not isinstance(segment, str) or not segment.strip():
        raise ValueError("exchange and segment context are required.")
    if not isinstance(product, str) or not product.strip():
        raise ValueError("Normalized product context is required.")
    if comparison_scope not in {"TRADE_FILL", "ORDER_FILL_SET"}:
        raise ValueError("Unsupported tariff estimate comparison scope.")
    if source_trade_record_id is not None:
        try:
            source_trade_record_id = str(UUID(str(source_trade_record_id)))
        except (TypeError, ValueError) as exc:
            raise ValueError("source_trade_record_id must be a valid UUID when provided.") from exc
    fill_ids: list[str] | None = None
    if comparison_scope == "TRADE_FILL":
        if source_fill_record_ids is not None:
            raise ValueError("TRADE_FILL scope does not accept a fill-set argument.")
        if source_trade_record_id is not None:
            fill_ids = [source_trade_record_id]
    else:
        if source_trade_record_id is not None or not source_fill_record_ids:
            raise ValueError("ORDER_FILL_SET requires only a nonempty exact fill set.")
        try:
            fill_ids = sorted({str(UUID(str(value))) for value in source_fill_record_ids})
        except (TypeError, ValueError) as exc:
            raise ValueError("Order fill set must contain valid UUIDs.") from exc
        if len(fill_ids) != len(source_fill_record_ids):
            raise ValueError("Order fill set must not contain duplicate fill IDs.")
    fill_ids_json = json.dumps(fill_ids, separators=(",", ":")) if fill_ids is not None else None
    fill_set_sha256 = _sha256(fill_ids_json) if fill_ids_json is not None else None

    request_json = json.dumps(
        {key: str(value) for key, value in sorted(request_parameters.items())},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    )
    response_json = json.dumps(response, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    response_sha256 = _sha256(response_json)
    rule_fingerprint = _sha256("|".join((
        "upstox-brokerage-api-v2", request_json, response_sha256,
        str(exchange).upper(), str(segment).upper(), product.strip().upper(),
    )))
    api_source_url = "https://api.upstox.com/v2/charges/brokerage"
    snapshots = []
    for component, calculated in component_amounts.items():
        key = _sha256("|".join((source_identity.strip(), component, trade_date.isoformat())))
        snapshots.append(TariffEstimateSnapshot(
            schema_version="upstox-brokerage-api-estimate-v1",
            idempotency_key=key,
            source_trade_record_id=source_trade_record_id,
            rule_fingerprint=rule_fingerprint,
            component=component,
            broker="Upstox",
            exchange=exchange.strip().upper(),
            segment=segment.strip().upper(),
            product=product.strip().upper(),
            transaction_side=str(request_parameters["transaction_type"]).upper(),
            calculation_basis="UPSTOX_API_ESTIMATE",
            trade_date=trade_date.isoformat(),
            rate="0",
            rate_unit="API_ESTIMATE",
            calculation_base="0",
            calculated_amount=format(calculated, ".2f"),
            currency="INR",
            rounding_policy="upstox-response-component-paise-v1",
            effective_from=trade_date.isoformat(),
            effective_to=None,
            source_url=api_source_url,
            source_retrieved_on=retrieved_at[:10],
            source_sha256=response_sha256,
            review_status="ESTIMATE_ONLY",
            minimum_inr=None,
            maximum_inr=None,
            comparison_scope=comparison_scope,
            source_fill_ids_json=fill_ids_json,
            source_fill_set_sha256=fill_set_sha256,
            source_kind="UPSTOX_BROKERAGE_API_ESTIMATE",
            api_version="2.0",
            api_endpoint="/v2/charges/brokerage",
            api_request_json=request_json,
            api_retrieved_at=retrieved_at,
            api_response_sha256=response_sha256,
            api_response_json=response_json,
            api_total_amount=format(total, ".2f"),
            dp_plan_name=dp_plan_name,
            dp_plan_min_expense=format(dp_minimum, ".2f"),
        ))
    # Total is retained in the common API response digest; the component snapshots
    # intentionally exclude DP minimum and do not synthesize a "total" actual component.
    if total < Decimal("0"):
        raise ValueError("Upstox response total must be nonnegative.")
    return tuple(snapshots)

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
