# Tradepro Improved — Handover

## Scope and repository safety
- Work only in `tradepro-improved`; do not modify the original `Tradepro` repository.
- Current work branch: `safety/fail-closed-trading-mode`.
- Keep live automated trading disabled. Never place real orders as a test.

## Confirmed from repository inspection
- The app has a FastAPI backend, SQLAlchemy models, strategy evaluation service, background worker, and Upstox adapter.
- Paper market orders use Upstox quotes for simulated fills; paper LIMIT orders are matched by the worker.
- The emergency switch `AUTOMATED_ENTRIES_ENABLED=false` blocks automated entries while allowing strategy exits.
- The current shared `ExecutionService.place_order` creates orders with `trading_mode="PAPER"` and performs local simulated accounting. It does not submit orders through the broker.
- The Upstox adapter contains a broker `place_order` method, but its existence does not mean the application has a complete or safe live-execution path.
- Instrument-master sync and market-data WebSocket streaming are explicitly unimplemented in the adapter.
- Strategy-level daily-loss protection exists. The safety branch adds a portfolio-wide realized-loss guard for automated strategy entries (default 2%) and a single-order paper notional cap (default 25% of starting virtual capital). The order cap applies to manual and automated paper orders but uses price × quantity; derivative lot/multiplier sizing is not verified. Portfolio-wide exposure and broker-error circuit breaker remain gaps.
- The audit reports CI results of 167 backend tests passing and a successful frontend typecheck/build. These are historical CI results, not a fresh run during this continuation.

## Priority order
1. **Current next task:** audit `BrokerOrder`, execution/fill models, migrations and reconciliation services before implementing transaction-safe broker trade/fill idempotency and partial-fill aggregation.
2. Add mocked tests for repeated trade IDs, concurrent/replayed intake, quantity aggregation and transaction rollback. Preserve PAPER accounting and prevent duplicate fills.
3. Keep the async preflight coordinator unregistered from API routes/workers. Keep `LIVE_ORDER_SUBMISSION_ENABLED=false`, `TRADING_MODE=PAPER`, and the existing `ExecutionService` PAPER-only.
4. After fill-intake foundations, complete broker-confirmed status/fill/cancel reconciliation, account-level kill switch and broker-error circuit breaker.
5. Run backend tests, SQLite/PostgreSQL migration checks where available, frontend typecheck/build and staging checks. Do not merge PR #1 without explicit authorization.

## Additional risk guard — safety branch
- `PORTFOLIO_DAILY_LOSS_LIMIT_PCT` defaults to 2.0. Once today's realized losses across all fills in a portfolio reach that percentage of starting virtual capital, the existing strategy risk engine blocks new automated entries for that portfolio.
- Set it in the backend environment; use 0 only if intentionally disabling this additional guard. It is not a live-trading risk control and does not intercept manual order requests.
- Targeted tests cover losses just below, exactly at, and above the threshold. CI must confirm them before merge.

## Additional request idempotency — safety branch
- API order requests may include `idempotency_key` (8–100 safe characters). Clients should reuse the same key only when retrying the same request after a timeout.
- A unique database constraint scopes keys to each portfolio. Matching retries return the existing order; changed payloads with the same key are rejected.
- This protects app-level request retries. It does not resolve unknown broker outcomes, reconcile after a process crash, or provide broker-side idempotency. CI/migration checks must pass before merge.

## Additional single-order value cap — safety branch
- `MAX_ORDER_VALUE_PCT_OF_VIRTUAL_CAPITAL` defaults to 25.0. Paper MARKET orders are checked against the fetched quote; paper LIMIT orders against their limit price.
- The check rejects orders above that percentage of starting virtual capital and is configurable through the backend environment. Set to 0 only to intentionally disable it.
- This is a per-order notional guard, not a total exposure control. Futures/options contract sizing and multipliers are not verified, so it must not be treated as a live risk limit.

## Release gate
Live trading remains **NOT READY** until broker execution, durable duplicate prevention, broker-state reconciliation, risk limits, credential handling, session expiry, operational controls, and relevant end-to-end tests have all been verified. No real orders are authorized by this handover.

