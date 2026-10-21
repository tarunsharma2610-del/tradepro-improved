## Current Phase 3 checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `3963c2bf4e6ffe2bb33d327b10e2995cd243d003`. Exact-head [Backend CI run 39607630055](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39607630055) passed **484 tests, 1 warning in 29.34s**; the broker-write boundary guard passed, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- New Phase 3 guard: broker-reported live-fill charge references are trimmed for storage and rejected when longer than the `Execution.charge_reference` 200-character column limit. This prevents a predictable storage error from being misreported as a concurrent promotion conflict. Regression coverage is included in the 484-test result.
- The existing Phase 3 safety gates remain active: replay must match the accounted fill and exact charge evidence; only broker-reported, internally consistent charges with a non-empty audit reference are accepted; durable staged trade quantities must match broker-confirmed child fills before promotion; exchange-time ambiguity/out-of-order fills fail closed; paper positions and cash remain isolated.
- **Phase 3 remains in progress, not complete.** Remaining review includes coordinator/identity boundaries, charge provenance/allocation semantics, full partial-fill and crash/restart acceptance criteria, and any explicitly selected bridge design. Keep `BrokerFillIdentity` separate from manual `BrokerTradeRecord` unless a reviewed Phase 3 design explicitly authorizes a narrow bridge.
- Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. The original `tarunsharma2610-del/Tradepro` repository remains untouched. Phase 2 remains closed.
- This checkpoint describes the verified code commit above. The documentation synchronization commit will trigger its own CI; do not treat that documentation commit as green until its exact-head run passes. Older checkpoint entries below are historical audit trail, not current status.

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

## Current verified checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- The lease-race audit now has both pieces of evidence: PostgreSQL test `test_postgres_write_fence_blocks_reclaim_until_persistence_transaction_finishes` proves reclaim waits while a fenced transaction holds the lease-row lock; new `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` runs 20 concurrent expiry-boundary renewal-versus-reclaim races and asserts expired owners cannot renew and generation/token ownership advances safely.
- CI logs confirm the full backend suite and source guard passed; the successful workflow includes SQLite and PostgreSQL 16 upgrade/downgrade/re-upgrade checks. The one Python warning is the existing Starlette/AnyIO deprecation.
- **Current task:** synchronize all authoritative documents with this result. The resulting documentation HEAD still needs exact-head CI and a final stale-status scan before Phase 2 is formally closed. Do not start Phase 3 before then.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

------

## Superseded checkpoint history — 21 October 2026


## Superseded checkpoint history — 21 October 2026

- **Current main HEAD:** `0bd502f83118799d5564e8fd5724d01e8dc975af`. Its exact-head backend CI [run 39566324985](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39566324985) passed. Code/test checkpoint `e56bf4c66f74b875a3ba8fe388138a9d688dd1e2` passed [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154): 471 tests, 1 warning, broker-write guard and SQLite/PostgreSQL 16 reversible migration cycles.
- The dependency/port matrix and `BrokerFillIdentity` versus manual `BrokerTradeRecord` workflow boundary are reviewed. No bridge or dual-write is approved in Phase 2.
- Phase 2 closure is in final consistency review: stale historical status statements in long-form audit documents are being aligned to the current verified checkpoint. Do not start Phase 3 until that review and its exact-head CI pass. Features classified as Phase 3/4 remain deferred by design.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

---
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
- Latest verified `main` HEAD: `0bd502f83118799d5564e8fd5724d01e8dc975af`; exact-head backend CI passed [run 39566324985](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39566324985).
- Latest code/test checkpoint `e56bf4c66f74b875a3ba8fe388138a9d688dd1e2` passed 471 tests, 1 warning, broker-write guard and SQLite/PostgreSQL 16 migration cycles in [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154).
- Older 439-pass run [39481385581](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581) is historical baseline evidence only.
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
- [x] Add focused regression coverage for idempotent trade identity, partial-fill aggregation, overfill rejection, batch rollback, malformed/inconsistent broker data, and paper-accounting isolation; latest addition covers failed-commit rollback (commit `e56bf4c66f74b875a3ba8fe388138a9d688dd1e2`; exact-head CI passed in run 39564568154).
- [x] Run focused tests, full backend pytest, PostgreSQL concurrency/integration tests, and reversible migrations on SQLite/PostgreSQL 16 (exact-head CI run 39564568154: 471 passed, 1 warning; source guard and SQLite/PostgreSQL 16 migration cycles passed).
- [x] Commit the slice and synchronize progress/audit with exact-head CI evidence (code/test commit `e56bf4c66f74b875a3ba8fe388138a9d688dd1e2`; documentation HEAD `0bd502f83118799d5564e8fd5724d01e8dc975af` passed run 39566324985. Any further changes require new exact-head CI before Phase 3).

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


