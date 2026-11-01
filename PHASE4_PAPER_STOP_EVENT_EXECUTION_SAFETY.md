# Phase 4 — PAPER stop-event execution safety gate

## Purpose

This note records the required safety gates before durable market stop events may trigger PAPER executions. The event claim and lifecycle primitives are state-coordination components only; they do not themselves provide exactly-once accounting.

## Current verified facts

- `PaperStopEventClaimService` validates user-owned active portfolio, active strategy/instrument ownership, and a non-flat portfolio/instrument position.
- The claim service rejects multiple active strategies sharing the same portfolio/instrument position. This is correct fail-closed behaviour because `Position` has one row per portfolio/instrument and no strategy allocation ledger exists.
- `PaperStopEventLifecycle` uses claim-token-fenced conditional updates for CLAIMED, EXECUTING, COMPLETED, RETRYABLE and FAILED states. It leaves transaction ownership with the caller.
- `MarketQuoteDispatcher` provides bounded in-process single-flight/coalescing. It is not durable and is not connected to stop-event execution.
- `ExecutionService._fill()` currently calls repository methods that commit internally: order creation, position get-or-create/save, portfolio save, and finally execution persistence. These commits split what must become one accounting transaction.

## Blocking failure mode

If a stop-event consumer calls the current execution path and the process fails after an early repository commit but before all accounting rows are persisted, the event may remain retryable while some effects are already committed. Reprocessing can create duplicate orders or leave cash, position, order and execution records inconsistent. Marking the event COMPLETED separately does not solve this crash window.

## Required design

1. Refactor the PAPER fill operation to perform order, position, portfolio cash, execution/charge and stop-event completion writes in one SQLAlchemy transaction. The caller owns commit/rollback; repository methods on this path flush only.
2. Persist a unique stop-event idempotency reference on the execution/order boundary. Enforce it with a database uniqueness constraint and provide a recovery lookup. Repeated delivery must return the existing committed result and must not apply a second fill.
3. Preserve one authoritative execution implementation and its existing depth pricing, cost estimation, portfolio risk, position math, and accounting. Do not build a parallel stop-only fill engine.
4. Establish and test a single lock order across portfolio, strategy, position, event and idempotency records. Revalidate user/portfolio ownership, strategy active state, position quantity/direction, stop condition, kill switch and risk under lock immediately before applying the fill.
5. Keep multiple active strategies on the same portfolio/instrument rejected until explicit per-strategy position allocation is designed, migrated and reconciled.
6. Add fault-injection coverage after each logical persistence stage; verify rollback leaves no order, position, cash, execution or completion side effects.
7. Add PostgreSQL 16 multi-session tests for duplicate delivery, concurrent consumers, stale claim tokens, worker crash/reclaim and exactly one accounting effect.
8. Only after those gates pass may the bounded dispatcher feed the durable stop-event consumer.

## Explicit non-goals and safety

- No live broker place/modify/cancel writes.
- No live mode enablement.
- No PR merge or deployment.
- No bypass of the existing PAPER risk, market-depth, kill-switch, charge-estimation or accounting paths.
- No modification to the original `tarunsharma2610-del/Tradepro` repository.

## Next implementation sequence

1. Introduce flush-only repository operations or equivalent unit-of-work methods without changing unrelated caller transaction behaviour.
2. Refactor `ExecutionService` to support caller-owned transactions while preserving existing API semantics.
3. Add the unique stop-event idempotency key and duplicate-result recovery.
4. Prove atomicity with failure injection and PostgreSQL 16 concurrency tests.
5. Integrate the lifecycle and dispatcher only after all above checks pass.
