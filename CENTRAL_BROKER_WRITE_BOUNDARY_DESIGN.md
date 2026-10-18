# Central Broker-Write Boundary and Safety-Control Design

**Status:** Proposed engineering contract; design artifact only.  
**Date:** 18 October 2026  
**Scope:** Phase 2 safety architecture for the `tradepro-improved` repository.  
**Non-goals:** This document does not implement API endpoints, authorize live trading, wire the existing routes/workers to a live adapter, or change the original `Tradepro` repository.

## 1. Current verified baseline

The current branch has a persistent account-wide live safety state and event service, PostgreSQL concurrency tests, and a read-only `LivePreflightCoordinator`. Existing manual order placement, cancellation, strategy evaluation and worker matching use the PAPER-only `ExecutionService`; that service rejects non-PAPER mode. The Upstox adapter exposes place/modify/cancel methods, but the current static inventory found no production application caller for those write primitives.

The live intent recovery service currently invokes `LiveExecutionService` directly rather than the coordinator. It persists an intent and can recover by broker tag, but it does not submit broker orders. This is a composition gap that must be closed before any live route or worker is wired.

Current safety state and event writes are committed in one SQLAlchemy transaction by `LiveAccountSafetyService._mutate`. This is a useful baseline, but it does not yet establish database-enforced append-only audit behavior, nor does it make a database transaction atomic with an external broker request. Existing `get_current_user` uses `UUID(payload["sub"])` without normalizing malformed-subject errors. Existing `User.is_admin` is a broad platform-admin flag, not a sufficient least-privilege safety permission system.

## 2. Non-negotiable safety invariants

1. **No direct adapter writes:** application code outside the one approved broker-write boundary must not call `UpstoxAdapter.place_order`, `modify_order`, or `cancel_order`. Only the boundary may hold/use a write-capable adapter reference.
2. **Paper/live separation:** keep `ExecutionService` paper-only. Do not make it a mode-switching live execution service. Paper fills and accounting remain separate from broker submissions.
3. **Default deny:** missing configuration, missing account safety state, stale/failed health, unknown circuit state, tripped kill switch, non-closed circuit, nonzero broker-error count, unavailable database/audit store, invalid permission, or unexpected exception must block new risk-increasing broker writes.
4. **One account-wide scope:** safety is keyed by authenticated owner/tenant and broker, not portfolio. Every route, strategy evaluation, scheduled worker, retry, recovery, modify, cancel and reconciliation path must resolve the same owner/broker safety record.
5. **No actor spoofing:** actor identity is derived from the authenticated principal or a separately authenticated service identity. Never trust an actor ID in request JSON.
6. **No blind retry:** a submission timeout or lost response is an unknown outcome, not proof of failure. Persist a stable broker tag and unknown state, then reconcile by tag/order lookup; do not issue a second submission just because the first response was ambiguous.
7. **Durable intent before network:** persist the intent, unique idempotency key, broker tag, state transition and audit event before a broker POST/PUT/DELETE is attempted. The DB cannot atomically commit with the external broker; use a durable state machine and reconciliation, not a false claim of distributed atomicity.
8. **Safety controls stay dark:** `TRADING_MODE=PAPER` and `LIVE_ORDER_SUBMISSION_ENABLED=false` remain the operating defaults. No live submission is enabled by this design.

## 3. Approved broker-write boundary

Proposed single service: `LiveBrokerWriteService` (name may change only with the same single-boundary rule). It is the sole application-level owner of the write-capable adapter and provides explicit methods:

- `submit(intent, actor/context, idempotency_key)`
- `modify(existing_order, approved_changes, actor/context, idempotency_key)`
- `cancel(existing_order, actor/context, idempotency_key)`

These are conceptual contracts, not implemented APIs.

### Submit and modify sequence

