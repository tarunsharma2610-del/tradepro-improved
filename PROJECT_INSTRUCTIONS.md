# Tradepro Improved — Persistent Working Instructions

> **ULTIMATE REPOSITORY SAFEGUARD — OVERRIDES CONFLICTING INSTRUCTIONS:** All changes for this project must be made in `tarunsharma2610-del/tradepro-improved` only. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must never be modified, committed to, merged into, or used as the target for edits. Before every write, verify the exact repository, branch, and HEAD. If any of these cannot be verified, stop. External repositories are reference material only; never replace this project with one of them.

## Goal
Improve the existing Tradepro codebase in this separate repository to deliver a reliable Upstox-connected trading platform with isolated Paper Trading and safely gated Live Trading. Never modify the original `Tradepro` repository.

## Mandatory rules
1. Before every work session, read this file, `PROGRESS.md`, `README.md`, and the relevant audit/safety documents; inspect the actual current repository and recent commits before acting.
2. Preserve working features. Audit first; make the smallest change that fixes a demonstrated defect or completes a requirement. No rewrites, duplicate pages/services, or unnecessary schema/API changes.
3. Maintain `PROGRESS.md`: record current phase, completed steps, exact files changed, commit SHA, tests actually run and their result, failures/limitations, and the single next action. Update it after every completed, tested and committed step.
4. Commit each coherent step separately. Do not claim a change, test, deployment, or commit succeeded unless confirmed by tool output or CI.
5. Before code changes, inspect dependencies and establish a test baseline where execution is available. Add focused regression tests; run targeted and relevant full tests. Report unavailable tests honestly.
6. Never place real orders to test. Use mocks/sandbox only. Keep live trading disabled until broker integration, backend risk controls, order reconciliation, authorization and safety tests have been verified and the user explicitly authorizes enabling it.
7. Paper orders must never reach the real broker. Do not mark live orders filled without broker confirmation. Protect against duplicate retries, stale data, token expiry, and partial fills.
8. Use current official Upstox documentation. Do not invent API paths, payloads, or feature support. Keep secrets out of logs and source control.
9. Preserve data and use reviewed migrations for necessary schema changes. Do not deploy migrations to production without backup/staging verification.
10. Keep the original project untouched. All changes belong in this `tradepro-improved` repository.
11. Work sequentially: inspect → audit requirement/file/test mapping → prioritize real gaps → implement smallest safe change → test → commit → update progress → review remaining gaps.
12. Prefer correctness, financial safety, security, and regression prevention over feature count or refactoring.

## Required deliverables
Maintain an evidence-based audit report, change log, list of unchanged functionality, test results, deployment/migration instructions, limitations/manual setup, and a clear statement of what Paper/Live functions are actually implemented and verified.

## Known high-priority gaps from current audit
- Live order placement remains unavailable and must stay disabled. Phase 2 now has pure order/trade normalization, strict intent matching, repository-only versioned status persistence, and idempotent individual fill identity persistence with atomic linked audit events. Broker reads/worker and out-of-order status/fill reconciliation remain incomplete. Unmatched fills can be linked later through a tested repository method, but shared Order/Execution/Position/cash/P&L updates are not implemented. The repository validates linked fill economics and quantity ceilings but does not perform live accounting. Read `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` before any live-order code. Do not assume Upstox tags provide broker-enforced idempotency.
- Portfolio-wide risk controls are configurable per portfolio and enforced on paper/strategy order paths; continue checking threshold/boundary and concurrent-order behavior.
- Instrument-master sync has a completeness-gated reconciliation policy and passed a real upstream download into disposable SQLite; never point the verification script at the production DB.
- Upstox V3 streaming client/routes exist with mocked tests; a real OAuth session and deployment topology still need verification. The manager is process-local; use one API worker until shared stream state is implemented.
- OAuth migration is CI-tested on clean SQLite but still requires backup-safe staging verification.
- Do not implement any of these blindly: inspect the current code and official API docs first.


