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