## Implementation update — fail-closed trading mode
- `backend/app/services/execution_service.py` now rejects order placement unless `TRADING_MODE` is exactly `PAPER` (case/whitespace normalized). This blocks LIVE and unknown values before portfolio/order processing.
- Added regression test `test_live_mode_fails_closed_before_creating_order` in `backend/tests/test_execution_service.py`; it asserts LIVE mode raises and creates no order.
- These changes are committed to the safety branch, but tests have not been executed in this environment. CI must pass before merge. This guard is a protective gate, not a live-execution implementation.


## Audit-driven adapter correction
- Repository-wide requirements review is recorded in `REQUIREMENTS_AUDIT.md`.
- Updated `UpstoxAdapter.place_order` to use the current official `api-hft.upstox.com/v2/order/place` host; other adapter methods were not changed.
- Added `backend/tests/test_upstox_adapter.py` using a mocked `_post` method. It verifies URL and payload only; no network request or real order is sent.
- Awaiting CI on the latest branch commit before considering this adapter correction verified.


## Read-only broker reconciliation foundation — safety branch
- Migration `202610170002_broker_status_metadata.py` adds nullable `broker_order_id`, `broker_status`, `broker_status_checked_at`, and `broker_status_error` fields.
- `BrokerReconciliationService.check_order_status(user_id, local_order_id)` checks ownership, requires `trading_mode=LIVE`, a persisted broker ID, and a usable Upstox token. It calls the existing adapter's order-status endpoint and verifies a returned order ID if present.
- It records the broker's raw status only. It intentionally does **not** infer local fills/cancellations or mutate positions/cash. No API/worker calls it yet and no live orders can currently be submitted by this application.
- Mocked tests cover a valid status response, PAPER order refusal, and mismatched broker order IDs. CI must pass before merge.


## Broker status API
- Authenticated endpoint: `GET /api/v1/portfolios/{portfolio_id}/orders/{order_id}/broker-status` (prefix may be configured by the app router).
- It verifies portfolio ownership and delegates to the read-only reconciliation service. It cannot place orders and will reject PAPER orders or LIVE orders without a stored broker ID/session.
- This endpoint is not evidence that live order placement is implemented. Do not enable live mode based on this status endpoint alone.


## Current continuation state — 17 October 2026

- Latest branch code is on `safety/fail-closed-trading-mode`; original `Tradepro` remains untouched.
- Paper fill accounting now commits order status, aggregate position, cash and execution together. Regression test deliberately fails execution persistence and verifies rollback.
- Added `StrategyPosition` allocations and strategy-specific realized P&L. Strategy evaluation no longer treats any portfolio-level position as its own, and manual sells cannot consume shares reserved to a strategy. The manual order UI now sends a stable idempotency key and reuses it for retries until success or payload changes. The migration backfills legacy strategy executions and open allocations; validate that backfill against a populated staging database before deploying.
- Futures/options are now rejected in order, strategy-create and backtest paths until full derivative instrument metadata, tick-size units, lot sizing and contract risk controls are verified. The frontend reflects this restriction; do not re-enable F&O dropdowns before the backend supports them.
- Latest verified backend CI: **188 tests passed, 1 warning**, plus clean SQLite migration upgrade: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39030790984.
- Frontend TypeScript passed, but the latest Next.js build failed in the Google-font resolver; an earlier build of unchanged frontend code passed. Re-run before merge and treat the build as unresolved until latest CI passes.
- Next: validate migration backfill on populated staging data; add evaluation-level de-duplication for strategy scheduling; address remaining instrument-master/tick-size gaps; keep live trading disabled.


## Mandatory continuation checkpoint — 17 October 2026

- Read `PROJECT_INSTRUCTIONS.md` and `PROGRESS.md` first at the start of every session.
- Latest verified code commit before the instruction/progress documentation commit: `ac93eb82688d573f9839da48ef1182d9929e56c4`.
- CI at that commit: backend **189 passed, 1 warning** plus clean SQLite migration; frontend TypeScript and Next.js build passed. Links are recorded in `PROGRESS.md`.
- Next task: create a populated pre-migration regression test for `202610170003_strategy_position_attribution.py`. Inspect migration/test/CI setup first; do not alter migration logic unless the test proves a defect.
- Live trading remains not ready; PR #1 is draft/open/unmerged. Original `Tradepro` remains untouched.


