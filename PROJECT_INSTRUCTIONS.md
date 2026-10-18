# Tradepro — Existing Codebase Audit, Improvement and Live Trading Upgrade

## 1. Objective

Improve the existing Tradepro codebase to deliver a reliable, secure trading platform supporting both **Paper Trading and Live Trading through Upstox**.

Create the improved version as a separate project. Do not modify, overwrite, or break the original project.

**Important principle: Preserve working functionality. Do not rewrite working code or change existing behavior unnecessarily.**

The goal is to improve and complete the existing application, not rebuild everything from scratch.

## 2. Audit Before Making Changes

First, inspect the entire existing codebase, including:
- Backend APIs, services, models and database schema.
- Frontend pages, components and existing user workflows.
- Strategy engine, scheduler and background workers.
- Paper-trading and order-execution logic.
- Upstox authentication, market data and broker integration.
- Risk management, portfolio accounting and P&L calculations.
- Backtesting, notifications, logging, configuration and deployment.
- Existing tests, dependencies and documentation.

For every requirement in this document, classify the existing implementation as:

1. **Working and complete:** Meets the requirement and passes appropriate tests.
2. **Working but incomplete:** Some functionality exists but requires improvement.
3. **Broken or incorrect:** Exists but does not work reliably or correctly.
4. **Missing:** Not implemented.
5. **Requires verification:** Cannot be confirmed from static inspection alone.

Verify functionality through existing tests and targeted tests where practical. Do not assume something works simply because its code exists.

## 3. Change Policy — Mandatory

Follow these rules throughout development:

- If a feature already works correctly, meets the requirements and has adequate test coverage, **leave it unchanged**.
- If a feature is partially implemented, improve the existing implementation rather than replacing it unnecessarily.
- If a feature is broken, fix the underlying problem.
- If a feature is missing, implement it using the existing architecture wherever practical.
- Refactor working code only when there is a demonstrable benefit, such as correcting a security vulnerability, preventing trading errors, fixing architectural conflicts or enabling a required feature.
- Do not remove working functionality, change APIs or database structures unnecessarily, or introduce avoidable breaking changes.
- Do not add duplicate services, models, pages or integrations when suitable implementations already exist.
- Before changing shared components, identify what depends on them and test for regressions.
- Preserve existing data and provide safe, tested database migrations whenever schema changes are necessary.
- If a proposed change is unnecessary, document that it was reviewed and retained as-is.

**A requirement being listed in this document does not automatically mean the code needs to change. Change only what the audit demonstrates needs changing.**

## 4. Paper Trading and Live Trading

Support both modes using the existing implementation wherever possible.

### Paper Trading
- Continue using real market data with simulated order execution.
- Support applicable order types, pending orders, fills, cancellations, slippage, charges, positions and P&L.
- Keep paper balances, orders, positions and performance separate from live trading.
- Ensure paper orders can never reach the real broker.

Retain existing paper-trading components if they already satisfy these requirements.

### Live Trading
- Use the official Upstox API for authorized real order placement.
- Track broker-confirmed orders, fills, rejections, cancellations, positions, holdings and available funds where supported.
- Handle partial fills, timeouts, retries, token expiry, API errors and reconnection safely.
- Do not mark orders as executed until confirmed by the broker.
- Prevent duplicate orders during retries, worker restarts and repeated strategy evaluations.
- Keep broker-specific operations separate from strategy logic where practical.

Audit the current code first. Reuse any existing, correctly implemented live-trading components and build only the missing pieces.

## 5. Trading Mode and Safety

Implement or improve the following only where necessary:
- Clear Paper/Live mode selection and visible mode indicators.
- Separate paper and live strategy configurations.
- Explicit authorization and confirmation before enabling live trading.
- Appropriate confirmation before the first live order.
- No automatic conversion of paper strategies or orders into live trading.
- Configurable limits for order value, position size, daily losses, exposure and order frequency.
- Validation of available funds, instrument eligibility, lot size, tick size and supported order types.
- Duplicate-order prevention and broker-state reconciliation.
- A kill switch that stops new automated entries.
- Safe handling of open orders and existing positions during failures.
- Audit logs for important trading actions and configuration changes.

