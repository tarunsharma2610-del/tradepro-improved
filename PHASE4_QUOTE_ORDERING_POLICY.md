# Phase 4 — Durable Quote Ordering and Transactional Watermark Policy

Date: 1 November 2026
Repository: `tarunsharma2610-del/tradepro-improved`
Scope: PAPER trailing-stop evaluation only

## Status

Core durable quote-ordering implementation, PostgreSQL 16 epoch-race/rollback coverage, supervised dispatch worker, and database quote-identity constraints are implemented and CI-verified. Multi-worker dispatcher lifecycle tests are now being expanded; scanner-to-PAPER evaluator wiring remains gated and is not enabled.

No dispatcher-to-execution wiring is authorized by this implementation alone.

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


## Implementation update — 1 November 2026

Commits:
- `ac93bc36d3fc218488e8b4945021638ce6b8153c`: nullable quote high-water migration.
- `29a4e56d34d5f2fc9b38dbd4b6d970cada2ccaa0`: Strategy model fields.
- `40862c282b936aaf09f52280b4f7de0cb4982d7b`: locked PAPER intake ordering enforcement.
- `32b213952cc56e0a3677298ada18afea03ec0e3e`: first service regression set.
- `c6b00ee86272976e160125a84c6449e73b144556`: exchange timestamp freshness guard.
- `fd525c3041642bf62e8b9db8fd360e46ae15356b`: timestamp regression and freshness tests.

The first service regression set covers durable identity persistence, duplicate/lower-version rejection, accepted newer epoch and rejection of a delayed prior epoch. Additional tests cover receive/exchange timestamp regression and stale exchange timestamps. The current CI run was started against commit `32b213952cc56e0a3677298ada18afea03ec0e3e`, before the final exchange-time freshness fix and its tests; a final exact-head run is therefore required.

Still required before dispatcher integration:
- PostgreSQL 16 independent-session races for duplicate/N/N+1/epoch transition.
- Transaction rollback tests proving neither quote identity, trailing watermark nor event persists on failure.
- Partial persisted-state and malformed identity tests.
- Consumer supervision, cancellation, bounded queue and retry/backoff tests.


## PostgreSQL 16 locking correction — 1 November 2026

Backend CI #41294699288 exposed PostgreSQL's restriction against applying an unrestricted `FOR UPDATE` to the nullable side of the outer join generated by Strategy's joined Instrument relationship. Both new independent-session concurrency tests failed at this lock query; 1,413 other tests passed.

Fix committed as `821fd427948c3af226e66848effcc2c6c1499193`: the strategy lock now uses SQLAlchemy `.with_for_update(of=Strategy)`, retaining the intended strategy-row lock while excluding the nullable joined Instrument side. This does not change the portfolio → strategy → position lock order.

Backend CI #41294894211 is running against the exact fix commit. Until it passes, the PostgreSQL concurrency tests and this fix remain unverified. The duplicate-trigger concurrency assertion must be reviewed after the PostgreSQL lock issue is cleared, because uniqueness conflict handling is a separate behavior to verify.


## Follow-up PostgreSQL locking correction — 1 November 2026

The first scoped Strategy lock exposed the same PostgreSQL outer-join restriction on Position: its joined-loaded optional Instrument relationship caused the Position query's unrestricted `FOR UPDATE` to fail. The intake service now uses `.with_for_update(of=Position)` as well, matching the existing claim service's scoped Position lock. The intended portfolio → strategy → position lock order is unchanged.

Fix commit: `2dc2d5b0beb59e4b6992e125c70787c410a915a1`. Exact-head Backend CI is required; no passing result is claimed yet.


## Identity-map concurrency correction — 1 November 2026

The latest PostgreSQL run passed the scoped Strategy and Position locks, and the duplicate-trigger race passed, but the N/N+1 race still exposed a real stale-state issue: the initial strategy discovery query had already loaded Strategy objects into the SQLAlchemy Session identity map before workers waited on the portfolio lock. The later `SELECT ... FOR UPDATE` could return that already-loaded object without refreshing its attributes, so a worker could compare against stale quote version data even after it acquired the row lock.

