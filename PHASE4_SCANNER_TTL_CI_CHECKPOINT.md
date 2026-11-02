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


## Quote-driven PAPER stop monitor audit — 30 October 2026

- Baseline `d6fd555d17faa02beff229a04acd3dfcd4cf86c5` passed Backend CI #41076913522.
- A separate architecture audit was saved in `PHASE4_PAPER_STOP_MONITOR_DESIGN.md`.
- A tick-driven stop monitor is intentionally not enabled yet. The audit identified missing durable event idempotency, strategy/position concurrency locks, ambiguous ownership when multiple strategies share one portfolio/instrument, exchange-timestamp freshness enforcement, and bounded quote dispatch/backpressure.
- LTPC WebSocket messages remain trigger/valuation data only; PAPER fills must continue through the existing shared ExecutionService and fresh Full Market Quotes V3 depth. No live broker order writes.
- Next work: implement/test a bounded coalescing dispatcher and durable stop-event claim/ownership model before connecting quote events to PAPER exits.


## Latest follow-up — 30 October 2026

Transactional PAPER stop-event claim service commit `6ac3882a98f3c66abb4cd62848971b6277ab3be7` passed exact-head Backend CI #41080156436. Claims validate tenant/strategy/instrument ownership, lock portfolio → strategy → position, reject ambiguous shared-position ownership and duplicate quote identity, and store a bounded lease. The dispatcher remains disconnected from the claim service and order execution. Next gates are PostgreSQL 16 multi-worker concurrency, event transitions/lease reclaim, crash recovery, explicit shared-position ownership, then controlled PAPER integration. PR #9 Draft/unmerged; PAPER mandatory; live broker writes disabled.



## Phase 4 authoritative audit/status — 2 November 2026
This section supersedes older Phase 4 resume pointers where they conflict; older entries remain historical.
- Scope only tarunsharma2610-del/tradepro-improved, branch phase4/redis-market-data-publisher. PR #9 targets phase4/roadmap-progress-checkpoints and remains OPEN, Draft, unmerged. Original tarunsharma2610-del/Tradepro remains untouched.
- Latest verified code/test head before this docs repair: 654b0a5d2cb898a0b6dcd4dcb6556b0af6c2ccc2. Exact-head Backend CI #41398555424 PASSED on that SHA, including stale LIVE broker-position snapshot regression. Preceding commit 502303d2f2d9be1ed0ece0ecb5b280ed5f7db2e4 passed #41398528946.
- Earlier API/Redis safeguards passed: #41397210305 (3281618), #41397227429 (a65c463), #41397602437 (d01146f), #41397616502 (147d59b). Prior docs CI #41398105822 passed on 027850d; this docs sync needs its own exact-head CI.
### Completed, CI-backed Phase 4 scope
- PAPER is the only enabled execution path. Broker place_order/modify_order/cancel_order writes remain disabled; AST broker-write boundary runs in Backend CI.
- Mode-aware portfolio analytics and ownership/isolation checks are implemented. LIVE balance does not fall back to simulated starting capital; LIVE positions fail closed rather than exposing PAPER positions.
- Read-only Upstox LIVE funds, positions and holdings sync uses allocated owner-scoped broker connection and immutable portfolio/user/connection-bound snapshots. Failed sync retains prior snapshot and does not mutate PAPER accounting.
- Analytics Token storage/ownership/expiry controls, Upstox V3 stream lifecycle, feed-mode subscription/reconnect/startup recovery and SDK compatibility review have prior green CI.
- Redis publisher/consumer has user-scoped TTL snapshots, schema/version and epoch/version checks, atomic publishing, Pub/Sub notifications, real Redis tests, restart/recovery and independent process delivery tests.
- Worker-managed Redis consumer lifecycle, lease/replica coordination, scanner intake and 15-second scanner TTL are implemented. Scanner-to-PAPER trailing-stop evaluation consumes fresh user/instrument-scoped LTP while five-minute candles remain indicator source.
- Durable PAPER stop-event claim/state/lease/retry/recovery, PostgreSQL 16 concurrency tests, bounded dispatcher and PAPER worker wiring have prior green CI. Full end-to-end market-to-ledger acceptance remains outstanding.
- Read-only LIVE unrealized P&L API GET /api/v1/portfolios/{portfolio_id}/live-unrealized-pnl checks owner/mode/current allocation/snapshot binding, reads exact instrument keys through user-scoped Redis consumer, fails closed on stale/missing/invalid quotes and Redis outage, and does not mutate accounting.
- LIVE position snapshots missing timestamps, future-dated or older than 120 seconds are rejected. Exact-head CI #41398555424 passed.
### Remaining gates
1. Full authenticated LIVE P&L API integration test using real ephemeral Redis publisher/consumer in the same test flow (component-level Redis tests already exist).
2. Internal realized-P&L ledger and broker fill/trade reconciliation; keep broker daily P&L, broker realized P&L and internal lifetime realized P&L distinct.
3. Frontend LIVE read-only P&L display with separate realized/unrealized values, freshness and unavailable states.
4. Full Redis→scanner→dispatcher→durable stop claim→PAPER fill→ledger/position/cash end-to-end tests, including crashes, retries, duplicate/out-of-order events and competing exits.
5. Multi-user/multi-instrument load/backpressure, metrics/alerts, runbooks, worker recovery; production Oracle restore and credentialed Upstox smoke tests remain deployment gates.
6. LIVE order readiness is not achieved; any future write gateway needs separate design, deny-by-default authorization, idempotency, audit and explicit approval.
### Security audit status
- PHASE4_P0_BASELINE_AUDIT.md exists (29 Oct) but is a static source/workflow audit; it explicitly did not perform runtime or credentialed smoke testing.
- Existing controls include broker-write AST enforcement, ownership/mode checks, encrypted Analytics Token handling, Redis tenant namespacing/freshness, PostgreSQL concurrency, migration/restore CI and audit logging.
- Comprehensive Phase 4 security assessment is NOT COMPLETE. No verified full IDOR sweep, SAST/DAST report, dependency vulnerability scan, authenticated/independent penetration test or production configuration review is evidenced. Do not claim penetration-tested or production security-approved.
- Remaining security: endpoint authorization matrix and adversarial IDOR tests; secret redaction/storage review; rate-limit/abuse tests; dependency/SAST; DAST on safe staging; broker-write reachability tests; tenant isolation/load; backup/restore and incident response.
### Safeguards
PAPER only; LIVE place/modify/cancel writes disabled; PR #9 Draft/unmerged; no deployment or LIVE gateway activation authorized. After docs sync, run CI on exact new docs head before saving a green checkpoint.



