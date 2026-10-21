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
- **Do next:** verify backend CI for current `main` HEAD. The connected GitHub workflow interface available in this session does not expose push-triggered run listing, so do not claim the latest head is green unless verified through the Actions run itself.
- If CI passes, resume Phase 2 safety-branch port mapping and decide the boundary between intent-based `BrokerFillIdentity` and manual-order `BrokerTradeRecord`. Keep live broker submission and automatic fill promotion disabled.


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

- Current verified main HEAD: `0ce59a7965e3e96da26d27b65ef43eb0cb755bc`.
- Exact-head [backend CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228) passed 461 tests, 1 warning, broker-write boundary guard, SQLite migration cycle, and PostgreSQL 16 migration cycle. Frontend TypeScript/build last passed on `d0437be8ef27c4e86d659a9b85bf42dbdb99ecc4`; no frontend files changed after that.
- Both `fail_orphaned_runs` and `LiveReconciliationLeaseRepository.claim` reject a lease with exactly one of token/expiry populated. Claim SQL only reclaims a released (both NULL) or expired lease.
- Regression coverage verifies a crash after lease release but before terminal summary persistence; after the run ages past the cutoff, the next worker marks it `FAILED/WORKER_INTERRUPTED` and proceeds with a new run. This is eventual recovery, not atomic completion.
- Next: decide whether run-summary finish and lease completion should share a transaction, then cover lost-lease and summary-ordering edge cases. Do not enable live submission, automatic accounting promotion, or a scheduler. Keep `BrokerFillIdentity` and `BrokerTradeRecord` separate.
