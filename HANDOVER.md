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
- Strategy-level daily-loss protection exists. Portfolio-wide loss, exposure, and order-frequency caps remain gaps according to `AUDIT_REPORT.md`.
- The audit reports CI results of 167 backend tests passing and a successful frontend typecheck/build. These are historical CI results, not a fresh run during this continuation.

## Priority order
1. Add and test a fail-closed guard so `ExecutionService` refuses to accept orders when `TRADING_MODE` is not `PAPER`, until a separately reviewed live execution service exists.
2. Add a regression test proving `TRADING_MODE=LIVE` fails before broker calls or database order creation.
3. Design durable idempotency with a database-enforced uniqueness constraint and restart-safe reconciliation; do not rely only on an in-memory lock.
4. Add portfolio-level daily-loss, exposure, order-value, and order-frequency limits enforced server-side.
5. Implement Upstox instrument master sync and streaming only after verifying the current official API documentation.
6. Add broker order lifecycle handling (partial fills, timeout/unknown state, retries, cancellation, reconciliation) before any live order placement.
7. Run targeted tests, full backend suite, frontend typecheck/build, migration checks, and inspect CI results; report exact results without claiming unrun tests.
8. Update `AUDIT_REPORT.md` with the implementation and test evidence. Verify migrations against staging before production deployment.

## Release gate
Live trading remains **NOT READY** until broker execution, durable duplicate prevention, broker-state reconciliation, risk limits, credential handling, session expiry, operational controls, and relevant end-to-end tests have all been verified. No real orders are authorized by this handover.