Fix committed as `572b14aea20481b9c86b1220fe136d9274b422e8`: the locked Strategy query now calls `.populate_existing()` before `.with_for_update(of=Strategy)`, ensuring the locked row refreshes from the latest committed database state. This preserves the lock order and makes the race test assert the intended invariant rather than scheduler order.

The next exact-head CI must confirm the N/N+1 race and all existing checks. No green result is claimed yet.


## PostgreSQL 16 epoch-race and rollback coverage — 1 November 2026

After the stale ORM identity-map correction, Backend CI #41296561087 passed on implementation commit `572b14aea20481b9c86b1220fe136d9274b422e8`; documentation-head CI #41296585343 also passed on `3240f9308e240c8912d10181e86e31b5365bbff8`. Both included PostgreSQL 16 migration and restore gates, broker-write boundary enforcement, and the full backend pytest suite.

Additional independent-session PostgreSQL tests are now submitted in commit `a15f55919f5393080654f7d996da182e7b39665d`:
- Race a delayed quote from an old WebSocket epoch against a quote from a newer epoch; final durable state must retain the new epoch and its version.
- Inject a stop-claim persistence failure, roll back the transaction, and verify through a separate database session that quote identity, watermark and stop events were not partially committed.

These new tests are not yet CI-verified. Await the exact-head Backend CI result before treating epoch-race and PostgreSQL rollback coverage as complete.


## PostgreSQL epoch-race and rollback CI verified — 1 November 2026

The independent-session delayed-old-epoch race and injected PostgreSQL transaction rollback tests passed in Backend CI #41296851101 on exact test commit `a15f55919f5393080654f7d996da182e7b39665d`. The documentation-head Backend CI #41296869835 also passed on `7ba2782e36f69d2109a2b1fdde814e06e5a04366`. Both completed the full backend suite, broker-write boundary, SQLite and PostgreSQL 16 migration cycle, and synthetic restore drill.

## Supervised quote-dispatch worker — submitted, CI pending

A PAPER-only async dispatch worker was added:
- Handles one user/instrument key at a time through the existing bounded single-flight dispatcher.
- Retries handler exceptions with exponential backoff capped by configuration.
- Retains key ownership during retry so a second worker cannot race the same key; newer quotes coalesce behind the in-flight item.
- Cancellation during handler work or retry delay releases the in-flight item, preferring a newer coalesced quote.
- Exposes processed and failure counters.
- Does not submit broker orders and is not wired into the application lifespan or scanner yet.

Implementation and tests are being added on the Phase 4 branch. Tests cover transient failure/retry, cancellation/requeue, newer-quote preference at shutdown, and invalid backoff bounds. Exact-head CI must pass before this worker is considered verified or integrated.


## Supervised dispatcher worker CI verified — 1 November 2026

Backend CI #41297279152 passed on worker test commit `40ad92f69fc888702349cfecc72163a5580d19a5`; documentation-head CI #41297295118 passed on `9bc7891b2763bbe21b5ba192d9945b554b52d13a`. The first worker draft had a flaky retry test caused by the mocked sleep yielding through the patched asyncio.sleep; the test was corrected. The worker retains per-key single-flight ownership through retry backoff, and cancellation releases the in-flight key for safe replay. The successful documentation-head run completed all backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration cycle and synthetic restore.

## Persisted quote identity database guard tests — submitted, CI pending

Added tests to verify the migration's `ck_strategies_quote_identity_complete` constraint:
- Reject partially populated quote identity tuples.
- Reject empty epoch, non-positive quote version and non-positive exchange timestamp.
- Accept the fully NULL tuple before the first quote.

Test commit: `700567dc2cf7ada0764ddb0f642818a3ed56a863`. Exact-head Backend CI must pass before this integrity coverage is considered verified.


## Database integrity test correction — 1 November 2026

Backend CI #41297560366 (test commit `700567dc2cf7ada0764ddb0f642818a3ed56a863`) and documentation CI #41297573966 (documentation commit `9aaeab39a71394ef6bb80458a71631a1309c1482`) failed in the new quote-identity constraint tests: 1,422 passed and 7 failed because the SQLite unit-test fixture builds its schema from SQLAlchemy ORM metadata (`Base.metadata.create_all`) rather than running Alembic migrations. The check existed in the Alembic migration but was absent from ORM metadata, so those test-created tables did not contain it.

