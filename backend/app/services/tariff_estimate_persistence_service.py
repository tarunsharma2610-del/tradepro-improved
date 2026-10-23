"""Transactional persistence for estimate-only tariff snapshots."""
from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tariff_estimate_snapshot_record import TariffEstimateSnapshotRecord
from app.services.tariff_estimate_snapshot import TariffEstimateSnapshot


def _existing_or_conflict(
    existing: TariffEstimateSnapshotRecord,
    snapshot: TariffEstimateSnapshot,
) -> TariffEstimateSnapshotRecord:
    if (
        existing.snapshot_sha256 != snapshot.snapshot_sha256
        or existing.snapshot_json != snapshot.canonical_json()
    ):
        raise ValueError("Conflicting tariff estimate replay; refusing silent overwrite.")
    return existing


def persist_tariff_estimate_snapshot(
    db: Session,
    snapshot: TariffEstimateSnapshot,
) -> tuple[TariffEstimateSnapshotRecord, str]:
    """Insert an immutable estimate or return its exact replay.

    The caller owns the outer transaction and commit. A database uniqueness
    constraint is the concurrency arbiter; nested transaction rollback keeps a
    duplicate insert from poisoning the caller's transaction.
    """
    existing = (
        db.query(TariffEstimateSnapshotRecord)
        .filter(TariffEstimateSnapshotRecord.idempotency_key == snapshot.idempotency_key)
        .with_for_update()
        .first()
    )
    if existing is not None:
        return _existing_or_conflict(existing, snapshot), "EXACT_REPLAY"

    record = TariffEstimateSnapshotRecord(
        idempotency_key=snapshot.idempotency_key,
        snapshot_sha256=snapshot.snapshot_sha256,
        snapshot_json=snapshot.canonical_json(),
        status="ESTIMATE_ONLY",
        comparison_scope=snapshot.comparison_scope,
        source_fill_ids_json=snapshot.source_fill_ids_json,
        source_fill_set_sha256=snapshot.source_fill_set_sha256,
    )
    try:
        with db.begin_nested():
            db.add(record)
            db.flush()
    except IntegrityError:
        # A concurrent transaction may have inserted this key after our read.
        existing = (
            db.query(TariffEstimateSnapshotRecord)
            .filter(TariffEstimateSnapshotRecord.idempotency_key == snapshot.idempotency_key)
            .with_for_update()
            .first()
        )
        if existing is None:
            raise
        return _existing_or_conflict(existing, snapshot), "EXACT_REPLAY"

    return record, "CREATED"