## Migration backfill test completed — 17 October 2026

- Added `backend/tests/test_strategy_position_migration.py` to upgrade a populated legacy database from Alembic revision `202610170002` to head.
- It verifies per-execution strategy P&L attribution, closed and open strategy allocations, weighted average entry price, legacy over-sell handling, preservation of aggregate portfolio positions/cash, and a second no-op upgrade.
- CI passed on commit `1fe681246cb88a9505302a1763128c51ab72802d`: **190 tests passed, 1 warning**, and SQLite migration upgrade succeeded. Frontend TypeScript/build also passed for that commit.
- See `PROGRESS.md` for current task sequence. Next task is to audit existing order idempotency call sites and repeated strategy evaluation before changing any code.


## Strategy idempotency hardening completed — 17 October 2026

- Audit found that manual UI order submission already retained its idempotency key on failed requests, so that workflow was retained unchanged.
- Strategy entries/exits now supply a deterministic key scoped to strategy ID, action side and latest candle timestamp. Automated entry/exit is skipped if the latest candle timestamp is unavailable, because a safe retry key cannot be constructed.
- Both idempotency checks compare `execution_reason` and `strategy_id`, preventing a reused key from returning a manual order for a strategy request or vice versa.
- Tests cover repeated same-candle entry, missing timestamp, and cross-scope key reuse. One initial test run failed because the test assumed ₹30,000 exceeded the default cap despite the fixture having ₹500,000 capital; the exact fixture value was checked, and the test was corrected to set a deterministic 1% cap. Latest backend suite passed: **193 passed, 1 warning**; SQLite migration and frontend checks passed.
- Latest verified code commit: `e9f8b7bb56f3300d1016195a773a26845d94d717`. See `PROGRESS.md` for links and the next live-execution audit task.


## Upstox V3 place-order endpoint correction — 17 October 2026

- The official Upstox docs mark the legacy V2 place-order page as deprecated and document Place Order V3 at `https://api-hft.upstox.com/v3/order/place`. V3 returns `data.order_ids` (a list), not the V2 `data.order_id` shape.
- Updated only the existing adapter method and its mocked regression test; it remains unconnected to the paper execution path. No live orders or real network requests were made.
- Verified commit: `ded6138b93f8e18f96117f5bb4fce0ec8aeaeb1b`; backend **193 passed, 1 warning** and clean SQLite migration; frontend TypeScript/build passed. See `PROGRESS.md`.
- Next: audit adapter subclasses and add the official V3 modify/cancel methods with mocked tests, without wiring them into live execution.


## Upstox V3 adapter methods completed — 17 October 2026

- The `BrokerAdapter` contract now includes `modify_order` and `cancel_order`; Upstox implements them using the official V3 endpoints. Requests are mocked in tests; no real network requests or orders were sent.
- The methods are not connected to the UI or `ExecutionService`, and do not change local order status, positions or cash. A successful cancel/modify request is not treated as final broker state.
- Latest verified code commit: `2bc21c59dc4c9b8d1cd2e38d24a611433e07d82c`: backend **195 passed, 1 warning**, clean SQLite migration; frontend TypeScript/build passed.
- Next: audit risk/instrument/auth/order-state/reconciliation prerequisites for a separate live execution service. Live trading remains disabled. See `PROGRESS.md`.


## Live execution readiness audit — 17 October 2026

- `ExecutionService.place_order` remains fail-closed for anything other than PAPER.
- OAuth state binding/single-use and encrypted token storage exist; expired tokens are rejected, but token refresh/reconnection automation is missing.
- Instrument validation is intentionally equity-only. Existing risk limits are not a complete live/manual order risk system; portfolio exposure controls and a broker-error circuit breaker are missing.
- The local order model has no `PARTIALLY_FILLED` state. Reconciliation only records a read-only broker status and deliberately does not mutate fills, cash or positions. No trade-book reconciliation or restart-safe live submission lifecycle exists.
- Upstox V3 place-order response uses `data.order_ids` (plural list); adapter modify/cancel methods exist but are not wired. See `PROGRESS.md` for the current focused task: require a matching broker order ID in status responses before saving status.


