<!-- Authoritative checkpoint audit: 2026-10-21; supersedes older status notes below. -->
## Current verified checkpoint — 21 October 2026

- The reconciliation crash-recovery/lease-fencing sub-slice is complete; backend CI run 39561621808 passed 470 tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- The broader Gate 2 safety-branch port and workflow-boundary work remains open. Gate 3 accounting integration and Gate 4 live-trading release gates remain blocked.
- The current documentation commit's exact-head CI status must be checked in the live [GitHub Actions page](https://github.com/tarunsharma2610-del/tradepro-improved/actions); older commit results are historical evidence, not proof for a newer HEAD.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled.

- Current `main` HEAD is the latest documentation synchronization commit; the verified code/test checkpoint is `fe07b77b193da1232787384efb38cb589e0d71b6`. Check the live repository HEAD and Actions page for the newest documentation-only commit and its CI result.
- Latest exact-HEAD backend CI: [run 39562094642](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39562094642) passed **470 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- Phase 2 slow-persistence/high-volume lease-expiry audit is **complete**; per-write lease fencing and regression tests are verified.
- Latest frontend CI remains [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474), passing TypeScript and Next.js build; no frontend code changed in this checkpoint.
- Documentation files were synchronized in commit `f369839f20efed60f62abdbc329fe6d4454faeaa`. Historical references to earlier commits and counts below are historical records, not current status.
- Phase 3 is not started. External-repository borrowing remains paused; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled.


- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest repository HEAD before this audit update:** `a297b1a356c133aaca0ed10079eb5226c03b747b` — documentation-only commit `docs: synchronize Phase 2 status with passing CI evidence`.
- **Latest code/test commit:** `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Recorded exact-commit backend CI run [39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. Frontend run [39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
- **Previously verified documentation CI:** commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da`, run [39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828), backend job completed successfully. The later documentation-only commit `a297b1a356c133aaca0ed10079eb5226c03b747b` was found on `main`; CI for that exact HEAD was not independently established before this audit update. Do not infer exact-head CI success from an earlier commit.
- **Phase 2 checkpoint verified in project records:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent lease token/expiry rejection; five-record renewal boundary; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Audit disposition:** checkpoint is suitable to resume from; recovery should not be reopened. The remaining planned Phase 2 engineering audit is **slow database persistence plus high-volume lease-expiry/renewal races**. It has not been started. Establish whether a race exists before changing transaction/fencing logic.
- **Safety constraints remain:** no real broker orders in tests; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled; keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.
- Older checkpoint entries below are retained as history, not current instructions. This top section is the authoritative current state. After this documentation commit, verify CI for its exact HEAD before treating the checkpoint audit as fully closed.

<!-- Latest verified status, updated 2026-10-21 -->
> **Latest verified checkpoint — 21 October 2026**
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; branch: `main`. Original `Tradepro` repository remains protected and untouched.
> - Latest code/test commit: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration checks. Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
> - Documentation audit commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da` passed [CI run 39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828).
> - Phase 2 checkpoint complete through atomic run/lease finalization, stale-run and cancellation recovery, lease-loss fencing, five-record renewal, and incomplete-summary warnings.
> - **Next engineering task (not started yet):** audit a single slow database persistence operation and high-volume lease-expiry races; implement transaction-level fencing only if the race is demonstrated.
> - Deferred safety-branch work remains tracked in `SAFETY_BRANCH_PORT_MATRIX.md`; no wholesale branch merge. Keep live broker submission and automatic accounting promotion disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`.
>
> The CI status above refers to the stated code and documentation commits. This documentation refresh will create a new commit and trigger its own CI run; do not call that new run passed until GitHub reports success.

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


## Follow-up implementation checkpoint — 18 October 2026 (partial; CI pending)

- Added explicit User.safety_permissions grants and require_safety_permission(); platform admin status is not a safety grant.
- Added a controlled 401 for malformed UUID sub claims and a reusable same-origin guard for cookie-authenticated mutation methods.
- Added tests for the above primitives. This does not close the endpoint design gates: recent-MFA step-up, permission provisioning, tenant-scoped audit reads, atomic HTTP state+event handling, route-level CSRF/Origin enforcement, and full negative HTTP tests remain outstanding.
- No safety route was added. Do not expose safety controls until these gates pass CI and receive review.