Correction submitted in commit `0b7535b3640ad4747a90cde8ae114c7aebac2ad5`: declare the same named `CheckConstraint` in `Strategy.__table_args__`. This keeps ORM-created test schemas aligned with the migration-created production schema. The Alembic migration remains the production schema-change mechanism. Exact-head CI must now verify both SQLite metadata-created tables and PostgreSQL migration behavior; no green status is assumed yet.


## Quote identity ORM/migration constraint alignment verified — 1 November 2026

The database integrity correction is now green:
- Backend CI #41297858951 passed on model fix commit `0b7535b3640ad4747a90cde8ae114c7aebac2ad5`.
- Documentation-head Backend CI #41297870322 passed on exact branch head `8c7b34259c4cf181f15a0b1a93b14d6ea916742e`.
- Both runs completed the full pytest suite, broker-write boundary enforcement, SQLite migration round-trip, PostgreSQL 16 migration round-trip, and synthetic PostgreSQL/document-volume restore.

The earlier seven failures were caused by the SQLite test fixture using ORM `create_all` without the Alembic-only CHECK constraint. The model now declares the same named `ck_strategies_quote_identity_complete` constraint; the migration remains in place for deployed schema upgrades.

## Multi-worker dispatcher lifecycle tests — submitted, CI pending

Added two worker-pool tests:
- Two independent supervised worker tasks share one dispatcher and must never process the same user/instrument concurrently; a newer quote is coalesced until the first worker acknowledges.
- A two-worker pool is bounded by unique keys, rejects overflow, and reaches zero pending/in-flight items with queue completion accounting after successful acknowledgement.

Test commit: `36aa713fa298985870be1ba57069c809be0138a5`, followed by deterministic acknowledgement synchronization in `afaea5d434ac1a3209e4240ee955d10aee45205d`. These tests exercise multiple tasks in one process; they do not prove distributed cross-process ownership. Durable cross-replica protection remains the PostgreSQL claim-token service. Exact-head CI is required before marking this lifecycle expansion verified.


## Multi-worker single-flight test refinement — 1 November 2026

Backend CI #41298564267 failed with 1,430 passed and one timeout in `test_two_workers_never_process_same_user_instrument_concurrently`. The failure showed the test still assumed worker affinity: after the first handler acknowledges, the dispatcher immediately requeues a coalesced successor and either available worker may consume it. The dispatcher does not promise FIFO worker assignment, and no such guarantee is required for same-key single-flight.

Correction submitted in commit `17ab764afc5eb7c601fddd256f7476aaef9efe0c`: both workers use a shared handler that tracks active invocations; the test holds version 1, publishes version 2, asserts version 2 cannot enter while version 1 is active, then allows either worker to process the successor and asserts maximum same-key concurrency is exactly one. It also verifies queue completion and zero pending/in-flight keys before cancelling idle workers. No production code changed. Exact-head CI remains pending.


## Scanner-to-dispatcher adapter submitted — 1 November 2026

The multi-worker lifecycle correction passed:
- Backend CI #41299089659 passed on `17ab764afc5eb7c601fddd256f7476aaef9efe0c`.
- Documentation-head Backend CI #41299105020 passed on `c161bfdac7461a24c2e75896481bf53423f38b4d`.

A narrow in-memory adapter is now added:
- `backend/app/services/market_scan_dispatch_pipeline.py` calls the existing fail-closed `MarketScanner`, then publishes accepted observations to the existing bounded `MarketQuoteDispatcher`.
- The callback can be supplied as `RedisMarketQuoteWorker(on_quote=pipeline.on_quote)`.
- It exposes counters for accepted observations, rejected quotes and dispatch-capacity drops.
- It has no database session, no strategy evaluation, no order writes, and no broker client.
- Tests cover valid conversion, cross-user/invalid/duplicate rejection, per-user isolation and bounded-queue overflow.

Implementation commit: `4a98c34c6a7caa4e09e6f93548cab8c05dc8970e`.
Test commit: `53c53cb8bb5c8e67bf19a8a5ee63d720ecf18400`.
Exact-head Backend CI is pending. This is a reusable adapter only: it is not yet wired into API startup or a deployed worker process. The next review must decide and test dedicated worker lifecycle/supervision before runtime activation. PAPER strategy evaluation and LIVE execution remain disabled at this boundary.


