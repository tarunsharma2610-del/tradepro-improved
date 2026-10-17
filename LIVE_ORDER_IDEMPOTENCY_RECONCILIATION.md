# Durable Live-Order Idempotency and Broker Reconciliation

Status: user-approved design; Phase 1 durable records/repository safeguards are CI-tested. Phase 2 has pure order/trade normalization, strict intent matching, versioned status persistence and individual broker-fill identity persistence. Broker reads/worker, fill aggregation/accounting and broker submission remain NOT implemented. Live order placement stays disabled.
Date: 2026-10-17
Scope: tradepro-improved only. Do not modify the original Tradepro repository.

## 1. Executive decision

Do not wire the existing PAPER execution path to the broker's place-order method. Build a separate, explicitly gated live execution orchestrator only after the design below has been reviewed and its migrations/tests are ready. The current `ExecutionService.place_order()` creates PAPER orders; the existing Upstox adapter has broker order placement/status/order-book methods, but these do not by themselves supply durable idempotency, uncertain-submit handling, fill deduplication, or reconciliation.

A distributed application cannot guarantee exactly-once external side effects solely with a database transaction. The safe target is: one durable intent per client key; no blind retry when broker acceptance is uncertain; broker-side correlation and reconciliation; and at-most-one automatic submit attempt until the outcome is established. Any uncertain state blocks further submissions for that intent.

## 2. Current-code findings

- `backend/app/models/order.py`: local Order has portfolio/instrument/side/type/quantity/price/status/trading_mode/reason and timestamps. It has no broker connection identity, durable client idempotency key, broker order ID, submit-attempt history, reconciliation state or version for optimistic concurrency.
- `backend/app/models/execution.py`: supports multiple executions per order in principle, but currently does not store broker trade ID or a uniqueness constraint that prevents the same broker fill being imported twice.
- `backend/app/repositories/order_repository.py`: commits create/save directly; there is no transactional outbox/claim protocol or idempotency lookup.
- `backend/app/services/execution_service.py`: the order path constructs PAPER orders. This must remain the only path for paper execution and must never call live broker submission.
- `backend/app/brokers/base.py` and `backend/app/brokers/upstox/adapter.py`: adapter exposes place order, order status, order book, positions and holdings. Existence of methods is not evidence of complete safe orchestration. Adapter response and order status normalization must be contract-tested against current official docs.
- Existing tests include a guard that PAPER market orders never call the live broker order endpoint. Keep and extend this regression test.

## 3. Proposed durable data model

Prefer additive tables first, avoiding a risky rewrite of the shared Order model.

### A. `live_order_intents` (durable client intent and state)
Required fields:
- `id` UUID primary key; `user_id`, `portfolio_id`, `broker_connection_id` foreign keys/scoped ownership.
- `client_idempotency_key` opaque client-supplied key; `request_hash` SHA-256 of canonical immutable order intent.
- immutable normalized order snapshot: instrument key, exchange/segment, side, order type, quantity, limit/trigger prices, product, validity, disclosed quantity, AMO/slicing fields if supported.
- `state`: CREATED, RISK_APPROVED, READY_TO_SUBMIT, SUBMITTING, SUBMITTED, SUBMISSION_UNKNOWN, ACKNOWLEDGED, OPEN, PARTIALLY_FILLED, FILLED, CANCEL_PENDING, CANCELLED, REJECTED, RECONCILIATION_REQUIRED, FAILED_FINAL.
- `broker_order_id`, broker correlation/tag, `submit_attempt_count`, `last_submit_at`, `last_reconciled_at`, `last_error_code` (sanitized), created/updated timestamps and optimistic version.
- Unique constraint scoped to the authenticated user + broker connection + client idempotency key. A duplicate key with the same request hash returns the existing intent/state; the same key with a different request hash returns a conflict and never submits.
- Unique broker order ID within broker connection when populated. Do not store access tokens or raw secrets in this table.

### B. `live_order_events` (append-only audit)
Record intent-created, risk decision, submit-started, broker response observed, timeout/unknown, reconciliation query/result, broker status transition, cancellation request, manual resolution and operator identity. Include correlation IDs, timestamp, sanitized error classification and safe state snapshots. Never store access tokens, client secrets or unredacted authorization headers. Restrict update/delete access; event history is the audit trail.

### C. `live_order_submit_outbox` (durable dispatch)
One dispatch row per intent, unique on intent ID. The intent and outbox row are committed in one DB transaction. A worker claims rows with a lease/claim token and bounded lease expiry. A lease expiry alone MUST NOT authorize resubmission if the prior request may have reached the broker; it authorizes reconciliation first. If a separate outbox table proves unnecessary during implementation, retain equivalent transactional guarantees and document the choice.

