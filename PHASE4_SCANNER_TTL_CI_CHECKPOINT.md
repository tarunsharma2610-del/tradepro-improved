# Phase 4 Scanner TTL and Worker Lifecycle Checkpoint — 30 October 2026

## Repository and safety boundary
- Repository: `tarunsharma2610-del/tradepro-improved` only.
- Implementation branch: `phase4/redis-market-data-publisher`.
- PR #9 targets `phase4/roadmap-progress-checkpoints`; it remains open, Draft and unmerged.
- Original `tarunsharma2610-del/Tradepro` is out of scope and must not be modified.
- PAPER mode is mandatory. Live broker order submission, modification and cancellation remain disabled. No deployment or credentialed Upstox smoke test is claimed.

## Exact-head verification
- Exact PR head: `b7d27bb5026cda96e465461bb4dc5621b2f76e88`.
- Backend CI [#41074310209 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41074310209).
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
- The worker's scanner observation is not yet consumed by strategy evaluation. PAPER strategy integration is therefore **not complete**.
- Preserve the existing five-minute indicator semantics, candle freshness gate, risk checks, kill switch, and PAPER-only execution. Do not substitute a raw LTP tick for candle history or allow a quote to bypass risk/freshness checks.
- `ExecutionService.place_order()` currently creates orders with `trading_mode="PAPER"`; PAPER market fills still require a fresh full market-depth snapshot and use the existing paper accounting path. Do not add or enable broker order writes.

## Next implementation sequence
1. Design a narrow, explicit strategy input contract: five-minute candles remain the indicator source; a validated fresh scanner observation may be used only for a reviewed purpose such as live valuation/trailing-stop price or a fail-closed freshness gate.
2. Ensure quote ownership is tied to the strategy portfolio user and exact instrument key; require matching epoch/version and <=15-second receive/exchange freshness.
3. Define safe behaviour for missing/stale quote, Redis outage, stream silence, reconnect and strategy worker replica handoff. No stale candle-close or cached quote fallback for any path that requires a live quote.
4. Add unit and integration tests proving cross-user/instrument quotes cannot influence a strategy; stale/missing quotes hold; candle indicators remain unchanged; kill switch/risk gates remain effective; entries/exits remain PAPER.
5. Audit whether multiple strategies share an instrument and how scanner observations are routed without cross-tenant leakage or duplicate evaluation.
6. Run full exact-head Backend CI; fix failures before recording a new green checkpoint.
7. Separately plan multi-user/multi-instrument sustained-load tests and deployment/credentialed smoke tests; these remain deferred.

## Current status
- Scanner observation expiry: implemented and exact-head CI passed.
- Redis consumer lifecycle and scanner callback wiring: present and covered by tests; production operation not yet validated.
- Scanner-to-PAPER strategy consumption: pending design and implementation.
- PR #9: Draft/open/unmerged; no merge or main update authorized.