Do not duplicate or replace risk controls that are already correct and adequately tested. Extend them where there are gaps.

## 6. Strategies, Execution and Accounting

Review existing functionality before changing it.

Ensure the platform can:
- Create, edit, backtest, activate, pause and stop strategies.
- Check strategy activation and trading mode before generating orders.
- Attribute orders, trades and positions correctly to their portfolio and strategy.
- Apply risk checks before order submission.
- Handle entries, exits, stop-losses, targets and supported trailing-stop logic.
- Track pending, partially filled, rejected, cancelled and completed orders correctly.
- Calculate realized and unrealized P&L using reliable execution data.
- Account for brokerage, taxes and other applicable charges where supported.
- Keep paper results and live results separate.

Resolve existing model or database conflicts only when the audit identifies a real correctness problem. Preserve compatible existing structures wherever possible.

## 7. Upstox Integration

Audit the current Upstox integration and complete missing or defective functionality for:
- OAuth authorization and callback validation.
- Secure token storage and expiry handling.
- Instrument master and contract validation.
- Quotes, candles and WebSocket market data where supported.
- Order placement, modification, cancellation and reconciliation.
- Trade book, positions, holdings, funds and margin information where supported.
- Rate limits, network errors and reconnection handling.

Use current official Upstox documentation. Do not invent endpoints or claim support for features the API does not provide.

Keep any correctly working integration unchanged unless a specific defect or required improvement is demonstrated.

## 8. Risk, Security and Reliability

Verify and improve as required:
- Risk limits enforced by the backend before live order submission.
- Protection against stale market data, duplicate execution and runaway strategy loops.
- Secure handling of API credentials and access tokens.
- Proper authentication and authorization for sensitive actions.
- Validated OAuth state and callbacks.
- Safe logging without secrets or access tokens.
- Consistent order state after restarts and broker disconnections.
- Appropriate market hours, holidays and end-of-day handling.
- Monitoring, error reporting and recovery procedures.

Prioritize changes that prevent unauthorized orders, duplicate orders, incorrect accounting or uncontrolled financial losses.

## 9. Frontend and User Experience

Inspect existing pages before creating or replacing any.

Retain working pages and components. Fix or add only what is needed to provide:
- Clear Paper/Live mode status.
- Strategy and portfolio management.
- Orders, positions, holdings and trade history.
- Funds and margin information where available.
- P&L, trading costs and risk-limit status.
- Broker connection status and actionable error messages.
- Live-trading confirmation and emergency controls.

Avoid duplicate pages, unnecessary redesigns and changes to working workflows without a clear reason.

## 10. Testing and Regression Prevention

Before modifying the application:
- Record the current working baseline.
- Run existing tests and available frontend build, lint and type checks.
- Record pre-existing failures instead of attributing them automatically to new changes.

For each modification:
- Add or update targeted tests.
- Run the relevant existing tests.
- Run regression tests for dependent features.
- Verify that unaffected workflows still work.
- Test paper/live isolation and live-trading safety.

Use mocks or supported test environments for broker testing. Never place real orders merely to verify the implementation without explicit authorization.

Do not claim tests passed unless they were actually executed.

## 11. Implementation Workflow

Work in the following order:

1. Inspect the codebase and document the current implementation.
2. Create a requirements audit mapping each requirement to existing files, services and tests.
3. Identify actual gaps, defects, security risks and incomplete features.
4. Prepare a prioritized change plan with the reason for each proposed change.
5. Implement the smallest safe set of changes that satisfies the requirements.
6. Test each change and check for regressions.
7. Review the completed application against every requirement.
8. Document what was retained unchanged, what was improved, what was added and what remains incomplete.

Keep the original project untouched and work only in the separate new project or branch designated for the improved version.