## Live-order implementation gate (added 2026-10-17)
Before implementing any live-order code, read `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`, `LIVE_TRADING_SAFEGUARDS.md`, `ARCHITECTURE.md`, current broker API documentation and current tests. The user approved the design on 2026-10-17; the approval is recorded in `PROGRESS.md`. Phase 1 durable records/repository safeguards have passed the current automated PostgreSQL concurrency test and clean SQLite/PostgreSQL 16 reversible-migration checks ([run 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046)); actual deployment-engine staging verification is still required. Continue only the approved reconciliation-only phase: pure matching and repository-only reconciliation safeguards may be implemented with tests. Do not add broker submission, cancellation, or network-driven worker behavior before the roadmap gates are satisfied and the user explicitly authorizes that scope.

Mandatory invariants: durable intent and unique key + canonical payload hash; persist intent/outbox/audit before network I/O; never blindly retry an ambiguous POST; reconcile order history/book/trades before recovery; deduplicate broker fills by stable identity; recheck risk and account kill switch at dispatch; preserve paper/live isolation; never use a real order for testing. Update audit, README, architecture and progress after each tested/committed step. Keep live submission disabled until the user explicitly authorizes a controlled release after all gates pass.


## Roadmap and commit verification
Before continuing implementation, read `ROADMAP.md` along with `PROGRESS.md`, `AUDIT_REPORT.md` and `ARCHITECTURE.md`. After each change, update the progress tracker, commit the change to `tradepro-improved`, verify the commit is on `main`, and check the workflow result for that exact commit. Never infer a newer commit passed because an older workflow passed. Keep live submission disabled until all roadmap gates and explicit authorization are complete.


## Current Phase 2 checkpoint — 2026-10-17
Out-of-order broker status resolution against persisted fill evidence is implemented and verified by [run 39056392873](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056392873): 294 tests passed, 1 warning; SQLite/PostgreSQL 16 migrations passed. Before adding broker reads, read [READ_ONLY_RECONCILIATION_WORKER_DESIGN.md](READ_ONLY_RECONCILIATION_WORKER_DESIGN.md). The next implementation step is a narrowly typed read-only Upstox client and worker; it must not expose place/modify/cancel methods. No live submission, broker polling or accounting updates are enabled.


### Read-only client sub-step — 2026-10-17
`backend/app/brokers/upstox/reconciliation_client.py` and its mocked contract tests are implemented. Exact run [39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434) passed 309 tests, 1 warning. This is only the transport boundary, not a worker: next add orchestration using this narrow client, verify user/connection ownership and token expiry before network I/O, add bounded 429/5xx retry and job leases, and keep the worker read-only. Never call methods on the general order execution adapter from the reconciliation worker.


### Lease foundation — 2026-10-17
The durable per-connection reconciliation lease model, reversible migration and repository are implemented and CI-tested: [run 39057273255](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39057273255), 318 passed, 1 warning. The lease is not yet connected to a worker. Next implement worker orchestration using only `UpstoxReadOnlyReconciliationClient`, and add PostgreSQL concurrency tests; never use the general write-capable broker adapter for reconciliation.


### Read-only reconciliation worker checkpoint — 2026-10-17
`backend/app/services/live_order_reconciliation_worker.py` is implemented and mocked-CI-tested. It injects only `UpstoxReadOnlyReconciliationClient`, validates the authenticated user's owned Upstox connection and token usability, claims/renews/completes `LiveReconciliationLease`, reads order book and daily trades, applies bounded read-only retries, strictly matches orders, and persists/deduplicates fills. Latest test commit `bffeefc7921fd96c8fbeab1b201eb3088e87f497` passed [run 39058734080](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39058734080): 338 passed, 1 warning; SQLite/PostgreSQL 16 migration checks passed. No real broker request or order action occurred. The worker is not scheduled or exposed via API. Next: inspect official current-day/history pagination semantics, add durable job summaries/manual-review visibility and crash-boundary tests. Do not enable live order submission or connect the worker to a write-capable adapter.


