# Phase 4 Scanner TTL and Worker Lifecycle Checkpoint — 30 October 2026

## Repository and safety boundary
- Repository: `tarunsharma2610-del/tradepro-improved` only.
- Implementation branch: `phase4/redis-market-data-publisher`.
- PR #9 targets `phase4/roadmap-progress-checkpoints`; it remains open, Draft and unmerged.
- Original `tarunsharma2610-del/Tradepro` is out of scope and must not be modified.
- PAPER mode is mandatory. Live broker order submission, modification and cancellation remain disabled. No deployment or credentialed Upstox smoke test is claimed.

## Exact-head verification
- Scanner TTL baseline: `b7d27bb5026cda96e465461bb4dc5621b2f76e88`; Backend CI [#41074310209 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41074310209).
- Scanner-to-PAPER trailing-stop integration: `9a4b6e6ffb54296d4bab2887d9046b8271c37329`; Backend CI [#41076227643 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41076227643).
- All workflow gates passed: backend pytest; Redis restart-recovery integration environment; broker-write boundary enforcement; SQLite upgrade/downgrade/re-upgrade; PostgreSQL 16 migration round-trip; synthetic PostgreSQL/document-volume restore; restore evidence retention.
- The previous run [#41074017601](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41074017601) failed with 1,329 passed and one failure in `test_scanner_expires_stale_observations`. Its test changed monotonic time to 15.1 after recording an uncontrolled initial clock value.
- Commit `b7d27bb` corrected the test to capture at monotonic 100.0 and query at 115.1. The exact-head CI above validates that correction and all workflow gates.

## Verified scanner and worker state
- `MarketScanner` computes read-only per-user/instrument observations; it does not emit trade signals, persist orders or call broker order endpoints.
- Scanner observation TTL is 15 seconds; stale observations are removed and returned as unavailable.
- Scanner validates user ownership, instrument identity, epoch/version ordering, positive finite LTP, exchange timestamp and timezone-aware receive timestamp. Missing optional market fields remain null.
- `app/worker.py` creates a `RedisMarketQuoteWorker` and forwards validated consumer quotes to `MarketScanner.process_quote`.
- `RedisMarketQuoteWorker` discovers active durable subscriptions from the database, scopes them to the owning Upstox broker connection/user, rejects conflicting feed-mode assignments, reconciles per-user consumers, uses token-checked Redis leases to coordinate replicas, renews/releases leases, isolates downstream callback failures, expires local quote cache entries, and cancels consumers/cleans up on shutdown.
- Worker consumer lifecycle unit tests cover lease ownership, replica exclusion/handoff, lease replacement, quote expiry, factory failure cleanup and scanner callback failure isolation.
- These are implementation/test findings, not evidence of production deployment, sustained load capacity, or live-account behaviour.

## Important remaining gap
- The scanner receives Redis quotes, but `StrategyExecutionService.evaluate()` still fetches historical plus intraday 5-minute candles independently and computes indicators from candles.
- `StrategyExecutionService` now accepts the worker's shared scanner and uses a fresh user+instrument-scoped LTP for trailing-stop evaluation when the candle signal is HOLD. The worker passes the same scanner instance used by the Redis quote callback.
- Five-minute candles remain the indicator source. Existing manual/API evaluation without an injected scanner retains candle-only behavior. This is a first PAPER integration slice, not full streaming strategy evaluation.
- Preserve the existing five-minute indicator semantics, candle freshness gate, risk checks, kill switch, and PAPER-only execution. Do not substitute a raw LTP tick for candle history or allow a quote to bypass risk/freshness checks.
- `ExecutionService.place_order()` currently creates orders with `trading_mode="PAPER"`; PAPER market fills still require a fresh full market-depth snapshot and use the existing paper accounting path. Do not add or enable broker order writes.

## Next implementation sequence
1. Add strategy-level regression proving an expired scanner observation cannot trigger a trailing stop; add exact-instrument mismatch coverage.
2. Audit the five-minute strategy evaluation cadence against the 15-second quote TTL. Current behavior only checks trailing stops during each scheduled strategy evaluation; it is not a tick-by-tick stop monitor.
3. Design a separate quote-driven PAPER stop-monitor cadence only if it can reuse existing risk, depth, idempotency and accounting boundaries without duplicating indicator/candle work.
4. Define safe behaviour for Redis outage, stream silence, reconnect and strategy worker replica handoff. No stale quote fallback for any path requiring a live quote.
5. Add multi-strategy/same-instrument tests proving one user-scoped quote can be read by that user's strategies without cross-tenant leakage or duplicate order creation.
6. Run full exact-head Backend CI; fix failures before recording a new green checkpoint.
7. Separately plan multi-user/multi-instrument sustained-load tests and deployment/credentialed smoke tests; these remain deferred.

## Current status
- Scanner observation expiry: implemented and exact-head CI passed.
- Redis consumer lifecycle and scanner callback wiring: present and covered by tests; production operation not yet validated.
- Scanner-to-PAPER strategy consumption: first slice implemented; exact-head CI passed on `9a4b6e6`; stale-observation strategy regression and cadence design remain pending.
- PR #9: Draft/open/unmerged; no merge or main update authorized.


## Scanner-to-PAPER integration follow-up — 30 October 2026

- Exact implementation commit `9a4b6e6ffb54296d4bab2887d9046b8271c37329` passed Backend CI #41076227643.
- Worker injects its shared `MarketScanner` into each `StrategyExecutionService` evaluation. A fresh per-user/per-instrument LTP is used for trailing-stop checks when candle-derived signal is HOLD; five-minute candles remain the indicator source.
- Tests cover fresh LTP trailing-stop exit and cross-user isolation. The follow-up test added on this documentation/test increment checks that a 15.1-second-old observation is unavailable to strategy evaluation.
- Important limitation: strategy evaluation still runs on a 300-second cadence. This is not a tick-by-tick stop monitor; next work must evaluate a safe quote-driven PAPER stop-monitor path without repeating candle downloads or bypassing execution/risk/depth/accounting safeguards.
- No live broker writes, deployment, or credentialed Upstox smoke test.
