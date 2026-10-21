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

<!-- Authoritative checkpoint audit: 2026-10-21; updated after Phase 2 lease-fencing verification. -->
## Authoritative checkpoint audit — 21 October 2026

- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest code/test commit:** `e56bf4c66f74b875a3ba8fe388138a9d688dd1e2` adds failed-commit rollback coverage. Exact-head backend CI [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests, 1 warning, broker-write guard and SQLite/PostgreSQL 16 reversible migrations. Documentation HEAD `adb69aeb05b70ba4fa9095fc73d9dea033d31eec` also passed [run 39565251793](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39565251793).
- **Exact-commit backend CI:** [run 39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808) passed **470 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. It includes lease-fence ownership/expiry tests, a high-volume batch-stop regression, and a PostgreSQL contention test proving an expired lease cannot be reclaimed while a fenced persistence transaction still holds the row lock.
- **Documentation checkpoint CI:** [run 39561881539](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561881539) passed on documentation commit `292cad087bf0febad7793dcec164ebb5435726e8`; this follow-up synchronizes the closure wording and design note.
- **Frontend:** no frontend files changed in this Phase 2 patch. The latest verified frontend CI remains [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474), which passed TypeScript and Next.js build on code/test commit `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`.
- **Previously completed Phase 2 protections:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent token/expiry rejection; five-record renewal checks; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Newly completed lease-expiry audit:** every worker-owned reconciliation persistence operation (fill identity, review issue, order transition and fill-to-intent link) now obtains a current, unexpired lease fence immediately before the write. The lease row is locked through the repository's persistence transaction, so a competing claimant must wait until that transaction commits or rolls back. Lease loss fails closed before the next mutation.
- **Scope clarification:** Phase 2's defined engineering checks are verified, including the dependency/port matrix, identity boundary, rollback coverage, full backend suite, PostgreSQL concurrency, source guard and reversible migrations. The final documentation sync must pass exact-HEAD CI before Phase 3 begins. Phase 3/4-only safety features remain deferred by design.
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

## Authoritative continuation checkpoint — 21 October 2026

- Latest code/test commit: [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2), adding a regression test that simulates database commit failure during live-fill promotion and asserts rollback leaves no Execution/LivePosition and does not alter the paper position.
- **Exact-head CI is not yet confirmed.** The commit-status query returned no statuses and the available workflow lookup returned no runs; neither result proves pass or failure. Verify the actual GitHub Actions run for this commit before closing Phase 2.
- The earlier reconciliation crash-recovery/lease-fencing checkpoint remains verified by backend run [39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808) (470 passed, 1 warning; source guard and SQLite/PostgreSQL 16 reversible migrations passed). This older run does not cover the newest test.
- The workflow-boundary decision is resolved for Phase 2: keep BrokerFillIdentity (intent-reconciliation evidence) separate from manual BrokerTradeRecord staging. Do not bridge or dual-write them. The dependency/port matrix is SAFETY_BRANCH_PORT_MATRIX.md; defer Phase 3/Phase 4-only safety, coordinator, charge-adjustment, and broker-write features instead of merging the safety branch wholesale.
- **Previous verified checkpoint:** code/test HEAD `00ee9bad0e962d92244da6f63da1e46ba058ad6f` passed [CI run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386). Current documentation sync and its exact-head CI status are recorded in the top checkpoint. Keep live broker submission, automatic accounting promotion, and automatic scheduling disabled. Original Tradepro remains untouched.

# Tradepro Improved — Handover

Last reviewed: 2026-10-21  
Repository: https://github.com/tarunsharma2610-del/tradepro-improved  
Working branch: `main`

## Non-negotiable safeguards
- Work only in this repository. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- Preserve existing behavior and use small, reviewable changes. Inspect the current branch before every change.
- Never place real broker orders in tests. Keep live order submission disabled; PAPER remains the safe default.
- Do not claim tests or migrations passed unless the exact run/commit proves it. Do not deploy production migrations without backup and staging verification.
- Do not merge or cherry-pick `safety/fail-closed-trading-mode` wholesale: the branch is materially divergent from `main`.

## Current main-branch baseline
- Latest verified code/test checkpoint: `84f3a3e48a64b6e1d764a87a2b337b2a8f052741`.
- GitHub Actions [run 39482592808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581): **439 passed, 1 warning**. SQLite and PostgreSQL 16 Alembic upgrade → downgrade → re-upgrade checks passed.
- Documentation commits after that code checkpoint record the baseline discrepancy and branch comparison. Exact-head CI after those documentation commits must be checked before calling the latest HEAD green.
- Current `main` has 38 `backend/tests/test_*.py` modules, including Upstox response parsing, broker trade staging and child-order reconciliation. The 18 October safety checkpoint at `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b` recorded **456 passed, 8 skipped, 1 warning** in [run 39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552), with 48 test modules on that branch. Twenty-two test modules and 19 related API/model/service paths from that branch remain absent on `main`. This is a different code/test tree, not proof that exactly 101 tests were deleted from the same commit line.
- GitHub reports the selected branch comparison as divergent (389 commits ahead / 1,029 behind). Port behavior and tests in dependency-complete slices; do not copy isolated tests that import absent services.
- Migration audit: 14 revision files form a linear chain from `202608170001` through terminal head `202610180008`, with no missing parent reference. CI verifies reversible migration cycles on SQLite and PostgreSQL 16.

## Current implementation boundaries
- The app has a FastAPI backend and Next.js frontend, paper trading, instrument sync, Upstox market-data streaming, portfolio risk controls, and a read-only reconciliation UI/worker foundation.
- The live-fill accounting service and supporting broker-order/trade/live-position models exist on `main`; the service remains intentionally unregistered.
- Broker-confirmed trade ingestion into reconciliation, one-transaction promotion into Execution/live positions with charge provenance, parent-order status accounting, and end-to-end crash/replay recovery are not yet complete.
- Live order submission is not implemented as a safe end-to-end path. Do not enable it. No real broker request or production migration was performed in the verified checkpoint.

## Immediate next task
Build a dependency map between the safety branch's missing tests and the source/migrations they require. Select one coherent behavior slice (start with broker trade staging and response parsing), inspect current `main` implementations, port only the required behavior, add compatible regression tests, run focused tests and full backend/PostgreSQL/migration CI, then record exact commit and run IDs in `PROGRESS.md` and `AUDIT_REPORT.md`.

## Required working sequence
Read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `AUDIT_REPORT.md`, `ARCHITECTURE.md`, and this handover. Then: inspect → map requirement/source/test dependencies → make one minimal change → run targeted tests → run relevant full suite and migrations → commit → update progress/audit → inspect exact-head CI. Keep all broker writes disabled.



## Resume checkpoint — broker-write source guard (2026-10-21)

This update supersedes the earlier "Immediate next task" paragraph above.

- Latest code/config commit: `c563683b85d7801cd19dcf3d1c7784ec6e433d1f`; current docs have been advanced in subsequent commits. Verify actual `main` HEAD before further writes.
- Added `backend/scripts/check_broker_write_boundary.py`, seven focused tests, and a required backend CI step. Documentation now records this guard.
- The previous 439-pass run applies to commit `84f3a3e48a64b6e1d764a87a2b337b2a8f052741`, not automatically to the new source-guard changes. The connected workflow tool does not list push-triggered runs; exact-head CI must be checked before claiming this step passed.
- First next action: inspect the CI result for current `main`; if it fails, read the guard findings and correct the scanner or narrowly document proven PAPER-only exceptions. Never blanket-ignore a broker-write call.
- After exact-head CI, continue the mapped safety-branch audit with one dependency-complete slice. Keep the intent worker's `BrokerFillIdentity` and manual-order `BrokerTradeRecord` paths separate until a reviewed bridge is designed. No live broker submission or automatic fill promotion.


## Resume note — tightened broker-write source guard (2026-10-21)

- Current work narrowed AST guard exemptions: the whole Upstox adapter is scanned, and the portfolios endpoint exception is limited to the actual `place_order` and `cancel_order` functions. Added tests for unexpected adapter calls and an unrelated helper in the same module.
- Relevant commits: `00c0986a0628cc6b55b842cfcf6e7fc01b071de4`, `30c1aa7b78de357e070f7cdb37b3719112ee8850`, `a75a15a0feae98fb2eb4d4301f199d33566c0acf`, `430d00ae787a250f5c7f425e2b72ad02a38c396a`.
- **Current verified checkpoint:** code/test HEAD `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`; documentation HEAD `ee3a3889e32b90b105ee2c2ca4fe6ca7c958d84e`.
- **Do next:** the completeness audit found no missing implementation within the read-only reconciliation recovery slice through the renewal-boundary checkpoint. Continue with the documented single-slow-record/high-volume lease-expiry audit; do not restart recovery unless new evidence identifies a concrete gap. Keep live submission and automatic accounting promotion disabled.


## Verified resume checkpoint — 2026-10-21

- Current `main` HEAD `975717b05a3aa5faa030f3f9e177dbcf6066daf3` is verified green: [GitHub Actions run 39550130192](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39550130192), **447 passed, 1 warning**. The AST broker-write guard passed; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed.
- The preceding commit's CI failure was caused by an incorrect expected line number in the guard test; the assertion was corrected in the current head. No current CI failure is open.
- Resume Phase 2 by reviewing the dependency map and deciding whether `BrokerFillIdentity` and `BrokerTradeRecord` represent separate workflows or need a carefully specified transactional bridge. Do not connect them before defining identity, owner/account scope, conflict handling, idempotent replay, rollback and crash recovery.
- Keep live broker submission and automatic accounting promotion disabled.

## Resume checkpoint — fill-workflow boundary review (2026-10-21)

- Latest code/test commit: `3683082509c4b331ab9c7ebceb928e925414de35` adds regression assertions that the intent-based reconciliation worker never creates manual `BrokerTradeRecord` staging rows, `Execution`, or `LivePosition`, and does not change portfolio cash, including on replay. Exact-head CI is pending.
- Architecture decision: keep `BrokerFillIdentity` and `BrokerTradeRecord` separate for now. They represent the intent-based reconciliation evidence path and the manual Order staging/accounting path, respectively. Their independent uniqueness constraints do not deduplicate across tables.
- Do not bridge or dual-write until canonical fill identity, owner/connection/order/intent linkage, conflict semantics, atomicity, idempotent replay, rollback and crash recovery are designed and tested.
- Next: verify exact-head CI, then continue Phase 2 stale-run/crash-recovery review. Live broker submission and automatic accounting promotion remain disabled.

## Resume checkpoint — orphaned run recovery (2026-10-21)

- Added explicit recovery for stale `RUNNING` reconciliation summaries. `fail_orphaned_runs` only marks a run `FAILED/WORKER_INTERRUPTED` when it is older than the cutoff and the scoped broker connection has no unexpired lease; it does not rerun broker I/O or touch fills/accounting.
- Tests cover stale run, active lease, user/connection scoping, cutoff validation. SQLite timestamp normalization and active-lease transaction rollback are included.
- Latest implementation commits: `c21dc711c9102c4a6f0aad36b404ba8c1b57d5f8`, `007383da7f0ca5a1793098288f610ed98de9eb71`, `298caa0a1a05124cdf6fdc9d94ff0644f20295a5`. Verify CI for the exact latest head before further changes.
- The recovery method is not wired to a scheduler yet. Keep the two fill workflows separate; no live broker submission or automatic accounting promotion.

## Latest verified checkpoint — stale-run recovery (2026-10-21)

- Exact current code head `c1c0d8c6fbbb5dcc1389d2da77e911c815958d88`, [GitHub Actions run 39551504884](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39551504884): **455 passed, 1 warning**; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- Worker recovery now runs before lease claim. Stale owner/connection-scoped `RUNNING` summaries become `FAILED/WORKER_INTERRUPTED` only when no unexpired lease is active; a recovery error prevents lease claim and broker I/O.
- Next: test recovery/lease-claim races on PostgreSQL and ensure interrupted run summaries are presented as incomplete. The stored summary counters are not incremental; zero values with `WORKER_INTERRUPTED` are not proof of no partial work.
- Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate, live broker submission disabled, and automatic accounting promotion disabled.


## Latest verified checkpoint — orphan recovery race and UI warning (2026-10-21)

- Exact current code/test HEAD `d0437be8ef27c4e86d659a9b85bf42dbdb99ecc4`: [backend run 39552046237](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046237) passed **456 tests, 1 warning**, source guard, SQLite/PostgreSQL 16 migration cycles; [frontend run 39552046207](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046207) passed TypeScript and Next.js build.
- PostgreSQL concurrency test now races orphan recovery against expired-lease claim and asserts that recovery and lease ownership cannot both win. The UI explicitly labels `WORKER_INTERRUPTED` counters as incomplete.
- Next: audit the crash window between lease release and summary persistence, and inconsistent lease state (token present but expiry missing). Keep recovery metadata-only, preserve separate fill workflows, and keep live submission/accounting promotion disabled.


## Resume checkpoint — Phase 2 lease/crash recovery (2026-10-21)

- Current verified code/test HEAD: `0ce59a7965e3e96a425fa8ae30c841eb0cb755bc`.
- Exact-head [backend CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228) passed 461 tests, 1 warning, broker-write boundary guard, SQLite migration cycle, and PostgreSQL 16 migration cycle. Frontend TypeScript/build last passed on `d0437be8ef27c4e86d659a9b85bf42dbdb99ecc4`; no frontend files changed after that.
- Both `fail_orphaned_runs` and `LiveReconciliationLeaseRepository.claim` reject a lease with exactly one of token/expiry populated. Claim SQL only reclaims a released (both NULL) or expired lease.
- Regression coverage verifies a crash after lease release but before terminal summary persistence; after the run ages past the cutoff, the next worker marks it `FAILED/WORKER_INTERRUPTED` and proceeds with a new run. This is eventual recovery, not atomic completion.
- Next: decide whether run-summary finish and lease completion should share a transaction, then cover lost-lease and summary-ordering edge cases. Do not enable live submission, automatic accounting promotion, or a scheduler. Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate.


## Latest verified checkpoint — atomic reconciliation lifecycle (2026-10-21)

- Current verified code/test HEAD: `8f967adaa2328f16a0a08a104c3ec394e62f9310`.
- Exact-head [CI run 39553655005](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553655005) passed 463 tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- Run finalization and lease release now execute in one transaction. A summary update failure rolls back lease release; a stale worker cannot release a newer lease and marks its run `LEASE_LOST` instead.
- The previous simulated-crash test now asserts the lease remains claimed when finalization fails, then verifies eventual orphan recovery after expiry. A repository-level rollback test and a stale-owner/new-owner regression test pass.
- Next: audit cancellation, unexpected exception, and lease renewal/expiry paths. Keep fill workflows separate and all live submission/accounting promotion disabled.


## Latest verified checkpoint — lease loss and cancellation recovery (2026-10-21)

- Current verified code/test HEAD: `2ac6bfaafd3475ee63360bd0049b0b6987236bc1`.
- Exact-head [backend CI run 39553981172](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553981172) passed 465 tests, 1 warning, broker-write guard, and SQLite/PostgreSQL 16 migration cycles.
- Worker now has regression coverage for losing lease ownership before local persistence and for cancellation during broker read followed by expiry-based recovery. A stale owner cannot write fill evidence or release the replacement owner's lease.
- Run-summary terminalization and lease release are atomic; failure rolls back lease release. The crash/cancellation recovery marker remains `WORKER_INTERRUPTED`, whose summary counters are incomplete.
- Next: review lease-renewal cadence for large batches and inspect any remaining cancellation/unexpected-error paths. Keep all live broker writes and automatic accounting promotion disabled.


## Latest verified checkpoint — documentation audit and renewal boundary (2026-10-21)

- Code/test HEAD: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`; backend [run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380): 466 passed, 1 warning, guard and migrations passed; frontend [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474): TypeScript/build passed. Latest documentation commit `7f9a1f3293ffc67579042a87b82cb2fb03ffba1f` passed [CI run 39556090575](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556090575).
- Lease renewal now occurs every 5 records during trade/order batches. A regression test simulates lease replacement at a renewal boundary and verifies the worker stops before writing the next record, keeps the new lease owner intact, and marks the run `LEASE_LOST`.
- UI warning now covers `LEASE_LOST` as well as `WORKER_INTERRUPTED`, because neither terminal status guarantees a complete summary.
- Phase 2 lease-expiry audit closed: per-write transaction-level fencing is implemented and verified by backend CI run 39561621808 (470 passed, 1 warning). Do not reopen unless new evidence identifies a regression.