1. Authenticate caller and enforce tenant ownership and operation-specific permission.
2. Validate immutable intent fields, broker connection, instrument, trading mode, independent live flag and explicit confirmation required by policy.
3. Lock/load account-wide safety state and check freshness, kill switch, circuit and error counter. Missing state or any read/check failure denies the operation.
4. Run the approved account-wide risk gate and fresh read-only broker snapshot preflight. Do not use the existing strategy-only risk engine as a substitute for account-wide risk.
5. In one DB transaction, insert/update the durable intent and append the matching event; enforce uniqueness for idempotency key and stable broker tag; commit before network I/O. If audit persistence fails, roll back and make no broker call.
6. Call the broker once using the persisted stable tag. Record accepted/rejected/unknown outcome in a subsequent transaction with a matching event. A timeout/connection loss transitions to `SUBMISSION_UNKNOWN`; do not retry the write until reconciliation resolves the original attempt.
7. On broker error, update the account safety service with a sanitized error code and idempotency key. Any failure to persist the result leaves the intent unresolved and blocks subsequent risk-increasing writes pending reconciliation.

A DB transaction cannot cover the broker network operation. The contract is atomic intent+audit within the DB before the call, followed by durable outcome+audit, with a conservative unknown state between them.

### Cancel sequence and emergency semantics

Cancellation is risk-reducing and must remain possible when the kill switch is tripped, otherwise the safety switch could prevent users from reducing exposure. It is **not** a general bypass: require authentication, tenant ownership, a known broker order ID or stable tag, operation permission, idempotency, durable cancel intent + audit before the network call, and broker-result reconciliation. Cancellation may bypass the *new-risk permission* of the kill switch only; it may not bypass identity, ownership, rate limits, event persistence, broker/account binding or ambiguity handling. Modify requests that increase exposure are blocked while safety is tripped; any future risk-reducing modification needs an explicit, separately tested allowlist and is not approved by this design.

### Adapter encapsulation and enforcement

- Only `LiveBrokerWriteService` imports or receives a write-capable adapter for write operations.
- Read-only quote, funds, positions, order-book, status and trade endpoints remain in read-only/preflight/reconciliation services.
- Do not expose a generic `execute(method_name, payload)` interface. Use typed operation methods and explicit state transitions.
- Static CI guard: scan application Python sources for calls/references to `.place_order(`, `.modify_order(`, and `.cancel_order(` and fail unless the exact approved service implementation and narrowly documented adapter tests are allowlisted. The allowlist must be path-specific, small and reviewed; tests that assert no writes should not be allowed to become production call sites.
- Complement source scanning with tests that instantiate manual, strategy, worker, recovery and reconciliation paths using a spy adapter and prove no adapter write occurs outside the approved boundary. Source scanning is a guardrail, not a proof against dynamic dispatch/reflection; avoid dynamic dispatch for broker writes.

## 4. Safety state and audit transaction contract

### State transitions

- Initialize: create account/broker state in a tripped state; emit an initialization event in the same DB transaction.
- Trip: one-way, safe/idempotent. A trip request is auditable even if already tripped; repeated idempotency key replays the original outcome.
- Health check: persist timestamp, result and sanitized reason; failed health trips the switch in the same transaction.
- Broker error/success: update error counter/circuit state and event together. Success never silently closes an open circuit or clears the kill switch.
- Reset: privileged manual operation only. Require fresh passing health, zero consecutive broker errors, circuit state exactly CLOSED, explicit reason, unique idempotency key, actor, and any required step-up proof. Lock state row; compare expected state version to prevent stale operator actions; transition and event commit atomically.
- Audit failure: roll back the safety mutation; the caller must treat the control action as failed. For an external broker result that cannot be rolled back, retain/reconcile a durable intent and fail closed on further writes until the missing outcome/event is repaired.

### Event schema and immutability

Use a strict allowlisted schema: event ID, UTC creation time, tenant/account ID, broker, actor type and actor ID (nullable only for explicitly defined system events), event type, sanitized reason, outcome, correlation/request ID, safe idempotency reference/hash, prior/new state version, kill-switch state, circuit state, consecutive-error count, and a bounded sanitized broker error code. Never store access tokens, credentials, authorization headers, full broker payloads, raw exceptions, arbitrary client JSON or unredacted secrets.

Application code must expose no event update/delete operations. Add database-level protections where supported (e.g. PostgreSQL trigger/permissions that reject UPDATE/DELETE to event rows), test them in PostgreSQL CI, and document SQLite's weaker guarantee. Restrict migration/DB owner privileges operationally; a trigger alone is not protection against a privileged database owner.

