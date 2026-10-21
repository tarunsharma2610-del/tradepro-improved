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
> - **Completed engineering task:** single slow-write and high-volume lease-expiry audit; transaction-level fencing and regression coverage passed backend CI run 39561621808 (470 passed, 1 warning).
> - Deferred safety-branch work remains tracked in `SAFETY_BRANCH_PORT_MATRIX.md`; no wholesale branch merge. Keep live broker submission and automatic accounting promotion disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`.
>
> The CI status above refers to the stated code and documentation commits. This documentation refresh will create a new commit and trigger its own CI run; do not call that new run passed until GitHub reports success.

# Safety-branch port matrix

## Current scope audit — 2026-10-21

- Latest test commit: [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2) adds failed-commit rollback coverage for live-fill accounting. Exact-head CI is not yet verified; do not infer a pass from an empty status response.
- The dependency inventory below is a phase-aware port decision, not a commitment to merge every safety-branch feature in Phase 2. Mainline has its own newer read-only reconciliation worker, schema, and lease controls; branch-only live execution and safety systems must be adapted as coherent later-phase work.
- Phase 2 closure decisions: compatible broker response parsing, broker-trade staging, child-order reconciliation, the broker-write source guard, crash recovery/lease fencing, focused idempotency/rollback tests, and the explicit decision to keep BrokerFillIdentity separate from manual BrokerTradeRecord. The latest test commit still needs exact-head CI.


The current mainline read-only reconciliation crash-recovery/lease-fencing slice is complete through atomic finalization, cancellation recovery, five-record lease renewal, renewal-boundary lease-loss tests, and transaction-level fencing for each persistence mutation. Backend CI run 39561621808 passed 470 tests, 1 warning, source guard and SQLite/PostgreSQL 16 migration cycles. The broader safety-branch port matrix and Phase 2 dependency/workflow-boundary work remain open. Safety-only live account safety, broker-write/preflight, live recovery/execution/accounting coordinator files remain intentionally deferred/blocked by the dependency gates below; they are not to be treated as completed or merged wholesale.

Last reviewed: 2026-10-21  
Repository: `tarunsharma2610-del/tradepro-improved`  
Comparison: `main` versus `safety/fail-closed-trading-mode`

## Baseline interpretation

The 18 October safety-branch run [39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552) reported 456 passed, 8 skipped. The 20 October mainline parser checkpoint [39477976464](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39477976464) reported 406 passed. These runs are from different source/test trees. The difference of 50 passing tests is not evidence of 50 deleted tests or 50 missing features.

Current main contains 40 `backend/tests/test_*.py` modules and the safety branch contains 48. There are 19 safety-only test modules and 11 main-only modules. Counts change as slices are ported; re-count before future decisions.

## Completed compatible slices on main

| Slice | Current status | Guardrail |
|---|---|---|
| Upstox response parsing | Ported as `backend/app/brokers/upstox/response_parsing.py` with `test_upstox_response_parsing.py`; 406-test checkpoint passed | Pure validation only; not wired to write paths |
| Broker trade staging | Ported `BrokerTradeIngestionService` and regression tests; adapted to main's stricter schema and mandatory exchange timestamp | Stages evidence only; must not mutate Execution, Position, portfolio cash, or Order state |
| Broker child-order reconciliation | Ported `BrokerChildOrderReconciliationService` and tests with current-main schema; validates staged quantity, weighted average price, monotonic fill quantity and terminal states | Updates only child status/fill quantity; does not mutate parent Order/accounting |

## Safety-only test modules and phase-aware dependency decisions

| Safety-branch test module | Required dependencies / compatibility concern | Phase disposition |
|---|---|---|
| test_api_live_analytics.py | Analytics routes, current-main schema, owner scoping and auth contracts | Defer to later product/API work; not a Phase 2 reconciliation dependency |
| test_broker_child_order_reconciliation.py | Child-order model, partial fills, status aggregation | Ported to Phase 2 mainline; keep main schema and exact CI evidence |
| test_broker_reconciliation.py | Competing broker reconciler, read-only worker, run/issue models | Compare against the existing mainline worker; only port a demonstrated missing behavior, never add a duplicate reconciler |
| test_broker_write_boundary_guard.py | AST guard and approved PAPER-only call-site rules | Ported to Phase 2; current latest test commit still needs exact-head CI |
| test_live_account_safety_postgres.py | Account safety model/service, PostgreSQL locks and schema | Phase 4; requires a separately reviewed safety-control implementation |
| test_live_account_safety_service.py | Safety-state service and API contracts | Phase 4; do not port tests without implementation and authorization design |
| test_live_broker_schema_migration.py | Branch-specific schema/migration history | Do not transplant; any required constraints must be reconciled into main's migration chain during later-phase design |
| test_live_broker_write_service.py | Central broker-write service, authorization and final safety interlock | Phase 4; live submission remains disabled |
| test_live_charge_adjustment_postgres.py | Charge adjustment records and concurrent promotion transactions | Phase 3; depends on reviewed accounting integration and final-charge provenance |
| test_live_charge_adjustment_service.py | Charge provenance and immutable final-charge adjustments | Phase 3; estimated charges must never be treated as final executed charges |
| test_live_execution_service.py | Live execution/accounting promotion and rollback | Phase 3; do not enable or register an unreviewed live accounting path |
| test_live_order_fill_reconciliation_coordinator.py | Staged trade ingestion, fill coordinator and parent-order accounting | Phase 3; must integrate with the existing mainline worker and keep workflow identities separate until bridge design is approved |
| test_live_order_fill_reconciliation_integration.py | DB integration, idempotency, rollback, replay and accounting isolation | Phase 3; follows the coordinator and transactional identity design |
| test_live_order_recovery_postgres.py | Recovery service, PostgreSQL locks, idempotency and ambiguous outcomes | Phase 4; depends on a reviewed live submission/recovery state machine |
| test_live_order_recovery_service.py | Intent lifecycle, broker outcome recovery and version transitions | Phase 4; do not copy branch-specific state machine blindly |
| test_live_position_isolation.py | Live versus paper account/position isolation | Phase 3 prerequisite for accounting integration; audit against current Position/Order models |
| test_live_pre_trade_risk_gate.py | Instrument/account snapshots, margin and risk gate | Phase 4; must match current-main risk services and fail closed |
| test_live_preflight_coordinator.py | Authorization, risk checks, intent creation and broker-write interlock | Phase 4; preflight must fail closed and remain unregistered until approved |
| test_strategy_position_migration.py | Strategy position schema and historical-data migration | Separate schema/product audit; not a Phase 2 reconciliation dependency; never merge migration histories blindly |
| test_upstox_adapter.py | Full broker adapter contract including write endpoints | Phase 4; current read-only reconciliation client remains narrow |
| test_upstox_live_risk_snapshot_service.py | Validated funds/margin snapshots and current portfolio risk service | Phase 3/4 prerequisite only if required by the reviewed integration; map to current parser/service first |

## Mainline-only tests that must be preserved

Main also contains test modules not present in the safety branch, including API reconciliation isolation, instrument service, PostgreSQL order-concurrency coverage, current read-only reconciliation worker/client, lease/repository tests, portfolio risk settings, and market-data streaming. These are evidence that the main branch has newer or different behavior and must not be overwritten by a wholesale branch merge.

## Phase 2 exit decision

The current Phase 2 boundary is not “merge every file from the safety branch.” Phase 2 closes only after (1) compatible reconciliation/staging behavior is implemented and tested on main, (2) the workflow identity boundary is explicitly decided, (3) focused tests and exact-head CI pass, (4) the broker-write source guard and SQLite/PostgreSQL 16 reversible migrations pass, and (5) roadmap, handover, progress, audit, requirements and design documents agree. Items classified as Phase 3 or Phase 4 above remain intentionally deferred and must not be represented as Phase 2 backlog or completed functionality.

## Porting gates

1. Select one behavior slice and identify its required models, services, routes, settings and migration revisions.
2. Port implementation first; adapt tests to main's actual schema and current service boundaries.
3. Preserve stricter mainline constraints. Example: main requires a broker connection on every `BrokerOrder`, so a historical test that expects an unbound child row to persist must instead assert the database rejects it.
4. Test both success and failure behavior: idempotency, duplicate/conflicting identities, cross-account access, malformed data, rollback and accounting isolation.
5. Require focused tests, full backend pytest, PostgreSQL concurrency/integration and SQLite/PostgreSQL reversible migration checks.
6. Record exact commit SHA and GitHub Actions run URL. Keep broker-write service disabled and never place real orders in CI.


## Follow-up safety finding — cumulative promotion and canonical intake

- Added aggregate per-child promotion cap to `LiveFillAccountingService`, backed by regression test `test_cumulative_promoted_trades_cannot_exceed_child_fill_quantity`; exact-head [run 39480669799](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480669799) passed 432 tests.
- Before wiring the staging service into the worker, determine whether the intent-based worker-side `BrokerFillIdentity` and manual Order accounting-side `BrokerTradeRecord` are separate workflows by design. If they need to interact, specify an idempotent transactional bridge with replay, conflict, and rollback semantics. Do not dual-write by default.


## Parent-order reconciliation lock guard — 2026-10-21

- Child reconciliation now locks/revalidates the owned parent Order after broker status I/O, checks LIVE mode and the pre-network instrument/side/quantity snapshot, then locks the BrokerOrder child before reading staged trade totals. This matches ingestion's parent→child lock order.
- Added a regression test that switches the local order to PAPER during the status read and confirms child status/fill quantity remain unchanged. Staged evidence remains available; no accounting rows are created.
- Exact code/test checkpoint `84f3a3e48a64b6e1d764a87a2b337b2a8f052741`, [CI run 39482592808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39482592808): **439 passed, 1 warning**, with SQLite/PostgreSQL 16 reversible migrations passing.
- This does not enable parent Order accounting or live submission. Keep `BrokerFillIdentity` and `BrokerTradeRecord` workflows isolated until their intended boundary is decided.



## Broker-write boundary guard — 2026-10-21

- Ported the source guard and its seven unit tests into main and wired `python -m scripts.check_broker_write_boundary` into the backend CI workflow.
- Implementation/config commit: `c563683b85d7801cd19dcf3d1c7784ec6e433d1f`. Later commits update the progress/audit/roadmap/handover docs.
- Exact-head CI remains unverified. Do not mark this port green until the workflow run for the current `main` HEAD passes. The AST check does not cover reflective/dynamic dispatch.

### Guard exception narrowing follow-up — 2026-10-21

- Follow-up review found the initial AST guard's adapter-file exemption and portfolios-module exemption too broad. Current `main` removes the file-wide adapter exemption and scopes PAPER exceptions to the known endpoint function names/call shapes.
- Added regression coverage for unexpected adapter calls and an unrelated helper in the otherwise approved portfolios module. See implementation/test commits `00c0986a0628cc6b55b842cfcf6e7fc01b071de4` and `30c1aa7b78de357e070f7cdb37b3719112ee8850`, with fixture newline correction in `430d00ae787a250f5c7f425e2b72ad02a38c396a`.
- At this historical checkpoint, exact-head CI was not yet verified. This is superseded by the latest verified code and documentation checkpoints below.


### Exact-head verification — 2026-10-21
Current main `975717b05a3aa5faa030f3f9e177dbcf6066daf3` passed [GitHub Actions run 39550130192](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39550130192): 447 tests, 1 warning; broker-write source guard passed; SQLite and PostgreSQL 16 reversible migrations passed. The prior CI failure was a line-number expectation in the guard test and is fixed. Next porting gate remains the dependency-reviewed boundary between `BrokerFillIdentity` and `BrokerTradeRecord`; no bridge without idempotency, owner/account scoping, conflict and rollback/recovery coverage.

### Latest documentation audit CI — 2026-10-21
Documentation audit commit `7f9a1f3293ffc67579042a87b82cb2fb03ffba1f` passed [GitHub Actions run 39556090575](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556090575). Current code/test checkpoint remains `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`; see `PROGRESS.md` for its backend/frontend evidence. Historical exact-head CI warnings above are superseded by these later verified checkpoints.
