<!-- Authoritative checkpoint audit: 2026-10-21; updated after Phase 2 lease-fencing verification. -->
## Authoritative checkpoint audit — 21 October 2026

- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest code/test commit:** `fe07b77b193da1232787384efb38cb589e0d71b6` — lease-fence failures now propagate out of persistence exception handlers rather than being misclassified as ordinary record conflicts.
- **Exact-commit backend CI:** [run 39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808) passed **470 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. It includes lease-fence ownership/expiry tests, a high-volume batch-stop regression, and a PostgreSQL contention test proving an expired lease cannot be reclaimed while a fenced persistence transaction still holds the row lock.
- **Documentation checkpoint CI:** [run 39561881539](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561881539) passed on documentation commit `292cad087bf0febad7793dcec164ebb5435726e8`; this follow-up synchronizes the closure wording and design note.
- **Frontend:** no frontend files changed in this Phase 2 patch. The latest verified frontend CI remains [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474), which passed TypeScript and Next.js build on code/test commit `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`.
- **Previously completed Phase 2 protections:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent token/expiry rejection; five-record renewal checks; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Newly completed lease-expiry audit:** every worker-owned reconciliation persistence operation (fill identity, review issue, order transition and fill-to-intent link) now obtains a current, unexpired lease fence immediately before the write. The lease row is locked through the repository's persistence transaction, so a competing claimant must wait until that transaction commits or rolls back. Lease loss fails closed before the next mutation.
- **Phase 2 disposition:** the planned slow-persistence/high-volume lease-expiry investigation has an implementation and regression coverage. Phase 2 is closed only when CI is green for the exact current HEAD and all project records agree; do not start Phase 3 before that gate.
- **Scope remains unchanged:** external-repository borrowing/adaptation is paused; no outside application code was imported. Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.
- Intermediate CI runs on partially applied commits were red while the new regression test preceded its matching fix; the final code/test commit above is the authoritative green result. Do not count those intermediate failures as the current code status.

<!-- Latest verified status, updated 2026-10-21 -->
> **Latest verified checkpoint — 21 October 2026**
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; branch: `main`. Original `Tradepro` repository remains protected and untouched.
> - Latest code/test commit: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration checks. Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
> - Documentation audit commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da` passed [CI run 39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828).
> - Phase 2 checkpoint complete through atomic run/lease finalization, stale-run and cancellation recovery, lease-loss fencing, five-record renewal, and incomplete-summary warnings.
> - **Next engineering task (not started yet):** audit a single slow database persistence operation and high-volume lease-expiry races; implement transaction-level fencing only if the race is demonstrated.
> - Deferred safety-branch work remains tracked in `SAFETY_BRANCH_PORT_MATRIX.md`; no wholesale branch merge. Keep live broker submission and automatic accounting promotion disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`.
>
> The CI status above refers to the stated code and documentation commits. This documentation refresh will create a new commit and trigger its own CI run; do not call that new run passed until GitHub reports success.

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

### Gate 1 — Baseline reconciliation and documentation
- [x] Verify the exact 18 October CI checkpoint and current main CI checkpoint.
- [x] Compare test-tree and application-path differences across the two branches.
- [x] Audit the current main migration graph.
- [x] Record findings in `PROGRESS.md` and `AUDIT_REPORT.md`; restore current handover/roadmap documents on main.
- [ ] Verify CI after the documentation commits against the exact new HEAD.

### Gate 2 — Port missing safety behavior in dependency-complete slices
- [ ] Build a file-by-file dependency matrix for missing tests and required models, services, API routes, migrations, and configuration.
- [x] Port pure Upstox response parsing and regression tests as an isolated, read-only validation slice; exact-head CI passed 406 tests.
- [x] Port broker trade staging with current-main schema adaptations and fail-closed timestamp validation; exact-head CI passed 431 tests.
- [x] Add cumulative live-fill accounting guard so already-accounted trades plus a new trade cannot exceed the broker-confirmed child fill quantity.
- [x] Port child-order status/fill reconciliation with strict current-main schema adaptation; exact-head CI passed 438 tests.
- [ ] Resolve the workflow boundary between intent-based `BrokerFillIdentity` and manual Order `BrokerTradeRecord`/`BrokerOrder` before connecting either flow to accounting promotion.
- [ ] Add focused regression coverage for idempotent trade identity, partial-fill aggregation, overfill rejection, batch rollback, malformed snapshots, and paper-accounting isolation as applicable to the chosen slice.
- [ ] Run focused tests, full backend pytest, PostgreSQL concurrency/integration tests, and reversible migrations on SQLite/PostgreSQL 16.
- [ ] Commit the slice and update progress/audit with exact-head CI evidence.

