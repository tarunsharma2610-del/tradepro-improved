# Tradepro Improved — Audit and Change Log

Audit target: `main` in this repository. The original `Tradepro` repository is read-only and has not been modified.

## Current findings

| Area / requirement | Status | Evidence / next action |
|---|---|---|
| FastAPI APIs, SQLAlchemy models/repositories | Existing; tests pass | Backend test suite passed on the current backend changes. Continue adding coverage as features change. |
| Paper market orders | Implemented, still needs operational validation | Uses Upstox LTP for simulated fills and records transaction costs and position/cash updates. Never fall back to a made-up price. |
| Order input validation | Improved | Service boundary rejects non-positive quantities, unsupported order types, missing/non-positive LIMIT prices, and a limit price attached to MARKET orders. API schema also rejects non-positive limit prices. |
| Quote price parsing | Improved | Rejects malformed, non-finite, zero, and negative LTP values before paper accounting. |
| Paper limit orders | Implemented; tests passed | Worker checks pending PAPER LIMIT orders during market passes, fills only when LTP crosses the limit, uses limit-or-better pricing, shares cost/cash/position accounting, and rejects delivery sells without holdings. Owners can cancel pending orders from the portfolio page. |
| Live order lifecycle | Partial / not enabled | Durable intent/tag recovery, risk gate, read-only snapshots, trade intake and child-order reconciliation are CI-tested. A separate unregistered atomic accounting service can promote staged trades to connection-scoped `LivePosition` + `Execution` only with an explicit fee breakdown/provenance; actual fee source is not verified and no route/worker invokes it. Full end-to-end status/cancel/accounting remains incomplete. Do not enable live orders. |
| Strategy activation | Fixed | Strategy evaluation returns HOLD for inactive strategies before contacting the broker; regression test added. |
| Live-fill accounting | Partial / unregistered | Staged-trade promotion coordinator obtains a read-only Upstox brokerage estimate, revalidates identity after async I/O, then atomically writes `Execution` + broker-scoped `LivePosition`; replay reuses persisted provenance. Non-zero daily DP minimums fail closed. Actual per-trade charges remain unverified; no route/worker invokes it. |\n| Daily risk controls | Partial | Strategy/portfolio paper-entry loss guards exist. Live gate adds absolute INR order/exposure/daily-loss limits, frequency caps, freshness/session checks and broker funds/margin checks, but its provider adapters and holiday calendar are not wired. No live order submission is enabled. |
| Broker OAuth | Improved | State is signed, expires after 10 minutes, and is bound to user/broker/connection. A nonce digest and expiry are persisted and consumed by a conditional database update, so repeated/concurrent callback attempts cannot consume the same state twice. |
| OAuth schema migration | Added; deployment not yet verified | `202608220001_oauth_state_replay.py` adds the two nullable state columns. Apply and verify migrations in a backup-safe staging environment before deploying to an existing database. |
| Upstox instrument sync / streaming | Missing | Adapter still has unimplemented instrument-sync and market-data-streaming work. Implement against current official API documentation and test with paper data. |
| Frontend dashboard | Improved | Root page is now a dashboard with portfolio/cash summaries and links to portfolios, backtests, news, broker settings, and notifications. It no longer duplicates the broker settings page. |
| Frontend typecheck/build | Verified in CI | TypeScript check and Next.js production build passed. The `lint` script runs TypeScript checking because the project uses Next.js 16, where the old `next lint` command is not available. |
| Database migrations | CI migration check passed on SQLite; staging still required | The full Alembic chain, including the OAuth nonce migration, successfully upgraded a clean SQLite database in CI. Verify against a backup and staging copy of the actual deployment database before production rollout. |

## Changes committed

1. Added a service-level inactive-strategy guard and a regression test.
2. Added signed, expiring OAuth state validation bound to the requesting user and broker connection.
3. Added persisted, one-time OAuth nonce consumption with an atomic conditional update and Alembic migration.
4. Added order validation at both the API schema and execution-service boundary.
5. Hardened last-traded-price parsing so invalid prices cannot enter paper-accounting calculations.
6. Added a worker-driven paper LIMIT matcher with crossing rules, limit-or-better pricing, cash/holding checks, and shared accounting.
7. Added an authenticated cancel endpoint and portfolio UI action for pending paper orders, with ownership and status checks.
8. Replaced the duplicate root broker-settings page with an account dashboard.
9. Updated the frontend check command for Next.js 16.
11. Added an environment-controlled emergency kill switch for automated strategy entries, with a regression test proving it blocks entry without creating a position; exits remain available.
10. Added GitHub Actions workflows for backend tests and frontend typecheck/build.

## Verification

- **Backend:** GitHub Actions run passed — **167 tests passed, 1 deprecation warning**, including the paper LIMIT matcher tests. [View backend run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39025837191).
- **Frontend:** TypeScript check and Next.js production build passed. [View frontend run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39025402726).
- The tests use SQLite and mocked broker calls; they do not prove a live Upstox session or live market-order execution works.
- The OAuth migration passed a clean SQLite upgrade in CI but has not been applied to your production database.
- No live orders have been submitted.

