"""Variance-only comparison of a tariff estimate with reviewed broker actual evidence.

This service does not promote charges or write per-fill allocation rows.
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.broker_charge_evidence import BrokerChargeEvidence
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
) -> TariffEstimateVarianceRecord:
    expected = (
        component.component_name,
        snapshot.snapshot_sha256,
        evidence.source_sha256,
        estimated,
        actual,
        variance,
        variance_percent,
    )
    actual_values = (
        existing.component_name,
        existing.estimate_snapshot_sha256,
        existing.evidence_source_sha256,
        Decimal(existing.estimated_amount),
        Decimal(existing.actual_amount),
        Decimal(existing.variance_amount),
        Decimal(existing.variance_percent) if existing.variance_percent is not None else None,
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
    snapshot = (
        db.query(TariffEstimateSnapshotRecord)
        .filter(TariffEstimateSnapshotRecord.id == estimate_snapshot_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
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

    component = (
        db.query(BrokerChargeSourceComponent)
        .filter(BrokerChargeSourceComponent.id == source_component_id)
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

    evidence = (
        db.query(BrokerChargeEvidence)
        .filter(BrokerChargeEvidence.id == component.evidence_id)
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
    if evidence.reviewed_by_user_id != component.reviewed_by_user_id:
        raise ValueError("Evidence and source-component reviewer provenance do not match.")
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
        ), "EXACT_REPLAY"

    return record, "CREATED"
