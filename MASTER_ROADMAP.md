# Tradepro Improved — Master Roadmap

Last reviewed: 18 October 2026
Working branch: `safety/fail-closed-trading-mode`
Pull request: #1 (draft; do not merge without explicit review)

## Operating rules
- Work only in `tarunsharma2610-del/tradepro-improved`; leave original `Tradepro` untouched.
- Read `PROJECT_INSTRUCTIONS.md`, this roadmap, `PROGRESS.md`, `AUDIT_REPORT.md`, `REQUIREMENTS_AUDIT.md`, `HANDOVER.md`, and `LIVE_ORDER_STATE_MACHINE.md` before substantive work.
- Preserve functioning code; prefer small, targeted changes. Update this roadmap and the relevant status files whenever a task is completed.
- Never claim a test passed unless it was actually executed. No live orders for testing. Live trading remains disabled and the existing PAPER-only execution guard must remain in place.

## Current verified state

### Latest code and CI evidence
- Implemented `AccountWideLiveRiskGate`, read-only Upstox quote/position/funds/margin/calendar parsers and collector, and credential-bound `LivePreflightCoordinator`.
- GitHub Actions [run #39112247035](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39112247035) on code/test SHA `e7a2ca8d473f9536839b02e0538bf6768343a627`: **326 passed, 1 warning in 26.85s**; SQLite Alembic upgrade passed.
- Preflight validates the interlocks, intent, ownership, instrument, strategy-entry switch and credentials before broker snapshots; it revalidates connection/token identity after async collection. All broker calls in CI are mocked.
- The coordinator remains unregistered. No order route/worker, broker order submission or live accounting is connected.

### Immediate next task
Audit `BrokerOrder`, execution/fill models, migrations and reconciliation services. Implement a minimal additive, transaction-safe broker trade/fill idempotency and partial-fill aggregation foundation with mocked tests; no live order route/worker or broker order endpoint.

## Release blockers
- Latest verified backend run: SHA `dd27afcecc64f5cafc91198e1cfc81b61616fff9`, 307 tests passed and SQLite Alembic upgrade passed.
- The risk gate's actual Upstox snapshot providers are not wired; weekday/session checks do not cover exchange holidays or special sessions.
- PostgreSQL migration behavior, real broker behavior, exact-head frontend build, deployment/staging and production readiness remain unverified.
- Full broker-confirmed order status/fill/cancel reconciliation, account-level kill switch, broker-error circuit breaker and operational recovery remain incomplete.
- Live trading is **NOT READY**. Keep it disabled.


### 18 October 2026 — broker-reconciliation CI investigation

- Added regression coverage for an Upstox status-check failure response; commit `2625191740554efe5a41f99eff15306ebd68ec5c`.
- Investigated workflow run `39028914012` (`Backend pytest`): it ran against the earlier PR merge checkout `d04dfa5` and reported `177 passed, 3 errors`; all three errors were fixture setup failures (`portfolio` not found) in that checkout. The current branch version of `backend/tests/test_broker_reconciliation.py` defines the fixture, but this alone is not proof the current branch passes.
- The GitHub integration's commit-SHA workflow lookup and combined-status lookup returned no results for the current branch head. The old failed run is not a valid test of current head `2625191740554efe5a41f99eff15306ebd68ec5c`; current CI remains unverified.
- Next: inspect the latest PR run in GitHub Actions (PR workflows check out the generated merge ref), confirm backend tests, migration and frontend results, and fix only current-head failures. Do not claim green CI or enable live trading.


## Historical checkpoint (superseded)

The older checkpoint below recorded broker-trade intake as the next task before implementation and CI evidence were available. It is retained in the Git history; the current state and next task are in the final authoritative checkpoint at the end of this file.


## Broker trade intake — implementation present, verification gate open (18 October 2026)

**Implemented on the safety branch:** normalized staging table and service, idempotency scoped to broker connection, ownership and child-order mapping checks, validation of side/quantity/price/instrument, conflicting replay rejection, quantity bound checks, and tests for paper isolation and same trade IDs across users. Schema migrations 005 and 006 add the staging table and scope broker order/execution identity constraints by connection.

**Important limit:** this records broker trade intake only; it does not account fills, change order states, update positions/cash/P&L, or call the broker. It is not wired to a route, worker, or live execution service. Actual live accounting, actual fee reconciliation, partial-fill aggregation and restart recovery remain incomplete.

**Current gate:** backend test suite and Alembic upgrade must pass on current head `32eea17c141d4cfbc727eed2ff2a1b40d21dbba3`. The connected GitHub API returned no workflow runs/statuses for this SHA and the local runtime could not clone GitHub due unavailable DNS. Do not proceed to live accounting wiring until current-head tests/migrations are verified.

Next sequence: (1) verify/fix current implementation, (2) add populated migration backfill coverage for connection-scoped IDs, (3) design actual charge reconciliation and safe live accounting promotion, (4) only later integrate a dedicated live lifecycle. PAPER-only guard stays in force; no merge or real orders.


### Latest test-scope update — 18 October 2026

Added populated legacy-data coverage for migration 006: a child order and execution created before the connection-scope migration must be backfilled to the owner's broker connection. Current head is `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`; the verification gate remains open until CI proves the new test and full migration chain pass.


### Final verification clarification — 18 October 2026

Code/test target SHA: `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`. The later branch commits only updated documentation; at the check, the PR head was `1b0056d9739cd55d50cd5484cddf955aa8bf07db`, with no workflow run/status returned. The verification gate is still open.


## Latest Phase 2 checkpoint — 18 October 2026

The latest code hardening commit is `2cdbbe290f8b661cb91110dbb4e165fcef36f800`; targeted regression tests were committed at `b780c39f770a6839dab0af63fc424c341eff9d70`. Intake now binds to the exact broker connection, rejects foreign/unbound connection references, requires a matching instrument token, and validates malformed side values. Documentation commits after the code/test commit update the progress/audit/handover files only. The current-head Actions result is absent; these changes are not verified. The next task after this gate passes is the separate, initially unregistered `LiveExecutionService` foundation with mocked tests, then durable submission recovery and broker lifecycle reconciliation in the order above. The intake service remains staging-only; no real orders, no live wiring, no merge.


### Latest regression coverage — 18 October 2026

Commit `264aa4c609d522cd01d07e8213bfee6f14c7a2bf` adds a test proving legacy child orders without a determinable broker connection are rejected by trade intake. This is added coverage, not a test pass. Current code/test target is `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`; the verification gate stays open.


## Branch divergence / PR safety note — 18 October 2026

The latest repository comparison reports PR branch `safety/fail-closed-trading-mode` is **198 commits ahead and 349 commits behind** current `main` (main SHA observed: `a2767e646ec19248e9b2c4a3d8fc688195c91eb3`; merge base: `2cf83089070e064c61f3b75fcb6b663021cbf625`). PR #1 remains draft/open/unmerged. This comparison makes merge/rebase unsafe to do casually: before any merge or rebase, audit the new main changes and reconcile conflicts in a separate reviewed step. Do not merge PR #1 as part of this task; keep working isolated on the safety branch and do not modify `main` or the original `Tradepro` repository.


## Phase 2 migration audit continuation — 18 October 2026

A further audit found that migration `202610180006` used an arbitrary `LIMIT 1` to infer a legacy broker connection. That is unsafe if data cannot establish a unique match. The migration now backfills `broker_orders` and linked `executions` only when exactly one owner/broker connection match exists; rows without a determinable connection stay NULL and the ingestion service rejects them. This preserves fail-closed behavior and avoids silently binding legacy records to an arbitrary account.

- Migration hardening commit: `81faa9f0225a8b50f1036b5316e747517c3f02ed`.
- Migration regression coverage commit: `203c7fcf47626ea85c4dce9762c165a2cd74ab26`, refined to model a legacy owner with no matching broker connection in `d2f7f87c82b286e54284da2a8c186be0ea28e852` and `669a3fb98cd47dccea7e75a1301c74c01c4a3ce3`.
- Latest code/test target: `669a3fb98cd47dccea7e75a1301c74c01c4a3ce3`.
- Verification: still pending. Current-head Actions query returns no run/status; do not claim tests or migrations pass until the configured workflow runs against this target.
- Next action remains the backend pytest + SQLite Alembic workflow gate. No live service wiring, production migration, PR merge, or live order is authorized by this checkpoint.


## Verified CI checkpoint — 18 October 2026

GitHub Actions run [#39109239829](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39109239829) completed successfully on commit `8a256828d202e25e3fba77b496f0da01899969b9` (safety branch). Evidence from the job log:

- Backend pytest: **266 passed, 1 warning, in 16.08s**.
- SQLite migration check: **`alembic upgrade head` succeeded**, including revisions `202610180005` and `202610180006`.
- Warning: Starlette test-client deprecation for `anyio.abc.BlockingPortal`; no test failure.
- Workflow job and overall run conclusion: **success**.

This verifies the code present at that SHA in CI. It does not validate PostgreSQL migration behavior, live broker connectivity, real order submission, live accounting, frontend build, or production deployment. Keep those as separate gates.


## Authoritative continuation checkpoint — 18 October 2026 (supersedes older pending-CI and next-task notes)

### Latest verified state

- Latest verified code/workflow SHA: `677fcf882e0ce1e6e02be3bb8df0d074b8fbf220`; commits after this SHA update documentation only and do not change the verified backend code.
- GitHub Actions [run #39109587876](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39109587876) on that exact SHA: **286 passed, 1 warning in 18.93s**, followed by successful SQLite `alembic upgrade head`. Run conclusion: success.
- Earlier verified baseline run #39109239829 had 266 passed; the newer 286-test run includes the new preflight tests. Do not use older “CI pending” paragraphs below as current status.
- The single Python warning is the existing Starlette/AnyIO deprecation. No test or migration failures occurred in the verified run.

### Completed in this continuation

1. Hardened migration 006 so it backfills broker connection IDs only when a unique owner/broker match exists; unresolved legacy rows remain unbound. Added regression coverage.
2. Added a separate `LiveExecutionService` preflight-only module and default-off `LIVE_ORDER_SUBMISSION_ENABLED` environment interlock.
3. Preflight requires `TRADING_MODE=LIVE`, the separate default-off interlock, explicit per-request confirmation, an injected reviewed account-wide risk gate, owned/active portfolio, active supported equity instrument, verified Upstox connection and usable token. Invalid inputs and risk-gate failures block.
4. The service returns a non-secret preflight plan only. It creates no Order row, does not call any broker adapter, does not persist a tag/intent, and does not change cash, positions, executions or trade staging. It is not registered to any API or worker. Live trading remains disabled.
5. Backend workflow now runs on `safety/**` pushes and relevant backend/workflow changes, while documentation-only changes do not retrigger backend CI.

### Next implementation task

**Stable idempotency/tag recovery for ambiguous submissions — design and mocked tests only.** Audit existing `Order.idempotency_key`, `broker_tag`, and adapter `get_order_history(tag=...)` behavior. Add a deterministic tag/intent persistence design and tests proving a retry never submits a second POST after a timeout. Do not implement or invoke real broker submission in this task; do not wire the service into routes/workers; do not merge PR #1 or enable live trading. After code/test commit, update progress, audit, requirements, roadmap, changelog, architecture, state-machine and handover files with exact CI evidence.

## Authoritative checkpoint — 18 October 2026 (idempotent live intent and tag recovery)

### Current verified implementation
- Latest code/test SHA: `de2e2b7524f09b1be2d4378a9b5ac29bdf26f9e7`. GitHub Actions [run #39110239225](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39110239225) completed successfully: **296 passed, 1 warning in 22.04s**; SQLite `alembic upgrade head` passed.
- Added `backend/app/services/live_order_recovery_service.py`: deterministic opaque 40-character broker tag, durable LIVE intent persistence, idempotency-key replay with exact-payload validation, submission-unknown state persistence, and read-only recovery through Upstox order-history-by-tag.
- Added `backend/tests/test_live_order_recovery_service.py`: stable tag, repeated intent, key/payload mismatch, fail-closed preflight, timeout/no-match no-resubmit, mismatched tag/intent, sliced child-order quantity reconciliation and repeated recovery.
- No `place_order` call is made by the new service. No API route or worker invokes it. Recovery stores broker child IDs only and does not infer order status/fills or change cash, positions, executions or P&L.
- The CI warning is a dependency/runner deprecation warning; test and SQLite migration steps passed. This run does not verify PostgreSQL migration, real broker API behavior, frontend build, or production deployment.
- Code and tests were committed separately: service `4990f28e7b8cfeadca85598abfac8111c8fe7130`; tests `de2e2b7524f09b1be2d4378a9b5ac29bdf26f9e7`.

### Next task
Implement a concrete, testable **account-wide live pre-trade risk gate** and inject it into the preflight path: current positions/exposure, order-value and order-frequency limits, market-session/stale-quote requirements, and broker funds/margin checks with fail-closed behavior. Mock all external calls. Do not add a broker POST, wire any route/worker, merge PR #1, or enable live trading in that task.

### Release status
PR #1 remains draft/open/unmerged. Original `Tradepro` remains untouched. Live trading remains **NOT READY**; no real orders have been submitted.

## Authoritative checkpoint — 18 October 2026: Upstox risk snapshots and official session calendar

### Verified code and tests
- Latest verified code/test SHA: `c683fbd16d114b2a41a80a646fc91ee2d4cf25eb`. GitHub Actions [run #39111682177](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39111682177) succeeded: **315 passed, 1 warning in 25.97s**; SQLite Alembic migration verification passed.
- Added strict read-only parsers in `backend/app/brokers/upstox/risk_snapshot_parsing.py` for full market quotes, open positions, official market holidays, special sessions and NSE timings.
- Added adapter calls for full quote, positions, funds/margin, estimated margin and official calendar endpoints, plus `backend/app/services/upstox_live_risk_snapshot_service.py` to collect and validate snapshots. It includes quotes for broker positions and unresolved live-order instruments, respects Upstox's 500-key quote limit, and contains no order-placement call.
- Added mocked regression coverage for malformed/naive quote timestamps, instrument identity mismatch, duplicate positions, holidays/special sessions, provider failure and the read-only collector. Current CI: 315 passed.
- The collector is not wired into a route, worker or order submission. Live mode remains disabled; no real broker requests or real orders were used in these tests.

### Remaining caveats
- The adapter/parser contract has been verified against mocks, not live Upstox responses. Broker-specific response fields and official calendar behavior need documented API-contract review before staging.
- Snapshot collection uses the currently supplied access token; safe orchestration from the user's encrypted connection into a fresh snapshot bundle and the synchronous risk gate is not yet implemented.
- Full live order status/fill/cancel reconciliation, connection-scoped fill idempotency and live accounting remain incomplete. PostgreSQL migration, exact-head frontend build and staging remain unverified.

### Next task
Implement a separate asynchronous, **preflight-only coordinator** that obtains a valid per-user Upstox token through the existing credential service, collects read-only risk snapshots, injects the snapshot-backed providers into `AccountWideLiveRiskGate`, and then invokes the existing `LiveExecutionService.preflight` contract without submitting or persisting an order. Add mocked tests for wrong user/connection, token expiry/provider failures, stale snapshots and successful preflight. Keep it unregistered: no route/worker, no broker POST, no live-mode enablement.

### Release status
PR #1 remains draft/open/unmerged. Original `Tradepro` remains untouched. Live trading is **NOT READY** and disabled. No real orders have been submitted.

## Authoritative checkpoint — 18 October 2026: reconcile-before-promote coordinator

### Verified code and CI evidence
- Latest verified code/test SHA: `cfa038fe49dfde1c441f77d5c4a12fcb13ba695a`. GitHub Actions [run #39118263100](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39118263100) succeeded.
- Full backend suite: **380 passed, 1 skipped, 1 warning in 27.98s**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL concurrency integration passed (**1 passed in 0.36s**).
- Added unregistered `LiveOrderFillReconciliationCoordinator`. It reconciles every mapped Upstox child order and its durable trade list before promoting any staged fill for that conceptual parent order. If any child fails reconciliation, none of the parent's fills are promoted.
- Multiple fills require distinct timezone-aware exchange timestamps, preventing ambiguous position-accounting order. Promotion stops at the first charge/accounting failure; completed fills are reported and retries remain idempotent.
- Regression tests cover successful chronological promotion, sibling reconciliation failure, missing/duplicate timestamps, and promotion failure. The parent Order remains unchanged; the coordinator contains no order-placement call and is not registered to routes/workers.

### Remaining caveats
- Coordinator tests currently inject fake reconciliation/promotion collaborators; the separate PostgreSQL integration test covers real SQLAlchemy service concurrency with synthetic records, not live Upstox behavior.
- Contract-note references remain caller supplied and not independently authenticated. Frontend build, staging, monitoring, account-level kill switch, broker-error circuit breaker, and complete production live lifecycle remain unverified/incomplete.
- PR #1 remains draft/open/unmerged; original `Tradepro` is untouched; live trading remains disabled and not ready.

### Next task
Add a service-level integration test that composes the **real** `BrokerChildOrderReconciliationService`, `BrokerTradeIngestionService`, `LiveFillPromotionService`, and `LiveFillAccountingService` with a fully mocked read-only Upstox adapter and charge estimator. Verify reconciliation happens before promotion, repeated runs are idempotent, failures leave no accounting rows, and paper cash/positions remain unchanged. Keep all promotion services unregistered; no order submission, PR merge, or live-mode enablement.

### Release status
Live trading is **NOT READY** and disabled. No real orders have been submitted.


## Continuation checkpoint — 18 October 2026: real-service reconciliation integration coverage

- **Implemented and committed test change:** `b5783d421f64fcb8e7f1d75f1af5185fd9029f59` — [commit](https://github.com/tarunsharma2610-del/tradepro-improved/commit/b5783d421f64fcb8e7f1d75f1af5185fd9029f59).
- Extended `backend/tests/test_live_order_fill_reconciliation_coordinator.py` with integration tests composing the real `BrokerChildOrderReconciliationService`, its real `BrokerTradeIngestionService`, `LiveOrderFillReconciliationCoordinator`, `LiveFillPromotionService`, and `LiveFillAccountingService`. Only broker read responses and the charge estimator are mocked.
- Coverage checks real service composition, repeat-run idempotency, all-sibling reconciliation failure blocking promotion, no Execution/LivePosition rows on reconciliation failure, and unchanged paper cash/positions. The mock exposes only read methods and contains no order-write path.
- **Verification status at documentation time:** no CI status checks were returned for this commit yet. Do not report these new tests as passing until a workflow result confirms it. No local test run was performed in this continuation.
- **Next action:** inspect the workflow result for this exact SHA; if it fails, diagnose and fix the targeted failure, rerun CI, and record exact evidence. If it passes, re-audit the remaining release blockers and choose the next distinct task—do not recreate the coordinator or repeat this integration-test task.
- Release guardrails unchanged: PR #1 remains draft/open/unmerged; live trading is NOT READY and disabled; no real orders submitted; original `Tradepro` untouched.


### Superseding integration-test commit — 18 October 2026

- Latest code/test commit: `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` ([GitHub](https://github.com/tarunsharma2610-del/tradepro-improved/commit/4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88)). It supersedes the earlier integration-test commit `b5783d421f64fcb8e7f1d75f1af5185fd9029f59`.
- Integration tests now delete pre-seeded staged trade records before invoking the real child reconciliation service. Thus the actual trade-ingestion path must insert rows from the mocked read-only broker response before status reconciliation and promotion. The failure case verifies staged rows can exist without any accounting rows when a sibling status lookup fails.
- CI remains **unverified/pending** for the latest commit; no test result is claimed. Next action remains checking the workflow for this exact SHA, fixing only demonstrated failures, then re-auditing the next distinct gap.

## Superseding verified checkpoint — 18 October 2026: real-service fill reconciliation integration

### Exact verification evidence
- Latest tested code/test SHA: `c779f2543ea1f20efbd8b7dca38a9c2aed201749`.
- GitHub Actions [run #39118955335](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39118955335): **success**. Full suite: **385 passed, 1 skipped, 1 warning in 34.01s**. SQLite migration upgrade passed, PostgreSQL 16 migration upgrade passed, and PostgreSQL concurrency integration passed (**1 passed in 0.35s**).
- This exact-head run verifies the fresh-ingestion integration test refinement from commit `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` and fixes for nondeterministic child order assertions and deleted ORM fixture access.
- The real-service integration test now begins with no staged trade rows: mocked Upstox trade reads must be inserted by the real `BrokerTradeIngestionService` before official status reconciliation and promotion. Repeated reconciliation/promotion is idempotent; sibling status failure prevents any fill accounting; charge-estimate failure creates no Execution/LivePosition rows; paper cash/positions and parent Order state remain unchanged.
- PostgreSQL 16 verifies migration compatibility and concurrent charge adjustments/fill promotion. Lock scoping explicitly avoids PostgreSQL's `FOR UPDATE` nullable outer-join error.

### Release status and caveats
- All broker API responses in tests are mocked. No live Upstox API requests or real orders were sent.
- The coordinator, fill promotion and charge-adjustment services remain unregistered in order routes/workers. Live order submission remains disabled.
- Frontend build/staging, real broker contracts, exchange holiday coverage, operational monitoring, account-level kill switch and broker-error circuit breaker remain outstanding. PR #1 remains draft/open/unmerged; original `Tradepro` untouched.

### Next distinct task
Implement and test the **persisted account-level live kill switch and broker-error circuit breaker**: durable state, fail-closed read behavior, reason/timestamp/audit trail, threshold-triggered circuit trips, manual-reset policy and account-wide scope across portfolios. Keep it unregistered from order submission until separately reviewed; do not merge PR #1 or enable live trading.

This checkpoint supersedes prior notes saying CI for `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` was pending. The latest verified test SHA is `c779f2543ea1f20efbd8b7dca38a9c2aed201749`.


## Latest Phase 2 continuation — partial-promotion failure and retry coverage

- Test commit: `1a3475c69d3a93ece7bfad22ace4dce52231bfa1` ([GitHub](https://github.com/tarunsharma2610-del/tradepro-improved/commit/1a3475c69d3a93ece7bfad22ace4dce52231bfa1)).
- Extended `backend/tests/test_live_order_fill_reconciliation_coordinator.py` with a third service-level integration scenario. The real services ingest fresh broker-trade rows; the charge estimator fails once on the second chronological fill. The test checks partial progress is reported, promotion stops, and a retry recognizes the first fill as a duplicate while accounting only the remaining fill.
- Safety assertions include no broker write calls, unchanged paper cash/positions, and exactly two executions after successful retry.
- **Verification status:** CI for this exact SHA is not yet confirmed; no pass is claimed. Do not treat the task as complete until the exact commit's workflow result is checked.
- Next: check CI for this SHA; diagnose only demonstrated failures. If green, review whether the real-service reconciliation and promotion path needs PostgreSQL-backed integration coverage and update the audit with the exact verified evidence. No live wiring, order submission, merge, or live-mode enablement.


## Phase 2 continuation — persistent account-level kill switch and broker circuit breaker

### Implemented, verification pending
- Added `backend/app/services/live_account_safety_service.py` to operate the existing account-wide `LiveAccountSafetyState` and append-only `LiveAccountSafetyEvent` tables.
- Added migration `backend/alembic/versions/202610180009_live_account_safety.py` (revision `202610180009`, revises `202610180008`) for durable safety state and event audit tables.
- Added `backend/tests/test_live_account_safety_service.py` covering missing-state fail-closed behavior, default tripped state, broker-error threshold/circuit trip, event idempotency, manual reset requirements, failed/stale health checks and unknown circuit values.
- Latest code/test head at this checkpoint: `57939799b7e8b436d5095924b86a89ce380a956e` ([GitHub commit](https://github.com/tarunsharma2610-del/tradepro-improved/commit/57939799b7e8b436d5095924b86a89ce380a956e)).
- **Verification pending:** GitHub returned no status checks/workflow runs for this exact head. Do not mark tests or migration green until Actions confirms backend pytest, SQLite migration upgrade, PostgreSQL 16 migration upgrade, and existing PostgreSQL integration job.

### Safety contract
- State scope is account/user + broker, not portfolio.
- Missing state, stale health, database exceptions, unknown circuit states, a tripped kill switch or an open/non-closed circuit all deny permission.
- New state is initialized with kill switch tripped. Broker success clears consecutive-error count only; it never silently closes an open circuit.
- Manual reset requires authenticated actor, a recent passing health-check event, zero consecutive broker errors, and an explicit reason. State changes are append-only audited and idempotency-keyed.
- Service is not registered in live order submission or routes; no live order capability was enabled.

### Next distinct steps
1. Verify CI and migration upgrades for exact head `57939799b7e8b436d5095924b86a89ce380a956e`; fix only observed failures.
2. Add PostgreSQL concurrency tests for duplicate error-event idempotency, concurrent threshold trips and manual-reset serialization.
3. Add a read-only preflight integration test that composes persisted safety decision with existing `AccountWideLiveRiskGate`; keep actual submission unregistered.
4. Review authentication/authorization API and operator audit visibility before any control endpoint exists.


### Test correction checkpoint — c97be866828bd47a23f22fc44fac2d3359e70f35

The manual-reset test was corrected in commit `c97be866828bd47a23f22fc44fac2d3359e70f35` to exercise the actual safety contract in order: missing health check blocks reset; a passing health check with a nonzero broker-error counter still blocks reset; broker success clears the counter but does not close the circuit; a fresh passing health check then permits explicit manual reset. This supersedes the previous test commit `57939799b7e8b436d5095924b86a89ce380a956e`. GitHub status/workflow results remain unavailable for this exact code SHA; test/migration verification is still pending.

## Superseding checkpoint — 18 October 2026: Alembic duplicate-revision fix under CI

- Regression test commit: [8e73e9156db260b26b92666ba4cb81b5cf0ff9ea](https://github.com/tarunsharma2610-del/tradepro-improved/commit/8e73e9156db260b26b92666ba4cb81b5cf0ff9ea) adds coverage that a database read exception in `LiveAccountSafetyService.check_allowed` denies permission.
- CI run [#605](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39120252989) exposed a migration graph defect: **392 passed, 1 skipped, 3 failed, 1 warning**. All three failures reported multiple Alembic heads caused by two migration files claiming revision `202610180009` (the charge-adjustment ledger and the newly added safety migration).
- Fix commit: [410e87e7ece87d72e33c717e42871028bd0e3c36](https://github.com/tarunsharma2610-del/tradepro-improved/commit/410e87e7ece87d72e33c717e42871028bd0e3c36) removes the duplicate `202610180009_live_account_safety.py`. The existing `202610180010_live_account_safety.py` is the canonical safety migration and follows the charge-adjustment revision `202610180009`.
- Verification for the fix: GitHub Actions [run #606](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39120397940) completed successfully. GitHub Actions run #606 reports **395 passed, 1 skipped, 1 warning in 28.61s**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL concurrency integration passed (**1 passed in 0.26s**). This closes the duplicate-revision verification gate for code/test SHA `410e87e7ece87d72e33c717e42871028bd0e3c36`.
- Safety unchanged: account safety service remains unregistered from order submission; live order submission is not enabled; PR #1 stays draft/open/unmerged; original `Tradepro` remains untouched.

Next distinct task: add PostgreSQL concurrency coverage for account-safety idempotency/threshold trips/manual-reset serialization, then test read-only composition with the existing preflight coordinator and risk gate. Keep it unregistered from order submission.

## Superseding verified checkpoint — 18 October 2026: account-safety PostgreSQL concurrency

- Code/test target SHA: [872eab69082b231117184d80b1bb4a7a96c15b6b](https://github.com/tarunsharma2610-del/tradepro-improved/commit/872eab69082b231117184d80b1bb4a7a96c15b6b). This includes the PostgreSQL account-safety concurrency tests and the workflow change that runs them alongside the existing charge-adjustment concurrency test.
- GitHub Actions [run #608](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39120699215): **success**. Full backend suite: **395 passed, 4 skipped, 1 warning in 29.36s**. SQLite Alembic upgrade passed. PostgreSQL 16 Alembic upgrade passed. Dedicated PostgreSQL integration: **4 passed in 0.44s**.
- PostgreSQL safety coverage now proves: two concurrent submissions with the same broker-error idempotency key count once; two distinct concurrent broker errors serialize and trip the circuit exactly at the configured threshold; concurrent manual resets permit only one reset and preserve the audit trail.
- Migration issue resolved: removed duplicate revision 202610180009_live_account_safety.py; canonical safety migration is 202610180010_live_account_safety.py, chained after 202610180009_live_charge_adjustment_ledger.py. The prior duplicate-revision failure is superseded by successful run #606 and then run #608.
- The account safety service remains unregistered from order submission. These tests use a real PostgreSQL test database and synthetic test users only; no live broker API or order-write endpoint was called. PR #1 remains draft/open/unmerged; original Tradepro remains untouched.
- **Next task:** add read-only preflight composition coverage using the existing LivePreflightCoordinator, AccountWideLiveRiskGate, and persisted LiveAccountSafetyService decision. Fail closed on any denial/error; do not register the composition with order routes/workers or enable live order submission.

## Superseding verified checkpoint — 18 October 2026: safety-aware read-only preflight composition

- Code/test target SHA: [3e73efd441315294970cb652ddeb9b37b00b67b9](https://github.com/tarunsharma2610-del/tradepro-improved/commit/3e73efd441315294970cb652ddeb9b37b00b67b9). The coordinator change is in commit [866336676b24b0da34fe833263b0f2c33204bf17](https://github.com/tarunsharma2610-del/tradepro-improved/commit/866336676b24b0da34fe833263b0f2c33204bf17).
- GitHub Actions [run #611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39121063921): **success**. Full backend suite: **398 passed, 4 skipped, 1 warning in 29.51s**. SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL integration passed (**4 passed in 0.41s**).
- LivePreflightCoordinator now checks the persisted account-wide LiveAccountSafetyService decision after local intent/ownership validation and before credentials or any broker snapshot. Missing safety state, a tripped latch/open circuit, stale health or an unexpected safety-check exception blocks preflight. The service is injectable for testing; default construction uses the same preflight clock.
- Regression tests prove missing state, a tripped latch, and an unexpected safety-check exception all block before any read-only broker call. Existing successful preflight tests explicitly establish a passing health check and manual reset in the test fixture.
- This is read-only preflight composition only. LivePreflightCoordinator remains unregistered from order routes/workers, no broker order-write method is called, live trading remains disabled, PR #1 stays draft/open/unmerged, and the original Tradepro repository remains untouched.
- **Next task:** audit authentication/authorization and operator audit visibility for any future safety-control endpoint. Do not create or wire a control route until that review is complete; keep live order submission disabled.


## Next gate: security and operator-audit design review — 18 October 2026

The static review is committed in [SECURITY_CONTROL_ENDPOINT_AUDIT.md](SECURITY_CONTROL_ENDPOINT_AUDIT.md), commit [10d87d9d9010b2c48ebcf25c832a2ea574100889](https://github.com/tarunsharma2610-del/tradepro-improved/commit/10d87d9d9010b2c48ebcf25c832a2ea574100889). Do not design or implement safety-control routes until the permission model, step-up auth, CSRF/origin policy, event redaction, atomic audit persistence, audit-read scoping and HTTP negative-test matrix are approved. After that design review, audit every order-entry/retry/recovery/broker-write path before wiring the preflight coordinator. Live order submission stays disabled; PR #1 stays draft/open; original Tradepro remains untouched.


## Order-entry path inventory gate — 18 October 2026

Static inventory is recorded in [ORDER_ENTRY_PATH_INVENTORY.md](ORDER_ENTRY_PATH_INVENTORY.md), commit [a477489c7e2d5b6883c299c1e9a8aee1cbef055f](https://github.com/tarunsharma2610-del/tradepro-improved/commit/a477489c7e2d5b6883c299c1e9a8aee1cbef055f). The manual order route and strategy/worker paths converge on a PAPER-only service; Upstox adapter write methods exist but no application caller was found in reviewed paths. The live intent recovery service does not yet compose the account-safety-aware coordinator. Next design the central write boundary, durable intent/audit transaction, role policy and source-call guardrails; then test before any route/worker wiring. Live remains disabled.


## Central broker-write boundary design gate — 18 October 2026

Design contract: [CENTRAL_BROKER_WRITE_BOUNDARY_DESIGN.md](CENTRAL_BROKER_WRITE_BOUNDARY_DESIGN.md), commit `40f9ca652cf4bf5e86ed51a9c5f21a3071ce7e06`. This commit is design-only: no endpoint, route/worker integration, adapter write or live enablement was added.

Required order:
1. Implement safety-event transaction/version/idempotency semantics and PostgreSQL append-only enforcement, with rollback and concurrency tests.
2. Add explicit least-privilege safety/broker permissions, tenant scope, recent MFA step-up for reset, CSRF/Origin protection and malformed JWT claim tests.
3. Implement one typed broker-write service; persist intent+event before network I/O; model unknown outcomes and prohibit blind retry.
4. Add CI source guard allowing adapter write call sites only in the approved service and isolated adapter tests.
5. Add HTTP/service/worker negative tests, then wire every reviewed path while live submission remains disabled.
6. Complete fresh audit, PostgreSQL CI and release review before any separate manual live-enable action.

Keep PR #1 draft/open, `TRADING_MODE=PAPER`, `LIVE_ORDER_SUBMISSION_ENABLED=false`, and original `Tradepro` untouched. Phase 2 remains incomplete.


### Broker-write source guard added — 18 October 2026

The CI source-call guard and scanner tests were added in commit `04583cd35ecf5360624bc0164c7b91231a058e5e`. Workflow run #614 is pending: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123034569. It rejects production references to adapter place/modify/cancel methods outside the future `app/services/live_broker_write_service.py` and the adapter definitions. This does not establish that the central service exists or that live submission is safe. Await CI result before proceeding; then implement storage/event transaction protections and authorization foundations.


### Guard correction — 18 October 2026

The first guard workflow run (#614) failed before tests because the scanner incorrectly treated paper `ExecutionService.place_order` as a broker adapter write. The scanner was narrowed to adapter-named receivers in commit `30599b1bd8d32293b856c88cdfb4e2facaa9ce0f`. New run #615 is pending at https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123199888. Do not mark the guard complete until this run passes.


### Latest source-guard status — 18 October 2026

The AST-based scanner now ignores comments/docstrings and flags adapter-named write references. Latest CI run #617 passed the guard but is still running pytest; SQLite/PostgreSQL migration and concurrency steps have not yet completed: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123311281. Full guardrail acceptance remains pending until all workflow steps pass.