## Remaining high-priority work

1. Safely orchestrate the async Upstox risk snapshot collector into live preflight only after all fail-closed environment, confirmation, ownership and credential checks pass.
2. Add broker-confirmed status/fill/cancel reconciliation, partial-fill accounting and connection-scoped trade deduplication.
3. Add broker-error circuit breaker, account-level kill switch and operations/recovery runbooks.
4. Implement instrument master sync and WebSocket market data using current official Upstox documentation.
5. Verify PostgreSQL migrations, frontend build and deployment behavior in staging.


## Continuation update — 17 October 2026

- Created `HANDOVER.md` on branch `safety/fail-closed-trading-mode` to preserve the confirmed implementation state, release gates, and next steps.
- Re-inspected `ExecutionService`, the order model, strategy execution, risk engine, worker, Upstox adapter, and the live-trading safeguards design.
- Confirmed that `ExecutionService.place_order` currently creates `PAPER` orders and performs simulated accounting; the adapter's broker `place_order` method is not wired into a complete live-order lifecycle.
- Confirmed that instrument master sync and WebSocket streaming return explicit not-implemented errors, and that current risk controls are strategy-level rather than portfolio-wide.
- Implemented a fail-closed guard in `backend/app/services/execution_service.py`: order placement now refuses `TRADING_MODE` values other than `PAPER`. Added regression test `test_live_mode_fails_closed_before_creating_order` in `backend/tests/test_execution_service.py`. The test has not yet been run in this environment; CI verification is still required.
- This continuation has not placed any broker orders. Live trading remains not ready.


## Audit-driven change — 17 October 2026

- The repository audit found the existing Upstox adapter used `https://api.upstox.com/v2/order/place`, while the current official Place Order documentation marks the older host deprecated and documents `https://api-hft.upstox.com/v2/order/place`. Updated only the adapter's place-order host; other broker methods were retained unchanged.
- Added `backend/tests/test_upstox_adapter.py`, a mocked test that verifies the endpoint URL and payload without making a network request or placing a real order.
- Added `REQUIREMENTS_AUDIT.md` mapping requirements to existing code, gaps, and a prioritized change plan.
- GitHub Actions run for commit `28ac7425f1f227e42c6107821cdc5ec011054526` completed successfully after the adapter URL correction and new mocked adapter test. Later documentation-only commits triggered additional runs; the code-bearing commit's backend test and migration workflow passed. The workflow does not verify live broker behavior.


## Continuation update — 17 October 2026 (idempotency and order-size controls)

- Added optional `idempotency_key` to the order API schema and service request. A unique constraint on `(portfolio_id, idempotency_key)` is backed by migration `202610170001_order_idempotency.py`. Same-key/same-payload retries return the prior order; key reuse with a different payload is rejected. Database uniqueness arbitrates concurrent inserts, but broker-side idempotency and timeout/restart reconciliation are still not implemented.
- Added regression tests for repeated keys and mismatched payloads.
- Added `MAX_ORDER_VALUE_PCT_OF_VIRTUAL_CAPITAL` (default 25%) as a configurable single-order cap in the existing paper execution service. LIMIT orders are checked against their limit price; MARKET orders use the fetched quote. Cash/holding rejection reasons are preserved by running those validations before the cap for market orders.
- The notional cap is price × quantity in the current accounting model. Futures/options multipliers and verified lot sizes are not yet supported, so this must not be treated as a live risk limit.
- Added regression tests for LIMIT and MARKET orders exceeding the cap.
- Latest backend CI passed: **177 tests passed, 1 warning**; the full Alembic chain including `202610170001` upgraded a clean SQLite database successfully. [View run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39028572660).
- Earlier order-value-cap CI runs failed because a pre-existing insufficient-cash test received the new cap's rejection message first. Adjusted validation order so insufficient cash remains the reported reason when applicable; the latest run passed after that correction.
- No real broker orders were submitted. Live execution remains disabled and not ready.


## Second-pass audit and corrective changes — 17 October 2026

- The current branch tree contains 219 files. The review compared the implementation with the requirements matrix and examined the main execution, accounting, strategy, risk, auth, API, frontend, migration and deployment paths. This is static review plus CI; it is not a production end-to-end test.
- **Atomic paper fills:** refactored the fill transaction so the order, aggregate position, cash balance and execution row commit together. A regression test forces execution persistence to fail and confirms the order/position/cash changes roll back.
- **Strategy attribution:** added a separate `StrategyPosition` allocation per strategy and `Execution.strategy_realized_pnl`. Strategy entry/exit decisions use the strategy's own allocation, manual sells cannot consume shares allocated to strategies, strategy P&L and daily-loss checks use strategy-specific realized P&L, and duplicate strategy entries are rejected under the portfolio lock.
- Added a forward Alembic migration that backfills strategy-specific P&L and open strategy allocations from existing strategy-tagged executions. The clean SQLite upgrade passes; the backfill still needs validation against a populated staging database before production rollout.
- **Derivative segment guard:** the existing importer only loads NSE equities and does not yet normalize tick-size units or import complete derivative contract data. Backend order, strategy and backtest APIs now reject futures/options instead of treating an equity as a derivative. The UI no longer offers unsupported derivative segments.
- The current paper LIMIT matcher is implemented; stale dashboard wording was corrected. README and requirements/handover docs are being aligned with the verified state.
- Latest verified backend CI: **188 tests passed, 1 warning**, with the full SQLite migration chain successful: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39030790984.
- The latest frontend TypeScript and Next.js build checks passed after an earlier intermittent Google-font resolver failure: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39030941702.
- No real broker orders were placed. Live trading remains **NOT READY**.