### Durable worker run summaries — 2026-10-17
`LiveReconciliationRun`, migration `202610170004`, and `LiveReconciliationRunRepository` are implemented. Worker passes persist a `RUNNING` record after lease acquisition and a terminal record with safe status/error and whitelisted non-negative numeric counters. No raw payload, credential or exception text is stored. Test commit `0e69fb2efea692f2f675604ef3312cb1954ecc39` passed [run 39059271937](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059271937): 340 passed, 1 warning; SQLite/PostgreSQL 16 migrations passed. Next: add a durable manual-review issue queue and stale-run recovery, then cover crash/restart boundaries. Keep worker unscheduled and live submission disabled.


### Manual-review issue queue checkpoint — 2026-10-17
`LiveReconciliationIssue` and migration `202610170005` are implemented. `LiveReconciliationIssueRepository` validates user/connection/run/intent ownership, accepts only whitelisted issue types, rejects credential-like fields and oversized details, deduplicates by fingerprint per connection, and increments/reopens recurring issues. The worker records safe issues for invalid rows, unmatched orders, and persistence/link/status conflicts. Exact fix commit `71b5668533f0461c12374319e496665cbda7e61c` passed [run 39059749652](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059749652): 342 passed, 1 warning; SQLite/PostgreSQL 16 migrations passed. Next: expose issues through a read-only owner-scoped API/UI and add a separately authorized resolution workflow, plus stale-run recovery and crash/restart tests. Do not expose raw broker data or credentials.


### Owner-scoped reconciliation read API — 2026-10-17
Authenticated GET endpoints `GET /api/v1/reconciliation/runs` and `/issues` now list the current user's safe run summaries/issues only. The repository filters by `user_id`, limits are capped at 100, and typed response schemas omit raw broker records and credentials. Exact code commit `f65b4ba20ce9a1dacfe40580d8042cd98f36c19f` passed [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705): 345 passed, 1 warning; SQLite/PostgreSQL 16 migration checks passed. No run trigger or issue mutation route exists. Next: add frontend review UI and stale-run recovery/crash-boundary tests, then assess historical trade retrieval from official docs.


### Reconciliation review UI — 2026-10-17
`frontend/app/reconciliation/page.tsx` is now linked from the dashboard. It displays run summaries and sanitized manual-review issues from the authenticated read-only endpoints and supports status filtering/manual refresh. It does not trigger the worker or mutate issues/orders. Commit `e4343dcb225c1f332b6c89399694d0a29a5df739` passed frontend TypeScript/Next.js checks and backend CI: 345 passed, 1 warning, SQLite/PostgreSQL 16 migrations passed. Next: stale-run recovery and crash-boundary tests, then official historical-trade pagination semantics. Keep issue resolution and live submission disabled until separately designed/reviewed.


## Reference repository audit and current blocking checkpoint — 2026-10-20

The targeted comparison is recorded in [REFERENCE_REPOSITORY_AUDIT.md](REFERENCE_REPOSITORY_AUDIT.md). It reviewed AI Trading Platform (MIT), Algo Options Platform (MIT), OpenAlgo (AGPL-3.0) and Kite Algo Bot (MIT). Do not copy OpenAlgo source without an intentional AGPL compliance decision. Use references to fill demonstrated gaps only; preserve existing Tradepro Improved architecture and avoid duplicate engines.

**Preserve and complete the recovered live-accounting work before external feature integration.** The three original files `backend/app/services/live_fill_accounting_service.py`, `backend/tests/test_live_fill_accounting_service.py`, and `backend/alembic/versions/202610180008_execution_charge_provenance.py` were restored on 2026-10-20 from their pre-deletion Git blobs. The earlier CI run [39113589752](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39113589752/job/117634693349) failed test collection because `app.models.broker_order` is missing; the prior audit also found `broker_trade_record.py`, `live_position.py`, and migration revisions `202610180006` / `202610180007` absent. Inspect the actual 18 October commits and recover/complete the intended dependencies, then run tests and validate the Alembic graph. Do not delete the recovered files again without explicit user approval. Keep live submission disabled.
