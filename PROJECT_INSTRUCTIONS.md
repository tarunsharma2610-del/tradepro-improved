# Tradepro Improved — Persistent Working Instructions

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