### Redis callback integration test added — 1 November 2026

The adapter is now exercised through the actual `RedisMarketQuoteWorker(on_quote=pipeline.on_quote)` callback contract using a validated snapshot fixture. The test asserts that the user-scoped Redis worker callback produces the expected scanner observation and dispatches it under the correct user/instrument key, then acknowledges it and checks pending/in-flight cleanup.

Test commit: `466fbdd43a5c49008d59491226ebba842b562691`. Exact-head CI is pending. This is an integration test of the callback boundary, not production worker activation: `app.worker` runtime wiring has not yet been changed. The existing periodic strategy evaluator continues to use its current scanner path until a dedicated dispatcher handler and safe transaction boundary are reviewed.


### Adapter unit-test CI passed; callback integration CI pending — 1 November 2026

- Backend CI #41299506942 passed on adapter test commit `53c53cb8bb5c8e67bf19a8a5ee63d720ecf18400`.
- Backend CI #41299613870 is running on Redis callback integration test commit `466fbdd43a5c49008d59491226ebba842b562691`.
- Documentation-head Backend CI #41299654388 is running on `731ed14c7bbcf09173fda885e56ad5b82bbc251b`.
- Earlier run #41299473379 on the first test draft failed; it is superseded by the corrected async test commit and passing #41299506942.
- Do not mark the callback integration or docs head verified until their exact-head runs are green.



## Phase 4 authoritative audit/status — 2 November 2026
This section supersedes older Phase 4 resume pointers where they conflict; older entries remain historical.
- Scope only tarunsharma2610-del/tradepro-improved, branch phase4/redis-market-data-publisher. PR #9 targets phase4/roadmap-progress-checkpoints and remains OPEN, Draft, unmerged. Original tarunsharma2610-del/Tradepro remains untouched.
- Latest verified code/test head before this docs repair: 654b0a5d2cb898a0b6dcd4dcb6556b0af6c2ccc2. Exact-head Backend CI #41398555424 PASSED on that SHA, including stale LIVE broker-position snapshot regression. Preceding commit 502303d2f2d9be1ed0ece0ecb5b280ed5f7db2e4 passed #41398528946.
- Earlier API/Redis safeguards passed: #41397210305 (3281618), #41397227429 (a65c463), #41397602437 (d01146f), #41397616502 (147d59b). Prior docs CI #41398105822 passed on 027850d; this docs sync needs its own exact-head CI.
### Completed, CI-backed Phase 4 scope
- PAPER is the only enabled execution path. Broker place_order/modify_order/cancel_order writes remain disabled; AST broker-write boundary runs in Backend CI.
- Mode-aware portfolio analytics and ownership/isolation checks are implemented. LIVE balance does not fall back to simulated starting capital; LIVE positions fail closed rather than exposing PAPER positions.
- Read-only Upstox LIVE funds, positions and holdings sync uses allocated owner-scoped broker connection and immutable portfolio/user/connection-bound snapshots. Failed sync retains prior snapshot and does not mutate PAPER accounting.
- Analytics Token storage/ownership/expiry controls, Upstox V3 stream lifecycle, feed-mode subscription/reconnect/startup recovery and SDK compatibility review have prior green CI.
- Redis publisher/consumer has user-scoped TTL snapshots, schema/version and epoch/version checks, atomic publishing, Pub/Sub notifications, real Redis tests, restart/recovery and independent process delivery tests.
- Worker-managed Redis consumer lifecycle, lease/replica coordination, scanner intake and 15-second scanner TTL are implemented. Scanner-to-PAPER trailing-stop evaluation consumes fresh user/instrument-scoped LTP while five-minute candles remain indicator source.
- Durable PAPER stop-event claim/state/lease/retry/recovery, PostgreSQL 16 concurrency tests, bounded dispatcher and PAPER worker wiring have prior green CI. Full end-to-end market-to-ledger acceptance remains outstanding.
- Read-only LIVE unrealized P&L API GET /api/v1/portfolios/{portfolio_id}/live-unrealized-pnl checks owner/mode/current allocation/snapshot binding, reads exact instrument keys through user-scoped Redis consumer, fails closed on stale/missing/invalid quotes and Redis outage, and does not mutate accounting.
- LIVE position snapshots missing timestamps, future-dated or older than 120 seconds are rejected. Exact-head CI #41398555424 passed.
### Remaining gates
1. Full authenticated LIVE P&L API integration test using real ephemeral Redis publisher/consumer in the same test flow (component-level Redis tests already exist).
2. Internal realized-P&L ledger and broker fill/trade reconciliation; keep broker daily P&L, broker realized P&L and internal lifetime realized P&L distinct.
3. Frontend LIVE read-only P&L display with separate realized/unrealized values, freshness and unavailable states.
4. Full Redis→scanner→dispatcher→durable stop claim→PAPER fill→ledger/position/cash end-to-end tests, including crashes, retries, duplicate/out-of-order events and competing exits.
5. Multi-user/multi-instrument load/backpressure, metrics/alerts, runbooks, worker recovery; production Oracle restore and credentialed Upstox smoke tests remain deployment gates.
6. LIVE order readiness is not achieved; any future write gateway needs separate design, deny-by-default authorization, idempotency, audit and explicit approval.
### Security audit status
- PHASE4_P0_BASELINE_AUDIT.md exists (29 Oct) but is a static source/workflow audit; it explicitly did not perform runtime or credentialed smoke testing.
- Existing controls include broker-write AST enforcement, ownership/mode checks, encrypted Analytics Token handling, Redis tenant namespacing/freshness, PostgreSQL concurrency, migration/restore CI and audit logging.
- Comprehensive Phase 4 security assessment is NOT COMPLETE. No verified full IDOR sweep, SAST/DAST report, dependency vulnerability scan, authenticated/independent penetration test or production configuration review is evidenced. Do not claim penetration-tested or production security-approved.
- Remaining security: endpoint authorization matrix and adversarial IDOR tests; secret redaction/storage review; rate-limit/abuse tests; dependency/SAST; DAST on safe staging; broker-write reachability tests; tenant isolation/load; backup/restore and incident response.
### Safeguards
PAPER only; LIVE place/modify/cancel writes disabled; PR #9 Draft/unmerged; no deployment or LIVE gateway activation authorized. After docs sync, run CI on exact new docs head before saving a green checkpoint.



