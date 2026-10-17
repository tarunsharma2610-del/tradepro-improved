# Tradepro Improved — Roadmap and Release Gates

Last reviewed: 2026-10-17
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
| Broker order/trade reconciliation | Phase 2 read-only worker implemented and mocked-CI-tested; operational invocation and real-account verification remain gated | Worker uses only the fixed-path GET-only Upstox client, user-scoped connection/token validation, lease, bounded retry and idempotent fill/status repositories. No write endpoint, scheduler, live submission or accounting updates. |
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
- [ ] Verify official API pagination/day-window semantics, add operator-facing persistent run summaries and manual-review visibility, then consider an explicitly approved read-only sandbox pass.


### Latest Phase 2 worker verification — 2026-10-17
- Worker implementation: [`live_order_reconciliation_worker.py`](backend/app/services/live_order_reconciliation_worker.py), commit [`4ee8427`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/4ee8427f890f7c31021e30f7b36177e2f3f227c3). It is GET-only by dependency construction and is not automatically scheduled or wired to an API route.
- Regression coverage now includes successful matching/fill linking, repeat-run deduplication, cross-user rejection, busy lease, missing token, no mutation when either read fails, bounded transient retry and Retry-After, 403 no-retry, malformed envelope/data rejection, and UNKNOWN execution status recovery when later trade evidence arrives.
- Latest code test run [39058734080](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39058734080) passed **338 tests, 1 warning**; SQLite/PostgreSQL 16 reversible migration checks passed. No live Upstox request, order action, production migration or accounting update occurred.
- Remaining Phase 2 work is operational hardening and current official API pagination/session-boundary verification; live order submission is a separate later phase and remains disabled.