## Idempotency hardening and verification — 17 October 2026

- Manual UI retry-key handling already existed and was retained.
- Strategy order submissions now use deterministic per-candle keys and refuse automated order creation when the latest candle timestamp is invalid. Key-reuse validation includes strategy ID and execution reason.
- Tests cover same-candle repeated entry, missing timestamp, and cross-scope key reuse. The first new test run failed because its assumed notional-cap threshold was wrong for the fixture's ₹500,000 virtual capital; the fixture and cap were verified, and the test now sets a deterministic 1% cap. Latest CI: 193 passed, 1 warning, SQLite migration passed, frontend TypeScript/build passed.
- Next audited area: existing Upstox order adapter and reconciliation/status foundation. Live submission remains disabled.


## Upstox order endpoint audit and fix — 17 October 2026

- Verified current official Upstox docs: legacy V2 Place Order is marked deprecated; Place Order V3 uses `https://api-hft.upstox.com/v3/order/place` and returns a list at `data.order_ids`. The adapter now uses the V3 URL; its test is mocked and checks that response shape. No real broker request was made.
- V3 modify and cancel endpoints are available, but the app's abstract adapter contract currently lacks those operations. Next step is to inspect adapter subclasses/test doubles, then add V3 adapter methods and mocked tests only. They must not be wired to live execution or change local order accounting yet.
- CI on `ded6138b93f8e18f96117f5bb4fce0ec8aeaeb1b`: backend 193 passed, 1 warning, clean migration; frontend TypeScript/build passed.


## Upstox V3 modify/cancel adapter update — 17 October 2026

- Added adapter-level V3 modify/cancel calls based on official docs, with mocked tests. The calls remain isolated and are not wired to the UI or execution service; local accounting is untouched.
- CI on `2bc21c59dc4c9b8d1cd2e38d24a611433e07d82c`: 195 backend tests passed, 1 warning, clean SQLite migration, frontend TypeScript/build passed.
- Next audit: define the preconditions for a separate live execution service, including broker order-ID list responses, idempotency, partial fills, cancellation/modify confirmation, risk controls and restart-safe reconciliation. Live remains disabled.


## Live execution readiness findings — 17 October 2026

- OAuth state binding/single-use, encrypted credentials, token expiry checks, an explicit PAPER-only order-service gate, equity-only instrument validation and read-only broker status checks already exist and are retained.
- Live readiness gaps: no full live submission service; no all-order live pre-trade exposure controls/circuit breaker; no partial-fill local state; no trade-book/position/holding reconciliation; no restart/timeout-safe submission recovery; V3 place responses can contain multiple order IDs; V3 modify/cancel adapters are not wired.
- Selected the smallest safe next change: require a non-empty matching `order_id` in the broker status response before storing the returned status. The official Upstox Get Order Details schema includes both `data.order_id` and `data.status`. This change is read-only and will use mocked tests only.


## Broker status identity validation — 17 October 2026

- Required a non-empty exact broker `order_id` match before saving a read-only broker status. Missing and mismatched IDs fail closed; local order status/fill state remains unchanged.
- Latest CI: 195 backend tests passed, 1 warning, clean SQLite migration, frontend checks passed. Next foundation is a read-only per-order trade lookup for future partial-fill reconciliation; it will not be wired into accounting in that step.


## Per-order trade lookup — 17 October 2026

- Added a read-only adapter method for Upstox `GET /v2/order/trades?order_id=...` to provide the data source needed for future partial-fill reconciliation. Mocked test verifies request and response shape. No real broker call or local accounting change.
- CI: 197 backend tests passed, 1 warning, clean SQLite migration, frontend checks passed. Next: add Order History lookup by stable tag/order ID for unknown-submission recovery.


## Read-only order-history lookup — 17 October 2026

- Added an adapter method for the official Upstox Order History API, supporting lookup by broker order ID and/or tag, with validation that blocks empty identifiers and tags over 40 characters before network access. Mocked tests cover all paths.
- First CI attempt failed due to missing `AsyncMock` import; corrected in a follow-up commit. Latest CI passed: 200 backend tests, 1 warning, clean SQLite migration, frontend checks passed.
- Next: document a broker-order state machine before implementing live execution, especially multi-order V3 responses, tag-based timeout recovery, partial fills, cancel/modify confirmation and restart safety.