### D. Fill deduplication
Extend Execution or add a broker fill table with broker connection ID, broker order ID, broker trade/fill ID, filled quantity, average/individual fill price, exchange timestamp, fees and raw-safe normalized status. Enforce a unique key on broker connection + broker trade ID (or the strongest stable broker execution identity confirmed in docs). If the API does not provide a stable trade ID, do not invent one; use a documented deterministic fallback and flag its limitations before implementation.

All migrations must be additive, reversible where practical, and tested against clean SQLite plus the actual deployment database engine in staging after backup. Do not run production migrations during implementation.

## 4. Idempotency contract

1. The authenticated client creates one random high-entropy idempotency key per intended user action and reuses it for HTTP retries. The server validates size/format and scopes it to user + broker connection; never trust user-supplied ownership identifiers without database ownership checks.
2. Canonicalize and validate the full economic intent before hashing: broker account/connection, instrument, side, product, order type, quantity, price/trigger, validity and all fields that change order behavior. Do not include mutable display-only fields.
3. In one transaction, insert the intent and outbox record with unique constraints. A uniqueness race is expected and handled by re-reading the winning record.
4. Same key + same hash returns existing state. Same key + different hash returns HTTP conflict. No second intent and no broker call.
5. Before the first broker call, atomically claim the intent and persist SUBMITTING plus a submission event. Commit before network I/O.
6. Use a deterministic opaque broker tag/correlation value derived from the durable intent ID only if it fits the documented broker constraints. Never put personal data in tags. Tag is for correlation/retrieval; do not call it broker-enforced idempotency unless Upstox explicitly documents that guarantee.
7. Never retry a submission after timeout, connection reset, ambiguous 5xx, process crash during request, or malformed/uncertain response. Transition to SUBMISSION_UNKNOWN / RECONCILIATION_REQUIRED and query the broker using documented order-history tag, order book, order details and trades endpoints.
8. A definitive broker rejection may be terminal only when response semantics are confirmed and no order was accepted. Rate limits, authentication failures and transport errors need classified handling; they must not all be treated as a safe-to-retry rejection.
9. A new economic attempt after definitive terminal rejection requires an explicit new client intent/key, fresh risk check and auditable linkage to the prior intent. Do not silently reuse a key to mutate order economics.

## 5. Broker reconciliation workflow

Run on startup and periodically during market hours, and on-demand after ambiguous submit/cancel results. Reconciliation is account/connection scoped and rate-limited.

1. Load nonterminal intents and any SUBMITTING/UNKNOWN records before accepting new live orders for that account.
2. Fetch current-day order book and query order history by broker order ID or correlation tag; fetch per-order trades where available. Verify response shape, account scope, instrument, side, order type, requested quantity, price, timestamps and tag before linking a broker order.
3. If exactly one matching broker order is found, persist broker ID and normalized status; apply fills idempotently using unique broker trade IDs; append audit events.
4. If no match is found, absence alone is not proof the order was never accepted (eventual consistency, API failure, day/session limits or missing tags may apply). Repeat bounded reconciliation with backoff; keep state UNKNOWN and block automatic resubmission until an explicitly defined confidence policy or human resolution proves safe.
5. If multiple matches or mismatched economics are found, freeze new submissions for that account/intent, set RECONCILIATION_REQUIRED, alert the operator and require manual resolution. Never guess which order is ours.
6. Normalize broker statuses using a documented mapping, including open/pending, partially filled, complete, rejected, cancelled and trigger-pending variants. Unknown broker statuses are not terminal; preserve raw status and escalate.
7. Treat broker trades/fills as the source of truth for executed quantity/price. Upsert each fill once, recalculate cumulative filled quantity, and verify it never exceeds the accepted order quantity except for explicitly documented sliced-order behavior. Sliced orders must be modelled as child broker orders under one parent intent, each with its own broker ID and unique fill identities.
8. A cancel request is also a stateful external side effect: persist CANCEL_PENDING before calling broker, then reconcile order status/trades. A cancel response does not prove zero fills; a race may produce partial/full fills.
9. Reconcile positions and holdings against local portfolio accounting as a separate account-level control. Do not automatically overwrite local positions from a snapshot without a documented policy for intraday netting, holdings, corporate actions, manual broker orders and imported trades.
10. Broker order book/history may be limited to the trading day; persist local evidence durably and define end-of-day checks using the official trade-history API where supported.

