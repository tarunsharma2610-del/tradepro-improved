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
| Live order placement | Incomplete / not enabled | Shared execution service still records PAPER orders; broker order placement and execution reconciliation are not complete. Do not enable live orders. |
| Strategy activation | Fixed | Strategy evaluation returns HOLD for inactive strategies before contacting the broker; regression test added. |
| Daily risk controls | Partial | Existing strategy-level daily-loss guard remains. An environment-controlled emergency switch now blocks new automated strategy entries while allowing exits. Portfolio-wide loss, exposure, and order-frequency caps still need implementation and tests. |
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

1. Add durable order idempotency/reconciliation before any live-trading implementation. The automated-entry kill switch is now present but must be included in deployment configuration and operational runbooks.
2. Add portfolio-wide loss/exposure controls and an exchange holiday calendar.
3. Implement instrument master sync and WebSocket market data using current official Upstox documentation.
4. Verify the Alembic migration path in staging and check the current deployment configuration.
5. Review remaining analytics and backtest behavior against the requested product requirements.


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
