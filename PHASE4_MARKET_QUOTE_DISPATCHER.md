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
