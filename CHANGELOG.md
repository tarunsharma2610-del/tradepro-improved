# Change Log — Tradepro Improved

## 2026-10-17 — audit and safety branch

### Existing functionality retained
- Paper order placement, paper LIMIT matching/cancellation, position accounting and transaction-cost calculation.
- Strategy scoring, trailing-stop evaluation, strategy-level daily-loss controls and automated-entry kill switch.
- Existing Upstox OAuth, encrypted per-user credentials, quotes, historical candles, order-status/order-book/positions/holdings adapter methods.
- Existing frontend pages, API routes, model/table structure and migration history.
- Original `Tradepro` repository and its `main` branch were not modified.

### Changes
1. Added `REQUIREMENTS_AUDIT.md` to map the specification to existing code and document remaining gaps.
2. Added a fail-closed check in `ExecutionService.place_order` so the existing paper-only service refuses requests if `TRADING_MODE` is anything other than `PAPER`. This is a safety gate, not live execution.
3. Added `test_live_mode_fails_closed_before_creating_order`.
4. Corrected `UpstoxAdapter.place_order` to use the current documented HFT order-placement host (`https://api-hft.upstox.com/v2/order/place`) instead of the deprecated host.
5. Added `test_place_order_uses_current_upstox_hft_host_without_network`, which mocks the HTTP helper and verifies URL/payload without contacting Upstox.
6. Added `HANDOVER.md` and updated `AUDIT_REPORT.md` with findings, release gates and next priorities.

### Verification
- The fail-closed guard and its test passed the backend GitHub Actions workflow before the adapter URL correction.
- GitHub Actions passed for the code-bearing commit containing the adapter correction and mocked regression test: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39027387591.
- The test suite uses mocks/SQLite and does not verify real broker execution.
- No real broker orders were submitted.

### Additional improvement — portfolio daily-loss guard
7. Extended the existing risk engine to aggregate today's realized losses across every fill in a portfolio, including manual orders, and block new automated strategy entries when losses reach configurable PORTFOLIO_DAILY_LOSS_LIMIT_PCT of starting virtual capital (default 2%; set to 0 to disable).
8. Added regression coverage below, at, and above the threshold. This only gates automated strategy entries; it does not guard manual order submission or provide a live-trading risk system.

### Remaining blockers
- Durable order idempotency and broker reconciliation.
- Portfolio-wide exposure, max-order-value/position-size controls and broker-error circuit breaker.
- Complete live-order lifecycle (broker-confirmed partial/full fills, cancellation/modification, timeouts and restart recovery).
- Verified full instrument-master sync and WebSocket feed.
- Market-hours/holiday handling, operational monitoring and production TLS/staging verification.
- Live trading remains not ready and must stay disabled.

### Additional improvement — durable request idempotency
9. Added optional client `idempotency_key` to order requests and persisted it with a database-enforced unique constraint per portfolio.
10. Repeated requests with the same key and identical order payload return the existing order; reusing a key for a different payload is rejected. Concurrent duplicate inserts are arbitrated by the database constraint.
11. Added regression tests for sequential retries and key/payload mismatch. This reduces duplicate submissions but is not a substitute for broker-side idempotency and post-timeout broker reconciliation.

### Additional improvement — single-order value cap
12. Added `MAX_ORDER_VALUE_PCT_OF_VIRTUAL_CAPITAL` (default 25%) to reject paper orders whose estimated notional exceeds the configured percentage of starting virtual capital. LIMIT orders use their limit price; MARKET orders use the fetched quote. Set to 0 to disable.
13. Added tests for both LIMIT and MARKET order rejection above the cap. This is a per-order notional guard, not a portfolio exposure limit; derivative multipliers/lot-size data still require verification.

### Additional improvement — read-only broker status reconciliation foundation
14. Added nullable broker-order reference/status/check timestamp/error metadata and a forward migration.
15. Added a read-only reconciliation service that checks ownership, refuses PAPER orders, requires a persisted broker order ID and usable Upstox session, validates the returned order ID, and records broker status without changing local order status, positions, or cash.
16. Added mocked tests for successful status capture, PAPER-mode refusal, and mismatched broker order IDs. This is a foundation only: there is no live order placement or automatic fill/cancel reconciliation.

### Additional improvement — authenticated broker-status API
17. Exposed a read-only authenticated endpoint `GET /portfolios/{portfolio_id}/orders/{order_id}/broker-status`. It checks portfolio ownership and returns the reconciliation service result. It does not place orders or modify local execution/accounting status.
18. The endpoint is useful only for a LIVE order that already has a stored broker order ID and a valid Upstox session; the app still has no live submission lifecycle.


