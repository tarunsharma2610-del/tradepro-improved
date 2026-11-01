# Phase 4 — Durable Quote Ordering and Transactional Watermark Policy

Date: 1 November 2026
Repository: `tarunsharma2610-del/tradepro-improved`
Scope: PAPER trailing-stop evaluation only

## Status

Design decision and implementation contract. This document does not claim that durable quote ordering has been implemented. The current `PaperStopEventIntakeService` validates receive-time freshness and locks portfolio → strategy → position, but it updates `current_watermark` without persisting the last evaluated quote epoch/version/timestamps. The scanner and Redis consumer maintain in-memory ordering high-water marks; those are not durable across worker restarts or independent replicas.

No dispatcher-to-execution wiring is authorized by this design alone.

## Existing facts verified at PR #9 head 4547fc55edbf5904694b4cc3ee7ea92d6dec65ea

- Redis publisher atomically increments a per-user/instrument version and stores the authoritative snapshot plus a Pub/Sub wake-up event.
- The publisher reuses the existing epoch while the Redis version key exists. If that key is absent (including Redis state loss/expiry), it generates a new opaque UUID epoch.
- Redis snapshots carry `epoch`, `version`, `received_at`, and `exchange_timestamp_ms`.
- `MarketScanObservation` carries the epoch/version and both timestamps.
- `MarketScanner` rejects non-increasing versions within the same epoch in its process-local state.
- `RedisMarketQuoteConsumer` also keeps process-local epoch/version high-water marks.
- `PaperStopEventIntakeService` validates receive-time freshness and locks portfolio → strategy → position before calculating and writing the shared trailing-stop watermark.
- `Strategy` already has `current_watermark` and `last_evaluated_at`; do not repurpose `last_evaluated_at`, which is a separate engine timestamp and does not encode quote identity.

## Required durable strategy high-water mark

Add nullable engine-managed fields to `strategies`:

- `last_quote_epoch`: opaque producer epoch, bounded to the Redis epoch field limit (128 characters).
- `last_quote_version`: positive integer for the last accepted quote in that epoch.
- `last_quote_received_at`: timezone-aware receive timestamp from the validated observation.
- `last_quote_exchange_timestamp_ms`: positive exchange timestamp in milliseconds.

All four fields are either all NULL (no quote accepted yet) or all populated. Add database checks for this all-null/all-present invariant, positive version, and positive exchange timestamp. Use a migration with a safe nullable backfill (existing strategies start with no quote high-water mark). Do not fabricate historical quote identities.

## Ordering and epoch policy

Epochs are opaque UUID-like generation identifiers; they are not sortable. Never compare epoch strings lexicographically and never accept an epoch change merely because it differs.

Under the existing portfolio → strategy → position row locks:

1. Validate owner, active PAPER portfolio/strategy relationship, instrument, non-flat position, positive finite LTP, timezone-aware receive timestamp, and configured receive-time freshness.
2. For the same epoch, accept only if version is strictly greater than the persisted version. Also reject a receive timestamp earlier than the persisted receive timestamp or an exchange timestamp earlier than the persisted exchange timestamp.
3. For a different epoch, treat it as a generation transition only if the incoming receive timestamp is strictly later than the persisted receive timestamp and the exchange timestamp is not earlier. This allows a Redis restart/version-counter reset while rejecting delayed observations from the prior generation.
4. If no prior high-water mark exists, accept the already validated observation.
5. Persist the accepted epoch, version, receive timestamp and exchange timestamp in the same transaction as the trailing-stop watermark update and, when triggered, durable stop-event creation.
6. A rejected duplicate, delayed or out-of-order observation must not change the quote high-water mark or trailing-stop watermark.
7. If the database transaction rolls back, neither watermark nor quote high-water mark nor stop event may persist.

