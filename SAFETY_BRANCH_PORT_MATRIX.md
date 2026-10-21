
# Safety-branch port matrix

## Current scope audit — 2026-10-21

The current mainline read-only reconciliation crash-recovery slice is audited complete through atomic finalization, cancellation recovery, five-record lease renewal, and renewal-boundary lease-loss tests. No missing implementation in that slice was identified. The remaining slow-persistence/high-volume expiry race review is still open. Safety-only live account safety, broker-write/preflight, live recovery/execution/accounting coordinator files remain intentionally deferred/blocked by the dependency gates below; they are not to be treated as completed or merged wholesale.

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

## Safety-only test modules and port decisions

| Test module | Required behavior/dependencies to audit | Decision |
|---|---|---|
| `test_api_live_analytics.py` | API routes, owner scoping, current analytics schema | Defer until route and schema dependencies are mapped |
| `test_broker_child_order_reconciliation.py` | Child-order model, partial fills, order state aggregation | Ported to main; exact-head CI run 39481385581 passed 438 tests |
| `test_broker_reconciliation.py` | Broker reconciliation service, current-main read-only worker and issue model | Compare semantics before porting; avoid duplicate competing reconciler |
| `test_broker_write_boundary_guard.py` | Source guard patterns and approved broker-write boundary | Ported to main with `backend/scripts/check_broker_write_boundary.py`, seven focused tests, and a CI invocation; exact-head CI still needs verification |
| `test_live_account_safety_postgres.py` | Account safety model/service, PostgreSQL locking and schema migration | Defer until full account-safety slice is ported |
| `test_live_account_safety_service.py` | Safety state model, service and API contracts | Defer; do not port tests without implementation |
| `test_live_broker_schema_migration.py` | Branch-specific schema and migration history | Do not transplant migration; compare intended constraints to main chain |
| `test_live_broker_write_service.py` | Central broker-write service, authorization, safety interlock | Blocked; live submission remains disabled |
| `test_live_charge_adjustment_postgres.py` | Charge-adjustment records and concurrent promotion transactions | Defer until charge model/service slice is implemented |
| `test_live_charge_adjustment_service.py` | Charge provenance and immutable final-charge adjustments | Defer; estimates must not be treated as final executed charges |
| `test_live_execution_service.py` | Live execution/accounting service, atomic fill promotion and rollback | Blocked until reviewed live-accounting path exists |
| `test_live_order_fill_reconciliation_coordinator.py` | Staged trade ingestion, fill coordinator, parent-order accounting | Candidate after staging slice passes; must integrate with main's existing worker |
| `test_live_order_fill_reconciliation_integration.py` | Full DB integration, idempotency, rollback, replay and accounting isolation | Defer until coordinator and dependencies are complete |
| `test_live_order_recovery_postgres.py` | Recovery service, PostgreSQL row locks, idempotency and ambiguous outcomes | Defer until recovery service is adapted |
| `test_live_order_recovery_service.py` | Intent lifecycle, broker outcome recovery, status/version transitions | Defer; do not copy branch-specific state machine blindly |
| `test_live_position_isolation.py` | Live versus paper account/position isolation | Audit requirements against main's current Position and Order models |
| `test_live_pre_trade_risk_gate.py` | Instrument/account snapshots, margin and risk gate | Defer until current-main live risk model is specified |
| `test_live_preflight_coordinator.py` | Authorization, risk checks, intent creation, broker-write interlock | Blocked; preflight must fail closed |
| `test_strategy_position_migration.py` | Strategy position schema and historical data migration | Compare product requirements; do not merge migration histories |
| `test_upstox_adapter.py` | Full broker adapter contract and order-write endpoints | Defer until explicit live-write design review; read-only reconciliation client stays narrow |
| `test_upstox_live_risk_snapshot_service.py` | Validated risk snapshot parser/service, funds/margin semantics | Candidate after mapping to current parser and portfolio risk service |

## Mainline-only tests that must be preserved

Main also contains test modules not present in the safety branch, including API reconciliation isolation, instrument service, PostgreSQL order-concurrency coverage, current read-only reconciliation worker/client, lease/repository tests, portfolio risk settings, and market-data streaming. These are evidence that the main branch has newer or different behavior and must not be overwritten by a wholesale branch merge.

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
