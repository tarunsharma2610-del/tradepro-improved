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
1. Add and test a fail-closed guard so `ExecutionService` refuses to accept orders when `TRADING_MODE` is not `PAPER`, until a separately reviewed live execution service exists.
2. Add a regression test proving `TRADING_MODE=LIVE` fails before broker calls or database order creation.
3. Client request idempotency is added. A read-only `BrokerReconciliationService` now records status for an explicitly LIVE order only when it has a persisted broker order ID; it validates ownership/session/response ID and never changes local accounting. Next add broker IDs from a separately reviewed live submission service, then restart-safe fill/cancel reconciliation.
4. Add portfolio-level daily-loss, exposure, order-value, and order-frequency limits enforced server-side.
5. Implement Upstox instrument master sync and streaming only after verifying the current official API documentation.
6. Add broker order lifecycle handling (partial fills, timeout/unknown state, retries, cancellation, reconciliation) before any live order placement.
7. Run targeted tests, full backend suite, frontend typecheck/build, migration checks, and inspect CI results; report exact results without claiming unrun tests.
8. Update `AUDIT_REPORT.md` with the implementation and test evidence. Verify migrations against staging before production deployment.

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