## Phase 4 security remediation checkpoint — 2 November 2026
This is the latest security/code checkpoint and supersedes older Phase 4 security next-step statements where they conflict.
- Latest verified code/test head: 2a98a07a8516c4cca4a46f8a0f511afcb2159e74.
- Exact-head Backend CI #41400727799 PASSED: 1,549 passed, 1 warning. Full workflow includes pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore and evidence retention.
- Confirmed finding fixed: Redis-backed rate limits previously failed open on Redis errors. The limiter now returns HTTP 503 when Redis is unavailable; test now asserts fail-closed behavior. Commits 62b7bdbdde812ed89d9eb3189b44c7922a7e63d7 and fdd00da6cd58242e2fe0cbf720f9cd66ee306ff8.
- Confirmed finding fixed: MFA disable previously required only an authenticated session. It now requires password re-verification and, when MFA is enabled, a current TOTP. Schema/service/API/tests are in 19a99b8, c369bb0, e6306be and 2a98a07. Exact-head CI above verifies the complete change.
- The Phase 4 P0 baseline audit exists but was a static source/workflow review, not a penetration test. These two findings are remediated; comprehensive security assessment remains NOT COMPLETE.
- Remaining security work: endpoint-by-endpoint IDOR/authorization matrix and adversarial tests; secret/token redaction/storage review; dependency vulnerability scan and SAST; DAST against isolated staging; broker-write reachability review; abuse/rate-limit and replay testing; tenant-isolation/load testing; deployment/backup/incident-response review; independent penetration test before any LIVE broker write.
- Other Phase 4 gates remain: authenticated LIVE P&L API against real Redis integration test; internal realized-P&L ledger and broker fill reconciliation; frontend LIVE read-only P&L; full Redis-to-PAPER-stop-to-ledger end-to-end proof; multi-user load/backpressure and operational runbooks.
- PAPER execution only; LIVE broker place/modify/cancel writes disabled; PR #9 remains Draft/open/unmerged; original Tradepro remains untouched. No deployment or LIVE gateway activation authorized.