### Follow-up correction — 18 October 2026

The Origin guard now requires an exact Origin serialization match (including rejecting a trailing slash), and unused imports were removed from the user model. Follow-up commits: f7c08e2605fb7f7828792154570af79cf5ccf724 and 4337d0ce4ef645914f32c56db87c81699c04763e. CI/status lookup has returned no run/status for the authorization changes; do not claim tests or migration passed until a workflow result is tied to the code/test SHA. Recent-MFA step-up and route wiring remain outstanding.

## Superseding checkpoint — recent-MFA step-up foundation (18 October 2026)

- Added a dedicated `POST /api/v1/auth/mfa/step-up` challenge. It requires an authenticated active user, MFA already enabled, fresh password verification and a valid TOTP code; it is rate-limited and applies the configured same-origin guard to cookie-authenticated requests. Successful challenges return a purpose-bound `step_up` JWT with `scope=safety.reset`, `amr=[pwd,totp]`, a verification timestamp, and a five-minute expiry. Failed credentials are audited without logging credentials or the token.
- Added `require_recent_safety_mfa`, which requires the separate `X-Safety-Step-Up` header, validates token type and purpose, verifies recent MFA and issuance timestamps, and binds the token to the authenticated user. It is not yet attached to a safety reset route because no safety-control routes have been exposed.
- Added unit/dependency tests for missing/wrong-scope/stale/user-mismatched step-up tokens and HTTP tests for success, invalid password and accounts without MFA. These tests are committed but **not yet verified by a GitHub Actions run for the latest code/test SHA**; do not claim they pass until exact-head CI is green.
- Latest code/test commit for this checkpoint: `ee8968f9d7d8698703e59911c7091d5f7c870c23`. Related commits: `325d9a854c05bb7dead6f6f626bf749383804a8e`, `9b65f92b060c0745c1e84e535ec5397cdf490b5d`, `1450a3d0dd8c3629e72142fe06cec699be7202f0`, `0bf5f86d9dd07ecaebe10b93149841647dfbccdf`, `1afd892fb1fa7aaf6c1b0028c248b59e06ec9994`, `aaad1d020cb629cb6d554bd08ff02d25fb1c4666`, and `ee8968f9d7d8698703e59911c7091d5f7c870c23`.
- Remaining authorization gates: trusted safety-permission provisioning, tenant-scoped/paginated audit reads, route-level permission + Origin + step-up enforcement, comprehensive negative HTTP tests, and latest-head CI. The helper does not solve these by itself. The safety status/audit/trip/reset routes and central broker-write service remain absent/unwired.
- Keep PR #1 draft/open/unmerged, keep `TRADING_MODE=PAPER` and `LIVE_ORDER_SUBMISSION_ENABLED=false`, never call broker order-write endpoints, and leave the original `Tradepro` repository untouched. Phase 2 remains incomplete.

### Superseding MFA guard correction

The step-up verifier now also denies a token if the authenticated user's MFA has since been disabled; regression coverage was added. Latest code/test commit: `ecf09e800c0dc7fc83d200d603f510348433aa58` (guard change `8a46241e766b9504c3a9bc3ba182043bac98a75d`). Exact-head GitHub Actions/status remains unverified; prior CI results do not cover this change. This remains a foundation only: the dependency is not wired to a safety-reset endpoint because those endpoints do not yet exist.

## Phase 2 checkpoint — tenant-scoped safety audit read (18 October 2026)

