"""Variance-only comparison of a tariff estimate with reviewed broker actual evidence.

This service does not promote charges or write per-fill allocation rows.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.broker_charge_evidence import BrokerChargeEvidence
from app.models.broker_connection import BrokerConnection
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.broker_charge_source_component import BrokerChargeSourceComponent
from app.models.tariff_estimate_snapshot_record import TariffEstimateSnapshotRecord
from app.models.tariff_estimate_variance_record import TariffEstimateVarianceRecord
from app.services.broker_charge_document_storage_service import read_verified_document

CENT = Decimal("0.01")
PERCENT_SCALE = Decimal("0.000001")


def _existing_or_conflict(
    existing: TariffEstimateVarianceRecord,
    *,
    snapshot: TariffEstimateSnapshotRecord,
    component: BrokerChargeSourceComponent,
    evidence: BrokerChargeEvidence,
    estimated: Decimal,
    actual: Decimal,
    variance: Decimal,
    variance_percent: Decimal | None,
    comparison_scope: str,
    source_fill_set_sha256: str | None,
    allow_legacy_digest: bool = False,
) -> TariffEstimateVarianceRecord:
    expected = (
        component.component_name,
        snapshot.snapshot_sha256,
        evidence.source_sha256,
        estimated,
        actual,
        variance,
        variance_percent,
        comparison_scope,
        source_fill_set_sha256,
    )
    actual_values = (
        existing.component_name,
        existing.estimate_snapshot_sha256,
        existing.evidence_source_sha256,
        Decimal(existing.estimated_amount),
        Decimal(existing.actual_amount),
        Decimal(existing.variance_amount),
        Decimal(existing.variance_percent) if existing.variance_percent is not None else None,
        existing.comparison_scope,
        (source_fill_set_sha256 if allow_legacy_digest and existing.source_fill_set_sha256 is None else existing.source_fill_set_sha256),
    )
    if actual_values != expected:
        raise ValueError("Conflicting estimate-versus-actual variance replay; refusing overwrite.")
    return existing


def compare_estimate_to_reviewed_actual(
    db: Session, *, estimate_snapshot_id: UUID, source_component_id: UUID
) -> tuple[TariffEstimateVarianceRecord, str]:
    """Persist a variance-only comparison after validating reviewed source evidence.

    The caller owns the outer transaction. Only a VERIFIED source component from
    a REVIEWED contract note is accepted. The estimate and actual remain separate
    records; this function never changes evidence/component/allocation status.
    """
    snapshot = db.query(TariffEstimateSnapshotRecord).filter(TariffEstimateSnapshotRecord.id == estimate_snapshot_id).one_or_none()
    if snapshot is None or snapshot.status != "ESTIMATE_ONLY":
        raise ValueError("An existing ESTIMATE_ONLY tariff snapshot is required.")
    try:
        payload = json.loads(snapshot.snapshot_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Tariff estimate snapshot JSON is invalid.") from exc
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if canonical != snapshot.snapshot_json:
        raise ValueError("Tariff estimate snapshot is not canonical JSON.")
    snapshot_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if snapshot_digest != snapshot.snapshot_sha256:
        raise ValueError("Tariff estimate snapshot digest does not match its payload.")
    try:
        estimated = Decimal(str(payload["calculated_amount"]))
    except (KeyError, ArithmeticError, ValueError) as exc:
        raise ValueError("Tariff estimate amount is invalid.") from exc
    if not estimated.is_finite() or estimated < 0:
        raise ValueError("Tariff estimate amount must be finite and nonnegative.")

    # Match the shared evidence -> source component -> fill lock order used by
    # ledger verification/promotion; the initial component read only discovers
    # the evidence parent ID and is rechecked after acquiring locks.
    component_hint = (
        db.query(BrokerChargeSourceComponent)
        .filter(BrokerChargeSourceComponent.id == source_component_id)
        .first()
    )
    if component_hint is None:
        raise ValueError("A VERIFIED broker source component is required for variance comparison.")
    evidence_hint = db.query(BrokerChargeEvidence).filter(
        BrokerChargeEvidence.id == component_hint.evidence_id
    ).one_or_none()
    if evidence_hint is None:
        raise ValueError("Reviewed contract-note evidence is required for variance comparison.")
    connection = (
        db.query(BrokerConnection)
        .filter(BrokerConnection.id == evidence_hint.broker_connection_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if connection is None:
        raise ValueError("Reviewed actual evidence broker connection was not found.")
    evidence = (
        db.query(BrokerChargeEvidence)
        .filter(BrokerChargeEvidence.id == evidence_hint.id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if (
        evidence is None
        or evidence.source_kind != "CONTRACT_NOTE"
        or evidence.status != "REVIEWED"
        or evidence.reviewed_by_user_id is None
        or evidence.reviewed_at is None
    ):
        raise ValueError("Reviewed contract-note evidence is required for variance comparison.")
    component = (
        db.query(BrokerChargeSourceComponent)
        .filter(
            BrokerChargeSourceComponent.id == source_component_id,
            BrokerChargeSourceComponent.evidence_id == evidence.id,
        )
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if component is None or component.status != "VERIFIED":
        raise ValueError("A VERIFIED broker source component is required for variance comparison.")
    if component.component_name != payload.get("component"):
        raise ValueError("Estimate and actual source component names do not match.")
    if component.currency != payload.get("currency") or component.currency != "INR":
        raise ValueError("Estimate and actual source component currencies do not match.")
    if component.reviewed_by_user_id is None or component.reviewed_at is None:
        raise ValueError("Actual source component review provenance is missing.")
    if component.reviewed_by_user_id == component.extracted_by_user_id:
        raise ValueError("Actual source component requires independent review.")
    if not component.eligible_fill_ids_json:
        raise ValueError("Actual source component must have a reviewed eligible-fill manifest.")
    comparison_scope = str(payload.get("comparison_scope", snapshot.comparison_scope or "TRADE_FILL"))
    if comparison_scope not in {"TRADE_FILL", "ORDER_FILL_SET"}:
        raise ValueError("Estimate snapshot comparison scope is unsupported.")
    source_trade_record_id = payload.get("source_trade_record_id")
    try:
        manifest_ids = json.loads(component.eligible_fill_ids_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Actual eligible-fill manifest is invalid.") from exc
    if (
        not isinstance(manifest_ids, list)
        or any(not isinstance(value, str) for value in manifest_ids)
        or manifest_ids != sorted(set(manifest_ids))
    ):
        raise ValueError("Actual eligible-fill manifest must be a canonical sorted unique fill set.")
    try:
        manifest_ids = [str(UUID(value)) for value in manifest_ids]
    except (TypeError, ValueError) as exc:
        raise ValueError("Actual eligible-fill manifest contains an invalid fill ID.") from exc
    canonical_manifest_json = json.dumps(manifest_ids, separators=(",", ":"))
    manifest_digest = hashlib.sha256(canonical_manifest_json.encode("utf-8")).hexdigest()
    if (
        canonical_manifest_json != component.eligible_fill_ids_json
        or component.eligible_fill_set_sha256 != manifest_digest
    ):
        raise ValueError("Actual eligible-fill manifest digest does not match its canonical fill set.")

    if comparison_scope == "TRADE_FILL":
        if not isinstance(source_trade_record_id, str):
            raise ValueError("Single-fill estimate snapshot must identify the exact broker fill.")
        try:
            expected_fill_ids = [str(UUID(source_trade_record_id))]
        except (TypeError, ValueError) as exc:
            raise ValueError("Estimate fill identity is invalid.") from exc
        snapshot_fill_json = payload.get("source_fill_ids_json")
        snapshot_fill_digest = payload.get("source_fill_set_sha256")
        expected_json = json.dumps(expected_fill_ids, separators=(",", ":"))
        expected_digest = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        if snapshot_fill_json is not None and snapshot_fill_json != expected_json:
            raise ValueError("Single-fill estimate snapshot fill manifest is inconsistent.")
        if snapshot_fill_digest is not None and snapshot_fill_digest != expected_digest:
            raise ValueError("Single-fill estimate snapshot fill-set digest is invalid.")
    else:
        if source_trade_record_id is not None:
            raise ValueError("Order-fill-set estimate must not identify only one source fill.")
        try:
            snapshot_fill_ids = json.loads(payload["source_fill_ids_json"])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Order-fill-set estimate requires a canonical exact fill manifest.") from exc
        if (
            not isinstance(snapshot_fill_ids, list)
            or not snapshot_fill_ids
            or any(not isinstance(value, str) for value in snapshot_fill_ids)
            or snapshot_fill_ids != sorted(set(snapshot_fill_ids))
        ):
            raise ValueError("Order-fill-set estimate manifest must be sorted, unique, and nonempty.")
        try:
            expected_fill_ids = [str(UUID(value)) for value in snapshot_fill_ids]
        except (TypeError, ValueError) as exc:
            raise ValueError("Order-fill-set estimate contains an invalid fill ID.") from exc
        expected_json = json.dumps(expected_fill_ids, separators=(",", ":"))
        expected_digest = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        if payload["source_fill_ids_json"] != expected_json or payload.get("source_fill_set_sha256") != expected_digest:
            raise ValueError("Order-fill-set estimate fill manifest or digest is invalid.")
        if snapshot.comparison_scope != comparison_scope or snapshot.source_fill_ids_json != expected_json or snapshot.source_fill_set_sha256 != expected_digest:
            raise ValueError("Persisted order-fill-set scope metadata does not match its immutable snapshot.")
    if manifest_ids != expected_fill_ids:
        raise ValueError("Actual source component fill set does not exactly match the estimate comparison scope.")
    source_fill_set_sha256 = manifest_digest
    if evidence.reviewed_by_user_id != component.reviewed_by_user_id:
        raise ValueError("Evidence and source-component reviewer provenance do not match.")
    if connection.broker.casefold() != str(payload.get("broker", "")).casefold():
        raise ValueError("Tariff estimate broker does not match the reviewed actual evidence connection.")
    trades = (
        db.query(BrokerTradeRecord)
        .filter(
            BrokerTradeRecord.id.in_([UUID(fill_id) for fill_id in expected_fill_ids]),
            BrokerTradeRecord.broker_connection_id == evidence.broker_connection_id,
        )
        .order_by(BrokerTradeRecord.id)
        .with_for_update()
        .populate_existing()
        .all()
    )
    if len(trades) != len(expected_fill_ids) or {str(trade.id) for trade in trades} != set(expected_fill_ids):
        raise ValueError("Estimate fill set is not fully present in the reviewed evidence broker connection.")
    if len({str(trade.broker_order_ref_id) for trade in trades}) != 1:
        raise ValueError("Order-fill-set estimate contains fills from different broker orders.")
    if payload.get("source_kind") == "UPSTOX_BROKERAGE_API_ESTIMATE":
        # Upstox's calculator is order-input based. Only compare it with reviewed
        # evidence when the exact request quantity, price, side and instrument match
        # the locked fill manifest; otherwise a plausible-looking variance is unsafe.
        if payload.get("api_endpoint") != "/v2/charges/brokerage" or payload.get("api_version") != "2.0":
            raise ValueError("Upstox API estimate endpoint/version provenance is invalid.")
        request_json = payload.get("api_request_json")
        try:
            request_parameters = json.loads(request_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Upstox API estimate request provenance is invalid.") from exc
        required_parameters = {"instrument_token", "quantity", "product", "transaction_type", "price"}
        if (
            not isinstance(request_parameters, dict)
            or set(request_parameters) != required_parameters
            or json.dumps(request_parameters, sort_keys=True, separators=(",", ":"), ensure_ascii=False) != request_json
        ):
            raise ValueError("Upstox API estimate request provenance is not canonical.")
        response_digest = payload.get("api_response_sha256")
        if (
            not isinstance(response_digest, str)
            or len(response_digest) != 64
            or any(ch not in "0123456789abcdef" for ch in response_digest)
            or response_digest != payload.get("source_sha256")
        ):
            raise ValueError("Upstox API estimate response digest is invalid.")
        try:
            request_quantity = int(request_parameters["quantity"])
            request_price = Decimal(str(request_parameters["price"]))
        except (TypeError, ValueError, ArithmeticError) as exc:
            raise ValueError("Upstox API estimate quantity/price provenance is invalid.") from exc
        if request_quantity <= 0 or not request_price.is_finite() or request_price <= 0:
            raise ValueError("Upstox API estimate quantity/price provenance must be positive.")
        if str(request_parameters["transaction_type"]).upper() != str(payload.get("transaction_side", "")).upper():
            raise ValueError("Upstox API request side does not match estimate transaction side.")
        if sum(trade.quantity for trade in trades) != request_quantity:
            raise ValueError("Upstox API estimate quantity does not match the exact reviewed fill set.")
        if any(trade.instrument_token != str(request_parameters["instrument_token"]) for trade in trades):
            raise ValueError("Upstox API estimate instrument does not match every reviewed fill.")
        if any(Decimal(trade.price) != request_price for trade in trades):
            raise ValueError("Upstox API estimate price does not match every reviewed fill.")
    expected_side = str(payload.get("transaction_side", "")).upper()
    if any(trade.side != expected_side for trade in trades):
        raise ValueError("Tariff estimate transaction side does not match every identified broker fill.")
    try:
        estimate_trade_date = date.fromisoformat(str(payload.get("trade_date", "")))
        actual_trade_dates = {datetime.fromisoformat(trade.exchange_timestamp).date() for trade in trades}
    except (TypeError, ValueError) as exc:
        raise ValueError("Tariff estimate or broker fill trade date is invalid.") from exc
    if actual_trade_dates != {estimate_trade_date}:
        raise ValueError("Tariff estimate trade date does not match every identified broker fill.")
    if component.source_sha256 != evidence.source_sha256:
        raise ValueError("Actual source component fingerprint does not match contract-note evidence.")
    if not evidence.storage_key:
        raise ValueError("Original contract-note document is unavailable.")
    try:
        read_verified_document(
            root=settings.BROKER_CHARGE_DOCUMENT_ROOT,
            storage_key=evidence.storage_key,
            expected_sha256=evidence.source_sha256,
            expected_size=evidence.byte_size,
        )
    except ValueError as exc:
        raise ValueError("Contract-note source integrity check failed.") from exc

    try:
        actual = Decimal(component.source_amount).quantize(CENT)
    except (ArithmeticError, ValueError) as exc:
        raise ValueError("Actual source component amount is invalid.") from exc
    if not actual.is_finite() or actual < 0:
        raise ValueError("Actual source component amount must be finite and nonnegative.")
    estimated = estimated.quantize(CENT, rounding=ROUND_HALF_UP)
    variance = (actual - estimated).quantize(CENT, rounding=ROUND_HALF_UP)
    variance_percent = (
        (variance / estimated * Decimal("100")).quantize(PERCENT_SCALE, rounding=ROUND_HALF_UP)
        if estimated != 0 else None
    )

    existing = (
        db.query(TariffEstimateVarianceRecord)
        .filter(
            TariffEstimateVarianceRecord.estimate_snapshot_id == snapshot.id,
            TariffEstimateVarianceRecord.source_component_id == component.id,
        )
        .with_for_update()
        .first()
    )
    if existing is not None:
        return _existing_or_conflict(
            existing, snapshot=snapshot, component=component, evidence=evidence,
            estimated=estimated, actual=actual, variance=variance,
            variance_percent=variance_percent,
            comparison_scope=comparison_scope, source_fill_set_sha256=source_fill_set_sha256,
            allow_legacy_digest="comparison_scope" not in payload,
        ), "EXACT_REPLAY"

    record = TariffEstimateVarianceRecord(
        estimate_snapshot_id=snapshot.id,
        source_component_id=component.id,
        evidence_id=evidence.id,
        component_name=component.component_name,
        estimate_snapshot_sha256=snapshot.snapshot_sha256,
        evidence_source_sha256=evidence.source_sha256,
        estimated_amount=estimated,
        actual_amount=actual,
        variance_amount=variance,
        variance_percent=variance_percent,
        currency="INR",
        status="VARIANCE_ONLY",
        comparison_scope=comparison_scope,
        source_fill_set_sha256=source_fill_set_sha256,
    )
    try:
        with db.begin_nested():
            db.add(record)
            db.flush()
    except IntegrityError:
        existing = (
            db.query(TariffEstimateVarianceRecord)
            .filter(
                TariffEstimateVarianceRecord.estimate_snapshot_id == snapshot.id,
                TariffEstimateVarianceRecord.source_component_id == component.id,
            )
            .with_for_update()
            .first()
        )
        if existing is None:
            raise
        return _existing_or_conflict(
            existing, snapshot=snapshot, component=component, evidence=evidence,
            estimated=estimated, actual=actual, variance=variance,
            variance_percent=variance_percent,
            comparison_scope=comparison_scope, source_fill_set_sha256=source_fill_set_sha256,
            allow_legacy_digest="comparison_scope" not in payload,
        ), "EXACT_REPLAY"

    return record, "CREATED"
