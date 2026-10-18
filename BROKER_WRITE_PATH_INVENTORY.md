# Broker-write path inventory

Status: Phase 2 review artifact — 18 October 2026

## Safety rule

No production service may invoke broker order mutation methods directly. The Upstox adapter is the low-level HTTP implementation, not an authorization boundary. The central `LiveBrokerWriteService` currently denies every mutation and must remain unwired until its full intent/authorization/recovery protocol is approved. PAPER execution must not call broker order endpoints.

## Current path inventory

| Component | Observed role | Write capability/status | Required control |
|---|---|---|---|
| `backend/app/brokers/upstox/adapter.py` | Low-level Upstox adapter | Defines `place_order`, `modify_order`, `cancel_order`; these methods can issue HTTP writes | Definitions only; no direct callers until central gate is reviewed |
| `backend/app/brokers/base.py` | Adapter interface | Abstract write method definitions | Contract only; never a runtime authorization decision |
| `backend/app/services/live_broker_write_service.py` | Planned single live write boundary | Deny-all for place/modify/cancel; no adapter calls | Keep fail-closed and unwired |
| `backend/app/services/execution_service.py` | Current execution engine | PAPER-only `place_order`; rejects non-PAPER mode; local PAPER cancel only | Preserve PAPER-only behavior; do not turn this into live broker submission |
| `backend/app/services/strategy_execution_service.py` | Strategy entry/exit orchestration | Calls `ExecutionService.place_order` for PAPER execution | Must continue using PAPER engine; no broker adapter write methods |
| `backend/app/services/live_execution_service.py` | Live intent preflight | Validates candidate intent; no broker write or persisted order submission | Preflight result is not permission to submit |
| `backend/app/services/live_preflight_coordinator.py` | Read-only live preflight composition | Reads account safety, quote/session/position/funds/margin snapshots; no order write | Keep unregistered; fail closed on stale/missing data |
| `backend/app/services/live_order_recovery_service.py` | Persisted intent identity and recovery | Persists intents and performs read-only broker history lookup; intentionally does not submit | Unknown/no-match must never auto-resubmit |
| `backend/app/services/broker_reconciliation_service.py` | Broker status reconciliation | Read-only order-status lookup | Keep separate from write authorization |
| `backend/app/services/broker_trade_ingestion_service.py` | Broker fill ingestion | Read-only broker trade lookup and local accounting updates | Never issue place/modify/cancel requests |
| `backend/app/api/v1/` | HTTP API routers | No order-placement router is currently present in this directory; verify before introducing one | Any future live order route must delegate to central boundary only |
| `backend/app/worker.py` | Background worker entrypoint | No direct live broker-write call was found in reviewed references | Re-run static guard whenever workers/tasks are added |

## Source guard

`backend/scripts/check_broker_write_boundary.py` scans production Python AST for references to `place_order`, `modify_order`, and `cancel_order` independent of the receiver's variable name. It allows only the known `self.execution.place_order` calls in `strategy_execution_service.py` because those call the PAPER `ExecutionService`, and it excludes low-level method definitions in the Upstox adapter. Regression tests cover generic receiver bypass attempts and the approved PAPER call.

This source guard does not prove safety against reflection, `getattr`, dynamic imports, aliases, or external callers. Review call sites and test behavior as well as running the guard.

## Before any future live write implementation

1. Require authenticated user and portfolio/account ownership on every mutation.
2. Require an immutable, persisted intent with a unique idempotency key and stable broker tag.
3. Check the account-wide safety latch, explicit current user confirmation, MFA/authorization where required, independent server interlocks, and a concrete fresh account-wide risk gate.
4. Serialize concurrent submissions/modifications/cancellations per broker account and order; commit the submission-unknown state before network I/O.
5. Treat timeouts, malformed responses, and no-match recovery as ambiguous; never blind-retry a broker POST.
6. Verify broker order state after modify/cancel; reconcile fills and child orders without double-counting.
7. Add tests proving every API, worker, retry, recovery, and adapter path is blocked by default, and test PostgreSQL concurrency.
8. Keep PAPER mode mandatory and live submission disabled until a separate explicit approval and review.

## Review limitation

This inventory is based on the repository's current route/service file listing and direct source inspection of the components named above. It is not a proof that no dynamic or future call path exists. Update this file in the same commit whenever a new order execution or broker adapter path is added.
