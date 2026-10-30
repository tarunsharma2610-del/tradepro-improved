# Phase 4 — Transactional PAPER Stop-Event Claim Service

Date: 30 October 2026
Repository: `tarunsharma2610-del/tradepro-improved`
Branch: `phase4/redis-market-data-publisher`

## Scope

This slice adds an atomic, database-backed claim operation for an already-validated stop quote. It is not connected to the Redis dispatcher and does not execute orders.

## Claim contract

- Caller supplies user, portfolio, strategy, instrument, subscription epoch, quote version and trigger price.
- Validate active user-owned portfolio; active strategy must match both portfolio and instrument; instrument must exist.
- Lock order is portfolio → strategy → position, matching the existing PAPER execution service's portfolio-first convention.
- Require an open non-zero portfolio/instrument position.
- Fail closed if another active strategy shares the same portfolio/instrument because Position is portfolio+instrument scoped, not strategy allocated.
- Enforce finite positive trigger price, positive quote version, non-empty bounded epoch, timezone-aware claim time and bounded lease duration.
- Insert event with unique strategy/event/epoch/version key, random claim token, lease expiry and attempt count.
- Duplicate quote claim returns None using a nested savepoint; it does not poison the caller's outer transaction.
- Caller owns commit/rollback. The claim is not durable until caller commits.

## Tests

- Persist claim token, state, lease and attempt count.
- Duplicate idempotency claim.
- Cross-user portfolio rejection.
- Strategy/instrument mismatch.
- Multiple active strategies sharing one position fail closed.
- Missing/flat position rejection.
- Invalid quote identity, price, time and lease rejection.

## Deliberate non-goals

- No dispatcher consumer.
- No event state transition to EXECUTING/COMPLETED.
- No order creation or call into ExecutionService.
- No automatic retry or lease reclaim yet.
- No live broker order writes; PAPER mode only.

## Concurrency limitation

The unique database constraint is the final duplicate guard. PostgreSQL row locks serialize claims for one portfolio/strategy/position when all writers use this service. Multi-replica PostgreSQL 16 tests are still required before the service is considered production-safe.
