## PostgreSQL CI execution confirmation — 24 October 2026

- Inspected `.github/workflows/backend-tests.yml` and successful Backend pytest run [39921411680](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39921411680) on commit `db1053d7f7c53e1c57016f153f11c9897fa59682`. The workflow provisions PostgreSQL 16, sets `TEST_POSTGRES_URL` for `python -m pytest -q`, and the Backend pytest job completed successfully. Thus the `skipif(not TEST_POSTGRES_URL)` PostgreSQL-only tests were enabled for that run (job logs/test output should be consulted if exact per-test counts are needed).
- The workflow also passed Alembic upgrade/downgrade/re-upgrade checks on SQLite and PostgreSQL 16, the broker-write-boundary guard, and an isolated synthetic database/document-volume restore drill.
- The restore drill uses synthetic data created inside CI. It does not substitute for restoring the user's actual retained Oracle Cloud backup or validating an authentic account-specific Upstox contract note.
- The existing source-verification/promotion race test covers allocation-ledger functions, but the integrated concurrency scenario that races real `LiveFillAccountingService.promote_trade` against ledger verification/promotion remains open. Do not mark Phase 3 accounting sign-off complete until that integration gap is addressed or explicitly accepted with evidence.
- PR #6 remains draft/unmerged; live broker order submission remains disabled. All changes are confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.

---

## Phase 3 concurrency integration status — 24 October 2026

- Current branch head before this documentation update: `2cacf392e5104a8b16307395847239bba945c87b`; branch-head backend CI run [39920815737](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39920815737) passed. PR #6 is draft and unmerged.
- The PostgreSQL-only allocation concurrency suite already contains `test_concurrent_source_verification_and_promotion_serialize_on_evidence`. It concurrently runs the real `verify_component_allocation_ledger` and `promote_verified_component_allocations` functions against synthetic persisted evidence and asserts that both allocations finish reconciled under one reconciliation reference.
- This is a useful source-ledger race test, but it is not the same as a concurrent call to `LiveFillAccountingService.promote_trade` using the real `_load_reconciled_allocation_fees` path while ledger verification/promotion races. That end-to-end live-fill integration scenario remains unproven and is still an acceptance gate.
- The other PostgreSQL allocation test races competing fill sets for a source component and expects exactly one fill set to own that component. Tests are skipped locally without `TEST_POSTGRES_URL`; CI must be checked to confirm the PostgreSQL service actually ran these tests rather than only passing via skips.
- Next engineering task: add or extend a disposable-PostgreSQL integration test using reviewed synthetic evidence, real reconciled allocations, and the actual live-fill accounting service. Assert no partial execution/position writes on failed verification, exactly-once replay, and no acceptance of a conflicting/unreconciled ledger. Then verify the exact resulting head's job logs and test counts.
- Real account-specific broker contract-note validation and restoration from an actual retained Oracle Cloud PostgreSQL/document backup remain separate operational checks.
- Live broker order submission remains disabled. PR #6 stays draft/unmerged. All work remains confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.

---

## Final conflict-recovery review checkpoint — 24 October 2026

- Reviewed `LiveFillAccountingService.promote_trade` replay and `IntegrityError` recovery paths on branch head `78c66b50714175df7e6923fa0e9328b98bb30cf2`.
- Existing-execution replay locks and refreshes the broker trade record, checks its immutable execution snapshot, and compares execution identity, fill details, charge values and evidence before returning `inserted=False`; conflicting details fail closed.
- The integrity-conflict recovery rolls back the losing transaction, re-queries the execution by broker connection/trade identity, and only returns an idempotent result when the existing execution matches; otherwise it raises a conflict requiring review. Generic failures also roll back.
- Latest branch-head backend pytest CI passed in run [39920205395](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39920205395). The concurrent PostgreSQL test uses a test-only stub for the charge-ledger loader, so it verifies parent/child locking and duplicate-promotion behavior, not the real allocation verifier under the same concurrency interleaving. Ledger validation is covered by separate accounting tests. Do not overstate this as a full production-like concurrent allocation integration test.
- Review status: the inspected replay/rollback paths have coverage and no additional code change is justified by this inspection alone. Phase 3 accounting sign-off is still gated on a final review of the real verifier/promotion concurrency interaction and confirmation of exact-head CI after this documentation update.
- Real broker contract-note authenticity and a restore drill from an actual retained Oracle Cloud PostgreSQL/document backup remain outstanding operational acceptance checks.
- PR #6 stays draft and unmerged; live broker order submission remains disabled. Changes remain confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is untouched.

---

## Phase 3 accounting checkpoint — 24 October 2026

- The concurrent exact-replay PostgreSQL regression passed in implementation CI run [39919563611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39919563611) for commit `f8441f6d11b863e3ad173282664663cd4985eeb2`. The test exercises two distinct fills and a simultaneous duplicate promotion, expecting two inserted executions and one idempotent replay.
- Documentation checkpoint run [39919590316](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39919590316) passed for commit `c99e4972cf4c2c902bddc076af6327c3bfd25fa7`.
- The next documentation CI checkpoint is still in progress: progress run `39919920878` succeeded, while handover run `39919925329` and audit run `39919932771` were in progress at last inspection. These are earlier documentation heads; any newly synchronized documentation needs its own exact-head CI.
- Accounting review remains open pending exact-head verification and final adversarial review. Passing tests are evidence for covered cases, not a guarantee against every possible concurrency interleaving.
- Real account-specific contract-note validation and restore of an actual retained Oracle Cloud PostgreSQL/document backup remain operational acceptance checks. Synthetic CI restore drills do not satisfy those real-environment checks.
- PR #6 remains draft and unmerged; live broker order submission remains disabled. All work is confined to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---

## Current Phase 3 checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `3963c2bf4e6ffe2bb33d327b10e2995cd243d003`. Exact-head [Backend CI run 39607630055](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39607630055) passed **484 tests, 1 warning in 29.34s**; the broker-write boundary guard passed, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- New Phase 3 guard: broker-reported live-fill charge references are trimmed for storage and rejected when longer than the `Execution.charge_reference` 200-character column limit. This prevents a predictable storage error from being misreported as a concurrent promotion conflict. Regression coverage is included in the 484-test result.
- The existing Phase 3 safety gates remain active: replay must match the accounted fill and exact charge evidence; only broker-reported, internally consistent charges with a non-empty audit reference are accepted; durable staged trade quantities must match broker-confirmed child fills before promotion; exchange-time ambiguity/out-of-order fills fail closed; paper positions and cash remain isolated.
- **Phase 3 remains in progress, not complete.** Remaining review includes coordinator/identity boundaries, charge provenance/allocation semantics, full partial-fill and crash/restart acceptance criteria, and any explicitly selected bridge design. Keep `BrokerFillIdentity` separate from manual `BrokerTradeRecord` unless a reviewed Phase 3 design explicitly authorizes a narrow bridge.
- Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. The original `tarunsharma2610-del/Tradepro` repository remains untouched. Phase 2 remains closed.
- This checkpoint describes the verified code commit above. The documentation synchronization commit will trigger its own CI; do not treat that documentation commit as green until its exact-head run passes. Older checkpoint entries below are historical audit trail, not current status.