### Second-pass audit fixes — 17 October 2026
19. Made paper fills atomic across order status, aggregate position, cash balance and execution row; added a rollback regression test.
20. Added per-strategy position allocation and strategy-specific realized P&L, preventing a strategy from treating a manual/other-strategy position as its own and preventing manual sells from consuming strategy-allocated shares.
21. Added a migration that backfills historical strategy-specific P&L and open allocations from strategy-tagged executions. The clean SQLite upgrade passes; populated staging-data validation remains required.
22. Added fail-closed instrument/segment validation to order, strategy and backtest paths. Futures/options are rejected until verified derivative instrument data, tick-size normalization, lot sizing and contract risk controls are implemented; frontend segment choices reflect this.
23. Corrected outdated documentation about the paper LIMIT matcher, kill switch, idempotency and instrument-master status.

### Verification after second-pass fixes
- Latest verified backend CI: **188 passed, 1 warning**, with clean SQLite Alembic upgrade: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39030790984.
- Latest frontend TypeScript and Next.js build checks passed after an earlier intermittent Google-font module resolution failure: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39030941702.
- No real broker orders were placed; live trading remains disabled.

24. Wired the manual portfolio order form to the existing backend idempotency key: the key is reused after network/server errors and cleared after success or when the payload changes.


### 17 October 2026 — migration verification and persistent instructions
- Added `PROJECT_INSTRUCTIONS.md`, a verbatim copy of the complete `Pasted text(6).txt` requirements, and `PROGRESS.md`, a persistent continuation checklist/state log.
- Added a populated legacy-database regression test for strategy-position migration backfill. It verifies realized P&L, weighted average/open allocation, long-only over-sell attribution, unchanged aggregate position/cash, and repeat upgrade.
- Verification on commit `1fe681246cb88a9505302a1763128c51ab72802d`: backend **190 passed, 1 warning** plus clean SQLite migration upgrade; frontend TypeScript and Next.js build passed.


### 17 October 2026 — strategy idempotency hardening
- Strategy orders now use stable per-candle idempotency keys; no strategy order is submitted when candle timestamp parsing fails.
- Reused keys must match strategy/manual execution reason and strategy ID, in addition to order parameters.
- Added regression tests for repeated same-candle entry, missing timestamps and cross-scope key reuse. First run exposed a test setup assumption (₹30,000 did not exceed the 25% cap on ₹500,000 virtual capital); the test was corrected with an explicit 1% cap.
- Latest verified code commit `e9f8b7bb56f3300d1016195a773a26845d94d717`: backend **193 passed, 1 warning**, migration upgrade passed, frontend TypeScript/build passed.


### 17 October 2026 — Upstox Place Order V3
- Updated `UpstoxAdapter.place_order` to the official V3 endpoint after verifying the current docs mark V2 place-order as deprecated. Updated the mocked test to assert the V3 URL and `data.order_ids` response shape.
- CI on `ded6138b93f8e18f96117f5bb4fce0ec8aeaeb1b`: backend **193 passed, 1 warning**, migration upgrade passed, frontend checks passed. No live requests.


### 17 October 2026 — Upstox V3 modify/cancel adapter methods
- Added abstract `modify_order` and `cancel_order` operations to the broker adapter contract and implemented the official Upstox V3 `PUT /order/modify` and `DELETE /order/cancel?order_id=...` calls.
- Added mocked tests for endpoint, payload/query and response shape. Methods remain unconnected; no local accounting is updated based on request acceptance.
- CI on `2bc21c59dc4c9b8d1cd2e38d24a611433e07d82c`: backend **195 passed, 1 warning**, migration upgrade passed, frontend checks passed.


### 17 October 2026 — live readiness audit
- Documented current risk, OAuth/token, instrument validation and reconciliation state in the progress/handover/audit records. The paper-only order guard remains mandatory.
- Selected a small read-only hardening task: reject broker status payloads without a matching order ID, using the documented Upstox Get Order Details response shape. No live order submission will be wired in this step.


### 17 October 2026 — broker status identity validation
- `BrokerReconciliationService` now requires the broker status payload to include a non-empty `order_id` matching the requested broker order before it stores the status.
- Added mocked coverage for missing broker order ID. The service remains read-only and does not infer fills/cancellations.
- CI on `9f1e1300acc15f85d8abf1e29e73de34f6ca14f3`: backend **195 passed, 1 warning**, migration check passed, frontend checks passed.
