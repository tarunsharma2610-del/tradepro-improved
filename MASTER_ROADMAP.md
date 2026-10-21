## Current Phase 2 audit checkpoint — 21 October 2026

- **Current main HEAD before this documentation synchronization:** `adb69aeb05b70ba4fa9095fc73d9dea033d31eec`.
- **Latest code/test commit:** [`e56bf4c66f74b875a3ba8fe388138a9d688dd1e2`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2). Exact-head backend CI [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed **471 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 Alembic upgrade → downgrade → re-upgrade checks.
- The latest pre-sync documentation HEAD `adb69aeb...` also passed backend CI [run 39565251793](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39565251793): **471 passed, 1 warning**; source guard and both database migration cycles passed. The commit-specific run logs were inspected.
- **Verified Phase 2 engineering scope:** dependency/port matrix reviewed; compatible parsing, staging and child-order reconciliation behavior tested; `BrokerFillIdentity` remains separate from manual `BrokerTradeRecord`; accounting idempotency/rollback coverage includes simulated commit failure; reconciliation crash recovery and transaction-level lease fencing are covered by tests.
- **Phase 2 closure rule:** keep Phase 2 limited to dependency-complete, safe ports on main. Live-account safety endpoints, central broker-write service/preflight, live charge adjustments, actual broker submission and the accounting coordinator remain classified as Phase 3/Phase 4 work in the matrix—not missing Phase 2 work. Do not wholesale-merge the divergent safety branch.
- **Final action:** synchronize this checkpoint across roadmap, handover, progress, audit, requirements, instructions, matrix and README; then verify the resulting exact `main` HEAD CI before any Phase 3 work. Until that final run passes, Phase 2 is **not yet formally closed**.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

---

<!-- Authoritative checkpoint audit: 2026-10-21; updated after Phase 2 lease-fencing verification. -->
## Authoritative checkpoint audit — 21 October 2026

- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest code/test commit:** `fe07b77b193da1232787384efb38cb589e0d71b6` — lease-fence failures now propagate out of persistence exception handlers rather than being misclassified as ordinary record conflicts.
- **Exact-commit backend CI:** [run 39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808) passed **470 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. It includes lease-fence ownership/expiry tests, a high-volume batch-stop regression, and a PostgreSQL contention test proving an expired lease cannot be reclaimed while a fenced persistence transaction still holds the row lock.
- **Documentation checkpoint CI:** [run 39561881539](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561881539) passed on documentation commit `292cad087bf0febad7793dcec164ebb5435726e8`; this follow-up synchronizes the closure wording and design note.
- **Frontend:** no frontend files changed in this Phase 2 patch. The latest verified frontend CI remains [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474), which passed TypeScript and Next.js build on code/test commit `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`.
- **Previously completed Phase 2 protections:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent token/expiry rejection; five-record renewal checks; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Newly completed lease-expiry audit:** every worker-owned reconciliation persistence operation (fill identity, review issue, order transition and fill-to-intent link) now obtains a current, unexpired lease fence immediately before the write. The lease row is locked through the repository's persistence transaction, so a competing claimant must wait until that transaction commits or rolls back. Lease loss fails closed before the next mutation.
- **Phase 2 disposition:** the reconciliation crash-recovery/lease-fencing sub-slice is complete. The broader Phase 2 safety-branch port remains open; do not describe the whole roadmap as backlog-free or advance to Phase 3 until its dependency/workflow-boundary gates are addressed.
- **Scope remains unchanged:** external-repository borrowing/adaptation is paused; no outside application code was imported. Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.
- Intermediate CI runs on partially applied commits were red while the new regression test preceded its matching fix; the final code/test commit above is the authoritative green result. Do not count those intermediate failures as the current code status.

## Current scope and backlog clarification — 21 October 2026

- The **reconciliation crash-recovery/lease-fencing slice** is complete. Code/test commit `fe07b77b193da1232787384efb38cb589e0d71b6` passed backend CI run [39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808): 470 tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- The documentation synchronization commit is CI-checked separately; use the live [GitHub Actions page](https://github.com/tarunsharma2610-del/tradepro-improved/actions) to verify the exact current `main` HEAD. Do not infer exact-HEAD CI from an earlier commit.
- **This does not mean the entire Phase 2/Phase 2 roadmap is backlog-free.** Phase 2 still has open work: complete the safety-branch dependency matrix, resolve the `BrokerFillIdentity` versus manual `BrokerTradeRecord` workflow boundary before any bridge, and complete the remaining focused accounting/idempotency/rollback tests for any selected port slice.
- Phase 3 live-fill accounting integration and Phase 4 live-trading release gates remain future work and are intentionally blocked. No live submission, automatic accounting promotion, or automatic scheduling is enabled.
- External-repository borrowing remains paused; the original `Tradepro` repository remains untouched. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.

<!-- Latest verified status, updated 2026-10-21 -->
> **Latest verified checkpoint — 21 October 2026**
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; branch: `main`. Original `Tradepro` repository remains protected and untouched.
> - Latest code/test commit: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration checks. Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
> - Documentation audit commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da` passed [CI run 39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828).
> - Phase 2 checkpoint complete through atomic run/lease finalization, stale-run and cancellation recovery, lease-loss fencing, five-record renewal, and incomplete-summary warnings.
> - **Completed engineering task:** audited single slow-write and high-volume lease-expiry races; transaction-level fencing and regression coverage passed backend CI run 39561621808 (470 passed, 1 warning).
> - Deferred safety-branch work remains tracked in `SAFETY_BRANCH_PORT_MATRIX.md`; no wholesale branch merge. Keep live broker submission and automatic accounting promotion disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`.
>
> The CI status above refers to the stated code and documentation commits. This documentation refresh will create a new commit and trigger its own CI run; do not call that new run passed until GitHub reports success.

## Authoritative Phase 2 audit — 21 October 2026

- Current code/test commit: [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2), adding failed-commit rollback coverage for live-fill accounting. Exact-head CI has **not yet been verified**; an empty commit-status response is not a pass.
- Reconciliation crash recovery and transaction-level lease fencing are implemented and previously passed backend CI run [39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808): 470 tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. This historical run does not verify the newest test commit.
- SAFETY_BRANCH_PORT_MATRIX.md is the authoritative dependency map. Phase 2 ports only compatible, dependency-complete safety behavior. Features requiring new live-safety endpoints, central broker-write authorization, live charge adjustments, or broker submission remain classified as Phase 3/Phase 4 work and must not be copied wholesale from the divergent branch.
- The accounting workflow decision is explicit: keep BrokerFillIdentity and manual BrokerTradeRecord workflows separate. No transactional bridge is approved in Phase 2.
- **Phase 2 is still open pending exact-head CI and the remaining final audit.** Do not start Phase 3 until latest CI, migration checks, source guard, documentation consistency, and every Phase 2 requirement are verified. Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled.

# Tradepro Improved — Master Roadmap

Last reviewed: 2026-10-21  
Repository: `tarunsharma2610-del/tradepro-improved`  
Working branch: `main`

## Rules of execution
1. Work only in this improved repository; never modify the original `Tradepro` repository.
2. Read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `AUDIT_REPORT.md`, `ARCHITECTURE.md`, and `HANDOVER.md` before substantive work.
3. Implement one coherent slice at a time. No wholesale branch merges or unreviewed test-file copying.
4. No real broker orders in tests. Live order submission stays disabled.
5. Record exact commit SHAs and CI run URLs; don't label a checkpoint green until the run corresponds to the exact code HEAD.

## Current verified baseline
- Latest verified code/test checkpoint: `84f3a3e48a64b6e1d764a87a2b337b2a8f052741`.
- [GitHub Actions run 39482592808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581): **439 passed, 1 warning**; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade passed.
- 18 October safety checkpoint: [run 39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552), SHA `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b`, 456 passed, 8 skipped, 1 warning. It belongs to a materially different, diverged branch.
- Tree audit: `main` has 38 test modules; the safety branch has 48. Twenty safety-branch test modules remain absent from main; see `SAFETY_BRANCH_PORT_MATRIX.md` for the dependency map. This explains why the test suites differ, but doesn't mean 101 tests were removed from an identical code line.
- Migration graph: 14 files, one linear path from `202608170001` to `202610180008`; no missing parents. The live-fill service is present but unregistered.

## Roadmap and gates

### Phase 1 — Baseline reconciliation and documentation
- [x] Verify the exact 18 October CI checkpoint and current main CI checkpoint.
- [x] Compare test-tree and application-path differences across the two branches.
- [x] Audit the current main migration graph.
- [x] Record findings in `PROGRESS.md` and `AUDIT_REPORT.md`; restore current handover/roadmap documents on main.
- [x] Verify CI after documentation commits against the exact new HEAD; latest code/test CI run 39561621808 passed and documentation commits have their own Actions runs.

### Phase 2 — Port missing safety behavior in dependency-complete slices
- [x] Build and maintain the file-by-file dependency/port matrix in SAFETY_BRANCH_PORT_MATRIX.md, including required models, services, API routes, migrations, configuration, and explicit defer/block decisions.
- [x] Port pure Upstox response parsing and regression tests as an isolated, read-only validation slice; exact-head CI passed 406 tests.
- [x] Port broker trade staging with current-main schema adaptations and fail-closed timestamp validation; exact-head CI passed 431 tests.
- [x] Add cumulative live-fill accounting guard so already-accounted trades plus a new trade cannot exceed the broker-confirmed child fill quantity.
- [x] Port child-order status/fill reconciliation with strict current-main schema adaptation; exact-head CI passed 438 tests.
- [x] Resolve the current workflow boundary: keep intent-based BrokerFillIdentity separate from manual Order BrokerTradeRecord/BrokerOrder; no bridge or dual-write is permitted in Phase 2.
- [x] Add focused regression coverage for idempotent trade identity, partial-fill aggregation, overfill rejection, batch rollback, malformed/inconsistent broker data, and paper-accounting isolation; latest addition covers failed-commit rollback (commit e56bf4c66f74b875a3ba8fe388138a9d688dd1e2; CI pending).
- [x] Run focused tests, full backend pytest, PostgreSQL concurrency/integration tests, and reversible migrations on SQLite/PostgreSQL 16 (exact-head CI run 39564568154: 471 passed, 1 warning; source guard and SQLite/PostgreSQL 16 migration cycles passed).
- [x] Commit the slice and synchronize progress/audit with exact-head CI evidence (code/test commit e56bf4c66f74b875a3ba8fe388138a9d688dd1e2; final documentation HEAD must still pass CI before Phase 3).

### Phase 3 — Live-fill accounting correctness
- [ ] Review `LiveFillAccountingService`, charge provenance, position math, and broker trade/order linkage.
- [ ] Implement a reviewed coordinator path for broker-confirmed trades with connection-scoped identity and transaction-safe idempotency.
- [ ] Prove replay safety, concurrency behavior, rollback behavior, partial fills, out-of-order updates, and crash/restart recovery.
- [ ] Ensure the paper `Position`, paper portfolio cash, and local order state cannot be changed by staged trades before validated promotion.
- [ ] Verify parent-order partial-fill and terminal-state behavior with integration tests.
- [ ] Keep the service unregistered until all gates pass and the path has been reviewed.

### Phase 4 — Live-trading release gates (blocked)
- [ ] Final race-safe safety interlock across authorization, intent claim, kill switch and broker request lifecycle.
- [ ] Broker status/fill/cancel reconciliation and ambiguous-outcome recovery.
- [ ] Account-level risk controls, circuit breaker, credential/token lifecycle and operational alerts.
- [ ] Exact-head unit, PostgreSQL concurrency/integration, migration, frontend build/typecheck, and security/source-guard checks.
- [ ] Backup-safe staging verification with no real-money order.
- [ ] Explicit user approval before any change that enables live submission.

## Current status and constraints
- Paper trading remains the usable execution mode. The current mainline includes portfolio risk controls, instrument-master sync, Upstox streaming, a read-only reconciliation interface/worker foundation, and live-fill accounting storage/service foundations.
- No claim of complete live trading, broker order submission, end-to-end live accounting, or production readiness is allowed.
- The original repository remains untouched. No production migrations or real broker orders have been performed.



## Broker-write source guard checkpoint — 2026-10-21

- [x] Add AST source guard for unapproved broker order-write references.
- [x] Add focused unit tests for blocked and explicitly allowed call sites.
- [x] Add guard invocation to `.github/workflows/backend-tests.yml`.
- [x] Verify the broker-write guard on exact current code/test HEAD; latest verified code/test run 39561621808 passed 470 tests and the guard.
- [ ] If CI identifies legitimate PAPER call sites or unapproved write references, review each finding and narrow the guard exceptions only when the actual code path is proven PAPER-only.
- [x] Review the dependency-mapped safety-branch port decisions; the current matrix now classifies each listed safety-only test by compatible port, Phase 3/Phase 4 dependency, or separate schema/product review. Keep BrokerFillIdentity and BrokerTradeRecord separate.
- Live broker writes and automatic accounting promotion remain disabled.


### Broker-write guard review follow-up — 2026-10-21
- [x] Review guard exception scope and identify broad adapter-file and module-wide endpoint exemptions.
- [x] Restrict exceptions to the exact approved PAPER call sites by file, function and attribute chain.
- [x] Add regressions proving unexpected adapter calls and unrelated helper calls are rejected.
- [x] Verify backend CI for the current code/test HEAD; latest verified run 39561621808 passed 470 tests and the guard.
- [x] Record the Phase 2 workflow-boundary decision: keep BrokerFillIdentity and BrokerTradeRecord separate; any future bridge requires a separately reviewed Phase 3 design with identity, owner/account scoping, replay, conflict, rollback, and recovery semantics.


### Exact-head verification update — 2026-10-21
- [x] Verify current `main` head `975717b05a3aa5faa030f3f9e177dbcf6066daf3` in [GitHub Actions run 39550130192](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39550130192): **447 passed, 1 warning**.
- [x] Confirm broker-write AST guard passes on the actual application source.
- [x] Confirm SQLite and PostgreSQL 16 migration upgrade → downgrade → re-upgrade checks pass.
- [x] Fix the failed guard-test line-number assertion from the previous run.
- [x] Review the `BrokerFillIdentity` versus `BrokerTradeRecord` workflow boundary; decision for the current phase is to keep them separate. Any future bridge remains blocked until identity, scoping, idempotency, conflict, rollback and recovery semantics are designed.
- Live broker submission and automatic accounting promotion remain disabled.

### Fill-workflow boundary decision — 2026-10-21
- [x] Inspect intent reconciliation, `BrokerFillIdentity`, manual staging `BrokerTradeRecord`, and `LiveFillAccountingService`.
- [x] Decide to keep the two workflows isolated in the current phase; their uniqueness constraints are separate and do not provide cross-table deduplication.
- [x] Add regression assertions that the read-only reconciliation worker/replay cannot create manual staging rows or accounting rows, nor change portfolio cash.
- [x] Verify CI for the recovery work in subsequent exact-head runs; latest reconciliation lease-fencing verification is backend run 39561621808 (470 passed, 1 warning).
- [x] Continue with stale reconciliation-run recovery and crash-boundary tests before any coordinator/bridge design; subsequent Phase 2 sections below record the completed recovery, atomic finalization, cancellation, and lease-fencing tests.
- [ ] Any future bridge must define canonical identity, account scoping, conflicts, transaction/idempotency, rollback and crash recovery. Live submission and automatic promotion remain disabled.

### Phase 2 — reconciliation crash recovery slice (2026-10-21)
- [x] Add owner/connection-scoped stale-run recovery for `RUNNING` summaries when no unexpired lease exists.
- [x] Preserve existing counters and use safe error code `WORKER_INTERRUPTED`; do not retry broker requests or mutate fill/accounting state.
- [x] Add tests for stale recovery, active-lease protection, ownership/connection isolation and cutoff validation.
- [x] Verify exact-head CI after implementation and timestamp-normalization fixes; subsequent exact-head runs are recorded below.
- [x] Review the crash window between lease release and terminal summary persistence; later work made run finalization and lease release atomic and added rollback/recovery tests. Operational invocation remains gated; no automatic scheduling or broker writes.

## Phase 2 — stale-run recovery integration verified (2026-10-21)

- [x] Add owner/connection-scoped recovery of stale `RUNNING` reconciliation summaries before a new lease is claimed.
- [x] Defer recovery while an unexpired lease exists; fail closed without claiming a lease or calling the broker if recovery errors.
- [x] Add worker-level tests for stale-run recovery, active-lease protection, and recovery-error behavior.
- [x] Exact-head [run 39551504884](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39551504884) for `c1c0d8c6fbbb5dcc1389d2da77e911c815958d88`: 455 passed, 1 warning; source guard and SQLite/PostgreSQL 16 migration cycles passed.
- [x] Add PostgreSQL concurrency coverage for stale-run recovery racing a lease claim; see the verified race/UI gates below.
- [x] Surface interrupted-run summaries as incomplete; the reconciliation UI warns for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- Live submission and automatic accounting promotion remain disabled.


## Phase 2 — stale-run recovery race/UI gates verified (2026-10-21)

- [x] Add PostgreSQL concurrency coverage for recovery racing an expired-lease claim.
- [x] Display a clear incomplete-summary warning when a run has `WORKER_INTERRUPTED`.
- [x] Exact code/test HEAD `d0437be8ef27c4e86d659a9b85bf42dbdb99ecc4`: [backend run 39552046237](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046237) passed 456 tests, 1 warning, source guard and both migration cycles; [frontend run 39552046207](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046207) passed TypeScript and Next.js build.
- [x] Audit crash between lease release and durable run-summary finish, including lease-token/expiry inconsistency; atomic finalization and focused recovery regressions passed CI.
- Recovery remains owner/connection-scoped and metadata-only. Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate; live submission and automatic accounting promotion remain disabled.


## Phase 2 — lease integrity and crash-window recovery verified (2026-10-21)
- [x] Fail closed on inconsistent token/expiry pairs during stale-run recovery.
- [x] Harden lease claim to reject inconsistent state and restrict reclaim to both-null released leases or expired leases.
- [x] Test the crash window where lease completion commits but terminal run-summary persistence fails; verify eventual stale-run recovery before the next worker proceeds.
- [x] Exact-head [CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228): 461 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- [x] Make lease completion and run-summary finish transactionally atomic; lost-lease, rollback, and terminal-state ordering regressions passed CI.
- Safety remains unchanged: read-only reconciliation only; no live order submission or automatic accounting promotion.


## Phase 2 — atomic run/lease finalization verified (2026-10-21)
- [x] Finalize terminal run summary and release matching lease in one database transaction.
- [x] Roll back lease release when run finalization cannot update exactly one RUNNING row.
- [x] Mark stale-owner completion as `LEASE_LOST` without releasing the current lease owner.
- [x] Worker regression covers summary-finalization failure, retained lease, expiry, and eventual orphan recovery.
- [x] Exact-head [CI run 39553655005](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553655005): 463 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- [x] Audit cancellation/unexpected exception and lease renewal/expiry paths under concurrent worker activity; regression tests and transaction-level fencing passed CI.
- Safety remains unchanged: read-only reconciliation only; no live order submission or automatic accounting promotion.


## Phase 2 — lease-loss and cancellation recovery verified (2026-10-21)
- [x] Test that lease loss before local processing prevents fill persistence and does not release the newer lease owner.
- [x] Test cancellation during broker read leaves a recoverable RUNNING summary/lease; after expiry, a subsequent worker marks it `WORKER_INTERRUPTED` before starting fresh.
- [x] Preserve atomic run-summary finalization and lease release; rollback keeps the lease when terminal summary persistence fails.
- [x] Exact-head [CI run 39553981172](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553981172): 465 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- [x] Review lease-renewal cadence for large batches and test expiry races around per-record persistence; transaction-level fencing and regression tests passed exact-code CI run 39561621808.
- Safety remains unchanged: read-only reconciliation only; no live order submission or automatic accounting promotion.


## Phase 2 — renewal-boundary and UI completeness gates verified (2026-10-21)
- [x] Reduce renewal cadence to every 5 records in trade and order batches.
- [x] Test that lease loss at a renewal boundary stops before the next record is persisted and preserves the replacement owner's lease.
- [x] Warn in the reconciliation UI for both `WORKER_INTERRUPTED` and `LEASE_LOST` incomplete summaries.
- [x] Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380): 466 passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- [x] Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474): TypeScript and Next.js build passed.
- [x] Audit a single slow persistence operation and high-volume processing for lease-expiry races; add transaction-level fencing and regression tests. Verified by backend CI run 39561621808 (470 passed, 1 warning).
- Safety remains unchanged: read-only reconciliation only; no live order submission or automatic accounting promotion.