## Live order state-machine design — 17 October 2026

- Added `LIVE_ORDER_STATE_MACHINE.md` before implementation. It documents current behavior, official endpoint response shapes, unknown timeout recovery, one-to-many broker order mapping, trade-level deduplication, partial-fill state transitions, confirmed modify/cancel, atomic accounting, restart recovery, risk gates and a test matrix.
- No live submission path was implemented. Next task is schema/model groundwork only, with the existing PAPER-only guard preserved.


## Broker-order schema foundation — 17 October 2026

- Added a child `BrokerOrder` table, stable local broker tag, wider status field and unique broker trade-ID metadata on executions, with additive migration 004. The migration test validates a populated pre-migration database and proves existing paper data is preserved.
- Latest CI: 201 backend tests passed, 1 warning, clean SQLite migration, frontend checks passed. New schema is not wired into any live order flow.
- Next: pure response-validation helpers for V3 order IDs, order details, history and trade payloads; then review them before a live service exists.


## Pure broker response validation — 17 October 2026

- Added pure typed parsers for V3 Place Order, Order Details, Order History and Order Trades responses with targeted malformed-data/identity/quantity/price tests.
- Corrected the parser to allow repeated order IDs in Order History because that endpoint is a status timeline, not a unique-order list.
- Latest CI: 223 backend tests passed, 1 warning, clean migration, frontend checks passed. Next is an audit of live pre-trade risk controls before any live submission service.


## Live risk audit — 17 October 2026

- The existing risk engine gates automated strategy entries on realized P&L; manual orders bypass it. Paper order value/cash/holding checks are not live controls, and unrealized drawdown is not included.
- Broker interface has no funds/margin method. Current Upstox Funds & Margin V3 (released 10 April 2026) provides `available_to_trade.total` at `GET /v3/user/get-funds-and-margin` with `Api-Version: 3.0`. Next task is read-only adapter support, not live submission.
- Live all-order exposure/loss/rate limits, stale quote/session checks and a live-account circuit breaker remain gaps. The automated strategy-entry stop must not be presented as a live account kill switch.


## Funds & Margin V3 adapter — 17 October 2026

- Added a read-only Upstox Funds & Margin V3 method and tests for endpoint, `Api-Version: 3.0`, response shape and 423 maintenance error. The response is not wired into risk checks.
- Latest CI: 225 backend tests passed, 1 warning, clean SQLite migration, frontend checks passed. Next: pure typed parsing of funds/cash/pledge values; do not use it to approve orders until the complete risk system exists.


## Funds & Margin V3 parser — 17 October 2026

- Added typed parsing for available-to-trade total, cash available, pledged margin, realized/unrealized losses and signed unsettled profit. The parser is strict about required nested structure and rejects malformed/non-finite amounts. No order approval path uses it.
- CI: 235 backend tests passed, 1 warning, clean migration and frontend checks passed. Next read-only foundation is instrument-specific margin calculation.


## Instrument margin calculation adapter — 17 October 2026

- Added read-only Upstox margin-estimate support via `POST /v2/charges/margin`, with input validation and mocked endpoint/payload/error tests.
- Latest verified CI: 238 backend tests passed, 1 warning; clean SQLite migration and frontend TypeScript/build passed. [Backend](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755714) · [Frontend](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755707).
- This does not implement live risk preflight, does not use margin results to approve orders, and does not enable live trading. Next is a bounded audit of the official response schema and current parsers.


## Margin-estimate response validation — 18 October 2026

The official Upstox Margin Details documentation specifies aggregate required_margin / final_margin values and per-instrument margins[] components. Added a pure typed parser with validation for required fields, non-empty rows, successful response status, and finite non-negative amounts, with mocked unit tests. This closes the raw-response parsing gap only. It does not implement a live pre-trade risk check, confirm available funds, or authorize orders. Live execution remains disabled. Code/test commits: 3c4dd6ac0d7d88a18916c241d28a224fc5031d5d, 6995f64429b44134edfa5985ad4f50c3b54cfcab. CI verification pending.


## Current verification state — 18 October 2026

The margin parser, tests, and follow-up documentation are committed on `safety/fail-closed-trading-mode`. The latest verified CI evidence still applies to the earlier code commit `e6abb6704b67c54f35bb5d7c2c41acd96846147d` (238 backend tests passed, one warning; SQLite migration and frontend checks passed). The GitHub integration did not return a workflow run for the new test commit/current documentation head, so the added parser tests are **not yet verified**. This is a verification gap, not evidence of failure or success. Next action is to inspect/trigger the current PR head's CI and record actual results. Live order submission remains unimplemented and disabled.


## Status correction — 18 October 2026 (supersedes stale next-step notes)

The following are now present in the branch: `BrokerAdapter.get_margin_details`, the Upstox `POST /v2/charges/margin` implementation with local request validation, pure `parse_margin_details`, and unit tests for success/error/malformed response shapes. Older notes saying the adapter method or typed parser is still missing are historical snapshots, not current status. The parser is read-only and is not used to authorize orders.