- Added `GET /api/v1/admin/safety/audit`, protected by the explicit `safety.audit.read` permission. It accepts bounded pagination (`limit=1..100`, `offset=0..100000`), returns a page envelope and uses a stable `created_at DESC, id DESC` order.
- The SQL query scopes rows to `AuditLog.user_id == authenticated_user.id` and `action LIKE 'safety.%'` before counting or pagination. The caller cannot provide a target user ID; unrelated audit actions and other users' events are not returned. This is an actor-scoped view of safety events, not an administrator-wide or target-account audit browser.
- Added HTTP regression tests for permission denial, pagination bounds, and tenant isolation / filtering. **The tests are committed but have not been executed locally; exact-head GitHub Actions status has not been confirmed.** Do not call the feature CI-verified yet.
- Relevant commits: endpoint `d608f4fdd8a9f10b0647fbe4083d35809b27061f`; response schemas `d46c9268c7c05ca9e207898ca80674df56883a03`; tenant isolation tests `eda5a3589765211105457e2b8950d0c20f00f011`; follow-up import/test cleanup `584b774e175b1aecd74784286bd5fca566e1be6d`.
- Remaining Phase 2 work: run/fix CI on the latest branch head; implement persistent safety status and kill-switch trip/reset routes with the correct permission, Origin and MFA gates; decide and document operator-vs-account audit visibility before expanding audit scope; ensure atomic state/event transactions and concurrency semantics; implement the central broker-write service and enforce it across every execution path. Live trading remains disabled and PR #1 remains draft/open/unmerged.

## Phase 2 checkpoint — authenticated safety control endpoints (18 October 2026)

- Added and registered `backend/app/api/v1/safety.py` with three user-scoped endpoints: `GET /api/v1/safety/status` requires `safety.status.read`; `POST /api/v1/safety/kill-switch/trip` requires `safety.kill_switch.trip`, cookie-Origin validation and an `Idempotency-Key`; `POST /api/v1/safety/kill-switch/reset` requires `safety.reset`, a fresh user-bound password+TOTP step-up token, cookie-Origin validation, an idempotency key, and a required `expected_version`.
- Status reads only the authenticated user's Upstox account safety state. Missing state is reported as blocked/unsafe without initializing or creating a state. Trip initializes missing state in the safe/tripped state before applying the idempotent trip. Reset delegates to the existing transaction-safe service and returns conflict if state/version/health requirements are not met.
- Reset deliberately does **not** accept a client assertion that a health check passed. The existing service requires a recent persisted `HEALTH_CHECK_PASSED` event, zero consecutive broker errors, and matching expected state version. No new public health-check endpoint was added because a caller-supplied “passed” flag would be unsafe without real broker/session/account snapshot validation.
- Added HTTP regression tests for permission denial, safe missing-state response, trip behavior, required idempotency key, reset MFA denial, reset blocked without a fresh successful health check, and cookie-Origin rejection. **These tests have not been executed in this environment.** GitHub Actions lookup exposed no PR-triggered run for the latest test commit and combined status was empty; the connector's workflow-run lookup filters to PR-triggered runs, so this is not proof that no push-triggered run exists. Exact-head test status remains unverified.
- Relevant commits: safety route/import cleanup `267da864b5187cfad91ac68b76ba86cf06b7848f`; schema `01f0deb4949cd13072fb2feda9924e0a97eaf5cf`; router registration `fc95e748197be9e8848c990f55079fbd8afc4a30`; endpoint tests `3ae21dac71edb449835124f99794f510c8b80761`.
- Review caveat: the existing `GET /api/v1/admin/safety/audit` still reads legacy `AuditLog` rows with `safety.*` action names; the durable state-transition history is in `LiveAccountSafetyEvent`. Before treating operator audit visibility as complete, update that endpoint to read the immutable event table and scope by the associated state owner and authorized actor.
- Remaining gates: run and fix CI on the current branch head; fix the safety audit endpoint's event source; perform security review of the grant/reset token purpose boundaries; add negative HTTP tests for every route and error path; verify atomic state/event concurrency at endpoint level; implement the central broker-write service and enforce it across API, strategy worker, recovery and adapter paths. Keep `TRADING_MODE=PAPER`, `LIVE_ORDER_SUBMISSION_ENABLED=false`, PR #1 draft/open/unmerged, and original `Tradepro` untouched. Phase 2 is incomplete.