Official Upstox docs reviewed on 2026-10-17:
- Place Order V2 (tag/correlation, response order ID): https://upstox.com/developer/api-documentation/place-order/
- Place Order V3: https://upstox.com/developer/api-documentation/v3/place-order/
- Order History (query by order ID or tag; current-day availability): https://upstox.com/developer/api-documentation/get-order-history/
- Order Book (current-day order states): https://upstox.com/developer/api-documentation/get-order-book/
- Order Details: https://upstox.com/developer/api-documentation/get-order-details/
- Order Trades: https://upstox.com/developer/api-documentation/get-trades-by-order/
These endpoints provide correlation and reconciliation evidence; this design does not assume the broker's tag is an idempotency token.

## 6. State transition invariants

- Every live submit has a committed intent, risk approval snapshot, outbox record and audit event before network I/O.
- Only a single worker can own a fresh submit claim; DB uniqueness and compare-and-swap/version checks protect concurrent requests.
- SUBMITTING is not evidence of broker acceptance. After process loss or uncertain transport, reconcile; do not resubmit.
- Broker acceptance is not a fill. Never mark FILLED based only on a placement response.
- A status regression or stale event must not erase a known fill. Recompute cumulative fills from deduplicated trades and preserve every raw broker event.
- Local terminal states cannot be changed to contradictory terminal states without a reconciliation event and explicit rules.
- No risk check may be bypassed by a retry. Recheck portfolio/account caps immediately before submission under concurrency-safe reservation/locking; pending and unknown submissions reserve worst-case exposure until resolved.
- Account kill switch, per-portfolio controls, broker connection identity and trading mode must be checked server-side for every new intent and again at dispatch. Kill switch blocks new entries; cancellation/reconciliation and explicitly approved risk-reducing exits must remain possible under a documented policy.
- Paper execution stays structurally unable to call live placement; test it at service and API boundaries.

## 7. Recovery and operator UX

Provide a read-only status view for intent ID, local state, broker ID, requested vs filled quantity, last reconciliation time and safe error category. For UNKNOWN/RECONCILIATION_REQUIRED, show "Broker outcome not yet confirmed — do not resubmit" with an operator action to reconcile or record a reasoned manual resolution. Never expose tokens or raw sensitive payloads.

Alerts: repeated reconciliation failure, unknown order past a threshold, broker/local quantity mismatch, duplicate broker matches, account kill switch activation and fill mismatch. Alert payloads contain IDs and safe summaries only.

Manual resolution must require appropriate authorization, reason, timestamp and audit event. It must not delete the intent or silently change an order to rejected/filled.

## 8. Implementation sequence and acceptance gates

### Phase 0 — Design review (current)
- Review this document, current Upstox API contracts, status enums, broker tag constraints and whether order-history is available for all supported order types.
- Confirm supported trading products, NSE/BSE/MCX derivatives, slicing behavior and account-level policy before schema work.

### Phase 1 — Schema and repository (no broker submission)
- Add migration and repositories for intents/events/outbox/fill identity.
- Test uniqueness races, same-key replay, different-payload conflict, transaction rollback and ownership isolation.
- Verify migrations on clean SQLite and staging copy of actual DB engine after backup.

### Phase 2 — Reconciliation-only adapter/service
- Normalize order book/history/trades and add mocked contract fixtures based on official response examples.
- Implement safe import/deduplication and unknown-status handling; do not place orders.
- Test duplicate/out-of-order status events, partial fills, multiple fills, sliced child orders, absent/multiple tag matches, API timeouts and day-boundary retention.

### Phase 3 — Submission orchestration in a hard-disabled sandbox
- Add transactional outbox claim and deterministic broker tag; keep global live-submit feature flag hard-disabled in deployed config.
- Test crash before network, crash after broker accepts but before response persists, timeout, duplicate API requests, worker races, rate limits, token expiry, broker rejection and cancellation races using mocks/sandbox only.
- Prove no automatic retry happens for unknown submission state.

### Phase 4 — Paper/sandbox and operator verification
- Run end-to-end sandbox tests and reconciliation drills. Sandbox success is not live account certification.
- Verify risk reservations, account kill switch, alerts, audit permissions, metrics and backup/restore.

### Phase 5 — Explicit release gate
- User explicitly authorizes a limited live pilot after reviewing limitations.
- Broker account/OAuth and current official API contracts verified; static-IP, authentication, applicable broker/exchange/SEBI requirements and compliance reviewed.
- Staging migration/restore test, monitoring and incident runbook complete.
- Begin with a deliberately limited pilot, explicit manual confirmation, low risk caps and immediate kill switch. No autonomous rollout by default.

## 9. Required regression test matrix