The current blocker is verification: the GitHub integration returned no workflow run and no commit status for the current PR head when checked. Earlier CI results (238 backend tests, one warning, migration/frontend checks green) belong to an older commit and do not verify the margin parser changes. No pass/fail conclusion is possible from the available evidence. Inspect or trigger the configured workflow from GitHub Actions and record actual results before advancing.

`MASTER_ROADMAP.md` is now the current sequencing guide. After this verification gate, the next implementation phase is a separate, initially unregistered `LiveExecutionService` with mocked tests, while preserving the current PAPER-only execution guard. Do not merge the draft PR, place real orders, or enable live trading.


### 18 October 2026 — broker-reconciliation CI investigation

- Added regression coverage for an Upstox status-check failure response; commit `2625191740554efe5a41f99eff15306ebd68ec5c`.
- Investigated workflow run `39028914012` (`Backend pytest`): it ran against the earlier PR merge checkout `d04dfa5` and reported `177 passed, 3 errors`; all three errors were fixture setup failures (`portfolio` not found) in that checkout. The current branch version of `backend/tests/test_broker_reconciliation.py` defines the fixture, but this alone is not proof the current branch passes.
- The GitHub integration's commit-SHA workflow lookup and combined-status lookup returned no results for the current branch head. The old failed run is not a valid test of current head `2625191740554efe5a41f99eff15306ebd68ec5c`; current CI remains unverified.
- Next: inspect the latest PR run in GitHub Actions (PR workflows check out the generated merge ref), confirm backend tests, migration and frontend results, and fix only current-head failures. Do not claim green CI or enable live trading.


## Authoritative status and next audit — 18 October 2026

This section supersedes stale next-step notes above. The branch contains a typed `parse_order_trades` parser, a `BrokerTrade` data type, broker child-order schema, nullable broker references on executions, and a uniqueness constraint on `(broker_name, broker_trade_id)`. Adapter trade lookup is read-only; no confirmed-trade ingestion service currently connects it to durable accounting.

**Current task:** audit and then implement broker-confirmed trade/fill ingestion with transaction-safe idempotency. Before changing code, verify the model/migration schema, local order-to-broker-child mapping, broker connection/account identity, user ownership, and existing accounting transaction semantics. Specifically investigate whether global `(broker_name, broker_trade_id)` uniqueness incorrectly couples separate broker accounts; the current schema does not include broker connection identity in that key. Do not assume this is safe for multiple accounts.

**Verification:** current PR #1 head observed as `540e1285d3de934b43829948a1b60c67658d1343`; the GitHub integration returned no workflow runs or combined statuses for that head. Current-head CI remains unverified. Older CI results are historical and must not be attributed to the current head. Live order submission remains absent/disabled; the existing PAPER-only execution guard must remain intact.


## Broker trade ingestion implementation — 18 October 2026 (verification pending)

Added `BrokerTradeRecord` and `BrokerTradeIngestionService` to stage normalized broker-confirmed trades independently from accounted `Execution` rows. The service enforces LIVE order scope, tenant ownership, exact local-order/child-order mapping, user broker-connection binding, side/instrument consistency, positive finite price and quantity, replay identity consistency, and parent-order quantity bounds. Exact replays are counted and skipped; conflicting trade-ID reuse is rejected.

The audit also identified that broker order IDs and execution trade IDs must be scoped by connection/account, not globally by broker name. Migration `202610180006` changes those uniqueness keys and backfills legacy connection links where safely identifiable. Migration `202610180005` adds the intake table with a unique `(broker_connection_id, broker_trade_id)` constraint.

**Accounting boundary:** this is durable intake only. It intentionally does not change local order status, broker child fill aggregates, positions, cash, or P&L, and it does not write into `executions`. That prevents estimated fees or an incomplete live-accounting flow from corrupting paper accounting. A later step must reconcile actual costs and promote staged fills into live accounting atomically.

Tests added/updated: `backend/tests/test_broker_trade_ingestion.py` and `backend/tests/test_live_broker_schema_migration.py`. Current head `32eea17c141d4cfbc727eed2ff2a1b40d21dbba3`; workflow/status lookup returned no results for that SHA. Local clone/test execution was unavailable due network DNS failure. **No test pass is claimed for this implementation yet.**


### Migration backfill coverage added — 18 October 2026

Added a regression test that seeds a legacy broker child order and execution at revision 005, upgrades to head, and asserts migration 006 backfills both broker connection IDs from the owning user's connection. Latest head: `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`. Current-head CI remains unverified.


### Final verification clarification — 18 October 2026

The last code/test commit is `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`; subsequent documentation updates advanced the branch without changing code. At the check, PR head `1b0056d9739cd55d50cd5484cddf955aa8bf07db` had no workflow run/status returned. The intake/migration changes remain unverified until backend tests and `alembic upgrade head` run on the current code.


## Phase 2 continuation audit — 18 October 2026 (broker intake hardening)