## Phase 4 authoritative audit synchronization — 2 November 2026

This is the current operational status; earlier entries remain historical.
- Repository `tarunsharma2610-del/tradepro-improved` only; branch `phase4/redis-market-data-publisher`; PR #9 targets `phase4/roadmap-progress-checkpoints`, OPEN/Draft/unmerged.
- Code/test head before this docs sync: `3ad06a045c16251b6daf1e2ec429837ddd390c59`; exact-head Backend CI #41402165142 PASSED: **1,550 passed, 1 warning**. Redis-backed pytest, broker-write guard, SQLite/PostgreSQL 16 migration round-trips, synthetic restore/evidence retention passed.
- New verified milestone: authenticated LIVE unrealized-P&L API test publishes a real user-scoped Redis quote and validates API P&L ₹40.00; accounting remains unchanged.
- Rate limiting now fails closed (HTTP 503) on Redis outage; MFA disable requires password re-verification and current TOTP when MFA is enabled. CI #41400727799 passed these remediations.
- Security audit status: **NOT COMPLETE**. Static baseline is not a penetration test. Remaining: endpoint IDOR/authorization matrix, cross-tenant adversarial tests, secret/token redaction, SAST/dependency scan, DAST, broker-write reachability, abuse/load tests, deployment hardening and independent penetration test.
- Remaining engineering: internal realized-P&L ledger/broker-fill reconciliation; frontend LIVE read-only P&L; Redis→scanner→dispatcher→durable PAPER stop→ledger end-to-end acceptance; multi-user load/backpressure, observability/runbooks; credentialed Upstox smoke test and production Oracle restore.
- PAPER remains the only enabled execution path; LIVE `place_order`, `modify_order`, `cancel_order` writes disabled. PR #9 stays Draft/unmerged. Original `tarunsharma2610-del/Tradepro` untouched.
- Documentation sync is not green until Backend CI passes on the final documentation head.


## Cross-tenant security regression checkpoint — 2 November 2026

