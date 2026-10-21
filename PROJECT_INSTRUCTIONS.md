## Phase 3 verified checkpoint — 21 October 2026

- **Verified code/test HEAD:** `06de3c10fa27ece1b35054a2cdd3b2362d8a068f`; exact-head [Backend CI run 39605379637](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39605379637) passed **481 tests, 1 warning in 32.58s**, the broker-write boundary guard, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks.
- Live-fill accounting rejects a single staged fill above the local order quantity, cumulative fills across broker child orders above that quantity, and fills mapped to a local order marked `REJECTED`. A `CANCELLED` order can still account a broker-confirmed partial fill without changing the local status.
- Exchange-time ordering is now fail-closed: later trades cannot be promoted while an earlier staged trade for the same broker connection/instrument remains unaccounted; an earlier trade arriving after a later execution was accounted is blocked for manual review. Same-time trades with different sides or prices are rejected as ambiguous. Broker trade ingestion and promotion share a connection-row lock to serialize this chronology check against normal staging.
- PostgreSQL concurrency regression coverage confirms separate child orders cannot concurrently overfill one local order. Regression tests also cover changed-fill replay, terminal order state, late/early trade chronology, and ambiguous timestamps.
- **Phase 3 is in progress, not complete.** Continue reviewing the explicit coordinator/identity design, charge provenance, replay conflicts, rollback, partial-fill, out-of-order and crash/restart acceptance criteria before phase closure.
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

------

## Current verified checkpoint — 21 October 2026

- **Latest CI-verified `main` HEAD:** `7798f03200ba823d51bdd359539594b38e9830e1`; exact-head backend CI [run 39567592850](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567592850) passed.
- **Latest code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard and SQLite/PostgreSQL 16 reversible migration checks.
- The slow-persistence/lease-race audit is complete: the PostgreSQL row-lock test proves reclaim waits while a fenced write transaction is open; `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` passed 20 concurrent expiry-boundary renewal/reclaim races. Expired owners cannot renew, and ownership generation/token advance is verified.
- Official Upstox V2 order-book and get-trades-for-day endpoints are current-day endpoints without documented pagination parameters. Historical trades are a separate paginated API; that API is not wired into the Phase 2 worker.
- **Current task:** synchronize the remaining historical architecture/roadmap/reference-audit notes. This documentation commit needs its own exact-head CI and a final stale-status scan before Phase 2 is formally closed. Phase 3 remains blocked until then.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

------

<!-- Authoritative checkpoint audit: 2026-10-21; supersedes older status notes below. -->
## Superseding current checkpoint — 21 October 2026