## Broker status identity hardening completed — 17 October 2026

- The official Upstox Get Order Details schema documents both `data.order_id` and `data.status`. The read-only reconciliation service now requires a non-empty returned ID and rejects mismatches before recording the status.
- Added a regression test for a status response that omits the ID. It confirms local order status remains PENDING and no fill timestamp is written.
- Latest verified code commit: `9f1e1300acc15f85d8abf1e29e73de34f6ca14f3`: backend **195 passed, 1 warning**, clean SQLite migration; frontend TypeScript/build passed.
- Next: add a read-only per-order trade lookup method for future partial-fill reconciliation. Do not wire it to local accounting yet. See `PROGRESS.md`.


## Per-order trade lookup completed — 17 October 2026

- Added read-only `get_order_trades(access_token, order_id)` to the broker interface and Upstox adapter, using the official `GET /v2/order/trades?order_id=...` endpoint. Mocked test validates URL, query and trade response shape; it does not contact Upstox.
- Latest verified code commit: `ebda043d4537353529007b8f3aa1aacceb13d4c4`: backend **197 passed, 1 warning**, clean SQLite migration; frontend TypeScript/build passed.
- Next: add read-only Order History lookup by stable tag or order ID to support safe recovery when a submission response is lost. No live submission will be enabled. See `PROGRESS.md`.


## Order-history lookup completed — 17 October 2026

- Added read-only `get_order_history(access_token, order_id=None, tag=None)` using the official `GET /v2/order/history` endpoint. At least one non-empty identifier is required; tags over 40 characters are rejected before a network call. Mocked tests cover tag-only, order-ID-only and invalid queries.
- The first CI run exposed a missing `AsyncMock` import in the new invalid-query test. The CI log was inspected, the import was fixed in the follow-up commit, and latest CI passed: **200 tests passed, 1 warning**, clean SQLite migration, frontend TypeScript/build passed.
- Latest verified code commit: `8b66df970d2dda91c060583ed6065c0101cd7837`. Next: create a live order state-machine design before implementing any live submission. See `PROGRESS.md`.


## Live order state-machine design completed — 17 October 2026

- Added `LIVE_ORDER_STATE_MACHINE.md` as a design-only artifact. It covers Upstox V3's multiple `data.order_ids`, stable tag recovery, unknown submission timeouts, broker-confirmed statuses, trade-ID deduplication, partial fills, cancel/modify confirmation, restart recovery, required schema changes, risk gates and test/release criteria.
- No live execution code was added or enabled. The paper-only gate remains unchanged.
- Next task: add an additive schema/model foundation for broker child orders, trade-ID deduplication and partial-fill status, with tests only; do not wire execution yet. See `PROGRESS.md`.


## Additive broker-order schema foundation completed — 17 October 2026

- Added `BrokerOrder` rows for one-to-many local-order to broker-order mapping, a unique nullable `Order.broker_tag`, expanded `Order.status` length, and nullable `Execution` fields for broker child-order reference and unique broker trade ID per broker.
- Added forward migration `202610170004_live_broker_order_state.py` and a populated-database migration regression test. Existing paper order/execution values are preserved; the test verifies multiple child IDs, duplicate broker-order/trade rejection and `PARTIALLY_FILLED` status storage.
- New schema is not wired into execution/reconciliation. CI on `dbd83c878753e7a0cb6e2a7935c55378ee56d7cb`: backend **201 passed, 1 warning**, clean SQLite migration; frontend TypeScript/build passed.
- Next: pure typed response-validation helpers for Upstox V3 place, order details, history and trades payloads. No live orders. See `PROGRESS.md` and `LIVE_ORDER_STATE_MACHINE.md`.


## Pure Upstox response parsers completed — 17 October 2026