## Phase 3 live-fill accounting checkpoint — 2026-10-21

- Latest reviewed code HEAD at this checkpoint: `ef60ec93d39543c644dfd557f6f73b48ab793b60`.
- Exact-head [Backend CI run 39609474410](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39609474410) completed successfully: **485 passed, 1 warning in 30.25s**; broker-write boundary guard passed; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- The one warning is non-failing; CI logs also report GitHub Actions Node.js 20 deprecation notices.
- Existing safeguards cover replay identity/charge validation, broker-confirmed fill quantities, cumulative child/order quantity limits, rejected-order protection, and atomic live-position/execution updates. This CI result verifies the current HEAD, not completion of all Phase 3 requirements.
- **Open Phase 3 requirement:** define and test the fee-allocation contract when a broker contract-note charge total covers multiple fills. The current API accepts a per-promotion breakdown and validates that its total equals its six components; it does not itself establish how a multi-fill contract-note total is allocated. Do not claim this issue resolved or wire in a coordinator/identity bridge until the rule is designed and regression-tested.
- Safety constraints unchanged: do not enable live broker submission, automatic accounting promotion, or automatic scheduling; keep `BrokerFillIdentity` and `BrokerTradeRecord` separate pending a reviewed bridge design. Phase 2 remains closed.


## Phase 3 checkpoint refresh — 2026-10-21

- **Repository boundary:** all current Phase 3 work is confined to `tarunsharma2610-del/tradepro-improved`, branch `main`. The original `tarunsharma2610-del/Tradepro` is a protected baseline and must not be modified.
- **Current HEAD at audit start:** `3b5c8831d4f3475eee320176b3c06bdbd5364bd2` (source-ledger design-gate documentation). The documentation synchronization commit created after this note requires its own exact-HEAD CI result.
- **Latest confirmed backend CI during this audit:** [run 39618611385](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39618611385) completed successfully on **commit `49f95bdd5f20ee99b21a573087c6e97a9bc03526`**, with **485 passed, 1 warning in 30.65s**. The broker-write boundary guard and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade steps passed. This run is an older SHA, not current HEAD; do not label later commits green based on it.
- **Phase 3 status:** in progress. Current blocker is verified actual-charge evidence and an approved allocation basis. Reviewed Upstox documented APIs provide trade data, aggregate charges, or estimates, but no verified per-fill actual-charge source/contract-note ingestion capability was found in the reviewed adapter/API catalogue. Do not treat estimates as actual charges or allocate aggregate totals by guess.
- **Next engineering sequence:** establish authoritative source format and retention/security boundary; then implement immutable source evidence and per-fill allocation records, migration, transactional reconciliation/idempotency, and required regression tests; finally verify exact-HEAD CI.
- **Safety:** live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. Phase 2 remains closed. This checkpoint is status tracking, not a claim that Phase 3 charge allocation is implemented.

## Latest Phase 3 continuation checkpoint — 2026-10-21

- Current reviewed repository HEAD at checkpoint start: 03b8e73cb918ab22e8c2a3857b77108c4a157942. This file's update will create a newer documentation-only commit.
- Re-inspected backend/tests/test_live_fill_accounting_service.py and backend/app/services/live_fill_accounting_service.py. The parametrized regression test includes ESTIMATED, AGGREGATE_CHARGES, TRADE_CHARGES_API and BROKER_ESTIMATE and asserts rejection before Execution/LivePosition writes. The service only accepts the literal source BROKER_REPORTED and validates reference presence/length, paise precision, non-negative components and total equality.
- Important limitation: the source string and reference are caller-supplied; this validation is not cryptographic/source provenance. No real per-fill actual-charge evidence path has been verified, so an arbitrary caller can still mislabel a source. This is not fixed by the negative-source tests.
- Exact-HEAD CI: not verified. The GitHub connector's workflow-run wrapper filters to pull-request-triggered runs; direct workflow-run endpoint access was rejected by the connector, so prior empty results cannot establish that no push run exists. Do not claim CI success or failure from these empty results. Inspect the actual Actions page/run for the newest SHA before marking green.
- Do not add a production importer, allocation formula, or schema migration until authoritative evidence defines the file structure and component-specific allocation basis. Continue with provenance design only where it can be made correct without assuming unknown broker fields.
- Safety and scope unchanged: all changes belong only in tarunsharma2610-del/tradepro-improved; original Tradepro is protected. Phase 2 remains closed. Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled.