## Superseding Phase 2 checkpoint — immutable safety audit source (18 October 2026)

- Updated `GET /api/v1/admin/safety/audit` to read `LiveAccountSafetyEvent` joined to `LiveAccountSafetyState`, rather than the legacy `AuditLog` table. Tenant scoping is performed in SQL using the authenticated user's state ownership before counting and pagination; callers cannot select another user/state. Output omits idempotency keys and request fingerprints and exposes only the safety event fields needed for audit review.
- Reworked the tenant-isolation/pagination HTTP test to seed durable safety events for two different account owners and a non-safety legacy audit row. It checks that only the authenticated tenant's immutable safety events are returned and sensitive replay metadata is not serialized.
- Commits: endpoint `cd68384c48a98f2bd2ded054f37bb04d24885b12`; regression test `7913f821a7ac194c537adf911a4ef39ba4410e41`.
- Verification status: exact-head CI/status lookup returned no runs/statuses for the latest test commit. Tests have **not** been run in this environment; treat this change as committed but unverified until GitHub Actions runs against the current branch head. No live broker write was called.
- Next: verify/fix current-head CI; then review reset/idempotency and endpoint transaction behavior, followed by central broker-write boundary implementation and enforcement across API, strategy workers, recovery/retry and adapter paths. Phase 2 remains incomplete. Keep PAPER mode, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Phase 2 checkpoint — MFA purpose separation (18 October 2026)

- Changed the MFA step-up request to accept only two explicit purposes: `safety.reset` (default for backward compatibility) and `safety.admin.permissions`. Permission-management purpose issuance is denied unless the authenticated user is a platform admin.
- Changed the recent-MFA dependency into a purpose-specific dependency factory. A token for `safety.reset` no longer satisfies the permission-grant/revoke route, which now requires `safety.admin.permissions`; unknown scopes fail at dependency construction. The issued purpose is included in the MFA step-up audit metadata.
- Added/updated HTTP and dependency regression tests for admin purpose usage, non-admin denial, and cross-purpose token rejection.
- Commits: schema `4c09723127b545fe111adc6bf6ff70cd509fa13d`; dependency `36e23c178b7fadcee0f5b9d0304363d6093cf9f3`; auth issuance `61dfcc54abe66825a2f3eccfc728920a3faef7c8`; admin route `af9b1d32b3d91d313a0cd9451f2b60f4a60d2df1`; tests `c9e35bc102c14683c4c1a8216abd9f6cd19908e` and `9d5eee236f252a5b8ef6c263553ac89100a52c44`.
- Verification remains pending: tests were not run locally; query available for exact-head workflow/status returned no records on the previous checkpoint and must be repeated for this latest head. Do not treat this change as passing until CI executes.
- Next: run CI and address failures, review the full safety MFA dependency/route matrix, then proceed to the central broker-write boundary. PAPER mode and disabled live order submission remain mandatory; Phase 2 is incomplete.


## Authorization/MFA route-matrix verification checkpoint — 18 October 2026

- During matrix review, identified a compatibility defect in the first scoped-MFA dependency refactor: existing direct unit tests and callers invoke `require_recent_safety_mfa(step_up_token=..., user=...)`, so turning that function itself into a factory would break those calls. Corrected by restoring `require_recent_safety_mfa` as the default `safety.reset` validator and adding `require_recent_safety_mfa_scope(scope)` for FastAPI route dependencies. Reset and admin permission routes now explicitly use their corresponding scope-specific dependency.
- Added route-level regression coverage proving a `safety.reset` token cannot grant safety permissions; existing coverage includes non-admin privilege denial, direct cross-purpose rejection, stale tokens, disabled MFA, wrong user/scope, Origin checks, default-deny permissions, tenant isolation, idempotency-header validation, and safe reset requiring fresh health evidence.
- Relevant commits: dependency compatibility fix `24b463894eca1fde37381bef66d47366a806fe32`; route wiring `0cfc3e290dbc730af9fb854954a95875809ad3cf` and `17088f172d40aa106d1cd1d5f8b674c056919a86`; test matrix update `6e77aa77a7c0bba84d2aae539b37fa6228c088b9`; route-level cross-purpose test `c40edddbeb8b65ec468ae0419897d1cd6cc2c325`.
- CI: GitHub Actions backend workflow is running for the preceding dependency/test commit (`39132630566`) and queued for latest route-level test commit (`39132698515`). The preceding run has not yet reached pytest; do not mark the matrix passed until latest-head workflow concludes. Monitor [latest workflow run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39132698515).
- Still outstanding: wait for latest-head CI; fix any failures and re-run; verify SQLite/PostgreSQL migrations and concurrency checks. This is a route-matrix review, not a complete authorization/security certification. PAPER mode remains mandatory, live broker order submission remains disabled, PR #1 remains draft/open/unmerged, and Phase 2 is incomplete.