- Added `backend/app/brokers/upstox/response_parsing.py` with typed parsers for Place Order V3 child IDs, Order Details, Order History and Order Trades. They are pure functions: no HTTP or DB calls.
- Tests cover malformed/missing fields, mismatched IDs, duplicate place IDs/trade IDs, invalid quantities/prices, and empty history/trade lists. Official docs confirm Order History is a status timeline, so repeated order IDs for different status events are valid; the parser was corrected accordingly.
- Latest verified code commit: `0d1ececff933e3271576096756192036963805ba`: backend **223 passed, 1 warning**, clean SQLite migration; frontend TypeScript/build passed.
- Next: audit the risk controls needed for a separate live service; do not wire live submission. See `PROGRESS.md`.


## Live pre-trade risk audit — 17 October 2026

- The existing risk engine gates automated strategy entries using realized losses; manual orders bypass it and unrealized loss is not included. The execution service's notional/cash/holding checks are PAPER controls only. Equity-only instrument validation remains fail-closed.
- Missing live prerequisites include broker funds/margin retrieval, live/manual all-order exposure and loss controls, order-rate limits, stale-quote/market-session validation, and a live-account circuit breaker. The automated-entry kill switch is not a live account kill switch.
- Current official Upstox docs show Funds & Margin V3 was released 10 April 2026. It uses `GET /v3/user/get-funds-and-margin`, requires `Api-Version: 3.0`, and returns `available_to_trade.total`. Next task: add this as a read-only adapter method with mocked tests; do not use it to authorize orders yet.


## Funds & Margin V3 adapter completed — 17 October 2026

- Added read-only `get_funds_and_margin` to `BrokerAdapter` and Upstox using official `GET /v3/user/get-funds-and-margin` and the required `Api-Version: 3.0` header. Official docs show a unified `available_to_trade` object with total, cash and pledge breakdown; the service is unavailable daily from 00:00 to 05:30 IST and may return 423.
- Mocked tests validate endpoint, API-version/auth headers, response shape and 423 error propagation. The data is not used to approve orders.
- Latest verified code commit `6f92a7f9ead0f9fe2da6222e122945a3f419bd1c`: backend **225 passed, 1 warning**, clean migration; frontend TypeScript/build passed.
- Next: add a pure typed funds-response parser that keeps cash separate from pledged margin and validates all numeric fields. See `PROGRESS.md`.


## Funds & Margin V3 parsing completed — 17 October 2026

- Added `FundsAndMarginV3` and pure `parse_funds_and_margin_v3`. It keeps total available-to-trade, cash available and pledged margin as separate fields; validates required nested structure and finite amounts; and permits signed unsettled profit/loss values without allowing negative available balances.
- Tests cover valid payload, missing fields, malformed/NaN/Infinity/negative values and error/423 response envelopes. No risk decision uses this parser yet.
- Latest verified code commit `27e87cca48c03528f5fe5fee5816ff2aa4438caa`: backend **235 passed, 1 warning**, clean migration; frontend TypeScript/build passed.
- Next: add read-only Upstox instrument margin calculation API support with mocked tests. See `PROGRESS.md`.


## Instrument margin calculation adapter completed — 17 October 2026

- Added read-only `get_margin_details` to `BrokerAdapter` and Upstox adapter using `POST /v2/charges/margin`. Inputs are locally validated and normalized; requests with empty/oversized batches, duplicate keys, invalid quantities, unsupported transaction/product values or invalid prices are rejected before network access.
- Mocked tests verify endpoint/payload and broker-error propagation. The response is still returned as the broker's raw result and is not used to authorize orders.
- Debugging note: CI first exposed missing decimal imports and a class helper accidentally nested beneath the module-level validator. A first patch repeated the helper placement error; after inspecting the exact source and failed test log, the helper was relocated once at class scope. Do not repeat blind text replacements; verify indentation and helper location.
- Latest verified commit `e6abb6704b67c54f35bb5d7c2c41acd96846147d`: backend **238 passed, 1 warning**, clean SQLite migration ([run 39035755714](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755714)); frontend checks passed ([run 39035755707](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755707)).
- Next: audit official margin response schema and existing parsers, then add a typed response parser only if needed. No live order approval is connected.


## Upstox Margin Details response parsing — 18 October 2026