- Same key/same payload concurrently => one intent and at most one initial submit claim.
- Same key/different payload => conflict, zero additional broker calls.
- Crash before POST => recovery can safely determine not dispatched from durable state/lease protocol.
- Timeout after broker acceptance => UNKNOWN; reconcile by tag/order book; no blind retry.
- Duplicate/late HTTP request while SUBMITTING/UNKNOWN => existing state, no second POST.
- Broker response accepted/open => not locally filled.
- Partial fills delivered twice/out of order => each trade recorded once; cumulative quantity correct.
- Cancel races with fill => final state and executions follow broker trades, not cancel response alone.
- Multiple or mismatched tag matches => frozen/manual resolution; never auto-link.
- Broker API unavailable/auth expired/rate limited => safe backoff, no unsafe resubmit.
- Process restart and two concurrent workers => no duplicate submit; unknown intents reconciled.
- Sliced orders => all child IDs/fills tracked and aggregate quantities reconciled.
- Paper API/service requests => never call live place endpoint.
- Kill switch and risk cap changes between intent creation and dispatch => dispatch rechecks and refuses unsafe entry.
- Audit log contains no access token, secret, authorization header or sensitive raw body.

## 10. Explicit non-goals / release blockers

This document does not implement live placement, change the current execution path, enable live trading, run a database migration, connect to a real Upstox account, or submit any order. Do not infer real-broker behavior from mocks or from the presence of adapter methods. Until every gate is met, keep `TRADING_MODE=PAPER` and live submission hard-disabled.


## Implementation checkpoint — Phase 1 — 2026-10-17

The user explicitly approved this design. Phase 1 has added the intent, event, outbox and broker-fill identity SQLAlchemy models, additive migration `202610170002`, and repository safeguards. Canonical SHA-256 is derived by the repository from normalized JSON and authenticated user/portfolio/broker-connection scope. Same key + same payload reuses the intent; same key + different payload conflicts. Intent, initial audit event and outbox row are committed together. Ownership checks and unique constraints are covered by tests.

Latest code/test checkpoint `5508b272efe55997252e8d8a51fdd29761a1070b` passed GitHub Actions [run 39047300286](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39047300286): 214 tests passed, 1 warning. CI verified clean SQLite migration upgrade → downgrade of revision `202610170002` → re-upgrade. Order snapshots and audit details now reject credential-like field names, but callers remain responsible for redacting secret values. The PostgreSQL CI test now forces two independent sessions to miss the same initial idempotency lookup simultaneously and verifies only one intent/outbox/event is persisted. GitHub Actions [run 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046) passed 215 tests and clean SQLite/PostgreSQL 16 migration upgrade → downgrade → re-upgrade. Gate 1 still requires migration/constraint verification against a backup-restored staging copy of the actual deployment database engine. No live order, broker POST, production migration, or reconciliation was performed.


## 11. Implementation checkpoint — Phase 2 normalization foundation