- Added authenticated two-user regression coverage for unauthorized contract-note upload/download, source-component create/review/reject, reconciliation run/issue access, and broker-settings connection scoping. Foreign broker-connection identifiers must not expose or mutate another user's data.
- Exact PR-head Backend CI [#41404633900 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41404633900) on `e8f8783fc32a96e43e710289721992e077dc4d82`; PR #9 head matches this SHA. Pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic restore and evidence retention all passed.
- This verifies the new regression coverage, not a complete IDOR sweep or penetration test. Comprehensive security assessment remains NOT COMPLETE.
- Remaining security gates: endpoint authorization matrix, secret/token redaction/storage review, dependency scan/SAST, isolated-staging DAST, broker-write reachability, abuse/load tests, deployment/incident-response review and independent penetration test.
- PAPER mandatory; LIVE broker place/modify/cancel writes disabled; PR #9 OPEN/Draft/unmerged; original `tarunsharma2610-del/Tradepro` out of scope.


## Security scanning and dependency remediation checkpoint — 2 November 2026

- Added GitHub Actions workflow `.github/workflows/security-analysis.yml` with CodeQL Python static analysis and `pip-audit` over backend requirements. CodeQL [#41406851928](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41406851928) and dependency audit [#41406857558](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41406857558) passed on exact commit `8be6a0369c81a519c00712d69095b2ab3ceb5faa`; dependency audit reported zero known vulnerabilities for resolved backend dependencies.
- Remediated vulnerable Starlette `0.46.2` resolution by upgrading FastAPI to compatible `0.143.x`; CI resolved FastAPI `0.143.5` and Starlette `1.10.0`. Full backend compatibility verified, not assumed.
- Backend CI [#41406857547 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41406857547) on same SHA; pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore/evidence retention passed.
- Security audit remains incomplete: these checks do not replace endpoint IDOR coverage, secret/token redaction review, DAST, broker-write reachability, abuse/load testing, deployment hardening or independent penetration testing.
- Prior rate-limit fail-closed, MFA step-up and cross-tenant contract-note/reconciliation protections remain in place. PAPER mandatory; LIVE order writes disabled; PR #9 OPEN/Draft/unmerged; original Tradepro repository out of scope.


## Authentication hardening and security verification — 2 November 2026

- Hardened JWT creation: optional extra claims can no longer override reserved `sub`, `type`, `iat`, or `exp` claims. Added regression tests for each reserved claim and a positive test for non-reserved claims.
- Corrected stale rate-limiter documentation: Redis outage behavior is fail-closed with HTTP 503; it is not fail-open.
- Exact code commit verified: `4ebc24c0ae129cf53614cd58c46c41cc55a204ab`. Backend CI [#41408254466 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41408254466); CodeQL and Python dependency audit [#41408254462 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41408254462). All three checks passed on the same SHA.
- Dependency audit reported zero known vulnerabilities for resolved backend dependencies. Security assessment remains INCOMPLETE: remaining work includes endpoint IDOR matrix, secret/token redaction and storage review, staging DAST, broker-write reachability, abuse/load tests, deployment hardening and independent penetration testing.
- PAPER mandatory; LIVE broker place/modify/cancel writes disabled; PR #9 OPEN/Draft/unmerged; original `tarunsharma2610-del/Tradepro` strictly out of scope.


## Production bootstrap secret hardening — verified code checkpoint, 2 November 2026

- Production configuration now fails closed unless an explicit stable `SECRET_KEY` (minimum 32 characters) and `MASTER_ENCRYPTION_KEY` are configured. Development retains its local random fallback. Regression tests cover missing secrets, valid production configuration and development fallback.
- Verified code/test commit: `d6619a58cd585ef35b79126d866c90bb903cb890`. Backend CI [#41410058905](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41410058905) and Security analysis [#41410058894](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41410058894) passed on that exact SHA. Security workflow includes CodeQL and pip-audit; this is not a penetration-test claim.
- Earlier JWT reserved-claim hardening remains verified on `4ebc24c0ae129cf53614cd58c46c41cc55a204ab`: Backend CI #41408254466 and Security analysis #41408254462 passed on that exact SHA. Redis rate limiting remains fail-closed (HTTP 503) on Redis failure; MFA disable requires password re-verification and current TOTP when MFA is enabled.
- This is part of the exact 28-document maintained set from the JWT checkpoint. Current documentation head before this batch: `4083cb6dfd382f0dfe5802a1ebc1dbcf3beea873`. The resulting documentation commit requires exact-head Backend CI and Security analysis before it is called green.
- Security assessment remains INCOMPLETE: HTTPS/production CORS, secret rotation and recovery, authentication-session controls, endpoint-by-endpoint authorization/IDOR, secret/token storage and redaction, broker-write reachability, isolated-staging DAST, abuse/load testing, deployment/incident response and independent penetration testing remain open.
- Safeguards unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` untouched; PAPER mandatory for development/tests/unverified workflows; LIVE broker `place_order`, `modify_order`, `cancel_order` writes disabled; PR #9 remains OPEN/Draft/unmerged; no deployment or LIVE gateway activation authorized.


## 2 November 2026 — security checkpoint reconciliation

- Session-security implementation verified on PR #9 head `77f44c7299f5e7157a4cdb2f8dfe7fbbfb6c08c6`: Backend CI #41460334989 and Security analysis #41460334979 passed on that exact head. Persisted sessions, refresh-token rotation/replay rejection, logout revocation and reserved JWT `sid`/`jti` handling are covered by tests.
- Transactional key-rotation service implementation commit `960c099b53d4c8e41daeb4f5691bc0972d5fb7b2`: Backend CI #41456734039 and Security analysis #41456734074 passed. It covers encrypted broker credentials, OAuth access tokens, Upstox Analytics Tokens, platform settings and MFA secrets; unreadable ciphertext fails closed. No production keys/data were rotated or accessed.
- Docs CI on the final documentation head is still required before calling this checkpoint green.
- Security assessment remains incomplete: endpoint IDOR authorization matrix, secret/token redaction review, broker-write reachability, staging DAST, abuse/load and tenant-isolation tests, deployment/restore/incident-response review and independent penetration testing remain.
- PAPER mandatory; LIVE broker `place_order`, `modify_order`, `cancel_order` writes disabled; PR #9 OPEN/Draft/unmerged; original `tarunsharma2610-del/Tradepro` untouched.