---

## Current verified checkpoint — 21 October 2026

- **Last verified code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- **Last verified documentation checkpoint before this status refresh:** `391dfefc9580abf9537ee659877578033baae4fd`; exact-head backend CI [run 39568264419](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39568264419) passed.
- The Phase 2 audit covers the dependency/port matrix, broker-fill workflow boundary, idempotency and rollback, reconciliation crash recovery, transaction-level lease fencing, slow persistence, 20 concurrent expiry-boundary renewal/reclaim races, and official Upstox current-day API semantics.
- Official Upstox V2 [order-book](https://upstox.com/developer/api-documentation/get-order-book/) and [get-trades-for-day](https://upstox.com/developer/api-documentation/get-trade-history/) endpoints are current-day endpoints without documented pagination parameters. Historical trades use a separate [paginated API](https://upstox.com/developer/api-documentation/get-historical-trades/); it is not wired into the Phase 2 worker.
- **Phase 2 technical checklist is complete.** Before any Phase 3 work, require a passing exact-head CI run for the then-current `main` and explicit user approval; never infer a later commit is green from an earlier run.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

---

## Current verified checkpoint — 21 October 2026

- **Verified code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- **Previously verified documentation checkpoint:** `a2e639f61e2c50070deb26d1a9a0741545c9737d`; exact-head backend CI [run 39568011689](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39568011689) passed. This is historical evidence for that SHA; every new commit still requires its own exact-head CI.
- The slow-persistence/lease-race audit is complete: the PostgreSQL row-lock test proves reclaim waits while a fenced write transaction is open; `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` passed 20 concurrent expiry-boundary renewal/reclaim races. Expired owners cannot renew, and ownership generation/token advance is verified.
- Official Upstox V2 [order-book](https://upstox.com/developer/api-documentation/get-order-book/) and [get-trades-for-day](https://upstox.com/developer/api-documentation/get-trade-history/) endpoints are current-day endpoints without documented pagination parameters. Historical trades use a separate [paginated API](https://upstox.com/developer/api-documentation/get-historical-trades/); it is not wired into the Phase 2 worker.
- Phase 2 technical audit and scope reconciliation are complete. Keep Phase 3 blocked until this final documentation commit's exact-head CI passes. Do not enable live broker submission, automatic accounting promotion or automatic scheduling. The original `Tradepro` repository remains untouched.

------

## Current verified checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- The lease-race audit now has both pieces of evidence: PostgreSQL test `test_postgres_write_fence_blocks_reclaim_until_persistence_transaction_finishes` proves reclaim waits while a fenced transaction holds the lease-row lock; new `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` runs 20 concurrent expiry-boundary renewal-versus-reclaim races and asserts expired owners cannot renew and generation/token ownership advances safely.
- CI logs confirm the full backend suite and source guard passed; the successful workflow includes SQLite and PostgreSQL 16 upgrade/downgrade/re-upgrade checks. The one Python warning is the existing Starlette/AnyIO deprecation.
- **Current task:** synchronize all authoritative documents with this result. The resulting documentation HEAD still needs exact-head CI and a final stale-status scan before Phase 2 is formally closed. Do not start Phase 3 before then.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

------

<!-- Authoritative checkpoint audit: 2026-10-21; supersedes older status notes below. -->
## Superseding phase-status note — 21 October 2026

- This security audit is a historical requirements inventory, not evidence that all safety-control endpoints or live broker-write protections are implemented. Features for persistent account safety, kill-switch trip/reset, trusted grants, central broker-write authorization, and live preflight remain deferred to the appropriate later phase and are not Phase 2 closure criteria unless explicitly listed in the master roadmap.
- Latest code/test checkpoint: [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2). Exact-head backend CI [39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests, 1 warning, the broker-write guard and SQLite/PostgreSQL 16 migration cycles. Latest docs HEAD passed [39566324985](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39566324985).
- Historical checkpoint note: cited code/test and documentation CI passed on their respective SHAs. This security document remains a historical requirements inventory, not evidence that Phase 3/4 live-safety endpoints are implemented. Live submission and automatic accounting promotion remain disabled.

## Current verified checkpoint — 21 October 2026

- The reconciliation crash-recovery/lease-fencing sub-slice is complete; backend CI run 39561621808 passed 470 tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- The defined Phase 2 dependency/port matrix and workflow-boundary decision are complete. Phase 3 accounting integration and Phase 4 live-trading release gates remain blocked by design.
- Historical verification rule: every new documentation commit requires its own exact-head CI. The latest verified documentation checkpoint before this refresh is recorded at the top of this file.
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
- **Historical audit disposition — superseded:** slow database persistence and high-volume lease-expiry/renewal races passed CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386).
- **Safety constraints remain:** no real broker orders in tests; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled; keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.
- Older checkpoint entries below are retained as history, not current instructions. This top section is the authoritative current state. After this documentation commit, verify CI for its exact HEAD before treating the checkpoint audit as fully closed.

<!-- Latest verified status, updated 2026-10-21 -->
> **Latest verified checkpoint — 21 October 2026**
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; branch: `main`. Original `Tradepro` repository remains protected and untouched.
> - Latest code/test commit: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration checks. Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
> - Documentation audit commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da` passed [CI run 39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828).
> - Phase 2 checkpoint complete through atomic run/lease finalization, stale-run and cancellation recovery, lease-loss fencing, five-record renewal, and incomplete-summary warnings.
> - **Completed engineering task:** audited single slow-write and high-volume lease-expiry races; transaction-level fencing and regression coverage passed backend CI run 39561621808 (470 passed, 1 warning).
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


## 2026-10-23 — live-fill/ledger concurrency checkpoint

- Added PostgreSQL integration test `test_live_fill_promotion_races_with_component_ledger_verification` in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`.
- Commit: `66fda569b1e4879d270a970cb5b6d216c2f55f9c`; exact-head CI run `39923699033` passed: **570 passed, 1 warning in 30.89s**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration checks, and synthetic database/document-volume restore drill passed.
- CI: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39923699033
- Safety: only `tarunsharma2610-del/tradepro-improved` changed; PR #6 remains draft/unmerged and live broker order writes remain disabled.
- Limitation: fixtures and document bytes are synthetic; authentic Upstox contract-note validation and a real Oracle-host backup restore remain outstanding.


## Phase 3 charge-calculation checkpoint — 23 October 2026

- Verified code/test commit `b37e6cab7c9cbba0897e5c02161812d121ba2c7e` passed the full Backend pytest workflow: [run 39933579727](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39933579727). Steps passed included pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, evidence retention, and cleanup.
- The branch now has arithmetic helpers/regression coverage for brokerage caps, GST on an explicit taxable base, buyer-side stamp duty, STT/CTT on an explicit base, and exchange/SEBI charges on explicit bases. These are arithmetic helpers, not a verified tariff engine: they do not establish official effective-dated rates, applicability by exchange/segment/instrument/product/side, exemptions, or per-fill attribution.
- Latest exchange/SEBI test commit: `b37e6cab7c9cbba0897e5c02161812d121ba2c7e` (CI passed). Documentation checkpoint commit `1c3906551903acc0bb5a4450c7b8a56b3f9a659a` was created afterward; exact-head CI has not yet returned a workflow result.
- Remaining Phase 3 gates: source and version official effective-dated tariffs with provenance; model applicability and taxable/calculation bases; connect rule evaluation to durable per-fill allocations; test rounding, caps, effective-date transitions, replay/idempotency, and reconciliation; verify full CI on the final documentation/code head.
- Automatic `QUANTITY`/`NOTIONAL` allocation remains fail-closed until the relevant component-specific rules are reviewed and accepted. Do not promote ambiguous or unsupported charges.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. All changes are confined to `tarunsharma2610-del/tradepro-improved`; the original `Tradepro` repository is out of scope and must remain untouched.


## Exact-head documentation CI result — 23 October 2026

- Exact checkpoint commit `d0de363bd0b034582754b41de17ae991f6c043aa` passed GitHub Actions [run 39934671391](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39934671391). This verifies the nine-document checkpoint head at the time of the run.
- Resume from the `phase3/durable-per-fill-charge-allocation` branch in `tarunsharma2610-del/tradepro-improved`. Next work: obtain/record official Upstox and statutory charge-rule sources with effective dates and provenance; model applicability by exchange/segment/instrument/product/side; then implement and test tariff-driven durable per-fill allocation and reconciliation.
- Arithmetic helpers are groundwork only, not a verified tariff engine. Keep unknown/ambiguous allocation fail-closed. PR #6 stays draft and unmerged until acceptance gates and explicit user approval. Live broker order writes remain disabled. Original `Tradepro` is outside scope and must remain untouched.


## Exact-head CI confirmation for saved checkpoint — 23 October 2026

- The nine-document checkpoint head `c2959ffed34f6dd1c299bdb36091b987df06c11a` passed full GitHub Actions run [39935827529](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39935827529). Verified steps: backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, isolated synthetic PostgreSQL/document-volume restore, evidence retention and cleanup.
- Resume work on `phase3/durable-per-fill-charge-allocation`. Next engineering task: verify and record current official Upstox, exchange and statutory charge rules with URLs, effective dates, applicability and provenance. Then implement tariff-driven component calculation and durable per-fill allocation, with regression tests for effective-date transitions, rounding, order caps, replay and reconciliation.
- Existing helpers for brokerage cap, GST, stamp duty, STT/CTT, exchange and SEBI charges are arithmetic groundwork only. They do not constitute a verified tariff engine. Keep unsupported/ambiguous scopes fail-closed.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; the original `Tradepro` repository remains outside scope.


## Upstox charge-rule source register — 23 October 2026

- Added `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` at commit `de97bd3bfe90e82b888181cf109ed6a1b8e41d41`. It records the official Upstox brokerage pricing page, Brokerage Details API, Get Trades Charges API, and official contract-note guidance, with their limits and implementation requirements.
- Key source URLs: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://upstox.com/help-center/how-can-i-access-and-download-the-contract-note-248457/ ; https://upstox.com/help-center/understanding-the-contract-note-248458/
- Research indicates the pricing page contains historical and current rate sections, including STT/CTT changes effective 1 April 2026 and NSE transaction-charge changes effective 1 March 2026. Therefore, do not hardcode a single timeless rate or use a rate from the wrong effective period. BSE scrip-group variation, commodity/currency segments, option premium/futures turnover, DP charges, GST base composition and per-crore unit normalization require explicit rules.
- The authenticated brokerage API can calculate supported orders from instrument, quantity, product, side and price; the trades-charges API provides a segment/financial-year breakdown. Treat the latter as aggregate reconciliation only, not per-fill evidence.
- Next: implement a versioned tariff-rule model with effective dates, explicit normalized units/bases, source provenance and review status; add applicability/rounding/effective-date regression tests before wiring rules into durable per-fill allocation. Unknown or ambiguous cases remain fail-closed.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Effective-dated tariff registry groundwork — 23 October 2026

- Added `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` (commit `de97bd3bfe90e82b888181cf109ed6a1b8e41d41`) documenting official Upstox pricing/API/contract-note sources, rate effective-date cautions, API limitations and the required provenance fields.
- Added `backend/app/services/broker_tariff_rules.py` (commit `0ec5590579c67c2575c8c4c72cf75bc56605120b`), a fail-closed rule selector requiring exact broker/exchange/segment/product/side/component/basis match, an effective date, source URL and SHA-256-shaped provenance, and APPROVED status. It rejects missing and overlapping rules and intentionally ships without active rates.
- Added `backend/tests/test_broker_tariff_rules.py` (commit `74240f2cc0af05befeee1fa97f988f2372a73be6`) covering exact-scope selection, review-state gating, scope mismatch, effective-date boundaries, overlap and invalid provenance/rates. CI has not yet returned a result for this latest test commit; do not mark it verified until the full workflow passes.
- This is rule-selection groundwork, not a complete tariff calculator and not proof that any specific rate is legally applicable. The next step is CI verification, then source-reviewed rules for specific segments/components and integration with durable per-fill allocation/reconciliation.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff amount calculation and CI checkpoint — 23 October 2026

- Both the tariff registry regression-test commit `74240f2cc0af05befeee1fa97f988f2372a73be6` and its nine-document checkpoint `14fa83fe144228bb81a3b935b48b73c7f454afe2` passed their full Backend tests workflows: [code run 39953794565](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39953794565) and [documentation run 39953906848](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39953906848).
- Added `calculate_tariff_amount` to `backend/app/services/broker_tariff_rules.py`, with distinct `PERCENT`, `INR_PER_CRORE`, and `INR_FIXED` units and paise rounding. Added tests for units, rounding and invalid bases. Latest test commit is `782d2d2c63905adfa6862f43abcdc057c47894a7`; its CI is pending and must be verified before treating the new calculation as green.
- No live tariff rates are activated. The new calculator requires a previously selected approved rule; rule selection still fails closed for missing or overlapping rules. This does not yet integrate the registry with durable per-fill allocation or prove component-specific legal applicability.
- Next: verify CI on the latest code commit, then build reviewed, source-backed test fixtures for exact tariff applicability and connect approved component calculations to durable allocation/reconciliation without enabling ambiguous QUANTITY/NOTIONAL allocation.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff calculation safety refinement — 23 October 2026

- Confirmed prior tariff-calculator code CI passed: [run 39954309954](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954309954). The prior nine-document checkpoint CI also passed: [run 39954408580](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954408580).
- Tightened `calculate_tariff_amount` so it refuses non-`TariffRule` values and any rule whose review status is not `APPROVED`. Added regression tests for DRAFT, REVIEWED and REJECTED rules.
- Latest safety-fix test commit: `83a70bdc88dfbc2cfabe8e80b8adfc858b516a6e`. Its full CI is pending; no green status should be inferred yet.
- Active rates remain intentionally absent pending rule-by-rule source verification and approval. Next: verify CI, then implement only specifically sourced rules with explicit applicability, normalized unit, basis, effective date and provenance before connecting to durable per-fill allocation.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Scoped tariff-calculation entry point — 23 October 2026

- Confirmed prior safety-fix code CI passed: [run 39954730200](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954730200). The previous nine-document checkpoint also passed: [run 39954836920](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954836920).
- Added `calculate_charge_for_trade` to `backend/app/services/broker_tariff_rules.py` (commit `d2d9c0c99a0cf31bca96fbde39c615b2569b1a97`) to select exactly one approved rule for the full trade scope/date and then calculate using its declared unit. Added tests for calculation result and fail-closed behavior without an approved match (commit `98c514d59d1b1da986a1d00117c2653c1e82d4c6`).
- Latest code CI is pending; do not mark this addition green until full Backend pytest, broker-write boundary, migrations and restore workflow pass.
- This entry point does not persist charge rows or allocate across fills. No production tariff rates are enabled. Next: verify CI, then design a persistence/integration boundary that records the selected rule version and calculation basis alongside the durable source component and per-fill allocation ledger.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff CI verification and estimate/allocation boundary — 23 October 2026

- Verified full Backend CI passed for tariff calculation commit `98c514d59d1b1da986a1d00117c2653c1e82d4c6`: [run 39955151533](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39955151533). Verified the nine-document checkpoint CI passed for `2a5c3cf5075c2ab217603868f6272cc366784b26`: [run 39955284700](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39955284700). Both include pytest, broker-write boundary, SQLite and PostgreSQL migration downgrade/re-upgrade, and isolated synthetic restore steps.
- Added `docs/PHASE3_TARIFF_TO_FILL_ALLOCATION_DESIGN.md` (commit `a49b37509db1658ce7026f8328a35e26422afaad`) to define the boundary between a tariff estimate, actual broker-evidenced source charge and reviewed per-fill allocation; it sets out idempotency, immutable rule snapshots, component-specific acceptance gates and safety constraints.
- Next: CI-check this design/documentation checkpoint, then implement persistence for estimates as a separate, immutable, idempotent record before wiring estimates into source-charge reconciliation. Estimates must never be represented as contract-note actuals or automatically promoted into accounting.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Immutable tariff-estimate snapshot groundwork — 23 October 2026

- Added `backend/app/services/tariff_estimate_snapshot.py` (commit `00ec9fcd449fb9c9c091b29ebc7c68377246242b`) with canonical JSON snapshots, rule/source provenance, SHA-256 fingerprints, explicit calculation base/rounding metadata, stable idempotency keys and exact-replay/conflict comparison.
- Added `backend/tests/test_tariff_estimate_snapshot.py` (commit `f89517a3ca0bc034dc84da6d2239f0fd18026990`) for deterministic serialization, exact replay, conflicting base replay, changed rule, unapproved rules, invalid base, missing identity and effective-date rejection.
- This is a deterministic snapshot and replay-comparison layer only; it does NOT yet persist estimates. Durable enforcement still requires a database table with a unique idempotency constraint, transactional insert/read comparison and a migration tested on SQLite/PostgreSQL. No estimate can become a broker actual or source component.
- Latest code CI must be verified before this work is considered green. Next: confirm test and migration conventions, add durable persistence plus migration, concurrency-safe idempotency, and tests proving rollback/replay behaviour.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Snapshot CI verification and idempotency correction — 23 October 2026

- Verified CI passed for the immutable snapshot implementation `f89517a3ca0bc034dc84da6d2239f0fd18026990`: [code run 39956149855](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956149855). Verified the associated nine-document checkpoint passed: [run 39956272786](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956272786). Both runs completed pytest, broker-write boundary, SQLite and PostgreSQL migration downgrade/re-upgrade, and synthetic restore checks successfully.
- Code review identified an idempotency-key flaw: including the tariff rule fingerprint in the key would allow the same trade/component event with a changed rule to receive a new key instead of conflicting. Corrected `tariff_estimate_snapshot.py` so event key is stable across rate/rule changes, and changed the regression test to require a same-event rule change to fail as a conflicting replay.
- Latest correction commits: `204574082c7953ac08262a9f51801f04fd09ead7` and test `fafa26b6fb686471ac38a041256659b273f97712`. CI for this correction is pending.
- The snapshot remains in-memory/canonical only. Durable database persistence is not implemented yet; adding a table/migration requires identifying the current Alembic head and testing a unique idempotency constraint with transactional exact-replay/conflict behavior.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Durable estimate-only tariff persistence — 23 October 2026

- Verified the previous idempotency-correction code CI passed: [run 39956721476](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956721476). Verified the previous nine-document checkpoint CI passed: [run 39956881266](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956881266).
- Added `TariffEstimateSnapshotRecord` model and model registration (commits `08fec41026dabf250bd8756e0a711c20bbbf1e2a`, `0f47e07abd8bad51e4a7e11a851c726dd9008882`), Alembic revision `202610240015` after `202610240014` (commit `d98f5e259c610f8a5d392461ea1b75f6b9471912`), and `persist_tariff_estimate_snapshot` (commit `bc8b7bb2666e73cf30aa3fa4a796ebfe4e4874e5`).
- Added persistence regression tests for create/exact replay, changed-base conflict, changed-rule conflict, and estimate-only status (commit `cc121e7c710038ee25a434634a86ec4296cd0d68`). The unique database idempotency key is the concurrency arbiter; the service uses a nested transaction and leaves the outer commit to its caller.
- Latest implementation CI is pending; do not consider durable persistence verified until full pytest, broker-write boundary, SQLite/PostgreSQL migration downgrade/re-upgrade and synthetic restore checks pass.
- The database record stores only estimate snapshot JSON and a digest and has a database constraint that fixes status at `ESTIMATE_ONLY`; it does not create or modify contract-note actual charge/source-component rows.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Persistence CI result and append-only enforcement — 23 October 2026

- Full CI passed for durable estimate persistence implementation commit `cc121e7c710038ee25a434634a86ec4296cd0d68`: [run 39957564616](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39957564616). Backend pytest, broker-write boundary, SQLite and PostgreSQL migration downgrade/re-upgrade, and synthetic restore steps all succeeded.
- Review then identified that the database row had no ORM-level guard against updates to the snapshot payload. Added an append-only SQLAlchemy `before_update` guard to `TariffEstimateSnapshotRecord` (commit `596d4396bfaa58da3f4bf8ad11978370cfc8edf2`) and a regression test proving payload mutation is rejected (commit `af07ad77c3c7621774f49771c5d9cb4665778c03`).
- The append-only guard is an ORM protection, not a database trigger; direct SQL updates outside the ORM are not blocked by this guard. Consider a portable DB-level immutability trigger only if required by the release threat model. The unique key and ESTIMATE_ONLY check remain database-enforced.
- Backend CI run [39979772325](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39979772325) passed on code/test commit `e54e405b74feee90e4658a6992fa208a3e2da5d3`, including the broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore drill. The subsequent documentation checkpoint must still receive exact-head CI; do not treat that newer commit as verified until all jobs complete successfully.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Latest tariff-safety correction checkpoint — 2026-10-23
Tariff safety correction commit `68dc2b6fa0a729cc77180725e581de61a88e9de1` passed CI run [39982723294](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39982723294), including broker-write boundary guard, database migration round-trips on SQLite and PostgreSQL 16, and synthetic restore drill. This is not authorization for live trading. PR #6 stays draft/unmerged, live broker order writes remain disabled, and all work remains limited to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is untouched. The docs synchronization commit must receive exact-head CI.


## Tariff safety + Upstox charge-source research — 2026-10-23

Code commit `ce0b4bc17eaf1656334e10ca8d6e32a68f50593b` adds a fail-closed stamp-duty unit guard: the specialized stamp-duty calculator accepts only percentage-based approved rules; regression tests reject `INR_FIXED` and `INR_PER_CRORE`. Exact-head CI [39987357989](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39987357989) passed backend tests, broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill.

Official Upstox sources reviewed:
- Brokerage calculator API: https://upstox.com/developer/api-documentation/get-brokerage/ — order-scoped estimate with brokerage, taxes, transaction/clearing/IPFT/SEBI charges and DP-plan metadata; `dp_plan.min_expense` is a daily per-scrip sell minimum outside the brokerage calculation.
- Trade charges API: https://upstox.com/developer/api-documentation/get-trade-charges/ — segment/date-range charge breakdown including brokerage, GST, STT, stamp duty, transaction, clearing, IPFT, SEBI turnover and demat transaction charges.
- Historical trades API: https://upstox.com/developer/api-documentation/get-historical-trades/ — trade ID, exchange, segment, quantity, amount, side and trade date.
- Public tariff page: https://upstox.com/brokerage-charges/ — includes historical and newer effective-date rows; never activate rates from a flattened scrape without preserving effective periods and source snapshot.

API charge breakdowns are reconciliation/reference inputs, not automatically contract-note evidence or a substitute for reviewed actual source components. Do not store tokens. DP per-scrip/day minimums, STT/CTT tax-event cases and other conditional models remain unsupported until represented and tested explicitly. No active production tariff registry is enabled. PR #6 stays draft/unmerged; live broker writes remain disabled; original `Tradepro` remains out of scope.

Security: the reviewed charge APIs are read-only GET endpoints; never persist or log access tokens. This research does not enable order placement, modification, or cancellation.


## Generic conditional-charge guard — 2026-10-23
The next audit found that the generic rate calculator could apply plain rate×base arithmetic to STT/CTT and DP/demat components, despite these requiring event- or day/scrip-specific semantics. Commit `ee09183e5b8eeff0311431faa90b807d9b561ce7` adds an explicit fail-closed block for STT, CTT, DP, DP charges and demat/depository transaction charges in the generic calculator, with parameterized regression tests. Exact-head CI run [39988242077](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39988242077) passed. The synchronized documentation commit `b1207def7d828c960e6fffe9c6af8b9ed0177c07` also passed exact-head CI run [39988578238](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39988578238).

Audit note: the implementation constant is `tariff-estimate-snapshot-v4`; older design text saying snapshot v3 is stale and is corrected in the accompanying design-document update. Remaining gated models include STT/CTT event-specific rules, DP daily per-scrip minimums, conditional lesser-of pricing, and reviewed source-backed effective-date rates. No live tariff registry or live broker order writes are enabled.

Security remains fail-closed: no broker order write is enabled by tariff calculation or API research.

## Phase 3 variance boundary note — 2026-10-24
Order-fill-set estimate variance is an audit comparison only, not an order-control endpoint or source for charge allocation. New tests reject tampered actual fill-set digest, mixed broker-order membership, side mismatch, and trade-date mismatch without persisting variance rows. Current-head CI is pending. Live broker order submission remains disabled; no change to public control endpoints is implied by these tests.

## CI verification — 2026-10-24
Backend pytest passed on head `bc8e5c1aa862589c660fd361d87f7df45d8ceb10` (run `40062975428`). Variance comparison remains an audit-only service, not an order-control endpoint and not an allocation source. Remaining checks concern concurrency, source review-state revalidation and proof of no accounting side effects. Live broker order submission remains disabled.

## Aggregate variance review-state boundary — 2026-10-24
Added regression tests ensure variance comparison cannot mutate reviewed source/evidence or per-fill allocation state, and fails closed if evidence/component review state changes before comparison. Exact-head CI is pending. This service remains audit-only and is not an order-control endpoint.

## Upstox SDK/agent safety boundary — 2026-10-24
The Upstox Agent Skill can execute live orders; never run it in a way that submits live orders or bypasses app controls. The official MCP is described as read-only, but account data access still requires explicit authorization and supported connector setup. Use official docs/SDK/skills as technical references under PAPER-only safeguards; do not expose tokens or account data. See `UPSTOX_API_INTEGRATION_POLICY.md`.

## Variance race acceptance — 2026-10-24
PostgreSQL concurrency coverage passed exact-head CI run `40064129721` (738 passed, 1 warning): simultaneous duplicate comparisons persist one immutable audit-only variance record and do not create allocation rows. This service is not an order-control or accounting-promotion path. Tariff-rule work must not turn estimate comparisons into actual charge evidence or bypass source-review/promotion safeguards. Live broker order writes remain disabled.

## Upstox charge API surface — 2026-10-24
The read-only reconciliation client now exposes only fixed GET methods for brokerage estimates, aggregate historical charges and paginated historical trades. Exact-head CI run `40064514873` passed (744 passed, 1 warning). Input validation and sanitized error categories remain in the shared transport; no order-write methods were added, and no live account call was made. API outputs must not bypass reviewed-source or promotion gates.

## API estimate provenance and variance guard — 2026-10-24 (CI verified)
Upstox brokerage estimates carry a canonical stored response and SHA-256 recomputed before variance comparison. The comparison validates request quantity, price, side and instrument against the exact reviewed fill set. The fixed GET-only broker client remains read-only; estimate snapshots are immutable and cannot create allocation rows. Exact-head CI run `40065219626` passed (**754 passed, 1 warning**).

## Order brokerage shape guard — 2026-10-24 (CI verified)
The estimate calculator supports fixed per-order fees and capped percentage brokerage only through explicit specialized shapes. It remains an estimate-only path and cannot promote actuals or create allocation rows. No tariff rate was activated. Exact-head CI run `40065607232` passed (**756 passed, 1 warning**).

## Tariff candidate registry safety — 2026-10-24 (CI verified)
The new Upstox candidate registry contains only DRAFT rules, and tests verify the selector rejects them. No API or calculation path can treat these candidates as approved tariff inputs. Exact-head CI run `40065979244` passed (**760 passed, 1 warning**); live broker writes remain disabled.

## Upstox estimate reconciliation — corrected test and exact-head CI verified — 24 October 2026

- The corrected test fixture commit is [2a39a67](https://github.com/tarunsharma2610-del/tradepro-improved/commit/2a39a67cd1d2c8dab16e22425c87e247974c10cd). It updates the reported total consistently with the STT change so the replay-conflict test exercises replay behavior rather than failing the aggregate-reconciliation guard.
- Exact-head backend CI run [40082629274](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40082629274) passed on the then-current branch head [7e373f2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/7e373f2f2ff0d2c7faae8397765df2d35b901599). Pytest, broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention all passed. This confirms the previously failing workflow was corrected.
- This documentation synchronization creates a newer head, so CI must be checked again on the final resulting head before the documentation gate is called green.
- API estimates remain estimate-only. No candidate tariff rates were activated, no estimate was promoted into actual charges, and automatic per-fill allocation remains disabled pending reviewed component-specific rules and durable accounting acceptance.
- PR #6 remains draft/unmerged. Live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` is out of scope.

## Upstox component provenance checkpoint — 24 October 2026

- Upstox estimate normalization preserves `transaction`, `clearing`, `ipft`, and `sebi_turnover` as distinct components; it does not collapse them into a generic exchange-charge value.
- The component-separation regression test passed on exact PR head [0112f92](https://github.com/tarunsharma2610-del/tradepro-improved/commit/0112f92f065156e93069332be0a3665c601ab940), via [Backend tests run #40083185015](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40083185015). Pytest, broker-write boundary guard, SQLite/PostgreSQL migration round-trips, synthetic restore drill, and evidence-retention steps passed.
- Estimate normalization is not tariff activation or actual-charge evidence. Do not map aggregate trade-charge outputs to individual fills or enable automatic transaction/clearing/IPFT allocation without reviewed component-specific semantics, source evidence, and an exact eligible-fill manifest.
- Open item: verify effective-dated component composition and GST taxable-base rules from official sources and reviewed fixtures; prevent IPFT double-counting where the tariff presentation combines it with transaction charges.
- PR #6 remains draft/unmerged; live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`, never the original `tarunsharma2610-del/Tradepro`.

## PostgreSQL allocation concurrency CI — 24 October 2026

- Corrected PostgreSQL concurrency test fixture now creates valid portfolio, instrument, application-order, and broker-order prerequisites before broker fills. The initial fixture failed on a foreign-key constraint because it used random, non-persisted broker-order IDs; fixed in [fc0c539](https://github.com/tarunsharma2610-del/tradepro-improved/commit/fc0c539dc24f87a705207a16a98789fd63d928f8).
- Exact corrected head passed [Backend CI #40084015153](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40084015153): **777 passed, 1 warning**. CI set `TEST_POSTGRES_URL`; the PostgreSQL concurrency integration ran, alongside broker-write boundary checks, SQLite/PostgreSQL migration round-trips, and synthetic database/document restore with retained evidence.
- This verifies allocation persistence/concurrency only; it does not authorize tariff activation or automatic charge allocation. Keep transaction, clearing, IPFT and SEBI components distinct until official component-composition and GST taxable-base rules are reviewed; prevent IPFT double-counting.
- PR #6 remains draft/unmerged; live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`, never the original `tarunsharma2610-del/Tradepro`.

## Exact-head CI checkpoint — 24 October 2026

- Documentation checkpoint commit `3e0ae8034f333e082bfa11b6da50aec9e620f242` passed GitHub Actions Backend tests run [`40091642139`](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40091642139): **787 passed, 1 warning**.
- Broker-write boundary guard passed. SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed. Synthetic PostgreSQL/document-volume restore drill and evidence-artifact retention passed.
- The warning is a Starlette/AnyIO deprecation warning; GitHub Actions also emitted Node.js 20 deprecation notices. No test or safety-guard failure was reported.
- This result applies to commit `3e0ae803` only; subsequent documentation commits require their own exact-head CI run.
- Phase 3 remains open pending final accounting acceptance and tariff-source applicability decisions. PR #6 remains draft/unmerged and live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; never the original `tarunsharma2610-del/Tradepro`.

## Upstox charge API audit and exact-head CI checkpoint — 24 October 2026

- Added official API guidance to `PROJECT_INSTRUCTIONS.md` and expanded `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`: use Brokerage Details API (`GET /v2/charges/brokerage`) for estimates; use supported P&L charge breakdowns for a selected reporting scope (aggregate, not per-trade) for reconciliation; compare realized charges with authenticated trade history and an actual broker-issued contract note/tax invoice.
- Exact branch head `640ebfba38a96c7d84d4ffc3501afcd2278b551b` passed Backend workflow [#40092513016](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40092513016): **787 passed, 1 warning in 48.85s**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore drill, and evidence retention passed.
- Warning: Starlette/AnyIO `BlockingPortal` deprecation. Workflow also reports Node.js 20 and dependency deprecation notices. No test or broker-write guard failure was reported.
- Source discovery is not approval: no account-specific Upstox response or contract-note fixture was verified here. GST taxable-component mapping and tariff scope/effective dates remain unapproved; candidate rules remain inactive. Do not double-count legacy IPFT with the current combined NSE transaction schedule.
- Future documentation/code commits need their own exact-head CI run. This entry records the successful run above only.
- PR #6 remains draft/unmerged; live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; never modify the original `tarunsharma2610-del/Tradepro`.

## Upstox API coverage and tariff-source correction — 24 October 2026

- Added read-only `get_profit_loss_report` for official `GET /v2/trade/profit-loss/data`, with fixed endpoint, segment/financial-year/date/pagination validation, and regression coverage. The API supplies paginated trade-wise realized P&L rows but does not document per-row charge components; do not treat it as per-fill charge evidence.
- Kept the three Upstox surfaces distinct: `/charges/brokerage` is a request-specific estimate; `/trade/profit-loss/charges` returns selected-scope aggregate charge components; `/trade/profit-loss/data` returns trade-wise P&L rows. Contract-note evidence and reviewed allocation rules remain required for charge promotion.
- Corrected DRAFT equity STT candidates for delivery buy/sell (0.1%) and intraday sell (0.025%) to the source-stated 1 April 2023 effective date rather than incorrectly implying a new 1 April 2026 effective date. Added regression coverage. All candidate rules remain DRAFT and non-selectable.
- Intermediate backend CI run [#40093110292](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40093110292) passed **789 tests, 1 warning** plus broker-write guard; however, this run predates the final effective-date correction. Latest exact-head validation is still running in [#40093198960](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40093198960); do not mark the latest head green until it completes successfully.
- PR #6 remains draft/unmerged and live broker order submission remains disabled. All work is in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` remains out of scope.


## 2026-10-24 — Charge API unusable-value provenance hardening

- Review found that `resolve_charge_api_value` retained the approved mapping's semantic and source fingerprint for usable values, but omitted source URL and SHA-256 provenance when the normalized field was `MISSING`, `NULL`, or `INVALID`. These values were already unusable, but their interpretation path was less auditable.
- Fixed the resolver to return approved mapping provenance for every normalized state while keeping missing/null/invalid values `usable=False`. Numeric zero remains a distinct present value; this change does not promote allocations or approve production Upstox mappings.
- Added regression coverage for missing, null, NaN, negative, boolean, and object values; assertions require mapping source URL, source SHA-256, and semantic to remain present. Added mapping effective-date and estimate-vs-actual guard cases.
- Implementation commit: `845e9e0dc924f11ae89b96ef73c94c59c2efb4b4`. Test commit: `1d7e24b0ba8c89062ec1eeddb93d0c4cd22a226f`. Documentation checkpoint is being synchronized; exact-head CI must pass before verification is claimed.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains out of scope.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Resolver now checks that the payload field name matches the terminal field in the selected approved mapping path. This closes a semantic mismatch where a caller could select `charges.ipft` but normalize another payload field.
- Implementation commit: `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression test commit: `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI for latest commits is pending; previous green runs apply only to earlier heads.
- Existing accounting tests cover lock ordering, replay idempotency, conflicting evidence and rollback. A genuine concurrent two-session verification-versus-promotion race is not demonstrated in the inspected live-fill test file; verify other integration coverage before marking complete.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Latest resolver CI and PostgreSQL concurrency suite verified

- Latest implementation/documentation checkpoint `ed346e823cbfae8448fae0134c4ff864bfcc60ac` passed Backend pytest workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654): **872 passed, 1 warning**, with the broker-write boundary guard also passing.
- Dedicated PostgreSQL concurrency tests are present in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`, including source verification vs allocation promotion and live-fill promotion vs ledger verification. The successful CI summary reports no skipped tests, so this run exercised the collected suite; the race tests are part of that test set.
- This confirms test execution and safeguards in the synthetic PostgreSQL test environment; it does not establish production broker tariff correctness or approve any real Upstox field mapping.
- PR #6 remains draft/unmerged. Live broker order submission and automatic quantity/notional allocation remain disabled. Work only in `tradepro-improved`; original `Tradepro` remains untouched.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` calculates charges from proposed order inputs; it is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver blocks this endpoint from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use, even if a mapping is misleadingly labelled. `/v2/trade/profit-loss/charges` remains aggregate-only for per-fill purposes. Regression tests cover both mislabelled cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. The prior head passed workflow #40111501429; latest implementation/test CI must be verified.
- Production mappings/tariffs unapproved; null is not zero; automatic quantity/notional allocation and live order submission disabled. PR #6 draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` untouched.

## Upstox Agent Skill trust boundary — 2026-10-24

The upstream skill is external development material, not an app authorization boundary. Static inspection found live order/GTT examples, a helper that can fall back to a local `config.json` token, and a smoke-test path that prints raw API exception bodies. Do not install it in the production runtime, execute write-capable examples with live credentials, or allow a skill's interactive confirmation to bypass application-level authorization, PAPER-mode enforcement, broker-write guards, idempotency, audit logs, or secret redaction. Details: [`docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md`](docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md).


## Phase 3 checkpoint — verified source-component canonicalization adapter (25 October 2026)

- Added `backend/app/services/broker_charge_verified_component_canonicalization.py` and focused tests in `backend/tests/test_broker_charge_verified_component_canonicalization.py`.
- The adapter accepts only persisted `VERIFIED` rows tied to the expected evidence ID and matching SHA-256, with INR currency, reviewer identity/timestamp, unique row IDs, and source locators. It delegates six-component and combined/split transaction/IPFT rules to the existing canonicalization contract and returns source-record provenance.
- Output remains `accounting_approved=false`. This is a validation adapter, not yet the transaction-owning persistence/promotion integration. It does not prove broker-origin authenticity, establish GST/tariff applicability, or enable automatic allocation.
- Implementation commit `d3a2fc076a4309f23edbb14b0a47ba41fec0b557`; regression-test commit `c8e3748f12c5674b1b77e76ff8fcf9b8f3dc68a6`. Exact-head CI is not yet verified; observed Backend workflow `40192323693` was in progress on the earlier implementation commit and does not validate the added tests. Do not call the latest head green.
- Next gate: integrate this adapter into the existing locked source-component verification/allocation-promotion path; persist canonical totals and source-row associations atomically; test duplicate/replay/conflict, rollback, partial fill sets, and PostgreSQL concurrency.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; production tariff/GST/IPFT interpretations unapproved.


## CI correction — verified source-component canonicalization adapter (25 October 2026)

- Backend workflow [#40192336466](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40192336466) passed on code/test commit `c8e3748f12c5674b1b77e76ff8fcf9b8f3dc68a6`; Backend pytest and the synthetic PostgreSQL/document-volume restore drill succeeded.
- Subsequent commits only synchronize documentation; no application code changed after the tested code/test head. No workflow run is associated with the latest docs-only head, so the code/test head is green, but the latest docs commit does not have separately verified exact-head CI.


## Phase 3 checkpoint — canonical source-to-allocation planning (25 October 2026)

- Added `backend/app/services/broker_charge_canonical_allocation_plan.py` and `backend/tests/test_broker_charge_canonical_allocation_plan.py`. The planning boundary composes reviewed-source canonicalization with deterministic paise allocation, returning per-fill amounts and source-row provenance without database writes or accounting approval.
- Only `EXPLICIT_REVIEWED` weights are enabled pending approved component-specific tariff rules. Contributing source rows must share the canonical fill manifest/hash, explicit weights, basis and allocation-method version. Split transaction/IPFT values are combined once into canonical exchange charges before allocation.
- Tightened the verified-source adapter to reject same-user extraction and review; added regression coverage.
- Commits: planner `a3a51ce8257b2300ead83158c423772f420545f8`; planner tests `1dffc90897e524a3c4065740daf3b31f2aaabf03`; independent-reviewer guard `f17e75ab4cc8eef448dd4743b942a13b0af8d2d0`; guard test `18d69d5fee2a4a2668cdf32a8ad0661aba8adbe3`.
- Backend workflow `40193811936` was in progress at the latest check. Do not mark the newest code/test head green until CI completes and covers the latest test commit. Database persistence/promotion integration remains the next gate.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; GST/tariff/IPFT interpretations unapproved.


## CI follow-up — canonical allocation planner (25 October 2026)

- Backend workflow [#40193836363](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40193836363) passed on independent-reviewer test commit `18d69d5fee2a4a2668cdf32a8ad0661aba8adbe3`. Backend pytest, SQLite migration cycle, PostgreSQL 16 migration cycle, and synthetic PostgreSQL/document-volume restore drill all succeeded.
- A newer docs-only checkpoint commit triggered Backend workflow [#40193954195](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40193954195), still in progress at last check. Code/test head is green; latest documentation head is not yet confirmed green.
- Next: wait for exact latest-head CI, then connect planning output to the locked persistence/reconciliation service using source-row provenance and canonical component identity. Do not promote accounting until transaction and replay/concurrency tests pass.


## Phase 3 checkpoint — verified canonical allocation persistence boundary (25 October 2026)

- Added `backend/app/services/broker_charge_verified_allocation_persistence_service.py`. It locks reviewed evidence and source rows, requires the approved `live-fill-accounting-component-set-v1` of six independently reviewed direct-mapped components, builds the verified canonical plan, and delegates to the existing idempotent allocation persistence service. It leaves allocations `PENDING_RECONCILIATION`, never commits, and requires caller-owned outer transaction.
- Added persistence-boundary tests in `backend/tests/test_broker_charge_allocation_persistence_service.py` for successful direct-component allocation and rejection of an unapproved component-set version.
- Split transaction/IPFT planning is supported, but persistence deliberately rejects it until a durable canonical-component ledger links multiple raw source rows to one canonical exchange-charge component.
- Implementation commit `d92219dcae765c2b8a305a825ae10c4596315f6a`; tests commit `9a837155260d0f2fef4cd9fd9dee458b2db13f90`. Exact-head Backend workflow [#40194167945](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194167945) was in progress at last check; do not mark the new boundary green until it completes.
- Next: inspect exact-head CI; if green, implement durable canonical-component/source-row associations for combined/split transaction/IPFT, then add rollback, replay/conflict and PostgreSQL concurrency tests.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; tariff/GST/IPFT interpretations unapproved.


## Phase 3 checkpoint — durable canonical source snapshots (25 October 2026)

- Added `BrokerChargeCanonicalComponent` model, migration `202610250023_canonical_charge_components.py`, model registration, and `broker_charge_canonical_component_snapshot_service.py`.
- The materializer locks reviewed evidence and source rows, verifies stored contract-note bytes against SHA-256/size, requires independent source review and the approved component-set version, canonicalizes reviewed rows, and creates six versioned canonical snapshots in `PENDING_REVIEW`. It preserves exact raw source row IDs, source fingerprint, mapping/representation version, amounts, fill manifest/weights, and allocation policy. Identical snapshots replay idempotently; changes to reviewed allocation metadata create a new revision.
- Tests cover direct snapshots, split transaction/IPFT mapping to one exchange-charge snapshot, idempotent replay, unverified rows, tampered source documents, and revisioning after allocation-metadata changes.
- Latest code/test commit: `af14297ee904b7b021fc149e3ac3adf2cb0743f1`. Exact-head Backend workflow [#40194614746](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194614746) was in progress at last check; do not call the new snapshot model/migration green until it completes.
- Next: verify migration/test CI, then add a distinct reviewer workflow for canonical snapshots and adapt allocation reconciliation to reference canonical snapshot IDs/source fingerprints rather than assuming one raw source row equals one canonical component.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6 draft/unmerged; PAPER mandatory; live broker writes and automatic accounting promotion disabled; production tariff/GST/IPFT interpretations unapproved.


## Phase 3 CI correction — canonical snapshot test (25 October 2026)

- Backend workflow [#40194614746](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40194614746) reported 1 failure and 951 passes. The failure was test-only: the split transaction/IPFT snapshot test passed string UUIDs to a SQLAlchemy UUID column query. Fixed the test to convert persisted source-row IDs to `UUID` objects in commit `0a7437b9b413f86832cc029b983751c25007e21a`.
- The prior run is not green overall. Verification of the correction is pending a new Backend CI result; do not report canonical snapshot work as green yet.
- The migration/model and snapshot materializer remain on the Phase 3 branch only. No live-order or accounting-promotion behavior was enabled.