The official Margin Details API documentation was checked: https://upstox.com/developer/api-documentation/margin/. Added pure parse_margin_details and immutable MarginEstimate / MarginBreakdown result types for data.required_margin, data.final_margin, and the seven documented per-instrument margin fields. Regression tests cover a valid documented response and malformed/error payloads, including missing fields, empty rows, negative/non-finite values and unsuccessful envelopes.

Commits: parser 3c4dd6ac0d7d88a18916c241d28a224fc5031d5d; tests 6995f64429b44134edfa5985ad4f50c3b54cfcab. CI verification is pending; inspect GitHub Actions before describing this as verified. The parser is not connected to order approval and must not be used as a live-trading authorization. Next: inspect CI for the current PR head returned by PR #1 at verification time; if no run is available, trigger/await the repository's supported CI workflow. Record only verified results in progress/audit/changelog. Do not merge PR #1 or enable live trading.


## Status correction — 18 October 2026 (supersedes stale next-step notes)

The following are now present in the branch: `BrokerAdapter.get_margin_details`, the Upstox `POST /v2/charges/margin` implementation with local request validation, pure `parse_margin_details`, and unit tests for success/error/malformed response shapes. Older notes saying the adapter method or typed parser is still missing are historical snapshots, not current status. The parser is read-only and is not used to authorize orders.

The current blocker is verification: the GitHub integration returned no workflow run and no commit status for the current PR head when checked. Earlier CI results (238 backend tests, one warning, migration/frontend checks green) belong to an older commit and do not verify the margin parser changes. No pass/fail conclusion is possible from the available evidence. Inspect or trigger the configured workflow from GitHub Actions and record actual results before advancing.

`MASTER_ROADMAP.md` is now the current sequencing guide. After this verification gate, the next implementation phase is a separate, initially unregistered `LiveExecutionService` with mocked tests, while preserving the current PAPER-only execution guard. Do not merge the draft PR, place real orders, or enable live trading.


### 18 October 2026 — broker-reconciliation CI investigation

- Added regression coverage for an Upstox status-check failure response; commit `2625191740554efe5a41f99eff15306ebd68ec5c`.
- Investigated workflow run `39028914012` (`Backend pytest`): it ran against the earlier PR merge checkout `d04dfa5` and reported `177 passed, 3 errors`; all three errors were fixture setup failures (`portfolio` not found) in that checkout. The current branch version of `backend/tests/test_broker_reconciliation.py` defines the fixture, but this alone is not proof the current branch passes.
- The GitHub integration's commit-SHA workflow lookup and combined-status lookup returned no results for the current branch head. The old failed run is not a valid test of current head `2625191740554efe5a41f99eff15306ebd68ec5c`; current CI remains unverified.
- Next: inspect the latest PR run in GitHub Actions (PR workflows check out the generated merge ref), confirm backend tests, migration and frontend results, and fix only current-head failures. Do not claim green CI or enable live trading.


## Authoritative handover checkpoint — 18 October 2026

