# Phase 4 — Bounded Market Quote Dispatcher

Date: 30 October 2026
Repository: `tarunsharma2610-del/tradepro-improved`
Branch: `phase4/redis-market-data-publisher`

## Purpose

Introduce a bounded in-process handoff between the validated Redis/scanner callback and future PAPER stop-event processing. The callback must remain fast and must not perform database, broker, or order work.

## Contract

- One pending slot per `(user_id, instrument_key)`.
- FIFO order is by first enqueue of each distinct key.
- Newer accepted versions for an already-pending key replace its pending value; they do not add queue entries.
- Duplicate or lower versions in the same epoch are rejected.
- A new epoch replaces the pending value for that key. Epoch authenticity/order is owned by the Redis consumer/scanner before publication.
- Unique keys are bounded by configurable `max_pending_keys` (default 1,024).
- If a new unique key arrives when full, it is rejected and `dropped_unique_keys` increments. No unbounded task spawning or queue growth.
- Consumer takes the newest value atomically for a key. Consumers must call `task_done()` exactly once per successful `get()`.
- Queue overflow is fail-closed: it drops dispatch work rather than bypassing the queue or executing inline.

## Deliberate limitation

This commit adds the isolated dispatcher and unit tests only. It does not yet connect quotes to strategy evaluation or order execution. The next step is to define the durable stop-event/position ownership state machine and its database schema/locking before any dispatcher consumer can trigger PAPER exits.

## Test gates in this slice

- Same-key coalescing to newest quote.
- Bounded unique-key overflow and explicit drop counter.
- Duplicate/out-of-order version rejection.
- Per-user and per-instrument key isolation.
- Epoch replacement.
- Invalid input rejection.

## Safety

- PAPER only; no live broker writes.
- No database or broker access in the dispatcher.
- No order creation from Redis callback.
- PR #9 remains Draft and unmerged.


## Durable PAPER stop-event storage — 30 October 2026

- Added `PaperStopEvent` as an inert durable idempotency/claim record keyed uniquely by strategy, event type, subscription epoch and quote version.
- Persisted fields include tenant/portfolio/strategy/instrument scope, trigger LTP, state, claim token/lease expiry, attempt count, safe error code and completion timestamp.
- Database checks constrain supported event type, state vocabulary, positive quote version/trigger price and nonnegative attempts.
- This is schema/model groundwork only: no dispatcher consumer creates events, no stop event can authorize an order, and no live broker write path was added.
- Unit tests cover persistence, duplicate quote-event rejection and database check constraints.
- Remaining before any event consumer: enforce strategy↔portfolio↔instrument and user↔portfolio consistency transactionally; define one owner for shared portfolio/instrument positions; add PostgreSQL row-lock/claim concurrency tests; define recovery for CLAIMED/EXECUTING after process death; connect only to existing PAPER execution after those gates.


## Latest follow-up — 30 October 2026

Transactional PAPER stop-event claim service commit `6ac3882a98f3c66abb4cd62848971b6277ab3be7` passed exact-head Backend CI #41080156436. Claims validate tenant/strategy/instrument ownership, lock portfolio → strategy → position, reject ambiguous shared-position ownership and duplicate quote identity, and store a bounded lease. The dispatcher remains disconnected from the claim service and order execution. Next gates are PostgreSQL 16 multi-worker concurrency, event transitions/lease reclaim, crash recovery, explicit shared-position ownership, then controlled PAPER integration. PR #9 Draft/unmerged; PAPER mandatory; live broker writes disabled.


## Cancellation recovery implementation — 1 November 2026

- Added `release()` for the same consumer task that owns the in-flight key. On cancellation/interruption it requeues the in-flight observation unless a newer coalesced observation exists, in which case the newest wins.
- `task_done()` remains the success acknowledgement. Both operations clear the in-flight ownership and maintain queue accounting.
- Regression tests cover cancellation requeue and latest-value preference.
- Exact-head Backend CI #41290374836 passed on `1e37ad6e52a3c94a35a5519cc496ab3000f3f44f`, including full pytest, broker-write boundary, SQLite/PostgreSQL 16 migration cycles and synthetic restore drill.
- Important limitation: this dispatcher is in-memory and process-local. `release()` handles cooperative task cancellation, not hard process death. Durable replay/recovery must be supplied by the upstream Redis delivery semantics and PostgreSQL claim/lease state. Do not treat the dispatcher as a durable queue.
- Next: supervised consumer lifecycle/backoff/shutdown tests, then non-blocking Redis callback → dispatcher wiring and a separately supervised PAPER-only durable consumer. Live broker writes remain disabled.



## Phase 4 authoritative audit/status — 2 November 2026
This section supersedes older Phase 4 resume pointers where they conflict; older entries remain historical.
- Scope only tarunsharma2610-del/tradepro-improved, branch phase4/redis-market-data-publisher. PR #9 targets phase4/roadmap-progress-checkpoints and remains OPEN, Draft, unmerged. Original tarunsharma2610-del/Tradepro remains untouched.
- Latest verified code/test head before this docs repair: 654b0a5d2cb898a0b6dcd4dcb6556b0af6c2ccc2. Exact-head Backend CI #41398555424 PASSED on that SHA, including stale LIVE broker-position snapshot regression. Preceding commit 502303d2f2d9be1ed0ece0ecb5b280ed5f7db2e4 passed #41398528946.
- Earlier API/Redis safeguards passed: #41397210305 (3281618), #41397227429 (a65c463), #41397602437 (d01146f), #41397616502 (147d59b). Prior docs CI #41398105822 passed on 027850d; this docs sync needs its own exact-head CI.
### Completed, CI-backed Phase 4 scope
- PAPER is the only enabled execution path. Broker place_order/modify_order/cancel_order writes remain disabled; AST broker-write boundary runs in Backend CI.
- Mode-aware portfolio analytics and ownership/isolation checks are implemented. LIVE balance does not fall back to simulated starting capital; LIVE positions fail closed rather than exposing PAPER positions.
- Read-only Upstox LIVE funds, positions and holdings sync uses the allocated owner-scoped broker connection and immutable portfolio/user/connection-bound snapshots. Failed sync retains the prior snapshot and does not mutate PAPER accounting.
- Analytics Token storage/ownership/expiry controls, Upstox V3 stream lifecycle, feed-mode subscription/reconnect/startup recovery and SDK compatibility review have prior green CI.
- Redis publisher/consumer has user-scoped TTL snapshots, schema/version and epoch/version checks, atomic publishing, Pub/Sub notifications, real Redis tests, restart/recovery and independent process delivery tests.
- Worker-managed Redis consumer lifecycle, lease/replica coordination, scanner intake and 15-second scanner TTL are implemented. Scanner-to-PAPER trailing-stop evaluation consumes fresh user/instrument-scoped LTP while five-minute candles remain the indicator source.
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