### Gate 3 — Live-fill accounting correctness
- [ ] Review `LiveFillAccountingService`, charge provenance, position math, and broker trade/order linkage.
- [ ] Implement a reviewed coordinator path for broker-confirmed trades with connection-scoped identity and transaction-safe idempotency.
- [ ] Prove replay safety, concurrency behavior, rollback behavior, partial fills, out-of-order updates, and crash/restart recovery.
- [ ] Ensure the paper `Position`, paper portfolio cash, and local order state cannot be changed by staged trades before validated promotion.
- [ ] Verify parent-order partial-fill and terminal-state behavior with integration tests.
- [ ] Keep the service unregistered until all gates pass and the path has been reviewed.

### Gate 4 — Live-trading release gates (blocked)
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
- [ ] Verify CI for the exact current `main` head; do not infer success from the prior 439-test run.
- [ ] If CI identifies legitimate PAPER call sites or unapproved write references, review each finding and narrow the guard exceptions only when the actual code path is proven PAPER-only.
- [ ] After exact-head verification, resume the dependency-mapped safety-branch port review. Do not connect `BrokerFillIdentity` and `BrokerTradeRecord` until the workflow boundary is reviewed.
- Live broker writes and automatic accounting promotion remain disabled.


### Broker-write guard review follow-up — 2026-10-21
- [x] Review guard exception scope and identify broad adapter-file and module-wide endpoint exemptions.
- [x] Restrict exceptions to the exact approved PAPER call sites by file, function and attribute chain.
- [x] Add regressions proving unexpected adapter calls and unrelated helper calls are rejected.
- [ ] Verify backend CI for the current `main` HEAD; do not use the earlier 439-test checkpoint as evidence for the guard changes.
- [ ] Once green, continue dependency-mapped safety-branch review. Do not bridge `BrokerFillIdentity` and `BrokerTradeRecord` before the design and replay/rollback behavior are explicit.


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
- [ ] Verify CI for test commit `3683082509c4b331ab9c7ebceb928e925414de35`.
- [ ] After green CI, continue with stale reconciliation-run recovery and crash-boundary tests before any coordinator/bridge design.
- [ ] Any future bridge must define canonical identity, account scoping, conflicts, transaction/idempotency, rollback and crash recovery. Live submission and automatic promotion remain disabled.

### Phase 2 — reconciliation crash recovery slice (2026-10-21)
- [x] Add owner/connection-scoped stale-run recovery for `RUNNING` summaries when no unexpired lease exists.
- [x] Preserve existing counters and use safe error code `WORKER_INTERRUPTED`; do not retry broker requests or mutate fill/accounting state.
- [x] Add tests for stale recovery, active-lease protection, ownership/connection isolation and cutoff validation.
- [ ] Verify exact-head CI after implementation and timestamp-normalization fixes.
- [ ] After green CI, review the lifecycle for a crash between releasing the lease and persisting the terminal run summary, then decide whether recovery should be invoked by a controlled maintenance path. Do not add automatic scheduling or broker writes without separate review.

## Phase 2 — stale-run recovery integration verified (2026-10-21)

- [x] Add owner/connection-scoped recovery of stale `RUNNING` reconciliation summaries before a new lease is claimed.
- [x] Defer recovery while an unexpired lease exists; fail closed without claiming a lease or calling the broker if recovery errors.
- [x] Add worker-level tests for stale-run recovery, active-lease protection, and recovery-error behavior.
- [x] Exact-head [run 39551504884](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39551504884) for `c1c0d8c6fbbb5dcc1389d2da77e911c815958d88`: 455 passed, 1 warning; source guard and SQLite/PostgreSQL 16 migration cycles passed.
- [ ] Add PostgreSQL concurrency coverage for stale-run recovery racing a lease claim.
- [ ] Ensure interrupted-run summaries are surfaced as incomplete because counters are not persisted incrementally. Do not interpret a zero summary after `WORKER_INTERRUPTED` as proof no partial fill work occurred.
- Live submission and automatic accounting promotion remain disabled.