- Added `backend/app/services/live_order_reconciliation.py` as a pure function layer. It makes no broker/network/database calls and has no order-placement/cancellation capability.
- It accepts documented Upstox order book/details/history field names, maps known status strings conservatively, validates required identity/economic fields and quantity/price sanity, preserves raw status, and flags unknown or contradictory status/fill combinations for review.
- Tests: `backend/tests/test_live_order_reconciliation.py`, covering documented statuses, partial fills, inconsistent full fills, unknown states, malformed values and the cancelled-order pending-quantity edge case.
- Official references: [order book](https://upstox.com/developer/api-documentation/get-order-book/), [order details](https://upstox.com/developer/api-documentation/get-order-details/), [order history](https://upstox.com/developer/api-documentation/get-order-history/) and [order-status appendix](https://upstox.com/developer/api-documentation/appendix/order-status/).
- Exact test commit `b37452210bf07ad03acee1495e0627fae1378582` passed [GitHub Actions run 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091): 247 passed, 1 warning; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed.
- This does not fetch broker records, establish ownership/account scope, match an order to an intent, persist status transitions, import trades/fills, or prove a missing broker match is safe to retry. Next is strict intent matching and ambiguity quarantine. No broker order was placed or cancelled.


## 12. Implementation checkpoint — strict intent matching

- Added ReconciliationIntentCandidate, IntentMatchResult and match_broker_order_to_intent() to backend/app/services/live_order_reconciliation.py. This is a pure helper with no network or database access.
- Candidate intents are filtered to the caller-supplied broker connection. A known broker order ID is preferred; otherwise an exact non-empty broker tag must uniquely nominate one intent. A tag is only correlation, not proof of identity.
- Both paths require exact economic checks for instrument, side, order type, quantity and product; LIMIT/SL require matching limit price, and SL/SL-M require matching trigger price. Missing local fields are mismatches. Duplicate tag candidates are ambiguous; mismatches and unknown/contradictory observations are not auto-linked.
- Regression tests cover matching, economic mismatch, duplicate tag ambiguity, missing fields, connection isolation and unknown status handling.
- Exact test commit e9b594ffc2e81c37e1b41c8c44947212d206f3e9 passed [GitHub Actions run 39050424898](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050424898): 255 passed, 1 warning, and SQLite/PostgreSQL 16 migration checks passed.
- Still not implemented: broker reads, persisted state transitions, audit/version guarded updates, trade/fill ingestion, automatic retry/recovery, cancellation, or order submission. Next: build a repository-only safe status-transition operation with concurrency/version tests before any broker I/O.


## 13. Implementation checkpoint — versioned state transition persistence

- Added LiveOrderRepository.apply_reconciliation_transition() as a repository-only operation. It has no broker/network dependency and must only be called after a broker observation has been matched to the intent.
- The method enforces an explicit state-transition allowlist, user ownership, expected version and previous-state compare-and-set, broker-order-ID uniqueness, and atomic persistence of intent state/version/last-reconciled time plus BROKER_STATUS_RECONCILED event. Credential-like keys are rejected from safe details.
- Repeated same-state observations at the current version are no-ops. FILLED cannot regress to OPEN; RECONCILIATION_REQUIRED is frozen; CANCELLED may progress to PARTIALLY_FILLED/FILLED when later broker trade evidence proves a cancel/fill race.
- Tests cover atomic audit/state persistence, same-state idempotency, stale-version rejection, invalid terminal regression, cancel/fill race and credential-field rejection.
- Exact code checkpoint b3332b839b6f2c39bf2ae678e1aa62ac1f2a3409 passed [GitHub Actions run 39050941218](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050941218): 261 passed, 1 warning, with SQLite/PostgreSQL 16 migration checks.
- Two intermediate CI attempts failed due to a malformed test import and an undefined prior-state variable; both were corrected, and the final run passed. No broker API reads, fill ingestion, order submission/cancellation or production migration occurred.
- Next: add a pure validated broker trade/fill normalizer, then a transactionally idempotent fill repository method using the existing unique broker-connection + broker-trade-ID constraint.


## 14. Implementation checkpoint — normalized trade and idempotent fill identity persistence

- Official Upstox per-order trades response documents `trade_id`, `order_id`, `instrument_token`, `transaction_type`, `quantity`, `average_price`, and `exchange_timestamp`; `trade_id` is the stable identity for each execution. See [Get Order Trades](https://upstox.com/developer/api-documentation/get-trades-by-order/).
- Added pure `normalize_upstox_trade()`; malformed identifiers, side, quantity, price or timestamp are rejected. Documented exchange-local timestamps are converted to UTC. This performs no network calls.
- Added repository-only `record_broker_fill()`. It scopes the write to an authenticated user's broker connection and optionally a matched intent in the same connection. It uses the unique `(broker_connection_id, broker_trade_id)` constraint. Identical duplicate deliveries are no-ops; reused IDs with different economic details fail closed. Linked fill + `BROKER_FILL_RECORDED` audit event commit atomically.
- Exact code/test checkpoint `001a6eed2bd7090e2c7a4d3a8f2f87e9d7fa62bc` passed [run 39052203329](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052203329): 274 passed, 1 warning, with SQLite/PostgreSQL 16 migration checks.
- This stores raw individual fill identity only. It does not reconcile the fill's instrument/side/quantity/price against the immutable intent snapshot, aggregate partial fills, update `Order`/`Execution`/`Position`/cash/P&L, fetch broker data, or run a worker. These are the next gates; no live submission is available.


## 15. Fill-to-intent economic checks

`record_broker_fill()` now fails closed unless a linked intent already references the same broker order ID. The observed fill must match the immutable intent's instrument, side, order type and product. Requested quantity must be a positive integer; one fill and the aggregate persisted fills cannot exceed the requested order quantity. For LIMIT/SL orders, BUY fills cannot exceed the limit price and SELL fills cannot be below it. These checks run before the fill is persisted.

Tests include instrument mismatch, missing broker-order linkage, aggregate partial-fill overrun and buy/sell limit-price violations. Exact checkpoint [run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770) passed 279 tests, 1 warning, with SQLite/PostgreSQL 16 migration checks. This is local validation only; no broker read or execution-accounting update is made. Next: quarantine/relink unmatched fills and reconcile out-of-order broker statuses against actual trade records.