A focused review of `BrokerTradeIngestionService` found two fail-closed gaps: connection resolution was performed by user/broker and checked against the child row afterward, rather than resolving the exact child-order connection directly; and an absent trade instrument token was accepted, preventing exact instrument identity validation. Corrected in `2cdbbe290f8b661cb91110dbb4e165fcef36f800`: resolve by `broker_connection_id + user_id + broker`, reject unbound child orders, and require the trade token to match the local instrument. Non-text side data now raises a controlled validation error. Regression coverage was added in `b780c39f770a6839dab0af63fc424c341eff9d70` for foreign-connection binding, absent instrument identity and malformed side data.

The service remains a staging-only intake ledger and is not connected to a route/worker/live order path. It does not mutate execution/accounting records. Current code/test target `b780c39f770a6839dab0af63fc424c341eff9d70` has no associated Actions run visible through the connected GitHub integration. Local pytest/migration execution was unavailable; these changes remain unverified until the workflow runs on this code.


### Legacy unbound child-order regression — 18 October 2026

Added a test for a legacy `BrokerOrder` with no `broker_connection_id`; intake must reject it without writing a trade record. Test commit: `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`. Latest code/test target is this SHA; Actions/test verification remains pending.


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


## Audit addendum — 18 October 2026: integration test of existing reconciliation lifecycle

