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


## Latest handover — order-entry path inventory (18 October 2026)

- Read [ORDER_ENTRY_PATH_INVENTORY.md](ORDER_ENTRY_PATH_INVENTORY.md) and [SECURITY_CONTROL_ENDPOINT_AUDIT.md](SECURITY_CONTROL_ENDPOINT_AUDIT.md).
- Inventory commit: [a477489c7e2d5b6883c299c1e9a8aee1cbef055f](https://github.com/tarunsharma2610-del/tradepro-improved/commit/a477489c7e2d5b6883c299c1e9a8aee1cbef055f).
- Manual order and strategy entry/exit paths converge on the PAPER-only ExecutionService; it rejects LIVE/unknown modes. The Upstox adapter's place/modify/cancel methods exist, but no caller was found in reviewed app paths. Recovery does not submit orders, but currently uses LiveExecutionService directly rather than LivePreflightCoordinator.
- No code paths were wired or changed. Keep live disabled and PR #1 draft/open. Original Tradepro untouched.
- Resume by designing a single allowed broker-write boundary, atomic intent+audit persistence, safety-specific permissions, source-call CI guardrails and negative tests. Only then plan safe route/worker integration.


## Latest handover — central broker-write boundary design (18 October 2026)

- Added [CENTRAL_BROKER_WRITE_BOUNDARY_DESIGN.md](CENTRAL_BROKER_WRITE_BOUNDARY_DESIGN.md), commit `40f9ca652cf4bf5e86ed51a9c5f21a3071ce7e06`.
- Design-only checkpoint: no API endpoint, order route/worker wiring, broker write call, or live-trading enablement was added.
- The proposed `LiveBrokerWriteService` is the sole approved production caller for adapter place/modify/cancel. New submissions and exposure-increasing modifications require all account-wide safety/risk/fresh-snapshot gates; cancellation has a narrow risk-reducing exception so a tripped kill switch cannot prevent risk reduction.
- Intent + audit event must commit atomically before broker I/O; external network calls cannot be part of the DB transaction. Unknown submission outcomes require stable-tag reconciliation, never blind retries.
- Least-privilege scopes, step-up MFA, CSRF/Origin, tenant-scoped audit reads, strict redaction, PostgreSQL append-only protection, malformed JWT normalization, and source-call CI guard are specified.
- Next: implement and test storage/event immutability and transaction semantics, then scoped authorization/step-up/CSRF foundation. Keep `TRADING_MODE=PAPER`, `LIVE_ORDER_SUBMISSION_ENABLED=false`, PR #1 draft/open, and original `Tradepro` untouched.


### Source-call guard update — 18 October 2026

- Added the production source-call guard `backend/scripts/check_broker_write_boundary.py` and three guard behavior tests in `backend/tests/test_broker_write_boundary_guard.py`.
- Added the guard as an explicit CI step in `.github/workflows/backend-tests.yml`; run #614 is pending at checkpoint time: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123034569.
- The exact allowlist reserves only `app/services/live_broker_write_service.py` as the future production writer; the adapter file is excluded because it defines the low-level methods. No such service exists yet and no production write path was added.
- Next verify CI, then implement transaction/event storage hardening and authorization foundations. Live remains disabled.


### Guard correction / current CI — 18 October 2026

The first workflow run with the guard (#614) failed because its initial generic method-reference pattern incorrectly flagged paper `ExecutionService.place_order` calls and descriptive text. This was a scanner false positive; the full suite was skipped, so it is not a backend test regression. Corrected the scanner to target adapter-named receivers in commit `30599b1bd8d32293b856c88cdfb4e2facaa9ce0f`. New run #615 is pending: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123199888. Verify its outcome before proceeding.


### Latest guard verification — 18 October 2026

Run #615 failed at the guard because a docstring contained the literal method name. The scanner now uses AST rather than raw line matching and has a docstring regression test. Latest run #617 has passed the guard and is running pytest; remaining DB steps are pending: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123311281. Confirm the full result before proceeding.


### Verified CI checkpoint — 18 October 2026

- CI run #617 passed on code/test SHA `bdf208efcc32b44a6367157dd2ab0aab946e6574`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123311281.
- Broker-write source guard: PASS. Backend suite: **402 passed, 4 skipped, 1 warning in 29.81s**. SQLite and PostgreSQL 16 Alembic upgrades: PASS. PostgreSQL concurrency tests: **4 passed in 0.39s**.
- Earlier guard runs failed on scanner false positives and were corrected; the final AST-based scanner ignores docstrings/comments and passed CI.
- Current resume point: review the design doc, then harden safety event transaction/version/idempotency and PostgreSQL append-only behavior before implementing scoped authorization/step-up/CSRF. No central writer or safety endpoint exists yet. Keep live submission disabled.


## Current resume point — safety-event transaction/immutability hardening (18 October 2026)

Code now includes migration `202610180011_safety_event_immutability.py`, request-fingerprint replay checks, a unique (state_id, state_version) audit constraint, SQLite/PostgreSQL UPDATE/DELETE rejection triggers, audit-write rollback coverage, and stale reset-version checks. PostgreSQL tests attempt UPDATE/DELETE against the migrated audit table and assert the original event remains intact.

CI run `39124213016` passed on SHA `2b38a0f0ba4dd167419ec116a630ebe63fabac92`, including the new rollback/fingerprint tests and both migrations. That run predates the newest expected-version/threshold-context change. Current latest-head run `39124312326` is pending: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39124312326. Verify exact-head CI before marking this step done.

Next: after CI is green, review trigger behavior and migration rollback, then implement explicit scoped authorization/step-up MFA/CSRF. Keep live disabled and PR #1 draft/unmerged.


### CI failure and correction — 18 October 2026

Run #39124312326 failed only `test_manual_reset_rejects_stale_expected_state_version`: the test passed `health.version` from a mutable ORM instance, which reflected the later mutation. The test now captures `health_version = health.version` before tripping the switch (commit `6cd0ced108e35d715359d649a463d80709dd1fb1`). New exact-head run #39124498280 is pending: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39124498280. Check the complete run before proceeding.


### Verified current CI — 18 October 2026

Run #625 passed on code/test SHA `6cd0ced108e35d715359d649a463d80709dd1fb1`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39124498280. Source guard passed; backend suite **406 passed / 5 skipped / 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **5 passed** including append-only event trigger tests. The earlier stale-version test failure was due to reading a mutable ORM object; the test now snapshots the version and the exact-head run is green.

Next: implement least-privilege authorization, tenant scope, recent MFA step-up and CSRF/Origin foundations. No central writer/endpoints/path wiring yet. Keep PR #1 draft/unmerged and live submission disabled.


## Authorization foundation — 18 October 2026

- User.safety_permissions is an explicit JSON grant list with an empty default. Allowed scopes: safety.status.read, safety.audit.read, safety.kill_switch.trip, safety.reset. is_admin does not grant any safety scope.
- require_safety_permission() denies by default; malformed signed JWT subject UUIDs are normalized to 401; require_same_origin_for_cookie_mutation() is available for cookie-authenticated mutation routes.
- Regression tests were added, but the new commits still require CI verification. The Origin dependency is not yet wired to routes; no safety endpoint has been exposed.
- Still required before endpoint work: recent-MFA step-up, safe trusted grant provisioning, endpoint-level tenant isolation tests, and attaching permission/Origin/step-up guards. Keep live submission disabled.

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

### Follow-up correction and verification checkpoint (18 October 2026)

- Corrected the safety-permission endpoint import formatting and cleaned test imports after reviewing the committed source through GitHub. Latest test-file commit: `ae46db76e86ea28116bcaf80b9a02c64eb713e9b`; endpoint import correction: `3ef5d32ddeb97ffbd43c61acb74945dd4f564729`.
- The repository connector did not expose a local test runner, and GitHub Actions/combined-status lookups returned no run/status for the latest code/test SHA. Tests remain **unexecuted/unverified**; the older CI run is not evidence for these changes. The next action must be to get CI running on the current branch head and resolve any failures before adding further security-sensitive behavior.
- Phase 2 remains incomplete. Keep PR #1 draft/open/unmerged, preserve PAPER-only defaults and live-order submission disabled, and leave the original `Tradepro` repository untouched.

## Phase 2 checkpoint — tenant-scoped safety audit read (18 October 2026)

- Added `GET /api/v1/admin/safety/audit`, protected by the explicit `safety.audit.read` permission. It accepts bounded pagination (`limit=1..100`, `offset=0..100000`), returns a page envelope and uses a stable `created_at DESC, id DESC` order.
- The SQL query scopes rows to `AuditLog.user_id == authenticated_user.id` and `action LIKE 'safety.%'` before counting or pagination. The caller cannot provide a target user ID; unrelated audit actions and other users' events are not returned. This is an actor-scoped view of safety events, not an administrator-wide or target-account audit browser.
- Added HTTP regression tests for permission denial, pagination bounds, and tenant isolation / filtering. **The tests are committed but have not been executed locally; exact-head GitHub Actions status has not been confirmed.** Do not call the feature CI-verified yet.
- Relevant commits: endpoint `d608f4fdd8a9f10b0647fbe4083d35809b27061f`; response schemas `d46c9268c7c05ca9e207898ca80674df56883a03`; tenant isolation tests `eda5a3589765211105457e2b8950d0c20f00f011`; follow-up import/test cleanup `584b774e175b1aecd74784286bd5fca566e1be6d`.
- Remaining Phase 2 work: run/fix CI on the latest branch head; implement persistent safety status and kill-switch trip/reset routes with the correct permission, Origin and MFA gates; decide and document operator-vs-account audit visibility before expanding audit scope; ensure atomic state/event transactions and concurrency semantics; implement the central broker-write service and enforce it across every execution path. Live trading remains disabled and PR #1 remains draft/open/unmerged.

## Phase 2 checkpoint — authenticated safety control endpoints (18 October 2026)

- Added and registered `backend/app/api/v1/safety.py` with three user-scoped endpoints: `GET /api/v1/safety/status` requires `safety.status.read`; `POST /api/v1/safety/kill-switch/trip` requires `safety.kill_switch.trip`, cookie-Origin validation and an `Idempotency-Key`; `POST /api/v1/safety/kill-switch/reset` requires `safety.reset`, a fresh user-bound password+TOTP step-up token, cookie-Origin validation, an idempotency key, and a required `expected_version`.
- Status reads only the authenticated user's Upstox account safety state. Missing state is reported as blocked/unsafe without initializing or creating a state. Trip initializes missing state in the safe/tripped state before applying the idempotent trip. Reset delegates to the existing transaction-safe service and returns conflict if state/version/health requirements are not met.
- Reset deliberately does **not** accept a client assertion that a health check passed. The existing service requires a recent persisted `HEALTH_CHECK_PASSED` event, zero consecutive broker errors, and matching expected state version. No new public health-check endpoint was added because a caller-supplied “passed” flag would be unsafe without real broker/session/account snapshot validation.
- Added HTTP regression tests for permission denial, safe missing-state response, trip behavior, required idempotency key, reset MFA denial, reset blocked without a fresh successful health check, and cookie-Origin rejection. **These tests have not been executed in this environment.** GitHub Actions lookup exposed no PR-triggered run for the latest test commit and combined status was empty; the connector's workflow-run lookup filters to PR-triggered runs, so this is not proof that no push-triggered run exists. Exact-head test status remains unverified.
- Relevant commits: safety route/import cleanup `267da864b5187cfad91ac68b76ba86cf06b7848f`; schema `01f0deb4949cd13072fb2feda9924e0a97eaf5cf`; router registration `fc95e748197be9e8848c990f55079fbd8afc4a30`; endpoint tests `3ae21dac71edb449835124f99794f510c8b80761`.
- Review caveat: the existing `GET /api/v1/admin/safety/audit` still reads legacy `AuditLog` rows with `safety.*` action names; the durable state-transition history is in `LiveAccountSafetyEvent`. Before treating operator audit visibility as complete, update that endpoint to read the immutable event table and scope by the associated state owner and authorized actor.
- Remaining gates: run and fix CI on the current branch head; fix the safety audit endpoint's event source; perform security review of the grant/reset token purpose boundaries; add negative HTTP tests for every route and error path; verify atomic state/event concurrency at endpoint level; implement the central broker-write service and enforce it across API, strategy worker, recovery and adapter paths. Keep `TRADING_MODE=PAPER`, `LIVE_ORDER_SUBMISSION_ENABLED=false`, PR #1 draft/open/unmerged, and original `Tradepro` untouched. Phase 2 is incomplete.


## Superseding Phase 2 checkpoint — immutable safety audit source (18 October 2026)

- Updated `GET /api/v1/admin/safety/audit` to read `LiveAccountSafetyEvent` joined to `LiveAccountSafetyState`, rather than the legacy `AuditLog` table. Tenant scoping is performed in SQL using the authenticated user's state ownership before counting and pagination; callers cannot select another user/state. Output omits idempotency keys and request fingerprints and exposes only the safety event fields needed for audit review.
- Reworked the tenant-isolation/pagination HTTP test to seed durable safety events for two different account owners and a non-safety legacy audit row. It checks that only the authenticated tenant's immutable safety events are returned and sensitive replay metadata is not serialized.
- Commits: endpoint `cd68384c48a98f2bd2ded054f37bb04d24885b12`; regression test `7913f821a7ac194c537adf911a4ef39ba4410e41`.
- Verification status: exact-head CI/status lookup returned no runs/statuses for the latest test commit. Tests have **not** been run in this environment; treat this change as committed but unverified until GitHub Actions runs against the current branch head. No live broker write was called.
- Next: verify/fix current-head CI; then review reset/idempotency and endpoint transaction behavior, followed by central broker-write boundary implementation and enforcement across API, strategy workers, recovery/retry and adapter paths. Phase 2 remains incomplete. Keep PAPER mode, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Phase 2 checkpoint — MFA purpose separation (18 October 2026)

- Changed the MFA step-up request to accept only two explicit purposes: `safety.reset` (default for backward compatibility) and `safety.admin.permissions`. Permission-management purpose issuance is denied unless the authenticated user is a platform admin.
- Changed the recent-MFA dependency into a purpose-specific dependency factory. A token for `safety.reset` no longer satisfies the permission-grant/revoke route, which now requires `safety.admin.permissions`; unknown scopes fail at dependency construction. The issued purpose is included in the MFA step-up audit metadata.
- Added/updated HTTP and dependency regression tests for admin purpose usage, non-admin denial, and cross-purpose token rejection.
- Commits: schema `4c09723127b545fe111adc6bf6ff70cd509fa13d`; dependency `36e23c178b7fadcee0f5b9d0304363d6093cf9f3`; auth issuance `61dfcc54abe66825a2f3eccfc728920a3faef7c8`; admin route `af9b1d32b3d91d313a0cd9451f2b60f4a60d2df1`; tests `c9e35bc102c14683c4c1a8216abd9f6cd19908e` and `9d5eee236f252a5b8ef6c263553ac89100a52c44`.
- Verification remains pending: tests were not run locally; query available for exact-head workflow/status returned no records on the previous checkpoint and must be repeated for this latest head. Do not treat this change as passing until CI executes.
- Next: run CI and address failures, review the full safety MFA dependency/route matrix, then proceed to the central broker-write boundary. PAPER mode and disabled live order submission remain mandatory; Phase 2 is incomplete.


## Authorization/MFA route-matrix verification checkpoint — 18 October 2026

- During matrix review, identified a compatibility defect in the first scoped-MFA dependency refactor: existing direct unit tests and callers invoke `require_recent_safety_mfa(step_up_token=..., user=...)`, so turning that function itself into a factory would break those calls. Corrected by restoring `require_recent_safety_mfa` as the default `safety.reset` validator and adding `require_recent_safety_mfa_scope(scope)` for FastAPI route dependencies. Reset and admin permission routes now explicitly use their corresponding scope-specific dependency.
- Added route-level regression coverage proving a `safety.reset` token cannot grant safety permissions; existing coverage includes non-admin privilege denial, direct cross-purpose rejection, stale tokens, disabled MFA, wrong user/scope, Origin checks, default-deny permissions, tenant isolation, idempotency-header validation, and safe reset requiring fresh health evidence.
- Relevant commits: dependency compatibility fix `24b463894eca1fde37381bef66d47366a806fe32`; route wiring `0cfc3e290dbc730af9fb854954a95875809ad3cf` and `17088f172d40aa106d1cd1d5f8b674c056919a86`; test matrix update `6e77aa77a7c0bba84d2aae539b37fa6228c088b9`; route-level cross-purpose test `c40edddbeb8b65ec468ae0419897d1cd6cc2c325`.
- CI: GitHub Actions backend workflow is running for the preceding dependency/test commit (`39132630566`) and queued for latest route-level test commit (`39132698515`). The preceding run has not yet reached pytest; do not mark the matrix passed until latest-head workflow concludes. Monitor [latest workflow run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39132698515).
- Still outstanding: wait for latest-head CI; fix any failures and re-run; verify SQLite/PostgreSQL migrations and concurrency checks. This is a route-matrix review, not a complete authorization/security certification. PAPER mode remains mandatory, live broker order submission remains disabled, PR #1 remains draft/open/unmerged, and Phase 2 is incomplete.


## CI failure triage update — 18 October 2026

- GitHub Actions run `39132630566` failed at `Run test suite`: `433 passed, 5 skipped, 1 failed`. The single failure was `test_non_admin_cannot_request_permission_management_step_up`, which returned 401 rather than the expected 403 because its test fixture enabled MFA but did not mock TOTP verification. The authorization code was not reached by that test.
- Fixed the test fixture to mock a valid `123456` TOTP code, isolating the authorization behavior under test. Fix commit: `b5c96fc5115bd4b9fae7be6fc0a168d55c5ace9c`.
- A new backend CI run is in progress for the fix: [run 39132803282](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39132803282). Do not consider the suite green until this exact-head run finishes successfully. Previous failures skipped migrations/concurrency stages because pytest failed first.


## CI verification result — PASS (18 October 2026)

- Backend workflow run `39132803282` passed for backend commit `b5c96fc5115bd4b9fae7be6fc0a168d55c5ace9c`: broker-write boundary guard passed; full backend suite **435 passed, 5 skipped, 1 warning**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL account-safety/charge-adjustment concurrency tests **5 passed**. One Starlette/AnyIO deprecation warning remains non-blocking.
- The earlier failing test was corrected by mocking valid TOTP in the non-admin purpose-denial test; the passing run confirms the corrected test setup and current backend changes. Documentation-only commits followed, so the tested application code is unchanged, but the docs commit itself did not trigger backend CI due workflow path filters.
- This is evidence for the current authorization/MFA test changes and listed CI gates, not a complete security certification or Phase 2 completion. Continue with broader authorization route matrix and broker-write boundary implementation; live order submission remains disabled and PAPER mode remains mandatory.


## MFA HTTP route-matrix follow-up — 18 October 2026

- Added two missing HTTP-level cases to `backend/tests/test_api_authorization.py`: cookie-authenticated `POST /api/v1/auth/mfa/step-up` without an Origin header must return 403; unsupported step-up purpose `safety.live_trade` must be rejected by request validation with 422. These complement existing tests for missing/disabled MFA, wrong password, non-admin privileged-purpose denial, reset-vs-admin token scope separation, stale/user-bound tokens, cross-origin mutations, permission denial, and reset health prerequisites.
- Test commit: `58778259324119379c69b03c822c13849b223d22`. GitHub Actions run [#39133596645](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39133596645) is running; broker-write boundary guard has passed and pytest is in progress at time of this note. Do not claim the new tests pass until the run completes and its pytest/migration/PostgreSQL steps conclude successfully.
- Review outcome so far: reset and permission-management routes explicitly use distinct MFA scopes; platform-admin status alone does not grant safety permissions; user audit is tenant-scoped to immutable safety events. The matrix is broader but not exhaustive, and no independent security certification is implied.
- Next after CI: fix only demonstrated failures; if green, proceed to the central broker-write authorization/gating design and enumerate every order-write path before wiring anything. Keep PAPER mode, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## MFA HTTP route-matrix CI result — PASS (18 October 2026)

- GitHub Actions [run #39133596645](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39133596645) passed for test commit `58778259324119379c69b03c822c13849b223d22`: broker-write boundary guard passed; backend suite **437 passed, 5 skipped, 1 warning in 28.01s**; SQLite Alembic migration passed; PostgreSQL 16 Alembic migration passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**.
- This run verifies the added missing-Origin and unsupported-purpose HTTP tests plus the existing MFA/authorization matrix at that tested code SHA. Later documentation-only commits did not alter application code. One non-blocking Starlette/AnyIO deprecation warning remains.
- This does not certify every auth route or complete Phase 2. Next task: map all broker order-write entry points and design a single fail-closed broker-write authorization gate, then test that all paths are blocked in PAPER mode and remain disabled absent explicit future approval. Do not wire real order submission in this task. Keep PR #1 open/unmerged and original `Tradepro` untouched.


## Central broker-write boundary — deny-all foundation (18 October 2026)

- Added `backend/app/services/live_broker_write_service.py` as the single planned choke point for place/modify/cancel operations. This is intentionally a deny-all foundation: every write method raises `LiveExecutionBlocked` with an explicit no-request-sent message. It does not import or call a broker adapter, and it is not registered with routes, strategy workers, recovery, or any execution path.
- Added `backend/tests/test_live_broker_write_service.py` covering all three write verbs and asserting each fails closed. Commits: service `3726484932e4d46d9f92a7ff41cb5b761cfb1720`; tests `f4442607b8b71df7fffbf4354ea11a532efb99d6`.
- Verification pending at this note: the backend workflow for test commit `f4442607b8b71df7fffbf4354ea11a532efb99d6` has passed the broker-write source guard and is in pytest. See [run #39134040222](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134040222). Do not claim tests/migrations passed until the run concludes.
- This does **not** complete the broker-write service. Next design must enumerate the persisted-intent lifecycle, ownership, user confirmation, account safety state, fresh pre-trade risk, token/connection stability, and timeout/recovery behavior before any adapter call can be implemented. Do not wire it or enable live orders. PAPER mode, disabled live submission, PR #1 draft/open/unmerged, and original `Tradepro` untouched remain mandatory.


## Central broker-write deny-all CI result — PASS (18 October 2026)

- GitHub Actions [run #39134040222](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134040222) passed for test commit `f4442607b8b71df7fffbf4354ea11a532efb99d6`: broker-write source guard passed; full backend suite **440 passed, 5 skipped, 1 warning in 32.49s**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**. A separate workflow for the service-only commit also passed.
- The deny-all broker-write service remains deliberately unwired and makes no adapter calls. This step proves the central choke-point stub refuses place/modify/cancel; it does not verify live submission (which remains disabled) and is not a complete broker-write implementation.
- Documentation-only checkpoint commits followed. Next: inspect every existing order-writing entry point and add a call-graph/inventory, then design the central gate around ownership, persisted intent/idempotency, account-level safety latch, live pre-trade risk, explicit confirmation, and ambiguous timeout recovery. Keep PAPER mode, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Broker-write path inventory and guard hardening — 18 October 2026

- Added `BROKER_WRITE_PATH_INVENTORY.md` documenting current adapter definitions, PAPER execution routes, read-only live preflight/recovery/reconciliation, and controls required before any live write is implemented. Commit `68f528edf4fe2dcb958161943b878b5863bbcd74`.
- Strengthened `backend/scripts/check_broker_write_boundary.py` to reject broker-write method references regardless of receiver name, rather than relying on adapter-like variable names. It now permits only the known PAPER `self.execution.place_order` calls in `strategy_execution_service.py` and the existing `ExecutionService(...).place_order/cancel_order` endpoints in `api/v1/portfolios.py`. The first strict run correctly exposed those two existing PAPER API call sites as exceptions that needed explicit, narrowly-scoped allowlisting; no live adapter write path was identified in those failures.
- Added guard tests for generic receiver bypass, central-service adapter-call rejection, and the approved PAPER call sites. Test updates are committed through `e9c31a043465e3d09223894ddfe45629cfc0302e`.
- CI for the latest guard/test fix is in progress: [run #39134878791](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134878791). Do not treat this guard hardening as verified until the exact-head workflow passes. The preceding strict-guard failures were expected detection/allowlist gaps and prevented pytest/migration stages from running.
- Live broker writes remain unimplemented and denied by the central service. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Central safety-preflight + durable intent composition — VERIFIED (18 October 2026)

- Added LiveOrderRecoveryService.persist_preflighted_intent(...). It accepts only a LiveOrderPreflight plan, verifies user/portfolio/instrument/broker and exact intent fields, rechecks the currently connected Upstox connection ID, then persists one stable PENDING_SUBMISSION LIVE intent with an opaque broker tag and portfolio-scoped idempotency key. It does not call a broker order endpoint.
- Updated LiveBrokerWriteService to expose prepare_order_intent(...): run LivePreflightCoordinator.preflight first (environment interlocks, explicit confirmation, ownership/instrument validation, persisted account safety latch, fresh read-only broker risk snapshots and account-wide risk gate), then persist the plan. If preflight fails, persistence is not attempted.
- Place/modify/cancel methods remain unconditional deny-all; this service does not send real orders and is not registered with routes/workers. PAPER-only ExecutionService is unchanged.
- Added tests for preflight-before-persistence, no persistence on denied preflight, exact plan matching, idempotent intent replay, and broker connection change after preflight.
- Verified GitHub Actions run #39136080295 on code/test SHA 27c4a4e5ed9fd9d864e38816c945e37371ee22f7: broker-write source guard passed; backend 448 passed, 5 skipped, 1 warning in 39.34s; SQLite migration upgrade passed; PostgreSQL 16 migration upgrade passed; PostgreSQL safety/charge-adjustment concurrency tests 5 passed.
- Code commits: recovery persistence 66675d34bee98cdc6c0f24388f4fb097e79348ac; central composition 4d8268ca86e08a36025182a8e46f43b18ba951e6; orchestration tests ab010e8106b02b182594c0a664df34647a234bdb; persistence tests 27c4a4e5ed9fd9d864e38816c945e37371ee22f7.
- Remaining: review persisted intent status transitions and duplicate/concurrent races, require account safety to be rechecked at any future submission boundary, and design broker-confirmed submission/recovery with ambiguous outcomes. No submit method is approved. Keep PAPER mode, live submission disabled, PR #1 draft/open/unmerged, and original Tradepro untouched.

## Post-preflight instrument revalidation — VERIFIED (18 October 2026)

- Hardened persist_preflighted_intent to re-read the instrument row after asynchronous broker snapshots and reject missing/inactive instruments or any instrument-key change since the preflight plan was produced. This closes the same time-of-check/time-of-use gap already covered for broker-connection identity.
- Added regression test mutating the instrument key after snapshot-plan creation; persistence is rejected and no LIVE Order row is created.
- GitHub Actions [run #39136563051](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39136563051) passed on code/test SHA c40689ac227ab56ca58993072112d6fd575aff46: broker-write source guard passed; backend **449 passed, 5 skipped, 1 warning in 32.68s**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**.
- Next: add concurrency/state-transition tests around persisted intent creation and submission-unknown marking. Any future submitter must recheck the account safety latch and independent interlocks immediately before network I/O. Actual place/modify/cancel remain denied and no live broker order request is enabled.

## Concurrent order-intent and submission-state checkpoint — VERIFIED (18 October 2026)

- Changed `LiveOrderRecoveryService.mark_submission_unknown` to use a SQL compare-and-set update restricted to tagged LIVE intents in `PENDING_SUBMISSION` or `SUBMISSION_UNKNOWN`. It reloads after commit and refuses to overwrite a concurrently written terminal/reconciled state. Repeated transition to `SUBMISSION_UNKNOWN` is idempotent.
- Added unit coverage for repeated `SUBMISSION_UNKNOWN` and refusal to transition a terminal `FILLED` order back into recovery.
- Added PostgreSQL independent-session concurrency tests for two simultaneous identical intent-persistence requests (exactly one durable Order row and shared ID) and two simultaneous `SUBMISSION_UNKNOWN` transitions (both return the same safe state). Updated `.github/workflows/backend-tests.yml` to actually execute `test_live_order_recovery_postgres.py`; this integration coverage was not included by the prior workflow.
- Verified GitHub Actions [run #39137705194](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39137705194), SHA `3626e0cdb8a5b7b3fe012fd00b07d2b7bc3bbe26`: broker-write source guard passed; backend **450 passed, 7 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **7 passed** (including the two new order-recovery concurrency cases).
- Recovery lifecycle review: timeout, lookup failure, invalid response, no match, and identity mismatch remain review-required outcomes; the service never blindly retries a broker POST. Recovered broker IDs are identity mapping only and do not imply fill/accounting confirmation.
- Remaining: production-grade submit/modify/cancel remains intentionally unimplemented and denied. Before any future broker POST, implement a separately reviewed submission state machine that commits a unique submission claim, rechecks account safety and independent interlocks immediately before I/O, handles crash/timeout ambiguity via read-only recovery, and requires broker-confirmed state reconciliation. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Submission-claim state separation — VERIFIED (18 October 2026)

- Added `SUBMISSION_CLAIMED` as a distinct, durable state before any future broker network I/O. `claim_submission_attempt` uses a SQL compare-and-set from `PENDING_SUBMISSION`; only one concurrent worker can win. This is a local database operation only and contains no broker write call.
- Read-only tag recovery now accepts `SUBMISSION_CLAIMED` as well as pending/unknown states, because a process crash after committing a claim cannot prove whether a request was sent. The recovery rule remains conservative: no-match, lookup error, malformed response or identity mismatch never authorizes an automatic resubmit.
- Added unit tests for one-time claim semantics and a PostgreSQL independent-session concurrency test requiring exactly one winner. Existing concurrent duplicate-intent and `SUBMISSION_UNKNOWN` transition tests remain enabled in the PostgreSQL CI step.
- Verified GitHub Actions [run #39138626298](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39138626298), SHA `b18841ff591eb943c25d3f85894d824923f2f371`: broker-write source guard passed; backend **451 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Safety boundary: this is state-machine groundwork only. No adapter place/modify/cancel call was added, no live submission route or worker was enabled, and no real order was sent. Before any future submitter is considered, require a dedicated reviewed protocol that rechecks the account safety latch and independent interlocks immediately before I/O, handles claim-crash ambiguity via read-only recovery, and only accepts broker-confirmed reconciliation. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Broker-account binding for recovery — VERIFIED (18 October 2026)

- Added nullable `orders.broker_connection_id` with FK/index and Alembic revision `202610180013`. New live intents persist the exact broker connection ID validated by preflight. Legacy rows are intentionally not backfilled because the currently connected account cannot prove which account was used originally.
- Read-only recovery now fails closed before calling order history if the original connection is missing, disconnected, or differs from the currently verified connection. Existing child mappings are reused only when connection ID, broker name, and stable tag match the persisted intent.
- Added regression tests proving a disconnected/original-connection mismatch and a legacy unbound intent produce `UNKNOWN_REQUIRES_REVIEW`, make no order-history call, create no child mapping, and never invoke a broker write. Migration runs are verified on SQLite and PostgreSQL 16.
- Verified GitHub Actions [run #39139728102](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39139728102), SHA `9cb7ab055a0cd55028f0001aa90d647f1518b667`: broker-write source guard passed; backend **453 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Remaining: this is still recovery identity binding, not broker submission. No place/modify/cancel network write is enabled. Any future submitter must perform a fresh account safety/interlock check immediately before I/O, commit and honor the single-winner claim, and route crashes/timeouts into read-only reconciliation. Keep PAPER mode mandatory, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Fresh pre-submission interlock revalidation — VERIFIED (18 October 2026)

- Added `LiveOrderRecoveryService.validate_claimed_submission(user_id, order_id)` as a validation-only primitive for any future separately reviewed submitter. It requires `TRADING_MODE=LIVE`, `LIVE_ORDER_SUBMISSION_ENABLED=true`, a user-owned tagged LIVE intent in `SUBMISSION_CLAIMED`, the original still-connected broker connection, automated-entry enablement for strategy orders, and a positive `LiveAccountSafetyService.check_allowed` result.
- The method does not call a broker adapter and no current write method invokes it. It explicitly documents that a future submitter must still solve the race between this check and network I/O; this check alone is not a safe live-submit implementation.
- Added regression tests for disabled runtime submission flag, missing account-wide safety state, and disconnected original broker connection. The first CI attempt exposed a test-fixture reference error; that fixture was corrected and the latest run is green.
- Verified GitHub Actions [run #39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552), SHA `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b`: broker-write source guard passed; backend **456 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Remaining: no actual broker order write is enabled. A future submitter must implement a race-safe final interlock protocol (e.g. coordinated safety-state lock/version and claim semantics), without holding unsafe database locks across network I/O, and must handle post-request crashes through read-only reconciliation. Keep PAPER mode mandatory, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.