## Phase 4 security remediation checkpoint — 2 November 2026
This is the latest security/code checkpoint and supersedes older Phase 4 security next-step statements where they conflict.
- Latest verified code/test head: 2a98a07a8516c4cca4a46f8a0f511afcb2159e74.
- Exact-head Backend CI #41400727799 PASSED: 1,549 passed, 1 warning. Full workflow includes pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore and evidence retention.
- Confirmed finding fixed: Redis-backed rate limits previously failed open on Redis errors. The limiter now returns HTTP 503 when Redis is unavailable; test now asserts fail-closed behavior. Commits 62b7bdbdde812ed89d9eb3189b44c7922a7e63d7 and fdd00da6cd58242e2fe0cbf720f9cd66ee306ff8.
- Confirmed finding fixed: MFA disable previously required only an authenticated session. It now requires password re-verification and, when MFA is enabled, a current TOTP. Schema/service/API/tests are in 19a99b8, c369bb0, e6306be and 2a98a07. Exact-head CI above verifies the complete change.
- The Phase 4 P0 baseline audit exists but was a static source/workflow review, not a penetration test. These two findings are remediated; comprehensive security assessment remains NOT COMPLETE.
- Remaining security work: endpoint-by-endpoint IDOR/authorization matrix and adversarial tests; secret/token redaction/storage review; dependency vulnerability scan and SAST; DAST against isolated staging; broker-write reachability review; abuse/rate-limit and replay testing; tenant-isolation/load testing; deployment/backup/incident-response review; independent penetration test before any LIVE broker write.
- Other Phase 4 gates remain: authenticated LIVE P&L API against real Redis integration test; internal realized-P&L ledger and broker fill reconciliation; frontend LIVE read-only P&L; full Redis-to-PAPER-stop-to-ledger end-to-end proof; multi-user load/backpressure and operational runbooks.
- PAPER execution only; LIVE broker place/modify/cancel writes disabled; PR #9 remains Draft/open/unmerged; original Tradepro remains untouched. No deployment or LIVE gateway activation authorized.