- Latest test commit: [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2), adding failed-commit rollback coverage. Exact-head backend CI [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests, 1 warning, the broker-write guard and SQLite/PostgreSQL 16 reversible migrations. Documentation HEAD `adb69aeb05b70ba4fa9095fc73d9dea033d31eec` passed [run 39565251793](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39565251793).
- Reconciliation crash recovery and per-write lease fencing are complete on the earlier verified checkpoint [39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808): 470 passed, 1 warning, source guard and SQLite/PostgreSQL 16 reversible migrations.
- Phase 2 workflow boundary: keep BrokerFillIdentity separate from manual BrokerTradeRecord; no bridge/dual-write. Follow SAFETY_BRANCH_PORT_MATRIX.md for phase-aware dependency decisions. Do not wholesale-merge the divergent safety branch or introduce real broker orders.
- Phase 2 engineering checks are verified. Complete the synchronized-documentation checkpoint and confirm its exact-head CI before starting Phase 3. Preserve PAPER defaults; live submission, automatic accounting promotion and scheduling remain disabled. Original Tradepro must remain untouched.

## Authoritative checkpoint audit — 21 October 2026

- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest repository HEAD before this audit update:** `a297b1a356c133aaca0ed10079eb5226c03b747b` — documentation-only commit `docs: synchronize Phase 2 status with passing CI evidence`.
- **Latest code/test commit:** `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Recorded exact-commit backend CI run [39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. Frontend run [39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
- **Previously verified documentation CI:** commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da`, run [39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828), backend job completed successfully. The later documentation-only commit `a297b1a356c133aaca0ed10079eb5226c03b747b` was found on `main`; CI for that exact HEAD was not independently established before this audit update. Do not infer exact-head CI success from an earlier commit.
- **Phase 2 checkpoint verified in project records:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent lease token/expiry rejection; five-record renewal boundary; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Historical audit disposition — superseded:** slow database persistence and high-volume lease-expiry/renewal races have now been tested. PostgreSQL CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed the slow-persistence lock test and the new 20-iteration concurrent expiry-boundary renewal/reclaim test. Do not reopen this audit unless a regression appears.
- **Safety constraints remain:** no real broker orders in tests; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled; keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.
- Older checkpoint entries below are retained as history, not current instructions. This top section is the authoritative current state. After this documentation commit, verify CI for its exact HEAD before treating the checkpoint audit as fully closed.

<!-- Latest verified status, updated 2026-10-21 -->
> **Latest verified checkpoint — 21 October 2026**
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; branch: `main`. Original `Tradepro` repository remains protected and untouched.
> - Latest code/test commit: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration checks. Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
> - Documentation audit commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da` passed [CI run 39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828).
> - Phase 2 checkpoint complete through atomic run/lease finalization, stale-run and cancellation recovery, lease-loss fencing, five-record renewal, and incomplete-summary warnings.
> - **Historical next-task note — completed:** audit slow persistence and high-volume lease-expiry races. See the current checkpoint at the top of this file and CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386).
> - Deferred safety-branch work remains tracked in `SAFETY_BRANCH_PORT_MATRIX.md`; no wholesale branch merge. Keep live broker submission and automatic accounting promotion disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`.
>
> The CI status above refers to the stated code and documentation commits. This documentation refresh will create a new commit and trigger its own CI run; do not call that new run passed until GitHub reports success.

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
- Live order placement remains unavailable and must stay disabled. The intent-based Phase 2 path has pure order/trade normalization, strict intent matching, versioned status persistence, idempotent `BrokerFillIdentity` storage, and an explicit on-demand GET-only reconciliation worker with leases, safe run/issues records, and owner-scoped read API/UI; tests use mocks and no real-account read has been verified. A separate manual `Order` path now has `BrokerTradeIngestionService`, `BrokerChildOrderReconciliationService`, `BrokerOrder`/`BrokerTradeRecord` staging, and an unregistered `LiveFillAccountingService`. These two paths are not connected: do not assume `BrokerFillIdentity` and `BrokerTradeRecord` are interchangeable. The Phase 2 decision is to keep them separate and prohibit a bridge/dual-write in Phase 2; any bridge is a separate reviewed Phase 3 design. No worker-to-accounting promotion, shared live Order/Execution/Position/cash/P&L lifecycle, or live broker submission is enabled. Read `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` before live-order code. Do not assume Upstox tags provide broker-enforced idempotency.
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

## Live-fill accounting recovery and verification — 2026-10-20

The deleted service, original tests and migration 0008 are restored to their original paths. Supporting models `BrokerOrder`, `BrokerTradeRecord`, `LivePosition` and migrations `202610180006` / `202610180007` were added to complete the chain. GitHub Actions [run 39475387511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39475387511) passed **355 tests, 1 warning**, plus SQLite and PostgreSQL 16 migration upgrade → downgrade → re-upgrade checks at code/test checkpoint `a906274b98f3f7e0c913f376128f4996b996c52b`.

This is not a complete live-fill pipeline: the service remains unregistered, ingestion and reconciliation integration remain outstanding, and no real-account or production migration was performed. Keep live order submission disabled. Continue Phase 2 reconciliation release gates and crash/recovery/fill-linkage checks. Do not delete the recovered files without explicit user approval.


## Current safety checkpoint — 2026-10-21

- Current code/test checkpoint: `84f3a3e48a64b6e1d764a87a2b337b2a8f052741`; GitHub Actions [run 39482592808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581) passed **439 tests, 1 warning**, including SQLite/PostgreSQL 16 reversible migration checks.
- The safety branch's 18 October run passed 456 tests, while main's earlier parser checkpoint passed 406. These runs used different test trees. Main now has 38 test modules; the safety branch has 48, with 20 safety-only modules remaining. See `SAFETY_BRANCH_PORT_MATRIX.md`; do not infer deleted functionality from raw counts.
- Broker trade staging and child-order reconciliation are implemented as an isolated manual-Order path. They update staged records and child metadata, not parent-order accounting. The live accounting service remains unregistered.
- Before further integration, inspect the intent-based `BrokerFillIdentity` worker path versus the manual `BrokerTradeRecord` path and explicitly document whether they are distinct by design or need a safe bridge. Keep live writes and automatic accounting promotion disabled.


### Broker-write guard follow-up — 2026-10-21
The AST source guard was tightened after review: no whole-file Upstox adapter exemption remains, and PAPER portfolio exceptions are restricted to the named endpoint functions. Regression tests cover unexpected adapter calls and unrelated helpers. The exact current `main` head still requires CI verification; do not mark this checkpoint green based on the earlier 439-pass run. Keep live submission and automatic accounting promotion disabled.


### Exact-head verification — 2026-10-21
Current main `975717b05a3aa5faa030f3f9e177dbcf6066daf3` passed [GitHub Actions run 39550130192](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39550130192): **447 passed, 1 warning**, broker-write source guard passed, and SQLite/PostgreSQL 16 reversible migrations passed. The previous CI failure was a guard-test line-number assertion, corrected in this head. Continue Phase 2 by reviewing the `BrokerFillIdentity` and `BrokerTradeRecord` workflow boundary; do not bridge them until transactional identity, ownership, conflict, replay, rollback and recovery rules are explicit. Live submission and automatic accounting promotion remain disabled.

### Fill-workflow boundary rule — 2026-10-21
Keep intent-based `BrokerFillIdentity` reconciliation and manual-order `BrokerTradeRecord` staging/accounting separate unless a reviewed coordinator is explicitly implemented. Their independent unique constraints do not prevent the same broker trade from appearing in both tables. Never dual-write or promote worker evidence automatically. Any future bridge must define canonical identity, owner/connection/order/intent scoping, conflicts, transaction-safe idempotency, rollback and crash recovery. Regression tests added at `3683082509c4b331ab9c7ebceb928e925414de35` enforce that the worker and its replay do not create manual staging/accounting rows or change portfolio cash; exact-head CI must be verified before the next code slice.

### Reconciliation crash-recovery rule — 2026-10-21
Stale reconciliation summaries may be marked `FAILED/WORKER_INTERRUPTED` only through owner/connection-scoped recovery and only when no unexpired lease is active. Preserve the summary counters. Never retry broker calls or change fill/accounting rows as part of run-summary recovery. The current `fail_orphaned_runs` method is not automatically scheduled; do not wire it into background execution until exact-head CI and crash-boundary behavior are reviewed. Live broker submission and automatic accounting promotion remain disabled.

## Current Phase 2 checkpoint — 2026-10-21

- Verify against main HEAD `0ce59a7965e3e96a425fa8ae30c841eb0cb755bc` and [CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228): 461 backend tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- Lease token and expiry must be both present or both absent. Do not allow claims or orphan recovery to silently overwrite half-populated lease records.
- `WORKER_INTERRUPTED` means reconciliation counters may be incomplete. Do not infer no fills from zero counters and do not auto-retry broker requests or promote accounting.
- Next work: review lease completion versus terminal run-summary persistence for transaction atomicity; add focused lost-lease and crash-ordering tests before lifecycle changes.
- Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled.


## Current Phase 2 checkpoint — 2026-10-21

- Verified code/test HEAD `8f967adaa2328f16a0a08a104c3ec394e62f9310`; [CI run 39553655005](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553655005) passed 463 backend tests, 1 warning, broker-write guard, and SQLite/PostgreSQL 16 migration cycles.
- Use `LiveReconciliationRunRepository.finish_with_lease` for worker terminalization. Do not split lease release and run-summary persistence into separate commits.
- If lease ownership has changed, preserve the newer lease and terminalize the old run as `LEASE_LOST`. If summary persistence fails, roll back lease release and allow expiry/recovery to handle the incomplete run.
- Next: audit cancellation/unexpected exception paths and lease renewal/expiry under concurrency. `WORKER_INTERRUPTED` means counters may be incomplete.
- Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate; live submission, automatic accounting promotion, and automatic scheduling remain disabled.


## Current Phase 2 checkpoint — 2026-10-21

- Verified code/test HEAD `2ac6bfaafd3475ee63360bd0049b0b6987236bc1`; [CI run 39553981172](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553981172) passed 465 backend tests, 1 warning, broker-write guard, and SQLite/PostgreSQL 16 migration cycles.
- Worker terminalization must use the atomic run/lease finalization method. Stale lease owners are marked `LEASE_LOST` without clearing a newer owner's token.
- Cancellation during broker reads is expected to leave a recoverable RUNNING summary/lease; after expiry, recovery marks it `WORKER_INTERRUPTED`. Its counters must not be treated as complete.
- Next: audit lease-renewal cadence for large batches and test expiry races around per-record persistence.
- Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate; live submission, automatic accounting promotion, and automatic scheduling remain disabled.


## Current Phase 2 checkpoint — 2026-10-21

- Code/test HEAD `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`; backend [run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed 466 tests, guard and migrations; frontend [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript/build. Latest documentation commit `7f9a1f3293ffc67579042a87b82cb2fb03ffba1f` passed [CI run 39556090575](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556090575).
- Renew the reconciliation lease every 5 records during trade/order batches. If ownership is lost, stop before the next record and do not clear the replacement owner's lease.
- UI must warn for both `WORKER_INTERRUPTED` and `LEASE_LOST`; summary counters can be partial.
- Next: inspect a single slow persistence operation and high-volume processing for lease-expiry races; add transaction-level fencing if needed.
- Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate; live submission, automatic accounting promotion, and automatic scheduling remain disabled.