Idempotency collisions must be scoped by tenant/account/broker and operation. A replay with the same key and same canonical request returns the original outcome; the same key with a different payload returns a conflict and creates no second broker write. Persist a request fingerprint, not secrets or full payload, if needed to compare replay equivalence.

## 5. Least-privilege permissions and audit visibility

Existing `is_admin` is not sufficient. Introduce explicit permission checks, ideally via a role/permission mapping rather than scattered booleans:

| Permission | Allowed action | Must not imply |
|---|---|---|
| `safety.status.read` | Read current safety status for explicitly scoped accounts | Audit history, trip, reset, broker writes |
| `safety.audit.read` | Read paginated safety events for authorized accounts | Reset, general platform administration |
| `safety.kill_switch.trip` | Trip a switch for an authorized account; idempotent and audited | Reset or trading enablement |
| `safety.reset` | Request reset after all gates and step-up checks | Bypass health, circuit/error gates, or enable live trading |
| `broker.order.submit` | Request a new risk-increasing order subject to all runtime gates | Modify/cancel permissions or safety reset |
| `broker.order.modify` | Modify an owned order subject to all gates | Submit or reset |
| `broker.order.cancel` | Request cancellation of an owned broker order under the risk-reducing exception | Submit/modify or reset |

Regular account owners may receive explicit permissions to operate only their own account, if that is the product model. Operator/service permissions must be separately granted and tenant-scoped. An administrator flag must not implicitly grant safety reset or broker submission. Background workers use a distinct service identity with a narrow scope, not a fabricated user actor.

### Operator audit API contract (future, not implemented)

- Read endpoints are GET-only and never mutate state; paginated with bounded page size and date/range filters.
- Scope is derived server-side from grants and account ownership; reject cross-tenant IDs even when guessed.
- Separate current-status read from event-history read.
- Trip/reset are explicit POST mutations, never GET; require reason and idempotency key. Reset additionally requires recent step-up authentication and fresh health state.
- Return sanitized event DTOs, never model dumps of credentials or arbitrary metadata.
- Rate-limit sensitive endpoints; normalize malformed JWT subject/claim errors to 401; use generic external errors and structured redacted internal logs.
- For cookie-authenticated mutations, enforce CSRF protection and Origin/Host policy. Bearer-only requests should follow a clearly specified policy rather than weakening cookie protections.
- Step-up authentication must verify a fresh MFA/TOTP challenge server-side; `mfa_enabled=True` alone is not proof of recent MFA. Define an explicit recent-auth window and bind proof to actor, action and target account. Never accept a client boolean as MFA proof.

## 6. Central composition for manual, strategy, worker, recovery and reconciliation

All order-intent producers should call a common orchestration interface that routes by explicit mode without turning the PAPER service into a live service:

- Manual order route: currently paper-only; must call the orchestration boundary, which dispatches to paper execution only while mode is PAPER and otherwise denies until live release is approved.
- Strategy manual evaluation and scheduled worker: same orchestration interface; strategy-specific checks are additional, never replacements for account-wide live gates.
- Intent recovery: must use the same coordinator and stable safety state when validating a new intent. Recovery of an already-submitted/unknown intent is reconciliation-only and must never blindly submit again.
- Modify/cancel: route through the central write boundary; no separate adapter call from routes or workers.
- Reconciliation: read-only broker status/trade methods can reconcile known intents. It may update local broker metadata/state and accounting only under separately reviewed fill rules; it must not submit or modify/cancel broker orders.
- Pending paper limit matcher and all paper fills remain explicitly PAPER-only.
- Broker adapter tests may call low-level methods directly only in isolated adapter tests; production application code may not.

Before wiring, produce a complete call-site inventory using a fresh branch checkout/source scan and verify every route, worker, strategy enter/exit, retry/recovery, cancel/modify and adapter path. New live routes remain blocked until the complete integration and release gates pass.

## 7. Required automated verification

