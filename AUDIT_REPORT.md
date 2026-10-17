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