- The audit identified a verification gap, not a missing coordinator: earlier coordinator tests injected fake child-reconciliation and promotion collaborators. This change addresses that gap by composing the real services in `backend/tests/test_live_order_fill_reconciliation_coordinator.py`.
- Commit: `b5783d421f64fcb8e7f1d75f1af5185fd9029f59` ([diff/commit](https://github.com/tarunsharma2610-del/tradepro-improved/commit/b5783d421f64fcb8e7f1d75f1af5185fd9029f59)).
- Only broker read payloads and the charge estimator are mocked; the real child reconciliation, ingestion, coordinator, promotion, and accounting logic is exercised. Tests cover replay idempotency, sibling failure blocking promotion, and paper-account isolation.
- Evidence status: **CI has not yet been confirmed for this commit**; therefore these tests are added but not yet classified as passing. No live API calls or order-write calls were made.


### Audit follow-up — latest integration test refinement

Commit `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` supersedes the initial test commit. Integration scenarios now begin without staged rows, forcing the real trade-ingestion service to insert the adapter-returned mock trades. CI for this exact SHA remains unverified; the test is not yet classified as passing.

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


## Audit addendum — partial promotion and safe retry

- Commit `1a3475c69d3a93ece7bfad22ace4dce52231bfa1` adds an integration regression for the real reconcile → ingest → promote → account path when a later fill's charge estimation fails once.
- The test is designed to prove the first successful fill is not duplicated on retry and the unprocessed fill is eventually accounted; paper-account isolation and no broker-write calls are asserted.
- **Evidence status: pending exact-SHA CI**. This is added test coverage, not a verified pass. Runtime remains unregistered and live trading remains disabled.


## Audit addendum — persistent account safety state (verification pending)

- Added a durable account-wide kill switch and broker-error circuit-breaker service using the existing safety state/event models. Migration revision `202610180009` creates the state and append-only event tables.
- Unit coverage targets missing-state denial, default tripped latch, threshold-based circuit trip, event idempotency, manual-reset gates, stale health and unknown circuit states.
- Positive safety properties: scope is user+broker rather than portfolio; state read errors deny; broker success cannot silently close an open circuit; manual reset requires a recent passing health event and cleared error count.
- Remaining risks: CI/migration result for head `57939799b7e8b436d5095924b86a89ce380a956e` is unverified; no PostgreSQL concurrency test yet; service is not integrated into the preflight caller and has no authenticated operator API; no real broker calls were made.
- Do not classify this as release-ready. Keep order submission disabled and PR #1 draft/unmerged.


### Test correction addendum — c97be866828bd47a23f22fc44fac2d3359e70f35

The manual-reset regression was corrected so each expected denial occurs for the right precondition: no health check, then nonzero broker-error counter despite a passing health check. It then clears the counter with broker success and records a new passing health check before testing reset. Latest code/test SHA is `c97be866828bd47a23f22fc44fac2d3359e70f35`; CI and migration results remain unverified.

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


## Security-control API readiness review — 18 October 2026

Static source review is recorded in [SECURITY_CONTROL_ENDPOINT_AUDIT.md](SECURITY_CONTROL_ENDPOINT_AUDIT.md), commit [10d87d9d9010b2c48ebcf25c832a2ea574100889](https://github.com/tarunsharma2610-del/tradepro-improved/commit/10d87d9d9010b2c48ebcf25c832a2ea574100889). Existing auth and tenant controls provide a useful baseline, but the system is **not ready for a live safety-control endpoint**. There is no operator audit visibility endpoint or distinct safety permission model; step-up authentication, CSRF policy, strict event metadata, atomic state/event persistence and database-enforced audit immutability remain design gaps. Malformed JWT subject handling and failure-injection/HTTP-level negative tests should be addressed. No endpoint was created and no live order was submitted. Treat this as a static review only, not a penetration test or production security sign-off.


## Order-entry and broker-write inventory — 18 October 2026

Added [ORDER_ENTRY_PATH_INVENTORY.md](ORDER_ENTRY_PATH_INVENTORY.md), commit [a477489c7e2d5b6883c299c1e9a8aee1cbef055f](https://github.com/tarunsharma2610-del/tradepro-improved/commit/a477489c7e2d5b6883c299c1e9a8aee1cbef055f). Static review found the manual portfolio order route and both strategy evaluation paths call the shared PAPER-only ExecutionService; it rejects non-PAPER mode. The Upstox adapter contains order-write primitives, but no production call site was found in the reviewed paths. Live recovery persists intents and reads recovery history without submitting; it currently uses LiveExecutionService directly rather than LivePreflightCoordinator, leaving an account-safety/snapshot composition gap. No code was wired or enabled. This is a static path inventory, not proof of runtime impossibility or a production sign-off.


## Audit addendum — central broker-write design (18 October 2026)

The design-only artifact `CENTRAL_BROKER_WRITE_BOUNDARY_DESIGN.md` now specifies a single typed broker-write boundary and the controls needed before endpoint implementation. Current findings remain open: live intent recovery bypasses the safety-aware coordinator; no dedicated least-privilege safety permissions or operator audit-history endpoint exists; recent-MFA step-up and CSRF/Origin policy are not established; database-level event immutability is not demonstrated; malformed JWT subject parsing can escape as a non-normalized error; and no CI guard yet prevents new direct adapter write call sites.

No code paths were wired or enabled by this design checkpoint. This is not a penetration test, runtime trace, broker sandbox verification, or release sign-off. Live submission remains disabled.


### Source-call guardrail status — 18 October 2026

A static source guard now scans production app Python sources for references to adapter `place_order`, `modify_order`, and `cancel_order`, with only the exact future central service path allowlisted (commit `04583cd35ecf5360624bc0164c7b91231a058e5e`). Its unit tests and CI run #614 are pending verification: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123034569. This is a preventive CI guard, not proof against dynamic dispatch/reflection and not a substitute for a complete call-path audit.


### Verified broker-write guard — 18 October 2026

The AST-based source guard passed CI run #617 on code SHA `bdf208efcc32b44a6367157dd2ab0aab946e6574` (402 passed, 4 skipped, 1 warning; SQLite/PostgreSQL migrations passed; four PostgreSQL concurrency tests passed): https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123311281. This reduces accidental direct adapter-write regressions but does not establish end-to-end enforcement or protect against dynamic dispatch. All earlier security/control design gaps remain open until implemented and tested.


## Safety-event storage hardening audit addendum — 18 October 2026

Implemented: request fingerprints for new safety events; idempotency mismatch denial; unique per-state state-version constraint; SQLite/PostgreSQL triggers rejecting UPDATE/DELETE; rollback regression coverage proving safety state is unchanged when event persistence fails; PostgreSQL direct-mutation rejection test; and optional expected-version validation on manual reset.

Limitations: historical events have a NULL fingerprint and cannot be proven equivalent on replay, so the service rejects such replays rather than assuming equivalence. The service accepts an omitted reset expected-version for compatibility; any future safety-control endpoint must require it. Triggers prevent ordinary row UPDATE/DELETE but do not protect against a privileged database owner disabling/dropping them. Exact-head CI run `39124312326` was pending at this checkpoint; the preceding successful run does not include all final changes. This is not production security sign-off.


### Expected-version regression-test status

Latest run #39124312326 failed one test due to the test retaining a mutable ORM state reference, not due to a demonstrated safety bypass. The test was corrected to snapshot the pre-mutation version in commit `6cd0ced108e35d715359d649a463d80709dd1fb1`. Verification of this correction is pending in run #39124498280. Do not represent storage hardening as fully verified until that run passes.


### Verified audit storage controls — 18 October 2026

Run #625 passed on code/test SHA `6cd0ced108e35d715359d649a463d80709dd1fb1`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39124498280. Backend suite 406 passed / 5 skipped; migrations passed on SQLite and PostgreSQL 16; PostgreSQL integration 5 passed, including event UPDATE/DELETE rejection. This verifies tested migration/trigger behavior under CI but is not a production penetration test or protection against a privileged database owner. Endpoint enforcement and central writer remain absent.


## 18 October 2026 — authorization foundation in progress

- Added explicit per-user safety permission grants and a default-deny dependency for status read, audit read, kill-switch trip and reset. Platform is_admin is not an implicit grant.
- Added malformed JWT subject normalization to 401 and a reusable Origin guard for cookie-authenticated mutation requests, plus focused regression tests.
- Not complete / not yet verified: recent-MFA step-up, trusted grant provisioning, attaching guards to safety endpoints, endpoint-level cross-tenant negative tests, and current-head CI. No safety-control routes are exposed and live submission remains disabled.

### Follow-up correction — 18 October 2026

The Origin guard now requires an exact Origin serialization match (including rejecting a trailing slash), and unused imports were removed from the user model. Follow-up commits: f7c08e2605fb7f7828792154570af79cf5ccf724 and 4337d0ce4ef645914f32c56db87c81699c04763e. CI/status lookup has returned no run/status for the authorization changes; do not claim tests or migration passed until a workflow result is tied to the code/test SHA. Recent-MFA step-up and route wiring remain outstanding.

## Superseding checkpoint — recent-MFA step-up foundation (18 October 2026)

- Added a dedicated `POST /api/v1/auth/mfa/step-up` challenge. It requires an authenticated active user, MFA already enabled, fresh password verification and a valid TOTP code; it is rate-limited and applies the configured same-origin guard to cookie-authenticated requests. Successful challenges return a purpose-bound `step_up` JWT with `scope=safety.reset`, `amr=[pwd,totp]`, a verification timestamp, and a five-minute expiry. Failed credentials are audited without logging credentials or the token.
- Added `require_recent_safety_mfa`, which requires the separate `X-Safety-Step-Up` header, validates token type and purpose, verifies recent MFA and issuance timestamps, and binds the token to the authenticated user. It is not yet attached to a safety reset route because no safety-control routes have been exposed.
- Added unit/dependency tests for missing/wrong-scope/stale/user-mismatched step-up tokens and HTTP tests for success, invalid password and accounts without MFA. These tests are committed but **not yet verified by a GitHub Actions run for the latest code/test SHA**; do not claim they pass until exact-head CI is green.
- Latest code/test commit for this checkpoint: `ee8968f9d7d8698703e59911c7091d5f7c870c23`. Related commits: `325d9a854c05bb7dead6f6f626bf749383804a8e`, `9b65f92b060c0745c1e84e535ec5397cdf490b5d`, `1450a3d0dd8c3629e72142fe06cec699be7202f0`, `0bf5f86d9dd07ecaebe10b93149841647dfbccdf`, `1afd892fb1fa7aaf6c1b0028c248b59e06ec9994`, `aaad1d020cb629cb6d554bd08ff02d25fb1c4666`, and `ee8968f9d7d8698703e59911c7091d5f7c870c23`.
- Remaining authorization gates: trusted safety-permission provisioning, tenant-scoped/paginated audit reads, route-level permission + Origin + step-up enforcement, comprehensive negative HTTP tests, and latest-head CI. The helper does not solve these by itself. The safety status/audit/trip/reset routes and central broker-write service remain absent/unwired.
- Keep PR #1 draft/open/unmerged, keep `TRADING_MODE=PAPER` and `LIVE_ORDER_SUBMISSION_ENABLED=false`, never call broker order-write endpoints, and leave the original `Tradepro` repository untouched. Phase 2 remains incomplete.

### Superseding MFA guard correction

The step-up verifier now also denies a token if the authenticated user's MFA has since been disabled; regression coverage was added. Latest code/test commit: `ecf09e800c0dc7fc83d200d603f510348433aa58` (guard change `8a46241e766b9504c3a9bc3ba182043bac98a75d`). Exact-head GitHub Actions/status remains unverified; prior CI results do not cover this change. This remains a foundation only: the dependency is not wired to a safety-reset endpoint because those endpoints do not yet exist.

## Superseding checkpoint — audited safety-permission provisioning (18 October 2026)

- Added `PUT /api/v1/admin/users/{user_id}/safety-permissions` for one explicit grant/revoke operation at a time. The request schema only accepts the four defined `safety.*` scopes; arbitrary scopes are rejected by validation.
- The actor must be a platform admin, must pass the five-minute user-bound password+TOTP step-up, and cookie-authenticated mutations must pass the configured Origin guard. `is_admin` alone is not enough. Self-grants are rejected; revocation remains allowed for an admin's own account to support removal of access.
- Target user's permission list and the audit record (`safety.permission.grant/revoke`, actor ID, target ID and scope) are committed in the same DB transaction. The route does not grant access to read other users' audit data and does not expose the safety status/audit/trip/reset endpoints.
- Added HTTP regression tests for missing step-up denial, self-grant denial, and grant/revoke behavior with audit evidence. **These tests have not been executed in this environment and exact-head CI has not been confirmed.** Treat them as committed, unverified tests, not passing tests.
- Relevant commits: endpoint `ed1cae900a326a4922dbf42a5dbe2b7ed9d50d13`; constrained schema `8a50e8176d25e26a58f52649b21ab01cafa60cad`; test additions `b1b326e7ff409b84d2feab438f69275678939d2f`; formatting follow-up `1d464907a2aec9d0a4e257cb960bf32b24d032ee`.
- Remaining gates: CI on latest code/test SHA, independent review of the permission-provisioning threat model, tenant-scoped audit reads, safety status/audit/trip/reset routes with explicit permission enforcement, state/event atomicity at endpoint level, central broker-write service and end-to-end path enforcement.
- Continue to keep PR #1 draft/open/unmerged and keep live order submission disabled. Phase 2 is incomplete; original `Tradepro` remains untouched.
