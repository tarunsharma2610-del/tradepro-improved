# Safety-Control Endpoint Security Audit

**Review date:** 18 October 2026  
**Scope:** Static review of the current feature branch before designing any API for live account safety controls.  
**Branch:** `safety/fail-closed-trading-mode`  
**Disposition:** Design gate only. No safety-control API endpoint was created or wired by this review.

## Executive result

Authentication and basic tenant/admin authorization primitives exist, and HTTP-level tests cover unauthenticated denial, regular-user denial of admin-only platform settings, and successful admin access. The audit trail is written by a helper and stored in an `audit_logs` table. However, the current implementation is **not yet sufficient to expose or operate live safety controls**: there is no audit-log read endpoint, no operator-visible safety-event view, and no safety-control route with action-specific authorization. Existing role checks are a single `is_admin` boolean, not a dedicated trading-safety operator permission model. MFA exists, but the reviewed routes do not require recent re-authentication or MFA for privileged state-changing actions.

This is a source-code review, not a penetration test or production deployment audit. No endpoint, reset operation, broker order, or live order write was exercised.

## Reviewed implementation

- `backend/app/core/deps.py`: `get_current_user` accepts an access cookie or Bearer token, validates token type, loads the user and rejects missing/inactive accounts. `require_admin` returns 403 for non-admin users.
- `backend/app/core/security.py`: JWT access/refresh tokens have expiry and type claims; password hashing uses Argon2id.
- `backend/app/api/v1/auth.py` and `backend/app/services/auth_service.py`: registration/login, refresh, logout, MFA enrollment/verification/disable; login is rate-limited and failed logins are audit logged.
- `backend/app/tests/test_api_authorization.py` (actual path: `backend/tests/test_api_authorization.py`): route-level tests cover unauthenticated denial, user access to own profile, regular-user 403 on platform settings, and admin access.
- `backend/app/middleware/audit.py` and `backend/app/models/audit_log.py`: helper writes an `AuditLog` row with actor, action, resource, request IP and optional JSON metadata; the model describes app-level append-only intent.
- `backend/app/api/v1/admin.py`: admin API is intentionally aggregate-only and does not browse another user's trading data.
- `backend/app/api/v1/settings.py`: platform integration settings are admin-only; user broker settings use authenticated user identity. Several credential/settings changes write audit events.
- `backend/app/api/v1/router.py`: no safety-control or audit-log router is registered.
- `backend/app/services/live_account_safety_service.py`: persistent safety transitions record their own account-safety events; service is intentionally not registered with order submission.
- `backend/app/services/live_preflight_coordinator.py`: read-only preflight composition only; it does not submit or mutate broker orders.
- `backend/app/api/v1/portfolios.py`, `backend/app/api/v1/strategies.py`, and `backend/app/worker.py`: manual paper-order route and strategy execution paths are present. These are not proof of a live-order path, and the live preflight remains unregistered.

## Findings

### Positive controls observed

1. **Authentication required by default for user-specific APIs:** `get_current_user` validates an access token and checks that the account remains active.
2. **Admin-only platform settings guard:** `require_admin` enforces a server-side 403, with a route-level regression test.
3. **Tenant scoping is used in the reviewed trading routes:** portfolio and strategy handlers check ownership before reading child resources; order placement uses the authenticated user's ID.
4. **Credential output is masked in tested platform settings:** an authorization test asserts a bot token is not echoed in full.
5. **MFA capability exists:** TOTP can be enrolled and verified; login enforces MFA when enabled.
6. **Audit event persistence exists:** login/MFA and selected credential/settings actions use `write_audit_log`; the live account safety service maintains a separate event history for safety transitions.
7. **Safety service defaults closed:** missing/stale/unknown safety state or a failed safety check does not authorize a live preflight.

### Gaps and risks to resolve before an endpoint is designed

