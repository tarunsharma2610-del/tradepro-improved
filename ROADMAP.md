## Phase 3 verified checkpoint — 21 October 2026

- **Verified code/test HEAD:** `d3aee27ae72253ceec72a30e244fd88fdc719cd1`; exact-head [Backend CI run 39603039152](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39603039152) passed **475 tests, 1 warning in 30.22s**, the broker-write boundary guard, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks.
- Phase 3 live-fill accounting now rejects a single staged fill above the local order quantity and rejects cumulative accounted fills across broker child orders above the local order quantity. Regression coverage includes both cases, including proof that rejected fills create no execution and do not mutate the live position.
- The concurrent-promotion replay integrity fix and changed-fill replay regression remain included in this code checkpoint.
- **Phase 3 is in progress, not complete.** This checkpoint proves the listed code and CI checks only; continue the remaining accounting correctness, idempotency, crash/retry and audit review before phase closure.
- Keep live broker submission, automatic accounting promotion, and automatic scheduling disabled. The original `Tradepro` repository remains untouched. Phase 2 remains closed.
- This is the current checkpoint summary. Older checkpoint notes below are retained as historical audit trail and must not be treated as newer than this entry.

---

## Current verified checkpoint — 21 October 2026

- **Last verified code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- **Last verified documentation checkpoint before this status refresh:** `391dfefc9580abf9537ee659877578033baae4fd`; exact-head backend CI [run 39568264419](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39568264419) passed.
- The Phase 2 audit covers the dependency/port matrix, broker-fill workflow boundary, idempotency and rollback, reconciliation crash recovery, transaction-level lease fencing, slow persistence, 20 concurrent expiry-boundary renewal/reclaim races, and official Upstox current-day API semantics.
- Official Upstox V2 [order-book](https://upstox.com/developer/api-documentation/get-order-book/) and [get-trades-for-day](https://upstox.com/developer/api-documentation/get-trade-history/) endpoints are current-day endpoints without documented pagination parameters. Historical trades use a separate [paginated API](https://upstox.com/developer/api-documentation/get-historical-trades/); it is not wired into the Phase 2 worker.
- **Phase 2 technical checklist is complete.** Before any Phase 3 work, require a passing exact-head CI run for the then-current `main` and explicit user approval; never infer a later commit is green from an earlier run.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

---

## Current verified checkpoint — 21 October 2026

- **Verified code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- **Previously verified documentation checkpoint:** `a2e639f61e2c50070deb26d1a9a0741545c9737d`; exact-head backend CI [run 39568011689](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39568011689) passed. This is historical evidence for that SHA; every new commit still requires its own exact-head CI.
- The slow-persistence/lease-race audit is complete: the PostgreSQL row-lock test proves reclaim waits while a fenced write transaction is open; `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` passed 20 concurrent expiry-boundary renewal/reclaim races. Expired owners cannot renew, and ownership generation/token advance is verified.
- Official Upstox V2 [order-book](https://upstox.com/developer/api-documentation/get-order-book/) and [get-trades-for-day](https://upstox.com/developer/api-documentation/get-trade-history/) endpoints are current-day endpoints without documented pagination parameters. Historical trades use a separate [paginated API](https://upstox.com/developer/api-documentation/get-historical-trades/); it is not wired into the Phase 2 worker.
- Phase 2 technical audit and scope reconciliation are complete. Keep Phase 3 blocked until this final documentation commit's exact-head CI passes. Do not enable live broker submission, automatic accounting promotion or automatic scheduling. The original `Tradepro` repository remains untouched.

------

<!-- Historical checkpoint retained for audit trail; superseded by the current verified checkpoint above. -->
> **Latest verified checkpoint — 21 October 2026**
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; branch: `main`. Original `Tradepro` repository remains protected and untouched.
> - Latest code/test commit: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration checks. Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
> - Documentation audit commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da` passed [CI run 39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828).
> - Phase 2 checkpoint complete through atomic run/lease finalization, stale-run and cancellation recovery, lease-loss fencing, five-record renewal, and incomplete-summary warnings.
> - **Historical next-task note — completed:** slow persistence and 20-round concurrent expiry-boundary renewal/reclaim tests passed CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386).
> - Deferred safety-branch work remains tracked in `SAFETY_BRANCH_PORT_MATRIX.md`; no wholesale branch merge. Keep live broker submission and automatic accounting promotion disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`.
>
> The CI status above refers to the stated code and documentation commits. This documentation refresh will create a new commit and trigger its own CI run; do not call that new run passed until GitHub reports success.

# Tradepro Improved — Roadmap and Release Gates

Last reviewed: 2026-10-21
Scope: this repository only. The original `Tradepro` repository must remain untouched.

## Current verified checkpoint

- User-approved live-order idempotency/reconciliation design is implemented partially for Phase 1: [LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md).
- Architecture, safeguards, README, audit, project instructions and progress tracker link to the design.
- Phase 1 records/repository/tests are on `main`; latest verified Phase 1 code checkpoint `dd36b48a92057ad50618f6f9941f908832c9cea3` passed [workflow 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046), **215 tests passed, 1 warning**. The Phase 2 normalization foundation is now on `main` at test commit `b37452210bf07ad03acee1495e0627fae1378582`; [workflow 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091) passed **247 tests, 1 warning**, including SQLite and PostgreSQL 16 reversible migration checks.
- The code checkpoint adds Phase 1 durable storage/repository safeguards and tests only. It does not implement live submission or reconciliation, does not run a production migration and does not prove live trading readiness.

## Status summary

| Workstream | Status | Evidence / next gate |
|---|---|---|
| Paper execution and existing safeguards | Existing functionality; preserve | Keep regression tests proving paper path cannot call live broker placement |
| Instrument-master snapshot validation | Implemented and regression-tested; operational sync was disposable/in-memory | Repeat verified staging sync before deployment; never mutate production from an incomplete snapshot |
| Upstox V3 WebSocket authorization/reconnect protections | Partial implementation and unit/regression coverage | Real authorized session test remains open; shared stream state across workers remains open |
| Portfolio-wide risk controls | Existing configurable controls, still require deployment-aware review | Confirm atomic reservations, exposure semantics and user-adjustable thresholds; don't represent cost-basis/realized-loss checks as mark-to-market broker margin |
| Durable live-order idempotency | Phase 1 partially implemented; CI green for latest code checkpoint | Add concurrency/race tests and cross-database migration review; no broker submission |
| Broker order/trade reconciliation | Phase 2 read-only worker + durable run summaries + deduplicated manual-review issue records implemented and CI-tested; operator UI/API and real-account verification remain gated | Worker uses only the fixed-path GET-only Upstox client, user-scoped connection/token validation, lease, bounded retry, idempotent fill/status repositories and count-only durable run summaries. No write endpoint, scheduler, live submission or accounting updates. |
| Live submission orchestration | Not implemented / disabled | Sandbox-only workflow after prior phases pass |
| Production deployment verification | Incomplete | Backup-restored staging migration against actual DB engine, rollback/restore drill and operational runbook |

## Ordered roadmap

### Gate 0 — Design review (complete — user approved 2026-10-17)
- Read [PROJECT_INSTRUCTIONS.md](PROJECT_INSTRUCTIONS.md), [ARCHITECTURE.md](ARCHITECTURE.md), [LIVE_TRADING_SAFEGUARDS.md](LIVE_TRADING_SAFEGUARDS.md), [AUDIT_REPORT.md](AUDIT_REPORT.md), and [LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md).
- Confirm order-field canonicalization, supported Upstox products/order varieties, broker tag limits, order-history/trade API semantics and status mapping against current official docs.
- User explicitly approved `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`; approval is recorded in `PROGRESS.md`. This authorizes Phase 1 durable storage/repository safeguards only, not live-order submission.

### Gate 1 — Durable records only (no broker POST) — in progress
- [x] Additive SQLAlchemy records and Alembic migration for live intents, audit events, dispatch/outbox and broker-fill identities.
- [x] Unique idempotency key scoped to user/broker connection, canonical JSON payload hash, same-key/same-payload reuse and same-key/different-payload conflict.
- [x] Transactionally persist intent + initial event + outbox; enforce portfolio and broker-connection ownership in the repository.
- [x] Focused repository tests and clean SQLite Alembic migration run passed in GitHub Actions: [run 39043177545](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39043177545), 210 tests passed, 1 warning.
- [x] Add rollback atomicity test and a deterministic independent-session simulation of a competing unique-key winner; repository recovery returns the committed winner.
- [x] Validate order snapshots and audit event details as finite JSON and reject credential-like keys (nested access/refresh tokens, secrets, passwords, API keys, authorization headers and cookies); regression tests pass.
- [x] Add simultaneous same-key creation coverage using two independent PostgreSQL sessions and a barrier that forces both requests past an initial empty lookup; [workflow 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046) passed.
- [x] CI verifies clean SQLite and PostgreSQL 16 upgrade → downgrade of revision `202610170002` → re-upgrade: [run 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046).
- [ ] Verify upgrade/downgrade and constraints against a backup-restored staging copy of the actual deployment DB engine. No production migration has run.
- Scope boundary: no worker, API route or code path submits/cancels/reconciles broker orders in this phase.

### Gate 2 — Reconciliation-only workflow — repository foundation implemented; broker integration remains open
- [x] Add pure normalization for documented Upstox order book/details/history statuses and required fields; preserve raw status and route unknown/inconsistent records to review. Tested in [run 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091).
- [x] Add pure strict intent matcher: scope candidates to the authenticated broker connection, prefer an existing broker order ID, otherwise require one exact broker tag and exact instrument/side/type/quantity/product plus applicable price fields. Multiple candidates, cross-connection candidates, economic mismatches and unknown/contradictory broker states are not auto-linked. Tests passed in [run 39050424898](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050424898).
- [x] Add repository-only status transition persistence with an allowlist of state transitions, optimistic version/state compare-and-set, broker-order-ID uniqueness handling, atomic audit event, credential-field validation and idempotent same-state no-op. [Run 39050941218](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050941218) passed 261 tests, 1 warning, plus SQLite/PostgreSQL 16 reversible migrations.
- [x] Add pure Upstox per-order trade normalizer using documented `trade_id`, `order_id`, `instrument_token`, `transaction_type`, `quantity`, `average_price` and `exchange_timestamp`; unknown/malformed fields are rejected. [Run 39052075052](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052075052).
- [x] Add repository-only `record_broker_fill()` keyed by broker connection + stable trade ID; atomically persist fill and linked intent audit event; identical replays are no-ops, conflicting replays fail closed, and cross-connection intent linking is rejected. [Run 39052203329](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052203329) passed 274 tests.
- [x] Validate each linked fill against the already broker-ID-linked intent: instrument, side, order type, product, positive integer requested quantity, per-fill/aggregate quantity ceilings, and limit/stop-limit price protection. Reject fills before persistence when any check fails. [Run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770) passed 279 tests, 1 warning, plus SQLite/PostgreSQL 16 migration checks.
- [x] Validate linked fills against the intent snapshot (instrument/side/product/type, linked broker order ID, integer order quantity, aggregate quantity ceiling and limit-price protection); safely link previously unmatched fills later after revalidation. [Run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921) passed 281 tests, 1 warning.
- [x] Reconcile out-of-order status/fill observations against persisted fill evidence. Stale active states cannot erase partial/full trade evidence; partial fills plus cancellation are represented as `PARTIALLY_FILLED_CANCELLED`; conflicting full/partial or reject/fill evidence is quarantined as `RECONCILIATION_REQUIRED`. [Run 39056392873](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056392873) passed 294 tests, 1 warning, with SQLite/PostgreSQL 16 migration checks.
- [x] Implement the read-only worker in `backend/app/services/live_order_reconciliation_worker.py`: validates user-owned Upstox connection and usable token, claims/renews/completes the per-connection lease, uses only the GET-only client, applies bounded retry, normalizes daily trades and order-book records, strictly matches intents, persists unmatched fill identities, links verified fills, resolves state against trade evidence, and returns safe summary counts. No worker schedule/API trigger is wired, and CI uses mocks only.
- Remaining: add durable operator-facing run summaries/manual-review queue, confirm order/trade pagination and session/day boundaries against current official API responses, cover sliced orders, and plan a read-only sandbox verification. Current worker rejects invalid envelopes, stops on token/permission errors, retries bounded transient failures, and records unmatched fills without linking. It does not calculate positions or update local Order/Execution rows.
- No order-placement call in this phase.

### Gate 3 — Disabled sandbox submission workflow
- Transactionally persist intent, risk decision, audit and outbox before network I/O.
- Unknown submission after timeout/crash is reconciled; never blindly retry an ambiguous POST.
- Test crashes before/after broker acceptance, concurrent workers, rate limits, token expiry, rejection and cancellation races with mocks/sandbox only.
- Global live-submit switch stays hard-disabled in deployed configuration.

### Gate 4 — Operational readiness
- Verify account kill switch, portfolio risk recheck/reservation, alerts, safe audit redaction, monitoring, backup/restore, migration rollback and incident runbook.
- Verify real authenticated market-data stream separately; stream verification is not order-path certification.
- Resolve process-local WebSocket state before using multiple API workers.

### Gate 5 — Explicit controlled release
- Requires successful prior gates, official API contract verification, broker/account configuration, applicable compliance review and explicit user authorization.
- Start with a limited manually confirmed pilot and low risk limits. No autonomous live rollout by default.

## Completion/reporting rules

- After every meaningful change, update `PROGRESS.md`; update `AUDIT_REPORT.md`, `README.md`, `ARCHITECTURE.md` and safeguards when the verified behavior or safety boundary changes.
- Commit changes to `tradepro-improved` and verify the exact commit SHA and GitHub Actions result. A successful older workflow does not validate a newer commit.
- Distinguish implemented, unit-tested, sandbox-tested, staging-verified and production-verified states. Never claim a real Upstox session or order test without evidence.
- Keep live trading disabled until all release gates and explicit authorization are complete.


### Read-only reconciliation client — implementation started
- [x] Added `backend/app/brokers/upstox/reconciliation_client.py`, a narrow fixed-path GET-only client for order book, order details, order history by order ID/tag, and per-order trades. It exposes no place/modify/cancel methods and classifies 401/403/429/5xx/network/timeout/non-JSON errors without returning response bodies.
- [x] Added contract tests for documented endpoints, query parameters, missing token, sanitized failures and absence of write methods. [Run 39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434) passed **309 tests, 1 warning**; SQLite/PostgreSQL 16 migration checks passed.
- [x] Implement worker orchestration, token/connection validation, bounded retries, job lease, order matching, fill import and safe in-memory summary counts. Verified with mocked worker tests; the code can make read-only GET calls only when explicitly invoked with a valid user-owned connection. It is not scheduled or wired into an API route.


### Worker lease foundation — implementation checkpoint
- [x] Added `LiveReconciliationLease` schema and reversible Alembic revision `202610170003` for one lease per broker connection.
- [x] Added `LiveReconciliationLeaseRepository` with bounded lease durations, atomic claims, expiry/reclaim, lease renewal, ownership checks and token-guarded completion. A stale worker cannot complete a newer worker's lease.
- [x] Added lease tests for contention, expiry/reclaim, stale-owner completion, renewal, cross-user ownership and invalid lease duration. [Run 39057273255](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39057273255) passed 318 tests, 1 warning; SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade passed.
- [x] Connect the lease to the read-only worker orchestration and add a PostgreSQL concurrency test proving only one simultaneous claim succeeds. [Lease concurrency test commit](https://github.com/tarunsharma2610-del/tradepro-improved/commit/bf0c2b707aaa023a961f899502ed9f2ae4d265a4).
- [x] Verify official API day-window semantics and document pagination boundaries; persistent run summaries and manual-review visibility are implemented. Official order-book and get-trades-for-day endpoints are current-day, with no documented pagination parameters. Historical trades use a separate paginated API that is not wired into this worker. No live/sandbox request was made.


### Latest Phase 2 worker verification — 2026-10-17
- Worker implementation: [`live_order_reconciliation_worker.py`](backend/app/services/live_order_reconciliation_worker.py), commit [`4ee8427`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/4ee8427f890f7c31021e30f7b36177e2f3f227c3). It is GET-only by dependency construction and is not automatically scheduled or wired to an API route.
- Regression coverage now includes successful matching/fill linking, repeat-run deduplication, cross-user rejection, busy lease, missing token, no mutation when either read fails, bounded transient retry and Retry-After, 403 no-retry, malformed envelope/data rejection, and UNKNOWN execution status recovery when later trade evidence arrives.
- Latest code test run [39058734080](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39058734080) passed **338 tests, 1 warning**; SQLite/PostgreSQL 16 reversible migration checks passed. No live Upstox request, order action, production migration or accounting update occurred.
- Historical Phase 2 status superseded: current-day API/session boundary has been checked against official Upstox documentation; see the current checkpoint at the top of this file. Historical-trade retrieval remains separate future work, not part of this worker's current-day contract.


### Durable reconciliation run summary checkpoint — 2026-10-17
- Added `LiveReconciliationRun`, migration `202610170004`, and `LiveReconciliationRunRepository`; worker now persists a count-only summary and sanitized status/error category for each leased run.
- Test commit [`0e69fb2`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/0e69fb2efea692f2f675604ef3312cb1954ecc39) passed [run 39059271937](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059271937): **340 passed, 1 warning**, with SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks.
- The run summary contains only known non-negative counters; no broker payload, token, header or exception text is stored. A run left in `RUNNING` after process crash is visible as incomplete, but automatic stale-run recovery and operator review UI remain future work.


### Durable manual-review issue checkpoint — 2026-10-17
- Added `LiveReconciliationIssue`, migration `202610170005`, and `LiveReconciliationIssueRepository`; the worker records safe, deduplicated issues for unmatched orders, malformed order/trade rows, trade persistence conflicts, fill-link conflicts and status-transition conflicts.
- Exact latest code commit [`71b5668`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/71b5668533f0461c12374319e496665cbda7e61c) passed [run 39059749652](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059749652): **342 passed, 1 warning**, plus SQLite/PostgreSQL 16 reversible migrations. An earlier run failed because normalization errors were caught by the persistence-conflict branch; that was fixed by separating normalization from persistence, and the latest exact commit is green.
- Historical checkpoint superseded: run summaries and safe review issues are exposed through owner-scoped read API/UI; stale-run recovery and crash-boundary tests are covered. A privileged issue-resolution workflow and historical-trade API integration remain separate future work. No real broker request/order action or accounting update occurred.


### Owner-scoped reconciliation read API checkpoint — 2026-10-17
- Added run and issue list endpoints, typed response schemas and a query repository; queries always scope by authenticated `user_id`, with optional connection/status/type filters and a hard maximum limit of 100.
- Added HTTP tests for unauthenticated rejection, cross-user isolation, connection filtering, status filtering, invalid status/limit and safe response fields. Exact code commit [`f65b4ba`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/f65b4ba20ce9a1dacfe40580d8042cd98f36c19f) passed [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705): **345 passed, 1 warning**, plus SQLite/PostgreSQL 16 reversible migrations.
- The API is read-only: no issue resolution, run trigger, broker call or order action is exposed. Frontend UI and historical trade window support remain open.


### Reconciliation review UI checkpoint — 2026-10-17
- Added `frontend/app/reconciliation/page.tsx` and dashboard navigation link. The page lists recent safe run summaries and issues from the authenticated read API, supports issue-status filtering and manual refresh, and exposes no action to trigger reconciliation or resolve an issue.
- Exact commit [`e4343dc`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e4343dcb225c1f332b6c89399694d0a29a5df739) passed [frontend checks](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060564743) and [backend CI](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060564787): TypeScript/Next.js build succeeded; **345 backend tests passed, 1 warning**, and SQLite/PostgreSQL 16 migration checks passed.
- Remaining: issue-resolution workflow, stale-run recovery, crash-boundary tests and historical trade window/pagination support. No live broker request or order action occurred.


## Reference-repository audit — 2026-10-20

See [REFERENCE_REPOSITORY_AUDIT.md](REFERENCE_REPOSITORY_AUDIT.md) for the source-level comparison and integration priorities.

### Current priority gate — updated 2026-10-20

1. The recovered live-fill accounting files and supporting model/schema dependencies are present again. Revisions `202610180006` → `202610180007` → `202610180008` now form a valid chain after `202610170005`.
2. Code/test checkpoint [run 39475387511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39475387511) passed **355 tests, 1 warning**, including SQLite and PostgreSQL 16 upgrade → downgrade → re-upgrade checks.
3. This does not make live-fill accounting end-to-end complete: service is deliberately unregistered; ingestion, worker integration, shared live order/status accounting and real-account reconciliation remain outstanding.
4. Next: continue Phase 2 reconciliation release gates and crash/recovery/fill-linkage checks. Integrate the service only through a separately reviewed and tested path.
5. Live order submission remains disabled; no real orders for testing. All work stays in `tradepro-improved`; original `Tradepro` remains untouched. Do not delete the recovered files without explicit user approval.


## Safety-branch port checkpoint — 2026-10-21

- Main code/test checkpoint `3f210e592c8aa2e643e536a04f186da8187bc06b`; [CI run 39480002328](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480002328) passed **431 tests, 1 warning**, with SQLite/PostgreSQL 16 reversible migration checks passing.
- Ported pure Upstox response parsing and isolated broker trade staging with tests. Staging rejects missing exchange timestamps and does not update executions, positions, portfolio cash, or local order status.
- See [`SAFETY_BRANCH_PORT_MATRIX.md`](SAFETY_BRANCH_PORT_MATRIX.md) for 21 safety-only test modules and dependency/port decisions. Branch test counts are not directly comparable because source and test trees differ.
- Next: audit and test child-order reconciliation/partial-fill aggregation; keep fill promotion and broker writes disabled until transaction, idempotency, recovery, and account-isolation gates pass.


## Cumulative fill-accounting guard — 2026-10-21

- Added aggregate per-child cap in `LiveFillAccountingService`: previously accounted executions plus the new trade cannot exceed the broker-confirmed child filled quantity.
- Added regression test for two distinct trade IDs attempting to overrun the same child fill total. Exact-head [run 39480669799](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480669799) passed **432 tests, 1 warning**, with SQLite/PostgreSQL 16 migration checks passing.
- Next architecture gate: reconcile the worker's `BrokerFillIdentity` intake with the staging/accounting path's `BrokerTradeRecord`; do not dual-write or connect them until idempotency and transaction boundaries are explicit.


## Child-order reconciliation port — 2026-10-21

- Ported child-order status/fill reconciliation with current-main schema compatibility. It validates the broker snapshot against durable staged trade quantities and weighted average price, locks the child row, rejects fill regressions/terminal-state conflicts, and updates only child status/fill quantity.
- Exact-head [run 39481385581](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581) passed **438 tests, 1 warning**, including SQLite/PostgreSQL 16 reversible migration checks.
- Remaining architecture gate: distinguish the intent-based `BrokerFillIdentity` workflow from the manual Order `BrokerTradeRecord`/`BrokerOrder` workflow, or design an explicit transaction-safe bridge. No live order submission or automatic accounting promotion is enabled.


## Phase 2 resume point — 2026-10-21

Latest main-branch checkpoint is `0ce59a7965e3e96a425fa8ae30c841eb0cb755bc`; exact-head [CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228) passed 461 backend tests, the broker-write guard, and SQLite/PostgreSQL 16 migration cycles. Phase 2 now covers stale-run recovery, incomplete-summary UI warning, inconsistent lease-state rejection, and eventual recovery after lease-release/summary-persistence crash. Next: review transaction atomicity between lease completion and run-summary finish and add lost-lease/ordering tests. Keep live submission and automatic accounting promotion disabled.


## Phase 2 resume point — 2026-10-21

Latest verified code/test HEAD `8f967adaa2328f16a0a08a104c3ec394e62f9310`; exact-head [CI run 39553655005](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553655005) passed 463 backend tests, the broker-write guard, and SQLite/PostgreSQL 16 migration cycles. Terminal run-summary persistence and lease release are now atomic; stale owners are marked `LEASE_LOST` without releasing a newer owner's lease. Next: audit cancellation, unexpected exceptions, and lease renewal/expiry concurrency. Keep live submission and automatic accounting promotion disabled.


## Phase 2 resume point — 2026-10-21

Historical checkpoint superseded by the lease-race audit: code/test HEAD `00ee9bad0e962d92244da6f63da1e46ba058ad6f` passed 472 tests, source guard and SQLite/PostgreSQL 16 migration checks in [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386). Large-batch expiry and renewal races are now covered. Keep live submission and automatic accounting promotion disabled.


## Phase 2 resume point — 2026-10-21

Historical checkpoint superseded: renewal remains every five records; UI marks `LEASE_LOST` and `WORKER_INTERRUPTED` summaries incomplete. Slow-record/high-volume expiry races and transaction-level fencing were subsequently audited and passed in CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386). Keep live submission/accounting promotion disabled.