### Unit/service
- Missing state, DB read/write failure, stale health, unknown circuit, tripped switch, open circuit, nonzero errors, bad clock, invalid owner and missing permission all fail closed before adapter writes.
- Submit/modify cannot proceed when any gate fails; a cancellation under a tripped switch is permitted only under the explicit risk-reducing contract.
- Audit insert failure rolls back state/intent and adapter spy sees zero calls.
- Intent and event exist before adapter call; adapter call occurs at most once for one persisted attempt.
- Timeout/lost response becomes unknown; recovery queries by stable tag and never blindly resubmits.
- Same idempotency key/same payload is replay-safe; same key/different payload is rejected.
- Concurrent submit/reset/trip and idempotency races do not create duplicate events or writes.
- Strategy and worker code cannot bypass the orchestration boundary.
- Event DTO redaction and paginated tenant-scoped audit reads are tested.

### HTTP/security
Unauthenticated, malformed JWT subject, inactive user, ordinary user, read-only safety role, trip-only role, reset role without recent MFA, authorized owner, cross-tenant access, missing/invalid reason, missing/replayed idempotency key, payload mismatch, CSRF/invalid Origin, rate limit, audit DB failure, stale health, broker error counter, concurrent reset and safe error responses.

### Database/CI
- SQLite and PostgreSQL Alembic upgrades.
- PostgreSQL integration tests for row locking, unique idempotency, atomic state+event rollback and append-only trigger/permission behavior.
- Source-call guard runs on every backend CI job and fails on unapproved broker-write call sites.
- All unit, API, worker and integration tests pass. Report exact CI run/SHA; local or prior CI results do not verify later code/doc commits unless their SHA is covered.

## 8. Sequenced implementation plan and release gates

1. **Design checkpoint (this document):** agree on boundary, operation semantics, permissions, transaction model, event schema and tests. No endpoints/wiring.
2. **Storage hardening:** add event request fingerprint/correlation metadata as needed, version/CAS semantics, PostgreSQL append-only enforcement and transaction failure tests.
3. **Authorization foundation:** explicit scoped permissions, recent step-up MFA dependency, CSRF/origin and malformed-token handling tests; still no live submission.
4. **Central write boundary:** implement typed submit/modify/cancel service with durable intent state machine and strict adapter encapsulation; keep runtime interlocks disabled.
5. **CI source guard and path tests:** guard direct adapter writes; prove all current callers remain paper-only and recovery is read-only.
6. **Safety-control status/audit/trip/reset API:** implement only after permissions and HTTP security foundation pass; keep reset unable to enable live mode.
7. **End-to-end composition:** wire all approved paths through central orchestration while live flag remains false; test all denial and failure cases.
8. **Release review:** fresh audit, PostgreSQL CI, security review, broker sandbox tests, operational runbook, explicit approval. Live enablement is a separate manual deployment action and is outside Phase 2 design.

## 9. Acceptance checklist

- [ ] Design reviewed and accepted; unresolved choices documented.
- [ ] Only one production service can perform broker order writes.
- [ ] CI fails for every unapproved adapter write call site.
- [ ] Account-wide safety gates are consistently enforced for submit/modify paths; cancellation has a narrowly tested risk-reducing exception.
- [ ] Intent/event transaction semantics and external-call unknown states are implemented and tested.
- [ ] Event history is redacted, tenant-scoped, paginated and append-only at the database layer where supported.
- [ ] Least-privilege permissions, recent MFA step-up and CSRF/origin policy are implemented and tested.
- [ ] Manual, strategy, worker, retry, recovery and reconciliation paths pass negative/bypass tests.
- [ ] PostgreSQL CI and all relevant workflows pass on the exact final code SHA.
- [ ] PR remains draft/unmerged until review; `TRADING_MODE=PAPER`; `LIVE_ORDER_SUBMISSION_ENABLED=false`.
- [ ] Original `Tradepro` repository is untouched.

## 10. Known decisions still requiring explicit review

- Whether account owners themselves receive `broker.order.*` grants or all live orders are operator-approved.
- The exact role/permission persistence model and who can grant/revoke grants.
- Recent-MFA time window and how step-up proof is issued/bound to the reset request.
- PostgreSQL trigger versus dedicated DB-role enforcement (prefer both where deployment permits).
- Broker tag constraints/maximum length and broker-specific idempotency guarantees.
- Safe cancellation when order status is unknown and exact reconciliation terminal states.
- Event retention/archival and operator audit access policy.
- The concrete account-wide risk policy and market/session/price freshness thresholds.

Until those are reviewed and the acceptance checklist is satisfied, no live order-write endpoint may be enabled.