## Phase 2 — stale-run recovery race/UI gates verified (2026-10-21)

- [x] Add PostgreSQL concurrency coverage for recovery racing an expired-lease claim.
- [x] Display a clear incomplete-summary warning when a run has `WORKER_INTERRUPTED`.
- [x] Exact code/test HEAD `d0437be8ef27c4e86d659a9b85bf42dbdb99ecc4`: [backend run 39552046237](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046237) passed 456 tests, 1 warning, source guard and both migration cycles; [frontend run 39552046207](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046207) passed TypeScript and Next.js build.
- [ ] Audit crash between lease release and durable run-summary finish, including lease-token/expiry inconsistency. Add focused regression coverage before any scheduler or new broker integration.
- Recovery remains owner/connection-scoped and metadata-only. Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate; live submission and automatic accounting promotion remain disabled.


## Phase 2 — lease integrity and crash-window recovery verified (2026-10-21)
- [x] Fail closed on inconsistent token/expiry pairs during stale-run recovery.
- [x] Harden lease claim to reject inconsistent state and restrict reclaim to both-null released leases or expired leases.
- [x] Test the crash window where lease completion commits but terminal run-summary persistence fails; verify eventual stale-run recovery before the next worker proceeds.
- [x] Exact-head [CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228): 461 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- [ ] Decide whether lease completion and run-summary finish should be transactionally atomic; test lost-lease, rollback, and terminal-state ordering before changing implementation.
- Safety remains unchanged: read-only reconciliation only; no live order submission or automatic accounting promotion.


## Phase 2 — atomic run/lease finalization verified (2026-10-21)
- [x] Finalize terminal run summary and release matching lease in one database transaction.
- [x] Roll back lease release when run finalization cannot update exactly one RUNNING row.
- [x] Mark stale-owner completion as `LEASE_LOST` without releasing the current lease owner.
- [x] Worker regression covers summary-finalization failure, retained lease, expiry, and eventual orphan recovery.
- [x] Exact-head [CI run 39553655005](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553655005): 463 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- [ ] Audit cancellation/unexpected exception and lease renewal/expiry paths under concurrent worker activity.
- Safety remains unchanged: read-only reconciliation only; no live order submission or automatic accounting promotion.


## Phase 2 — lease-loss and cancellation recovery verified (2026-10-21)
- [x] Test that lease loss before local processing prevents fill persistence and does not release the newer lease owner.
- [x] Test cancellation during broker read leaves a recoverable RUNNING summary/lease; after expiry, a subsequent worker marks it `WORKER_INTERRUPTED` before starting fresh.
- [x] Preserve atomic run-summary finalization and lease release; rollback keeps the lease when terminal summary persistence fails.
- [x] Exact-head [CI run 39553981172](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553981172): 465 tests passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- [ ] Review lease-renewal cadence for large batches and test expiry races around per-record persistence.
- Safety remains unchanged: read-only reconciliation only; no live order submission or automatic accounting promotion.


## Phase 2 — renewal-boundary and UI completeness gates verified (2026-10-21)
- [x] Reduce renewal cadence to every 5 records in trade and order batches.
- [x] Test that lease loss at a renewal boundary stops before the next record is persisted and preserves the replacement owner's lease.
- [x] Warn in the reconciliation UI for both `WORKER_INTERRUPTED` and `LEASE_LOST` incomplete summaries.
- [x] Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380): 466 passed, 1 warning; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- [x] Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474): TypeScript and Next.js build passed.
- [ ] Audit a single slow persistence operation and high-volume processing for lease-expiry races; add transaction-level fencing if the evidence requires it.
- Safety remains unchanged: read-only reconciliation only; no live order submission or automatic accounting promotion.