## CI failure triage update — 18 October 2026

- GitHub Actions run `39132630566` failed at `Run test suite`: `433 passed, 5 skipped, 1 failed`. The single failure was `test_non_admin_cannot_request_permission_management_step_up`, which returned 401 rather than the expected 403 because its test fixture enabled MFA but did not mock TOTP verification. The authorization code was not reached by that test.
- Fixed the test fixture to mock a valid `123456` TOTP code, isolating the authorization behavior under test. Fix commit: `b5c96fc5115bd4b9fae7be6fc0a168d55c5ace9c`.
- A new backend CI run is in progress for the fix: [run 39132803282](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39132803282). Do not consider the suite green until this exact-head run finishes successfully. Previous failures skipped migrations/concurrency stages because pytest failed first.


## CI verification result — PASS (18 October 2026)

- Backend workflow run `39132803282` passed for backend commit `b5c96fc5115bd4b9fae7be6fc0a168d55c5ace9c`: broker-write boundary guard passed; full backend suite **435 passed, 5 skipped, 1 warning**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL account-safety/charge-adjustment concurrency tests **5 passed**. One Starlette/AnyIO deprecation warning remains non-blocking.
- The earlier failing test was corrected by mocking valid TOTP in the non-admin purpose-denial test; the passing run confirms the corrected test setup and current backend changes. Documentation-only commits followed, so the tested application code is unchanged, but the docs commit itself did not trigger backend CI due workflow path filters.
- This is evidence for the current authorization/MFA test changes and listed CI gates, not a complete security certification or Phase 2 completion. Continue with broader authorization route matrix and broker-write boundary implementation; live order submission remains disabled and PAPER mode remains mandatory.


## MFA HTTP route-matrix follow-up — 18 October 2026