Use a consistent UTC representation for comparisons. Normalize SQLite-returned naive `DateTime(timezone=True)` values as UTC at the persistence boundary, matching the existing claim-lease timezone handling. Do not weaken freshness checks to make ordering tests pass.

### Important limitation of this policy

This policy relies on `received_at` being assigned by the trusted Upstox/Redis ingestion path and carried unchanged into `MarketScanObservation`. It is not a cryptographic authenticity mechanism. The PAPER consumer must never accept user-supplied quote observations or trust Pub/Sub payload quote values; it must consume validated authoritative Redis snapshots.

## Transaction and lock contract

- Keep the repository's established lock order: portfolio → strategy → position. The durable quote high-water mark is stored on the locked strategy row.
- Resolve and validate the user-owned portfolio and active strategy/instrument association before applying any state change.
- Preserve the existing shared `check_trailing_stop` function; do not create another trailing-stop calculation.
- Update strategy quote high-water mark and `current_watermark` in the same caller-owned transaction.
- If a stop is hit, create the durable idempotent `PaperStopEvent` in that same transaction. The event's unique strategy/event/epoch/version key remains a second line of idempotency, not a replacement for quote ordering.
- Do not commit inside the intake service. The supervised consumer owns commit/rollback and must hand off only committed claims to the existing PAPER execution service.
- Do not perform database access, strategy evaluation, broker work or order execution inside the Redis callback.

## Required regression tests

### Unit/service tests

- First quote initializes all four high-water fields and seeds the existing watermark.
- Same-epoch higher version is accepted.
- Same-epoch duplicate and lower version are rejected without mutating either watermark.
- Higher version with older receive timestamp is rejected.
- Higher version with older exchange timestamp is rejected.
- New epoch with strictly newer receive timestamp and nondecreasing exchange timestamp is accepted and resets the version baseline.
- Old epoch delivered after a newer epoch is rejected.
- New epoch with equal/older receive timestamp is rejected.
- New epoch with older exchange timestamp is rejected.
- Malformed/missing epoch, version, receive timestamp or exchange timestamp fails closed.
- Stale/future receive timestamps and invalid prices are rejected.
- No-position and ambiguous shared-position ownership do not create events.
- Triggering quote updates quote identity, trailing watermark and stop event atomically.
- Injected claim/flush/commit failure rolls back both high-water marks and event creation.
- SQLite naive timestamp reloads are normalized safely; PostgreSQL timestamps remain timezone-aware.

### PostgreSQL 16 concurrency tests

- Two independent sessions process the same quote concurrently: one accepted state transition, at most one stop event.
- Two sessions process versions N and N+1 concurrently: persisted state ends at N+1; N cannot overwrite it after waiting on locks.
- A delayed lower version racing a newer version cannot regress either watermark.
- A new epoch racing a delayed old-epoch quote cannot be overwritten by the old quote.
- Rollback after lock acquisition leaves the previous durable high-water mark intact.
- Verify the actual final database state from a fresh session; do not rely on SQLAlchemy identity-map objects.

## Acceptance gates before dispatcher integration

1. Implement the migration, model fields, locked ordering check and atomic updates.
2. Add all service/unit tests above.
3. Add PostgreSQL 16 concurrency tests using independent sessions/connections.
4. Add supervised consumer lifecycle tests for retry/backoff, cancellation, shutdown and queue accounting.
5. Run exact-head Backend CI: full pytest, broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, and synthetic restore/evidence checks.
6. Review the exact PR head and confirm PR #9 remains Draft/unmerged.
7. Only after all gates pass, connect synchronous scanner → bounded dispatcher publish and a separately supervised PAPER-only consumer.

## Safety

- PAPER only. This work must not invoke live broker place/modify/cancel operations.
- The PAPER/LIVE product target remains one application with selectable modes and independent balances, orders, positions and P&L. This design does not claim that mode separation is complete.
- Live broker order writes remain disabled.
- PR #9 remains Draft/unmerged.
- Work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope and must not be modified.
