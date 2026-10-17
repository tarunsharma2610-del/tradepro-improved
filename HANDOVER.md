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
3. Client request idempotency is now added on this branch using a DB unique constraint; next add broker correlation and restart-safe reconciliation before any live execution.
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
