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
- A proposed fail-closed guard in `execution_service.py` was not committed. It still needs to be applied and tested in a controlled code-editing environment. No source-code change or test run is claimed in this continuation.
- This continuation has not placed any broker orders. Live trading remains not ready.