- Added two missing HTTP-level cases to `backend/tests/test_api_authorization.py`: cookie-authenticated `POST /api/v1/auth/mfa/step-up` without an Origin header must return 403; unsupported step-up purpose `safety.live_trade` must be rejected by request validation with 422. These complement existing tests for missing/disabled MFA, wrong password, non-admin privileged-purpose denial, reset-vs-admin token scope separation, stale/user-bound tokens, cross-origin mutations, permission denial, and reset health prerequisites.
- Test commit: `58778259324119379c69b03c822c13849b223d22`. GitHub Actions run [#39133596645](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39133596645) is running; broker-write boundary guard has passed and pytest is in progress at time of this note. Do not claim the new tests pass until the run completes and its pytest/migration/PostgreSQL steps conclude successfully.
- Review outcome so far: reset and permission-management routes explicitly use distinct MFA scopes; platform-admin status alone does not grant safety permissions; user audit is tenant-scoped to immutable safety events. The matrix is broader but not exhaustive, and no independent security certification is implied.
- Next after CI: fix only demonstrated failures; if green, proceed to the central broker-write authorization/gating design and enumerate every order-write path before wiring anything. Keep PAPER mode, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## MFA HTTP route-matrix CI result — PASS (18 October 2026)

- GitHub Actions [run #39133596645](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39133596645) passed for test commit `58778259324119379c69b03c822c13849b223d22`: broker-write boundary guard passed; backend suite **437 passed, 5 skipped, 1 warning in 28.01s**; SQLite Alembic migration passed; PostgreSQL 16 Alembic migration passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**.
- This run verifies the added missing-Origin and unsupported-purpose HTTP tests plus the existing MFA/authorization matrix at that tested code SHA. Later documentation-only commits did not alter application code. One non-blocking Starlette/AnyIO deprecation warning remains.
- This does not certify every auth route or complete Phase 2. Next task: map all broker order-write entry points and design a single fail-closed broker-write authorization gate, then test that all paths are blocked in PAPER mode and remain disabled absent explicit future approval. Do not wire real order submission in this task. Keep PR #1 open/unmerged and original `Tradepro` untouched.


## Central broker-write boundary — deny-all foundation (18 October 2026)

- Added `backend/app/services/live_broker_write_service.py` as the single planned choke point for place/modify/cancel operations. This is intentionally a deny-all foundation: every write method raises `LiveExecutionBlocked` with an explicit no-request-sent message. It does not import or call a broker adapter, and it is not registered with routes, strategy workers, recovery, or any execution path.
- Added `backend/tests/test_live_broker_write_service.py` covering all three write verbs and asserting each fails closed. Commits: service `3726484932e4d46d9f92a7ff41cb5b761cfb1720`; tests `f4442607b8b71df7fffbf4354ea11a532efb99d6`.
- Verification pending at this note: the backend workflow for test commit `f4442607b8b71df7fffbf4354ea11a532efb99d6` has passed the broker-write source guard and is in pytest. See [run #39134040222](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134040222). Do not claim tests/migrations passed until the run concludes.
- This does **not** complete the broker-write service. Next design must enumerate the persisted-intent lifecycle, ownership, user confirmation, account safety state, fresh pre-trade risk, token/connection stability, and timeout/recovery behavior before any adapter call can be implemented. Do not wire it or enable live orders. PAPER mode, disabled live submission, PR #1 draft/open/unmerged, and original `Tradepro` untouched remain mandatory.


## Central broker-write deny-all CI result — PASS (18 October 2026)

- GitHub Actions [run #39134040222](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134040222) passed for test commit `f4442607b8b71df7fffbf4354ea11a532efb99d6`: broker-write source guard passed; full backend suite **440 passed, 5 skipped, 1 warning in 32.49s**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**. A separate workflow for the service-only commit also passed.
- The deny-all broker-write service remains deliberately unwired and makes no adapter calls. This step proves the central choke-point stub refuses place/modify/cancel; it does not verify live submission (which remains disabled) and is not a complete broker-write implementation.
- Documentation-only checkpoint commits followed. Next: inspect every existing order-writing entry point and add a call-graph/inventory, then design the central gate around ownership, persisted intent/idempotency, account-level safety latch, live pre-trade risk, explicit confirmation, and ambiguous timeout recovery. Keep PAPER mode, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Broker-write path inventory and guard hardening — 18 October 2026

- Added `BROKER_WRITE_PATH_INVENTORY.md` documenting current adapter definitions, PAPER execution routes, read-only live preflight/recovery/reconciliation, and controls required before any live write is implemented. Commit `68f528edf4fe2dcb958161943b878b5863bbcd74`.
- Strengthened `backend/scripts/check_broker_write_boundary.py` to reject broker-write method references regardless of receiver name, rather than relying on adapter-like variable names. It now permits only the known PAPER `self.execution.place_order` calls in `strategy_execution_service.py` and the existing `ExecutionService(...).place_order/cancel_order` endpoints in `api/v1/portfolios.py`. The first strict run correctly exposed those two existing PAPER API call sites as exceptions that needed explicit, narrowly-scoped allowlisting; no live adapter write path was identified in those failures.
- Added guard tests for generic receiver bypass, central-service adapter-call rejection, and the approved PAPER call sites. Test updates are committed through `e9c31a043465e3d09223894ddfe45629cfc0302e`.
- CI for the latest guard/test fix is in progress: [run #39134878791](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134878791). Do not treat this guard hardening as verified until the exact-head workflow passes. The preceding strict-guard failures were expected detection/allowlist gaps and prevented pytest/migration stages from running.
- Live broker writes remain unimplemented and denied by the central service. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Latest verified Phase 2 checkpoint — 18 October 2026

- Latest verified GitHub Actions run: [#39136563051](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39136563051), code/test SHA `c40689ac227ab56ca58993072112d6fd575aff46`.
- Result: broker-write source guard passed; backend **449 passed, 5 skipped, 1 warning**; SQLite and PostgreSQL 16 migration upgrades passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**.
- Central `LiveBrokerWriteService.prepare_order_intent` composes safety-aware read-only preflight with durable idempotent intent persistence. The persistence path rechecks owner/intent fields, active instrument and instrument key, and current broker-connection identity.
- Scope limitation: this is preflight and local intent persistence only. `place_order`, `modify_order`, and `cancel_order` remain deny-all; no real broker order-write request is enabled. Keep PAPER mode mandatory and live submission disabled.
- Next: test concurrent intent creation and state transitions, including submission-unknown recovery. Any future submitter must recheck account safety/interlocks immediately before network I/O and must not blindly retry ambiguous outcomes. PR #1 stays draft/open/unmerged; original `Tradepro` remains untouched.

## Concurrent order-intent and submission-state checkpoint — VERIFIED (18 October 2026)

- Changed `LiveOrderRecoveryService.mark_submission_unknown` to use a SQL compare-and-set update restricted to tagged LIVE intents in `PENDING_SUBMISSION` or `SUBMISSION_UNKNOWN`. It reloads after commit and refuses to overwrite a concurrently written terminal/reconciled state. Repeated transition to `SUBMISSION_UNKNOWN` is idempotent.
- Added unit coverage for repeated `SUBMISSION_UNKNOWN` and refusal to transition a terminal `FILLED` order back into recovery.
- Added PostgreSQL independent-session concurrency tests for two simultaneous identical intent-persistence requests (exactly one durable Order row and shared ID) and two simultaneous `SUBMISSION_UNKNOWN` transitions (both return the same safe state). Updated `.github/workflows/backend-tests.yml` to actually execute `test_live_order_recovery_postgres.py`; this integration coverage was not included by the prior workflow.
- Verified GitHub Actions [run #39137705194](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39137705194), SHA `3626e0cdb8a5b7b3fe012fd00b07d2b7bc3bbe26`: broker-write source guard passed; backend **450 passed, 7 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **7 passed** (including the two new order-recovery concurrency cases).
- Recovery lifecycle review: timeout, lookup failure, invalid response, no match, and identity mismatch remain review-required outcomes; the service never blindly retries a broker POST. Recovered broker IDs are identity mapping only and do not imply fill/accounting confirmation.
- Remaining: production-grade submit/modify/cancel remains intentionally unimplemented and denied. Before any future broker POST, implement a separately reviewed submission state machine that commits a unique submission claim, rechecks account safety and independent interlocks immediately before I/O, handles crash/timeout ambiguity via read-only recovery, and requires broker-confirmed state reconciliation. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Submission-claim state separation — VERIFIED (18 October 2026)

- Added `SUBMISSION_CLAIMED` as a distinct, durable state before any future broker network I/O. `claim_submission_attempt` uses a SQL compare-and-set from `PENDING_SUBMISSION`; only one concurrent worker can win. This is a local database operation only and contains no broker write call.
- Read-only tag recovery now accepts `SUBMISSION_CLAIMED` as well as pending/unknown states, because a process crash after committing a claim cannot prove whether a request was sent. The recovery rule remains conservative: no-match, lookup error, malformed response or identity mismatch never authorizes an automatic resubmit.
- Added unit tests for one-time claim semantics and a PostgreSQL independent-session concurrency test requiring exactly one winner. Existing concurrent duplicate-intent and `SUBMISSION_UNKNOWN` transition tests remain enabled in the PostgreSQL CI step.
- Verified GitHub Actions [run #39138626298](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39138626298), SHA `b18841ff591eb943c25d3f85894d824923f2f371`: broker-write source guard passed; backend **451 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Safety boundary: this is state-machine groundwork only. No adapter place/modify/cancel call was added, no live submission route or worker was enabled, and no real order was sent. Before any future submitter is considered, require a dedicated reviewed protocol that rechecks the account safety latch and independent interlocks immediately before I/O, handles claim-crash ambiguity via read-only recovery, and only accepts broker-confirmed reconciliation. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Broker-account binding for recovery — VERIFIED (18 October 2026)

- Added nullable `orders.broker_connection_id` with FK/index and Alembic revision `202610180013`. New live intents persist the exact broker connection ID validated by preflight. Legacy rows are intentionally not backfilled because the currently connected account cannot prove which account was used originally.
- Read-only recovery now fails closed before calling order history if the original connection is missing, disconnected, or differs from the currently verified connection. Existing child mappings are reused only when connection ID, broker name, and stable tag match the persisted intent.
- Added regression tests proving a disconnected/original-connection mismatch and a legacy unbound intent produce `UNKNOWN_REQUIRES_REVIEW`, make no order-history call, create no child mapping, and never invoke a broker write. Migration runs are verified on SQLite and PostgreSQL 16.
- Verified GitHub Actions [run #39139728102](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39139728102), SHA `9cb7ab055a0cd55028f0001aa90d647f1518b667`: broker-write source guard passed; backend **453 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Remaining: this is still recovery identity binding, not broker submission. No place/modify/cancel network write is enabled. Any future submitter must perform a fresh account safety/interlock check immediately before I/O, commit and honor the single-winner claim, and route crashes/timeouts into read-only reconciliation. Keep PAPER mode mandatory, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Fresh pre-submission interlock revalidation — VERIFIED (18 October 2026)

- Added `LiveOrderRecoveryService.validate_claimed_submission(user_id, order_id)` as a validation-only primitive for any future separately reviewed submitter. It requires `TRADING_MODE=LIVE`, `LIVE_ORDER_SUBMISSION_ENABLED=true`, a user-owned tagged LIVE intent in `SUBMISSION_CLAIMED`, the original still-connected broker connection, automated-entry enablement for strategy orders, and a positive `LiveAccountSafetyService.check_allowed` result.
- The method does not call a broker adapter and no current write method invokes it. It explicitly documents that a future submitter must still solve the race between this check and network I/O; this check alone is not a safe live-submit implementation.
- Added regression tests for disabled runtime submission flag, missing account-wide safety state, and disconnected original broker connection. The first CI attempt exposed a test-fixture reference error; that fixture was corrected and the latest run is green.
- Verified GitHub Actions [run #39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552), SHA `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b`: broker-write source guard passed; backend **456 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Remaining: no actual broker order write is enabled. A future submitter must implement a race-safe final interlock protocol (e.g. coordinated safety-state lock/version and claim semantics), without holding unsafe database locks across network I/O, and must handle post-request crashes through read-only reconciliation. Keep PAPER mode mandatory, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Main-branch continuation note — 2026-10-21

The current main-branch checkpoint is summarized at the top of this file. Historical branch-specific findings and commit references below remain useful context, but the safety branch was not merged wholesale. For the latest Phase 2 status, follow `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, and `AUDIT_REPORT.md`.


## Main-branch continuation note — 2026-10-21

The latest verified main-branch Phase 2 checkpoint is summarized at the top of this file. Historical branch-specific findings remain useful context, but the safety branch was not merged wholesale. See `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, and `AUDIT_REPORT.md` for current lifecycle changes.


## Main-branch continuation note — 2026-10-21

The latest verified main-branch Phase 2 checkpoint is summarized at the top of this file. Historical branch-specific findings remain useful context, but the safety branch was not merged wholesale. See `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, and `AUDIT_REPORT.md` for current lifecycle changes.


## Main-branch continuation note — 2026-10-21

The latest verified main-branch Phase 2 checkpoint is summarized at the top of this file. Historical branch-specific findings remain useful context, but the safety branch was not merged wholesale. See `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, and `AUDIT_REPORT.md` for current lifecycle changes.