## 12. Required Deliverables

Provide:
- The separate improved codebase.
- An audit report showing which requirements were already satisfied.
- A change log explaining each meaningful modification and why it was necessary.
- A list of existing functionality deliberately retained unchanged.
- Test results, including any failures or unverified areas.
- Database migration and deployment instructions where applicable.
- A list of remaining limitations and manual configuration steps.
- Confirmation of which Paper Trading and Live Trading capabilities are actually implemented and verified.

## Final Instruction

**Audit first, preserve what works, fix what is broken, improve what is incomplete, and build what is missing. Do not rewrite the project merely to follow this specification.**

Correctness, security, financial safety and regression prevention take priority over unnecessary refactoring or adding more code.

Live Trading must remain disabled until its broker integration, risk controls, order reconciliation, security checks and relevant end-to-end tests have been verified. Enabling real trading requires explicit user authorization.


## Continuation checkpoint — 18 October 2026

Before starting any continuation, read the latest authoritative checkpoint at the end of `MASTER_ROADMAP.md`, `PROGRESS.md`, `AUDIT_REPORT.md`, and `HANDOVER.md`. Do not restart a task already marked completed. The latest roadmap task was a real-service integration test for the existing reconcile-before-promote coordinator—not creation of another coordinator. Continue by checking the latest code commit and CI result, fixing only demonstrated failures, then update the checkpoint files with verified evidence. Keep live trading disabled, do not call order-write endpoints, do not merge PR #1, and do not touch the original `Tradepro` repository.

 
### Superseding checkpoint — integration tests now exercise fresh intake

The integration test was refined in commit `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` so each scenario starts with no staged trade rows; the real ingestion service must insert broker-returned trades before status reconciliation/promotion. This supersedes the earlier test-only SHA `b5783d421f64fcb8e7f1d75f1af5185fd9029f59`. CI remains unverified; check the latest commit before claiming the task complete.

## Superseding verified checkpoint — 18 October 2026: real-service fill reconciliation integration