1. **No operator audit visibility.** No registered route exposes a filtered, paginated audit history or safety-event history. Admin stats intentionally expose aggregate counts only. Operators currently cannot inspect a coherent history of safety trips, health checks, broker errors, manual resets and denied actions through the API.
2. **No dedicated safety-operator permission.** `is_admin` is a broad boolean used for platform settings. It does not distinguish read-only audit viewers from people permitted to trip a kill switch or perform a reset. A future endpoint must not assume every admin is automatically allowed to reset live safety state.
3. **No step-up authentication for privileged actions.** The reviewed dependencies validate an ordinary access token; no reviewed pattern requires recent password/MFA confirmation for a safety reset. MFA is optional at account level and disable-MFA does not require a fresh password or MFA challenge in the route.
4. **Audit helper has transaction coupling that needs an explicit policy.** `write_audit_log` commits the supplied SQLAlchemy session. A safety endpoint must decide how the state transition and audit event are made atomic. A successful state change must never be reported if its required audit event failed to persist. Avoid a second independent commit that could leave a state change without the corresponding audit record.
5. **Audit immutability is an application convention, not a demonstrated database guarantee.** The model is described as append-only, but this review did not find a database-level immutability control or separate write-only/read-only database roles. Treat this as a required control for production, not a verified guarantee.
6. **Audit payload policy needs tightening.** Metadata is arbitrary JSON. New safety events must use a strict allowlist and must never include access/refresh tokens, broker credentials, MFA secrets, full request bodies or other secrets. Avoid unnecessary PII. Define retention and redaction rules.
7. **Actor attribution must be mandatory for operator actions.** The safety service supports nullable actor IDs for system-originated events. An API-triggered trip/reset must always record the authenticated actor ID, action, target account/broker, reason, idempotency/correlation identifier, timestamp, and outcome. System events should use a distinct explicit actor type, not masquerade as a human operator.
8. **Audit reads need independent authorization and tenant controls.** A normal user must not query arbitrary users' safety events by changing a URL/query ID. Define separate scopes for self-service account status, operator audit read, and privileged state changes; filter at the database query, not only in the UI.
9. **Cookie-authenticated state changes need CSRF review.** Access tokens are accepted from cookies and browser requests use credentialed CORS. Existing cookie SameSite is `lax`, but no dedicated CSRF token check is visible in the reviewed route/dependency path. A future state-changing safety endpoint needs an explicit CSRF/origin policy as well as authentication.
10. **Token subject parsing hardening.** `get_current_user` converts the token `sub` claim to UUID after decoding. The reviewed code does not locally translate malformed UUID subjects into a controlled 401. Add a negative test and normalize malformed subjects to an authentication failure before exposing a new privileged route.
11. **Negative tests are incomplete for future safety controls.** Existing route tests are useful but do not establish role separation, cross-account audit denial, invalid/missing reason denial, stale/expired access token denial at every privileged route, MFA/step-up policy, audit-write failure behavior, replay/idempotency, rate limits, or concurrent reset behavior through an HTTP endpoint.
12. **Operator actions require reason and replay controls.** The underlying safety service has idempotency-key support and requires actor/reason for manual reset, but a future API contract must validate these at the HTTP boundary and must not allow client-supplied actor IDs to override the authenticated principal.

## Required endpoint design gates (not implementation)

Before creating any safety-control API, document and approve:

- Separate permissions: `safety.audit.read`, `safety.status.read`, `safety.kill_switch.trip`, and `safety.reset`; default deny. Assign least privilege and do not map every permission blindly to `is_admin`.
- Mandatory authenticated actor derived from `get_current_user`; never accept actor identity from request body.
- Reset requires step-up authentication (fresh MFA where enrolled and an explicitly defined policy for accounts without MFA), a non-empty bounded reason, fresh passing health state, zero broker-error counter, closed/resettable circuit conditions, and a unique idempotency key.
- Trip action must be available as a safer one-way action and must be auditable even when the requested transition is already applied; define idempotent response semantics.
- Atomic persistence of state transition plus safety event, with rollback on audit failure; test failure injection.
- Append-only event policy with strict event schema, redaction allowlist, UTC timestamp, actor type/ID, target user/account/broker, reason, outcome, correlation/request ID, idempotency key hash or safe reference, and state version. Never store secrets.
- Read endpoints must be paginated, bounded, filtered by server-enforced scope, and protected against cross-tenant IDOR. Audit readers should not automatically gain reset rights.
- CSRF/origin protection for cookie-authenticated mutations, rate limits, generic error responses, no secrets in logs, and no GET endpoints that mutate state.
- HTTP-level tests for unauthenticated, regular-user, read-only operator, privileged operator, cross-account access, missing/invalid reason, idempotency/replay, audit database failure, CSRF, stale health, error-counter/circuit gates, and concurrent reset.
- Do not enable live order submission until every order entry point is audited and the approved safety control and audit policies are integrated end-to-end.

## Next action

Complete a dedicated authentication/authorization and operator-audit design review against the findings above. Then review every manual route, strategy-triggered route, worker, retry/recovery and broker write method before choosing endpoint shape. Keep the PR draft, keep live order submission disabled, and do not modify the original `Tradepro` repository.