Resume with **broker-confirmed fill ingestion**, not live submission. Re-read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md`, `REQUIREMENTS_AUDIT.md`, and this handover before edits.

Already present: Upstox order-trade read method, `parse_order_trades` and typed `BrokerTrade`; `BrokerOrder` child rows; nullable broker-order/trade fields on `Execution`; unique constraint `(broker_name, broker_trade_id)`. The parser is tested in source, but the ingestion/accounting path is not wired or proven. Do not create a duplicate parser/service without auditing the current repositories first.

First inspect model/migration/repository/service/test files. Verify user and broker-connection scoping, child-order mapping, and whether broker-trade uniqueness must include connection/account ID. Then implement only the missing transactional idempotent persistence, with regression tests. Never treat order status as a fill, never let broker fills mutate paper balances/positions, and preserve the PAPER-only execution guard. Current PR #1 head last observed: `540e1285d3de934b43829948a1b60c67658d1343`; no current-head workflow run/status was returned by the integration. CI is unverified. Do not merge PR #1 or enable live trading.


## Latest handover — broker trade intake committed, tests pending (18 October 2026)

Current head: `32eea17c141d4cfbc727eed2ff2a1b40d21dbba3` on `safety/fail-closed-trading-mode`; PR #1 remains draft/open/unmerged.

Files added/changed: `backend/app/models/broker_trade_record.py`, `backend/app/services/broker_trade_ingestion_service.py`, `backend/alembic/versions/202610180005_broker_trade_ingestion.py`, `backend/alembic/versions/202610180006_broker_connection_scoped_trade_ids.py`, `backend/app/models/broker_order.py`, `backend/app/models/execution.py`, `backend/app/models/__init__.py`, `backend/tests/test_broker_trade_ingestion.py`, and `backend/tests/test_live_broker_schema_migration.py`.

The service stages normalized trade records with connection-scoped uniqueness and exact mapping/ownership validation. It deliberately does not create `Execution` rows or change cash, positions, order status, broker-child fill aggregates or P&L. This is the safety boundary until actual fees and atomic live accounting are designed.

**Immediate next action:** obtain current-head backend pytest and Alembic migration results, then fix failures. Workflow/status lookups returned no results for this SHA; the local environment could not reach GitHub to run tests. Do not claim green CI, do not wire the service into live execution, do not merge PR #1, and do not enable live trading.


### Latest change — 18 October 2026

Added a populated migration-backfill regression test for connection-scoped broker IDs. It starts from revision 003, upgrades to 005, seeds legacy broker child-order/execution rows without connection IDs, then upgrades to head and checks that migration 006 resolves both links. Latest head: `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`. Run/inspect CI for this exact SHA before proceeding.


### Final verification clarification — 18 October 2026

Last code/test SHA: `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`; later commits are documentation-only. PR head observed after those docs updates: `1b0056d9739cd55d50cd5484cddf955aa8bf07db`; no workflow run/status returned. Continue by obtaining test/migration evidence for the code, not by assuming the historical green CI applies.


## Continuation handover — Phase 2 intake hardening (18 October 2026)

Read `PROJECT_INSTRUCTIONS.md`, `ARCHITECTURE.md`, `MASTER_ROADMAP.md`, `PROGRESS.md`, `AUDIT_REPORT.md`, `REQUIREMENTS_AUDIT.md`, `HANDOVER.md` and `LIVE_ORDER_STATE_MACHINE.md` before further changes. Current branch: `safety/fail-closed-trading-mode`; PR #1 remains draft/open/unmerged; original `Tradepro` repository must remain untouched.

Latest code/test target: `264aa4c609d522cd01d07e8213bfee6f14c7a2bf` (test follow-up to `b780c39f770a6839dab0af63fc424c341eff9d70`; code hardening commit: `2cdbbe290f8b661cb91110dbb4e165fcef36f800`). Intake now resolves the exact child-order broker connection and rejects missing/mismatched instrument tokens and malformed side values. Added regression coverage for foreign connection binding and malformed/missing identity fields.

**Immediate next step:** run `.github/workflows/backend-tests.yml` manually with `workflow_dispatch` on the safety branch. Current-head Actions lookup returned no run; do not claim the new tests/migrations passed. Fix and rerun failures before starting the next Phase 2 task. The service remains unregistered and does not touch execution accounting, cash, positions, order status or P&L. Do not merge, deploy to production, or enable live trading.


Latest test addition: `264aa4c609d522cd01d07e8213bfee6f14c7a2bf` covers rejection of legacy child-order rows that have no connection binding. Latest code/test target is `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`; test and migration results are still pending.


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


## Latest handover checkpoint — 18 October 2026: service-level integration test

- Current change commit: `b5783d421f64fcb8e7f1d75f1af5185fd9029f59`.
- Added real-service integration coverage in `backend/tests/test_live_order_fill_reconciliation_coordinator.py`: actual child reconciler + ingestion + coordinator + promotion + accounting, with only broker read payloads and charge estimator mocked.
- Checks successful promotion/replay idempotency, sibling status failure blocks all promotion, and no paper cash/position changes. This does not make live trading ready and does not call a write endpoint.
- **Before coding again:** inspect CI for this exact SHA. If failing, fix the demonstrated failure; if successful, select the next distinct gap from the audit. Do not recreate the coordinator; it already exists. No local tests were run in this continuation and CI was not yet confirmed.
- Safety: PR #1 stays draft/unmerged, live trading stays disabled, original `Tradepro` untouched.


### Superseding handover update

Use latest test commit `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` (supersedes `b5783d421f64fcb8e7f1d75f1af5185fd9029f59`). Integration tests now force real ingestion to create staged trade rows rather than replaying fixture-seeded rows. First check CI for this exact SHA. Do not recreate the coordinator or mark tests green without workflow evidence.

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


## Handover — latest Phase 2 checkpoint

- Latest test commit: `1a3475c69d3a93ece7bfad22ace4dce52231bfa1`.
- Added an integration scenario for partial fill promotion followed by retry after a one-time charge-estimation failure. It composes the real child reconciler, trade ingestion, coordinator, promotion and accounting services; only read-only broker responses and the test estimator are mocked.
- First action in the next continuation: check CI for this exact SHA. Fix only failures supported by test/log evidence; do not assume green. If green, assess PostgreSQL-backed integration coverage and update this checkpoint with actual evidence.
- Existing `LivePreflightCoordinator` and `AccountWideLiveRiskGate` already exist—do not recreate them. Keep PR #1 unmerged, live trading disabled, and original `Tradepro` untouched.


## Latest handover — account safety service implementation (CI pending)

- Latest code/test head: `57939799b7e8b436d5095924b86a89ce380a956e`.
- Added `backend/app/services/live_account_safety_service.py`, migration revision `202610180009`, and `backend/tests/test_live_account_safety_service.py`.
- Read current `PROJECT_INSTRUCTIONS.md`, `MASTER_ROADMAP.md`, `PROGRESS.md`, `AUDIT_REPORT.md` before the next edit. Do not recreate the safety models, preflight coordinator, risk gate or reconciliation coordinator.
- First action: verify GitHub Actions for this exact head. Required evidence: pytest passes, SQLite Alembic upgrade passes, PostgreSQL 16 Alembic upgrade passes, existing PostgreSQL integration job passes. If failure, use job logs and fix only evidenced problems. No local run or CI success is claimed yet.
- Next after green: PostgreSQL concurrency tests for idempotency and reset serialization, then read-only composition with existing preflight. Keep service unregistered from order submission, PR #1 draft/unmerged, live trading disabled, original `Tradepro` untouched.


### Superseding latest code checkpoint

- Latest code/test SHA: `c97be866828bd47a23f22fc44fac2d3359e70f35` (supersedes `57939799b7e8b436d5095924b86a89ce380a956e`).
- Reset test now verifies the error-counter gate only after a fresh passing health check, then requires broker success plus another fresh passing health check before reset.
- GitHub status and workflow queries for this exact SHA returned no results. First action remains obtaining backend Actions evidence; do not assume tests or migrations passed. Keep live order submission disabled and PR #1 draft/unmerged.

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


## Latest continuation handover — safety-control security audit (18 October 2026)

- New audit document: [SECURITY_CONTROL_ENDPOINT_AUDIT.md](SECURITY_CONTROL_ENDPOINT_AUDIT.md).
- Audit commit: [10d87d9d9010b2c48ebcf25c832a2ea574100889](https://github.com/tarunsharma2610-del/tradepro-improved/commit/10d87d9d9010b2c48ebcf25c832a2ea574100889).
- Review is static only. Existing access-token validation, active-user check, admin guard, ownership checks, MFA capability and audit writes are documented alongside gaps. There is no operator audit-history API or dedicated safety permission model. Step-up auth, CSRF, atomic state/event persistence, immutable audit enforcement, strict redaction and HTTP-level safety endpoint tests are unresolved.
- No safety-control endpoint was created. No order route/worker wiring was changed. Live trading remains disabled and original Tradepro remains untouched.
- **Resume here:** read PROJECT_INSTRUCTIONS.md, PROGRESS.md and SECURITY_CONTROL_ENDPOINT_AUDIT.md; approve the safety permission and audit contract; then perform an exhaustive order-entry/retry/recovery/broker-write path inventory before implementing an endpoint.
