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

### Implemented and verified on current CI head
- Broker child-order schema and connection-scoped trade identity, normalized broker-trade staging, idempotent ingestion, ownership checks, conflicting replay rejection, and regression tests.
- Upstox response parsers for place-order IDs, order details/history/trades, Funds & Margin V3 and margin estimates.
- Separate unregistered `LiveExecutionService` preflight foundation. Requires default-off `LIVE_ORDER_SUBMISSION_ENABLED`, `TRADING_MODE=LIVE`, explicit confirmation, a supplied risk gate, valid owned portfolio/instrument, and usable broker connection/token. It has no submit method/path and makes no DB/order/accounting side effects.
- GitHub Actions run [#39109587876](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39109587876) on `677fcf882e0ce1e6e02be3bb8df0d074b8fbf220`: **286 passed, 1 warning**; SQLite `alembic upgrade head` succeeded.

### Immediate next task
Build and test stable idempotency/tag recovery for ambiguous submissions, without calling Place Order or wiring any route/worker. Inspect current `Order.idempotency_key`, `broker_tag`, and order-history-by-tag adapter first. A timeout is unknown, not rejection; no blind retry. The next change must prove a retry cannot submit a duplicate.

## Release blockers
- Current PR CI for the new margin parser/tests is not confirmed.
- A complete live order lifecycle and broker reconciliation are not verified end-to-end.
- Live risk controls, account-level kill switch, OAuth/token operational recovery and production prerequisites require further verification.
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

- Latest verified code/workflow SHA: `677fcf882e0ce1e6e02be3bb8df0d074b8fbf220`; subsequent commits only update documentation. Current branch head after those docs commits: `7fb582f5ce75165f178e296472beb0a50cd03ac9`.
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
