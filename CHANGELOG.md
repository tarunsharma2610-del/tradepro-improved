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