### Exact verification evidence
- Latest tested code/test SHA: `c779f2543ea1f20efbd8b7dca38a9c2aed201749`.
- GitHub Actions [run #39118955335](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39118955335): **success**. Full suite: **385 passed, 1 skipped, 1 warning in 34.01s**. SQLite migration upgrade passed, PostgreSQL 16 migration upgrade passed, and PostgreSQL concurrency integration passed (**1 passed in 0.35s**).
- This exact-head run verifies the fresh-ingestion integration test refinement from commit `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` and fixes for nondeterministic child order assertions and deleted ORM fixture access.
- The real-service integration test now begins with no staged trade rows: mocked Upstox trade reads must be inserted by the real `BrokerTradeIngestionService` before official status reconciliation and promotion. Repeated reconciliation/promotion is idempotent; sibling status failure prevents any fill accounting; charge-estimate failure creates no Execution/LivePosition rows; paper cash/positions and parent Order state remain unchanged.
- PostgreSQL 16 verifies migration compatibility and concurrent charge adjustments/fill promotion. Lock scoping explicitly avoids PostgreSQL's `FOR UPDATE` nullable outer-join error.

### Release status and caveats
- All broker API responses in tests are mocked. No live Upstox API requests or real orders were sent.
- The coordinator, fill promotion and charge-adjustment services remain unregistered in order routes/workers. Live order submission remains disabled.
- Frontend build/staging, real broker contracts, exchange holiday coverage, operational monitoring, account-level kill switch and broker-error circuit breaker remain outstanding. PR #1 remains draft/open/unmerged; original `Tradepro` untouched.

### Next distinct task
Implement and test the **persisted account-level live kill switch and broker-error circuit breaker**: durable state, fail-closed read behavior, reason/timestamp/audit trail, threshold-triggered circuit trips, manual-reset policy and account-wide scope across portfolios. Keep it unregistered from order submission until separately reviewed; do not merge PR #1 or enable live trading.

This checkpoint supersedes prior notes saying CI for `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` was pending. The latest verified test SHA is `c779f2543ea1f20efbd8b7dca38a9c2aed201749`.


## Latest continuation checkpoint — 18 October 2026: partial-promotion retry

- Latest test/code commit: `1a3475c69d3a93ece7bfad22ace4dce52231bfa1` ([commit](https://github.com/tarunsharma2610-del/tradepro-improved/commit/1a3475c69d3a93ece7bfad22ace4dce52231bfa1)).
- Added an integration scenario using the real child reconciler, broker-trade intake, reconciliation coordinator, fill-promotion service and atomic accounting service. A test estimator fails once for the second chronological fill, then succeeds on retry.
- Expected assertions: first fill is accounted once, later promotion stops at the charge-estimation error, retry treats the first fill as a duplicate and accounts only the remaining fill, with no paper-account changes or broker write calls.
- **Do not claim this test passes until CI for this exact SHA is confirmed.** No local test execution was available in this continuation. Do not create another coordinator or repeat the already implemented preflight coordinator.
- Next action: inspect CI for this exact commit; fix only evidenced failures. If green, review PostgreSQL-backed reconciliation/promotion coverage and release blockers. Keep PR #1 draft/unmerged, live trading disabled, and original `Tradepro` untouched.


## Latest continuation checkpoint — persistent account safety controls

- New service commit: `9ef0ed6e2738ff5fa92b3817deca31b03712de4e`; migration commit: `5b61799efa76f0311174bb130ead4408c8fd4d6c`; idempotency fix: `140da30c93fa8e9e2a44935fce342ab1133eac5e`; tests/refinement latest code SHA: `57939799b7e8b436d5095924b86a89ce380a956e`.
- Implemented `LiveAccountSafetyService` over the already-registered `LiveAccountSafetyState` / `LiveAccountSafetyEvent` models. Added Alembic revision `202610180009` after `202610180008` and unit tests for missing-state denial, initial tripped latch, threshold circuit opening, idempotency, manual reset prerequisites, stale health, and unknown circuit state.
- **No claim of test or migration success yet:** GitHub status/workflow query for latest head `57939799b7e8b436d5095924b86a89ce380a956e` returned no status checks/runs. The backend workflow is configured for pushes to `safety/**`; re-check exact-head Actions results and fix only evidenced failures.
- Service remains intentionally unregistered from order submission. Missing/stale state blocks; new state starts kill-switch tripped; broker successes never auto-close an open circuit; manual reset requires a fresh passing health event, zero consecutive errors and an actor.
- Next: verify pytest plus SQLite/PostgreSQL Alembic upgrade on exact head; then test PostgreSQL concurrency/idempotency for safety-state transitions. Only after review consider a read-only integration into preflight. Never enable order submission, merge PR #1, or modify original `Tradepro`.


### Superseding code-test checkpoint — c97be866828bd47a23f22fc44fac2d3359e70f35

The reset-gate test was corrected in commit `c97be866828bd47a23f22fc44fac2d3359e70f35` so it first records a passing health check while the error counter remains nonzero, then verifies reset is denied for that specific reason. After broker success clears the counter, the test records a new passing health check before successful manual reset. This supersedes the earlier test SHA `57939799b7e8b436d5095924b86a89ce380a956e`. GitHub still returns no status checks or workflow runs for this exact commit; do not claim verification. The next action is to obtain a real backend workflow result for this code SHA.

## Superseding verified checkpoint — 18 October 2026: account-safety PostgreSQL concurrency

- Code/test target SHA: [872eab69082b231117184d80b1bb4a7a96c15b6b](https://github.com/tarunsharma2610-del/tradepro-improved/commit/872eab69082b231117184d80b1bb4a7a96c15b6b). This includes the PostgreSQL account-safety concurrency tests and the workflow change that runs them alongside the existing charge-adjustment concurrency test.
- GitHub Actions [run #608](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39120699215): **success**. Full backend suite: **395 passed, 4 skipped, 1 warning in 29.36s**. SQLite Alembic upgrade passed. PostgreSQL 16 Alembic upgrade passed. Dedicated PostgreSQL integration: **4 passed in 0.44s**.
- PostgreSQL safety coverage now proves: two concurrent submissions with the same broker-error idempotency key count once; two distinct concurrent broker errors serialize and trip the circuit exactly at the configured threshold; concurrent manual resets permit only one reset and preserve the audit trail.
- Migration issue resolved: removed duplicate revision 202610180009_live_account_safety.py; canonical safety migration is 202610180010_live_account_safety.py, chained after 202610180009_live_charge_adjustment_ledger.py. The prior duplicate-revision failure is superseded by successful run #606 and then run #608.
- The account safety service remains unregistered from order submission. These tests use a real PostgreSQL test database and synthetic test users only; no live broker API or order-write endpoint was called. PR #1 remains draft/open/unmerged; original Tradepro remains untouched.
- **Next task:** add read-only preflight composition coverage using the existing LivePreflightCoordinator, AccountWideLiveRiskGate, and persisted LiveAccountSafetyService decision. Fail closed on any denial/error; do not register the composition with order routes/workers or enable live order submission.

## Superseding verified checkpoint — 18 October 2026: safety-aware read-only preflight composition

- Code/test target SHA: [3e73efd441315294970cb652ddeb9b37b00b67b9](https://github.com/tarunsharma2610-del/tradepro-improved/commit/3e73efd441315294970cb652ddeb9b37b00b67b9). The coordinator change is in commit [866336676b24b0da34fe833263b0f2c33204bf17](https://github.com/tarunsharma2610-del/tradepro-improved/commit/866336676b24b0da34fe833263b0f2c33204bf17).
- GitHub Actions [run #611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39121063921): **success**. Full backend suite: **398 passed, 4 skipped, 1 warning in 29.51s**. SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL integration passed (**4 passed in 0.41s**).
- LivePreflightCoordinator now checks the persisted account-wide LiveAccountSafetyService decision after local intent/ownership validation and before credentials or any broker snapshot. Missing safety state, a tripped latch/open circuit, stale health or an unexpected safety-check exception blocks preflight. The service is injectable for testing; default construction uses the same preflight clock.
- Regression tests prove missing state, a tripped latch, and an unexpected safety-check exception all block before any read-only broker call. Existing successful preflight tests explicitly establish a passing health check and manual reset in the test fixture.
- This is read-only preflight composition only. LivePreflightCoordinator remains unregistered from order routes/workers, no broker order-write method is called, live trading remains disabled, PR #1 stays draft/open/unmerged, and the original Tradepro repository remains untouched.
- **Next task:** audit authentication/authorization and operator audit visibility for any future safety-control endpoint. Do not create or wire a control route until that review is complete; keep live order submission disabled.


## Continuation rules — security-control API gate (18 October 2026)

Read [SECURITY_CONTROL_ENDPOINT_AUDIT.md](SECURITY_CONTROL_ENDPOINT_AUDIT.md) before any future safety-control API design. The audit is static review only and identifies missing operator audit visibility, dedicated safety permissions, step-up auth, CSRF/origin policy, atomic state/event persistence, DB-enforced audit immutability, strict metadata redaction and endpoint-level negative tests. Do not create or wire a safety-control endpoint until these are resolved in an explicit design. Next map all manual/strategy/worker/retry/recovery/broker-write paths. Keep PR #1 draft/unmerged, live order submission disabled, and original Tradepro untouched. Update PROGRESS.md, HANDOVER.md, MASTER_ROADMAP.md, AUDIT_REPORT.md, ARCHITECTURE.md, REQUIREMENTS_AUDIT.md and CHANGELOG.md for every verified checkpoint.


## Continuation checkpoint — order-path inventory (18 October 2026)

Read [ORDER_ENTRY_PATH_INVENTORY.md](ORDER_ENTRY_PATH_INVENTORY.md) and [SECURITY_CONTROL_ENDPOINT_AUDIT.md](SECURITY_CONTROL_ENDPOINT_AUDIT.md). Static inventory shows manual and strategy orders use the PAPER-only ExecutionService; the Upstox adapter write primitives exist but no production caller was found in reviewed paths. LiveOrderRecoveryService currently calls LiveExecutionService directly rather than LivePreflightCoordinator, so account-wide safety and fresh snapshot composition is incomplete on that foundation. Do not wire routes/workers or enable live. Next design a single central broker-write service, atomic intent/audit persistence, safety permissions, audit visibility, source-call CI guardrails and endpoint/service negative tests. Preserve original Tradepro unchanged and update all checkpoint docs after verified changes.


## Continuation checkpoint — central broker-write and safety-control design (18 October 2026)

Read `CENTRAL_BROKER_WRITE_BOUNDARY_DESIGN.md` before implementing any broker-write service or safety endpoint. This is a proposed contract only; no API endpoint, adapter wiring, or live order submission was implemented. The design requires one typed `LiveBrokerWriteService` boundary, atomic DB intent+event transactions before external calls, explicit unknown-outcome recovery, least-privilege permissions, recent-MFA step-up for reset, CSRF/Origin controls, tenant-scoped audit reads, PostgreSQL append-only event enforcement, and CI source scanning for unapproved adapter writes. Preserve `TRADING_MODE=PAPER`, `LIVE_ORDER_SUBMISSION_ENABLED=false`, PR #1 draft/unmerged, and original `Tradepro` untouched. Work next through storage/authorization foundations and tests; do not wire live routes until every gate is verified.


### Source-call guard checkpoint — 18 October 2026

Added `backend/scripts/check_broker_write_boundary.py`, tests in `backend/tests/test_broker_write_boundary_guard.py`, and a CI step in `.github/workflows/backend-tests.yml` to reject broker write method references outside the exact future boundary file and low-level adapter definitions. The CI run for this change is pending at checkpoint time. This guard does not implement the broker-write service or make live trading possible; do not widen its allowlist casually.


### Latest guard verification note — 18 October 2026

The AST-based source guard and docstring regression test are committed. Run #617 passed the guard step but the full test suite and database steps are still running: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123311281. Do not report this guard/CI task complete until the entire run succeeds.


### Verified guard CI checkpoint — 18 October 2026

CI run #617 passed on code SHA `bdf208efcc32b44a6367157dd2ab0aab946e6574`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123311281. Guard PASS; backend suite 402 passed / 4 skipped / 1 warning; SQLite and PostgreSQL migrations PASS; PostgreSQL concurrency tests 4 passed. The source guard is in CI, but the actual central writer, safety endpoints, authorization model, event immutability and route/worker wiring remain unfinished. Continue from the storage-hardening step in `CENTRAL_BROKER_WRITE_BOUNDARY_DESIGN.md`; do not enable live orders.


### Current checkpoint — safety-event storage hardening

Read the latest `PROGRESS.md` and `HANDOVER.md` before resuming. Code adds revision `202610180011` for safety-event request fingerprints, unique per-state event versions and SQLite/PostgreSQL triggers that reject audit event updates/deletes. The service now rejects idempotency-key payload mismatches and can reject stale manual-reset expected versions. Regression tests cover audit-write rollback; PostgreSQL integration attempts direct update/delete.

Exact-head CI is not yet verified: run `39124312326` for SHA `2ece7b2f5b85faf4b0bbef55b97d5d0fe4c1e9b3` was pending at this checkpoint. Wait for its final result and inspect every workflow step. Do not claim success from earlier run `39124213016`, which predates the final changes. Next after green CI: review migration/trigger behavior, then implement scoped authorization/MFA/CSRF. Do not wire live orders, enable live mode, merge PR #1, or touch original `Tradepro`.


### Latest CI correction — safety storage

Run #39124312326 failed one new stale-version test because the test retained a mutable ORM object and read its version after a later mutation. Commit `6cd0ced108e35d715359d649a463d80709dd1fb1` snapshots the version before mutation. Latest exact-head run #39124498280 is pending; inspect all steps before claiming success. Do not enable live trading.


### Verified storage checkpoint — 18 October 2026

The previous pending note is superseded by CI run #625, which passed on exact code/test SHA `6cd0ced108e35d715359d649a463d80709dd1fb1`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39124498280. Guard PASS; backend tests 406 passed / 5 skipped / 1 warning; SQLite/PostgreSQL migrations PASS; PostgreSQL integration tests 5 passed including audit immutability. Continue with authorization/MFA/CSRF foundations; do not wire broker writes or enable live mode.


## Authorization foundation continuation rule — 18 October 2026

The current authorization work is partial until all of these are implemented and verified: explicit safety permission grants (is_admin is never a grant), recent-MFA step-up for reset, malformed authentication token normalization, cookie CSRF/Origin enforcement attached to mutations, tenant/account-scoped audit reads, trusted permission provisioning, and negative HTTP tests before registering safety-control routes. Keep the original Tradepro repository untouched, keep the PR draft, do not merge, and keep live order submission disabled. Never claim CI passed unless the exact code/test SHA has a successful run.

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

## Superseding checkpoint — audited safety-permission provisioning (18 October 2026)

- Added `PUT /api/v1/admin/users/{user_id}/safety-permissions` for one explicit grant/revoke operation at a time. The request schema only accepts the four defined `safety.*` scopes; arbitrary scopes are rejected by validation.
- The actor must be a platform admin, must pass the five-minute user-bound password+TOTP step-up, and cookie-authenticated mutations must pass the configured Origin guard. `is_admin` alone is not enough. Self-grants are rejected; revocation remains allowed for an admin's own account to support removal of access.
- Target user's permission list and the audit record (`safety.permission.grant/revoke`, actor ID, target ID and scope) are committed in the same DB transaction. The route does not grant access to read other users' audit data and does not expose the safety status/audit/trip/reset endpoints.
- Added HTTP regression tests for missing step-up denial, self-grant denial, and grant/revoke behavior with audit evidence. **These tests have not been executed in this environment and exact-head CI has not been confirmed.** Treat them as committed, unverified tests, not passing tests.
- Relevant commits: endpoint `ed1cae900a326a4922dbf42a5dbe2b7ed9d50d13`; constrained schema `8a50e8176d25e26a58f52649b21ab01cafa60cad`; test additions `b1b326e7ff409b84d2feab438f69275678939d2f`; formatting follow-up `1d464907a2aec9d0a4e257cb960bf32b24d032ee`.
- Remaining gates: CI on latest code/test SHA, independent review of the permission-provisioning threat model, tenant-scoped audit reads, safety status/audit/trip/reset routes with explicit permission enforcement, state/event atomicity at endpoint level, central broker-write service and end-to-end path enforcement.
- Continue to keep PR #1 draft/open/unmerged and keep live order submission disabled. Phase 2 is incomplete; original `Tradepro` remains untouched.

### Follow-up correction and verification checkpoint (18 October 2026)

- Corrected the safety-permission endpoint import formatting and cleaned test imports after reviewing the committed source through GitHub. Latest test-file commit: `ae46db76e86ea28116bcaf80b9a02c64eb713e9b`; endpoint import correction: `3ef5d32ddeb97ffbd43c61acb74945dd4f564729`.
- The repository connector did not expose a local test runner, and GitHub Actions/combined-status lookups returned no run/status for the latest code/test SHA. Tests remain **unexecuted/unverified**; the older CI run is not evidence for these changes. The next action must be to get CI running on the current branch head and resolve any failures before adding further security-sensitive behavior.
- Phase 2 remains incomplete. Keep PR #1 draft/open/unmerged, preserve PAPER-only defaults and live-order submission disabled, and leave the original `Tradepro` repository untouched.

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
