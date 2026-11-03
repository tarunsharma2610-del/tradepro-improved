## Current verified Phase 4 checkpoint — 3 November 2026

- Repository: `tarunsharma2610-del/tradepro-improved` only; implementation branch: `phase4/operational-alerting`.
- Verified implementation commit: `e4910f3c93d556bf2c7c7d71df4a6b9f045a1f36`.
- Backend CI [#41669605371 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41669605371): **1,650 passed, 8 warnings**; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trips passed; synthetic PostgreSQL/document-volume restore drill passed.
- Security analysis [#41669605381 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41669605381): CodeQL and Python dependency audit passed.
- Durable PAPER stop-event process recovery remains verified by `test_sigkilled_execution_worker_recovers_paper_stop_without_redis`: a separate worker process is killed after the production claim commit; PostgreSQL-only recovery completes the event, rejects the stale token, and leaves one filled PAPER order/execution, a flat position and one cash mutation.
- Host watchdog now enumerates all Compose worker containers with `docker compose ps --all -q worker`, inspects each container, and reports `running`, `degraded`, `down`, or `unknown` fleet state. Tests cover mixed running/stopped replicas, all-stopped replicas, incomplete inspection, and restart-count transitions. These are unit tests with mocked Docker responses; a real Docker Compose multi-container fault drill and Oracle VM installation remain pending.
- PR #12 remains **OPEN, Draft, and unmerged**. No merge or live broker order-write enablement is authorized.
- Safety remains mandatory: PAPER-only; live broker `place_order`, `modify_order`, and `cancel_order` writes disabled; original `tarunsharma2610-del/Tradepro` untouched.
- Remaining Phase 4 gates: real multi-container/replica failure injection; realistic sustained load using full database handler work (not just dispatcher throughput); Oracle VM watchdog installation and failure drill; independent cloud/VM monitoring; final independent security/penetration review. CI is not production-scale performance certification or deployment sign-off.

Historical checkpoint notes below are retained as history; this section supersedes older "next step", test-count, commit, and PR-number summaries.
## Current verified Phase 4 checkpoint — 3 November 2026

- Repository: `tarunsharma2610-del/tradepro-improved` only; implementation branch: `phase4/operational-alerting`.
- Verified implementation commit: `b91a03b7ee70fcf4392bb4c4bcde783185ea1c24`.
- Backend CI [#41667865847 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41667865847): **1,647 passed, 8 warnings**; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trips passed; synthetic PostgreSQL/document-volume restore drill passed.
- Security analysis [#41667865822 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41667865822): CodeQL and Python dependency audit passed.
- New verified fault-injection coverage: `test_sigkilled_execution_worker_recovers_paper_stop_without_redis` starts a separate Python worker process on PostgreSQL 16, waits for the production claim path to commit and enter execution, kills that OS process, and recovers the event from PostgreSQL without Redis redelivery. It verifies a new claim token, rejection of the killed worker's stale token, exactly one filled PAPER order and execution, a flat position, and one cash-balance mutation.
- Existing Redis market-data worker process-kill/restart coverage, concurrent duplicate stop execution, indicator-exit/stop-event race, lease recovery, and database-level replay tests remain in place; this new test fills the distinct stop-execution process-crash gap rather than duplicating them.
- PR #12 remains **OPEN, Draft, and unmerged**. No merge or live broker order-write enablement is authorized.
- Safety remains mandatory: PAPER-only; live broker `place_order`, `modify_order`, and `cancel_order` writes disabled; original `tarunsharma2610-del/Tradepro` untouched.
- Remaining Phase 4 gates: multi-container/replica failure injection; realistic sustained load using full database handler work (not just dispatcher throughput); Oracle VM watchdog installation and failure drill; external VM monitoring; final independent security/penetration review. The current CI suite is not production-scale performance certification or deployment sign-off.

Historical checkpoint notes below are retained as history; this section supersedes their older "next step", test-count, commit, and PR-number summaries.
## Phase 4 concurrency and safety audit update — 3 November 2026

Source review confirms these items are already implemented and covered; do not keep them on the unstarted list:
- PostgreSQL 16 independent-worker race between indicator exit and durable stop-event exit: `test_postgres_indicator_exit_and_stop_event_race_flatten_position_once` in `backend/tests/test_paper_stop_event_execution_postgres_concurrency.py`. It asserts one filled order, one execution, flat non-negative position, and an obsolete stop event when the indicator exit wins.
- Concurrent duplicate stop-event execution by two PostgreSQL workers returns the same filled order and creates one execution.
- Trading mode configuration fails closed unless PAPER: `backend/tests/test_trading_mode_safety.py`.
- Broker write boundary AST guard rejects direct/dynamic `place_order`, `modify_order`, and `cancel_order` bypasses: `backend/tests/test_broker_write_boundary_guard.py`.
- Existing owner-scoped API isolation tests cover portfolios, broker allocations/snapshots, reconciliation and broker evidence.

Remaining work is narrower: verify CI actually ran the PostgreSQL 16 tests in the relevant workflow (not merely that test code exists); complete an adversarial review of mode switching and every API/worker boundary; continue crash-window/multi-replica coverage outside the already-tested races; review alerting and sustained-load evidence. Runtime configuration remains PAPER-only and live broker writes disabled.

Verified code checkpoint for these tests: `215650c3b059f9aabee307ac1665d6a7549d29e5` (Backend #41638885400 and Security #41638885315 passed). Latest docs checkpoint before this note: `4b9f10e2c41bc296ee45f9db7eb6e10b162e7db2` (Backend #41639526130 and Security #41639526161 passed). This note itself requires exact-head CI before it becomes a new docs checkpoint.

---

## Phase 4 latest verified recovery checkpoint — 3 November 2026

- Verified implementation: `2ee2939969b9679dda859086278ef07c4355d173`; Backend #41610938641 and Security #41610938496 both passed on this exact commit.
- Backend: 1,631 passed, 8 warnings; broker-write boundary guard, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore drill and evidence retention passed.
- Verified recovery coverage already present: real Redis 7 connection loss/re-subscription; real Redis server-process restart with volatile snapshot/version loss, fresh epoch/version reset and stale-quote rejection; multi-process publisher/consumer; four-process 400-quote load; bounded queue saturation and authoritative-snapshot retry; worker cancellation/release and supervised PAPER fill/ledger acceptance with duplicate-delivery idempotency.
- These tests are bounded integration/stress checks, not production-scale performance certification or proof of deployment readiness.
- Latest documentation synchronization: `61792d6649351a68f68da49aa2494f3656717ba1`; Backend #41611831152 and Security #41611831095 passed on that exact documentation commit.
- Next engineering review: inspect the worker's exhausted-retry recovery callback and its coupling to scanner high-water reset / authoritative Redis snapshot replay; add a focused regression only if a concrete uncovered failure mode is found. Then update the checkpoint documents and verify their exact-head CI.
- Safety remains mandatory: PAPER only; live broker order writes disabled; PR #9 OPEN, Draft, unmerged; only `tradepro-improved` in scope; original `Tradepro` untouched.

---

## Latest Phase 4 operational observability checkpoint — 3 November 2026

This update supersedes earlier "next step" and latest-head summaries in this document.

- Repository: `tarunsharma2610-del/tradepro-improved` only. Branch: `phase4/redis-market-data-publisher`. PR #9 remains OPEN, Draft, and unmerged.
- Verified implementation commit: `d5f4a3f2bea7f6c086d163a10765d46fe1391a61`.
- Backend PR CI [#41593091254 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41593091254) on the exact commit: full pytest, broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore and evidence retention passed.
- Security PR CI [#41593091256 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41593091256) on the exact commit: CodeQL and Python dependency vulnerability audit passed. Push-triggered Security [#41593085684 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41593085684) also passed on the same SHA.
- Earlier observability work remains verified at `b932ed039f9c2ab51347e3938fad31510ac8e9ac`: fixed process-local PAPER counters for dispatcher accept/coalesce/drop/reject/process/failure/exhaustion and admin-only `GET /api/v1/admin/market-data-metrics`.
- Hardening in `d5f4a3f`: metric names restricted to a fixed seven-counter allowlist; zero-initialized snapshots; tests for arbitrary-name rejection, actual HTTP endpoint authorization (401 unauthenticated / 403 non-admin / 200 admin), aggregate-only payload and no user/instrument identifiers.
- CI also revalidated the dependency-aware `/ready` endpoint and the bounded 512-instrument / 64-slot dispatcher burst regression from earlier commits in the same branch history.
- Metrics remain explicitly PROCESS-LOCAL, not fleet-wide. No Prometheus/Redis aggregation or production alerting is claimed. Do not treat a single replica's counters as system-wide totals.
- Next work, in order: design safe multi-replica aggregation and scrape identity; add queue saturation / worker failure thresholds; run reproducible sustained-load and restart-recovery tests; complete API authorization and cross-user isolation review; synchronize documentation and verify exact docs commit CI.
- Safety: PAPER mandatory; live broker `place_order`, `modify_order`, `cancel_order` writes remain disabled. No deployment, LIVE readiness or production restore is claimed. Original `tarunsharma2610-del/Tradepro` remains out of scope and unmodified.

---

# Phase 4 Security Audit Status — 2 November 2026

## Executive status

NOT COMPLETE.

The project has an existing Phase 4 static baseline audit and several automated security controls. It does not yet have a comprehensive, independently verified Phase 4 security assessment or production penetration-test result. Do not claim that Tradepro Improved is penetration-tested, fully secure or approved for LIVE order execution.

## Scope

- Repository: tarunsharma2610-del/tradepro-improved
- Branch: phase4/redis-market-data-publisher
- PR #9: OPEN, Draft, unmerged.
- Audited checkpoint: implementation/test head 654b0a5d2cb898a0b6dcd4dcb6556b0af6c2ccc2, exact-head Backend CI #41398555424 PASSED.
- Original tarunsharma2610-del/Tradepro is out of scope and was not modified.

## Existing audit and verified controls

1. PHASE4_P0_BASELINE_AUDIT.md exists from 29 October 2026. It is a static source/workflow inspection and explicitly records that runtime tests and credentialed smoke tests were not executed as part of that audit.
2. Backend CI enforces the AST broker-write boundary and includes backend tests, SQLite/PostgreSQL 16 migration round-trips and synthetic restore checks.
3. Portfolio routes use authenticated ownership checks; LIVE funds/positions/holdings reads are bound to the currently allocated broker connection and immutable user/portfolio snapshots.
4. PAPER/LIVE analytics and portfolio mode constraints have regression coverage. The LIVE positions route fails closed rather than exposing PAPER position rows.
5. Upstox Analytics Token handling has encrypted storage, owner access and expiry checks. Do not log or expose access tokens.
6. Redis quote snapshots/notifications are user-scoped and validated for schema, epoch/version, TTL and timestamps. Consumers fail closed on stale/missing data and Redis outage.
7. LIVE unrealized P&L is a read-only endpoint; it checks owner, LIVE mode, current allocation and position-snapshot freshness (120 seconds), and uses quote freshness (15 seconds). It does not mutate accounting or submit broker orders.
8. PostgreSQL 16 multi-worker concurrency, stop-event idempotency/lease/recovery and migration/restore checks have prior green CI evidence.
9. Latest relevant code/test CI: #41398555424 PASSED on exact head 654b0a5d2cb898a0b6dcd4dcb6556b0af6c2ccc2; stale snapshot implementation CI #41398528946 also passed.

## Findings and limitations

- The existing P0 baseline audit is static; it is not a penetration test.
- The AST broker-write guard is defense-in-depth, not a formal proof against every dynamic/reflection path.
- Green CI proves only the automated checks included in the workflow; it does not prove production security, broker-provider correctness, sustained load capacity or Oracle production recovery.
- No verified current report was found for a full endpoint-by-endpoint IDOR/authorization attack sweep, SAST, DAST, dependency vulnerability scan, authenticated penetration test, independent red-team test or production configuration review.
- No credentialed Upstox smoke test or production deployment is claimed.
- PAPER is the only enabled execution path. LIVE broker place_order, modify_order, and cancel_order writes remain disabled.

## Required security work

| Priority | Work | Acceptance evidence |
|---|---|---|
| P0 | Enumerate every authenticated API and test owner/tenant/mode authorization, including IDOR and cross-user object references | Automated negative tests for every resource family; no cross-tenant data leakage |
| P0 | Trace all broker order-write call paths, including indirect/dynamic dispatch, and prove PAPER cannot reach a live write | AST guard plus targeted call-graph/adversarial tests; deny-by-default live gateway |
| P0 | Review token encryption, access control, expiry, refresh, logs, exceptions and secret redaction | Tests and code-review checklist; no token/secret leakage |
| P1 | Dependency vulnerability scanning and SAST | Saved scan report, reviewed findings, remediation or documented accepted risk |
| P1 | DAST against isolated non-production deployment | Authenticated and unauthenticated scan report; triaged findings |
| P1 | Abuse/rate-limit, replay, CSRF/CORS, session and authentication tests | Repeatable security tests and documented configuration |
| P1 | Redis/PostgreSQL tenant isolation and concurrency under adversarial workloads | Multi-user race and load test report |
| P2 | Deployment hardening, static IP, TLS, least privilege, firewall, backups, alerting and incident response | Deployment checklist and operational runbook |
| P2 | Independent penetration test before any LIVE broker write enablement | Signed/dated report and closure of critical/high findings |

## Next sequence

1. Complete the documentation synchronization and pass exact-head Backend CI.
2. Build the endpoint authorization/IDOR matrix and add missing negative tests.
3. Add automated dependency and SAST scans to CI, then review findings.
4. Add DAST to a safe non-production deployment when available.
5. Complete secret-handling, rate-limit and broker-write reachability review.
6. Conduct independent penetration testing before any LIVE order-write authorization.
7. Keep PAPER-only execution and PR #9 Draft/unmerged until explicitly authorized.

## Safeguards

- Modify only tarunsharma2610-del/tradepro-improved; original Tradepro remains untouched.
- PAPER execution only; LIVE broker order writes disabled.
- PR #9 remains Draft/open/unmerged.
- No production deployment, credentialed broker test or LIVE gateway activation is authorized by this audit.



## Phase 4 security remediation checkpoint — 2 November 2026
This is the latest security/code checkpoint and supersedes older Phase 4 security next-step statements where they conflict.
- Latest verified code/test head: 2a98a07a8516c4cca4a46f8a0f511afcb2159e74.
- Exact-head Backend CI #41400727799 PASSED: 1,549 passed, 1 warning. Full workflow includes pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore and evidence retention.
- Confirmed finding fixed: Redis-backed rate limits previously failed open on Redis errors. The limiter now returns HTTP 503 when Redis is unavailable; test now asserts fail-closed behavior. Commits 62b7bdbdde812ed89d9eb3189b44c7922a7e63d7 and fdd00da6cd58242e2fe0cbf720f9cd66ee306ff8.
- Confirmed finding fixed: MFA disable previously required only an authenticated session. It now requires password re-verification and, when MFA is enabled, a current TOTP. Schema/service/API/tests are in 19a99b8, c369bb0, e6306be and 2a98a07. Exact-head CI above verifies the complete change.
- The Phase 4 P0 baseline audit exists but was a static source/workflow review, not a penetration test. These two findings are remediated; comprehensive security assessment remains NOT COMPLETE.
- Remaining security work: endpoint-by-endpoint IDOR/authorization matrix and adversarial tests; secret/token redaction/storage review; dependency vulnerability scan and SAST; DAST against isolated staging; broker-write reachability review; abuse/rate-limit and replay testing; tenant-isolation/load testing; deployment/backup/incident-response review; independent penetration test before any LIVE broker write.
- Other Phase 4 gates remain: authenticated LIVE P&L API against real Redis integration test; internal realized-P&L ledger and broker fill reconciliation; frontend LIVE read-only P&L; full Redis-to-PAPER-stop-to-ledger end-to-end proof; multi-user load/backpressure and operational runbooks.
- PAPER execution only; LIVE broker place/modify/cancel writes disabled; PR #9 remains Draft/open/unmerged; original Tradepro remains untouched. No deployment or LIVE gateway activation authorized.


## Phase 4 authoritative audit synchronization — 2 November 2026

This is the current operational status; earlier entries remain historical.
- Repository `tarunsharma2610-del/tradepro-improved` only; branch `phase4/redis-market-data-publisher`; PR #9 targets `phase4/roadmap-progress-checkpoints`, OPEN/Draft/unmerged.
- Code/test head before this docs sync: `3ad06a045c16251b6daf1e2ec429837ddd390c59`; exact-head Backend CI #41402165142 PASSED: **1,550 passed, 1 warning**. Redis-backed pytest, broker-write guard, SQLite/PostgreSQL 16 migration round-trips, synthetic restore/evidence retention passed.
- New verified milestone: authenticated LIVE unrealized-P&L API test publishes a real user-scoped Redis quote and validates API P&L ₹40.00; accounting remains unchanged.
- Rate limiting now fails closed (HTTP 503) on Redis outage; MFA disable requires password re-verification and current TOTP when MFA is enabled. CI #41400727799 passed these remediations.
- Security audit status: **NOT COMPLETE**. Static baseline is not a penetration test. Remaining: endpoint IDOR/authorization matrix, cross-tenant adversarial tests, secret/token redaction, SAST/dependency scan, DAST, broker-write reachability, abuse/load tests, deployment hardening and independent penetration test.
- Remaining engineering: internal realized-P&L ledger/broker-fill reconciliation; frontend LIVE read-only P&L; Redis→scanner→dispatcher→durable PAPER stop→ledger end-to-end acceptance; multi-user load/backpressure, observability/runbooks; credentialed Upstox smoke test and production Oracle restore.
- PAPER remains the only enabled execution path; LIVE `place_order`, `modify_order`, `cancel_order` writes disabled. PR #9 stays Draft/unmerged. Original `tarunsharma2610-del/Tradepro` untouched.
- Documentation sync is not green until Backend CI passes on the final documentation head.


## Cross-tenant security regression checkpoint — 2 November 2026

- Added authenticated two-user regression coverage for unauthorized contract-note upload/download, source-component create/review/reject, reconciliation run/issue access, and broker-settings connection scoping. Foreign broker-connection identifiers must not expose or mutate another user's data.
- Exact PR-head Backend CI [#41404633900 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41404633900) on `e8f8783fc32a96e43e710289721992e077dc4d82`; PR #9 head matches this SHA. Pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic restore and evidence retention all passed.
- This verifies the new regression coverage, not a complete IDOR sweep or penetration test. Comprehensive security assessment remains NOT COMPLETE.
- Remaining security gates: endpoint authorization matrix, secret/token redaction/storage review, dependency scan/SAST, isolated-staging DAST, broker-write reachability, abuse/load tests, deployment/incident-response review and independent penetration test.
- PAPER mandatory; LIVE broker place/modify/cancel writes disabled; PR #9 OPEN/Draft/unmerged; original `tarunsharma2610-del/Tradepro` out of scope.


## Security scanning and dependency remediation checkpoint — 2 November 2026

- Added GitHub Actions workflow `.github/workflows/security-analysis.yml` with CodeQL Python static analysis and `pip-audit` over backend requirements. CodeQL [#41406851928](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41406851928) and dependency audit [#41406857558](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41406857558) passed on exact commit `8be6a0369c81a519c00712d69095b2ab3ceb5faa`; dependency audit reported zero known vulnerabilities for resolved backend dependencies.
- Remediated vulnerable Starlette `0.46.2` resolution by upgrading FastAPI to compatible `0.143.x`; CI resolved FastAPI `0.143.5` and Starlette `1.10.0`. Full backend compatibility verified, not assumed.
- Backend CI [#41406857547 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41406857547) on same SHA; pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore/evidence retention passed.
- Security audit remains incomplete: these checks do not replace endpoint IDOR coverage, secret/token redaction review, DAST, broker-write reachability, abuse/load testing, deployment hardening or independent penetration testing.
- Prior rate-limit fail-closed, MFA step-up and cross-tenant contract-note/reconciliation protections remain in place. PAPER mandatory; LIVE order writes disabled; PR #9 OPEN/Draft/unmerged; original Tradepro repository out of scope.


## Authentication hardening and security verification — 2 November 2026

- Hardened JWT creation: optional extra claims can no longer override reserved `sub`, `type`, `iat`, or `exp` claims. Added regression tests for each reserved claim and a positive test for non-reserved claims.
- Corrected stale rate-limiter documentation: Redis outage behavior is fail-closed with HTTP 503; it is not fail-open.
- Exact code commit verified: `4ebc24c0ae129cf53614cd58c46c41cc55a204ab`. Backend CI [#41408254466 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41408254466); CodeQL and Python dependency audit [#41408254462 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41408254462). All three checks passed on the same SHA.
- Dependency audit reported zero known vulnerabilities for resolved backend dependencies. Security assessment remains INCOMPLETE: remaining work includes endpoint IDOR matrix, secret/token redaction and storage review, staging DAST, broker-write reachability, abuse/load tests, deployment hardening and independent penetration testing.
- PAPER mandatory; LIVE broker place/modify/cancel writes disabled; PR #9 OPEN/Draft/unmerged; original `tarunsharma2610-del/Tradepro` strictly out of scope.


## Production bootstrap secret hardening — verified code checkpoint, 2 November 2026

- Production configuration now fails closed unless an explicit stable `SECRET_KEY` (minimum 32 characters) and `MASTER_ENCRYPTION_KEY` are configured. Development retains its local random fallback. Regression tests cover missing secrets, valid production configuration and development fallback.
- Verified code/test commit: `d6619a58cd585ef35b79126d866c90bb903cb890`. Backend CI [#41410058905](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41410058905) and Security analysis [#41410058894](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41410058894) passed on that exact SHA. Security workflow includes CodeQL and pip-audit; this is not a penetration-test claim.
- Earlier JWT reserved-claim hardening remains verified on `4ebc24c0ae129cf53614cd58c46c41cc55a204ab`: Backend CI #41408254466 and Security analysis #41408254462 passed on that exact SHA. Redis rate limiting remains fail-closed (HTTP 503) on Redis failure; MFA disable requires password re-verification and current TOTP when MFA is enabled.
- This is part of the exact 28-document maintained set from the JWT checkpoint. Current documentation head before this batch: `4083cb6dfd382f0dfe5802a1ebc1dbcf3beea873`. The resulting documentation commit requires exact-head Backend CI and Security analysis before it is called green.
- Security assessment remains INCOMPLETE: HTTPS/production CORS, secret rotation and recovery, authentication-session controls, endpoint-by-endpoint authorization/IDOR, secret/token storage and redaction, broker-write reachability, isolated-staging DAST, abuse/load testing, deployment/incident response and independent penetration testing remain open.
- Safeguards unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` untouched; PAPER mandatory for development/tests/unverified workflows; LIVE broker `place_order`, `modify_order`, `cancel_order` writes disabled; PR #9 remains OPEN/Draft/unmerged; no deployment or LIVE gateway activation authorized.


## Authoritative session-security and key-rotation checkpoint — 2 November 2026, 19:59 IST

- Repository: `tarunsharma2610-del/tradepro-improved` only. PR #9 remains OPEN, Draft and unmerged; head branch `phase4/redis-market-data-publisher`, base `phase4/roadmap-progress-checkpoints`. Original `tarunsharma2610-del/Tradepro` remains out of scope.
- **Exact PR head verified:** `77f44c7299f5e7157a4cdb2f8dfe7fbbfb6c08c6`.
- **Backend CI #41460334989 — SUCCESS** on that exact PR head. **Security analysis #41460334979 — SUCCESS** on that exact PR head. Security analysis includes CodeQL and Python dependency audit; successful automation is not a penetration-test result.
- Session persistence/authentication work includes the `auth_sessions` migration (`202611020044_auth_sessions.py`), persisted-session authorization, refresh-token rotation/replay rejection, logout revocation, and dedicated JWT session/token identifiers. Reserved `sid`/`jti` values are passed through dedicated parameters and cannot be overwritten through extra claims. API test fixtures now create persisted sessions rather than bypassing the authorization dependency.
- Added an end-to-end auth regression: login → refresh rotates the refresh token → replay of the old refresh token returns 401 → logout revokes the persisted session → reuse of the prior access token returns 401. This is covered on the verified PR head.
- Transactional encryption-key rotation service is present for encrypted broker API credentials, OAuth access tokens, Upstox Analytics Tokens, platform settings and MFA secrets. It fails closed on unreadable ciphertext and leaves transaction commit/rollback to the caller. Code/test commit `960c099b53d4c8e41daeb4f5691bc0972d5fb7b2`; Backend CI #41456734039 and Security analysis #41456734074 passed on that implementation commit. **No production database, production key or production ciphertext was rotated or accessed.**
- Earlier HTTPS/CORS correction commit `39899ea17f4370549a12fc6424ba85c79dcbb748`: Backend CI #41455950986 and Security analysis #41455951065 passed.
- Documentation files were stale and contained older checkpoint dates/heads. This update is being applied to the maintained project documents. **The resulting documentation commit(s) still require exact-head Backend CI and Security analysis; do not call the docs checkpoint green until both pass on the final documentation head.**
- Remaining security work is not complete: endpoint-by-endpoint authorization/IDOR matrix and adversarial tests; secret/token storage and redaction review; broker-write reachability audit; staging DAST; abuse/load and tenant-isolation tests; deployment hardening, backup/restore and incident-response evidence; independent penetration testing before any LIVE order-write enablement.
- Remaining Phase 4 engineering: full Redis snapshot → scanner → dispatcher → durable stop-event → PAPER ledger/position end-to-end proof; multi-process/multi-replica crash-window races (especially indicator exits versus stop-event exits); PAPER/LIVE data and API/UI isolation; operational observability, alerting and sustained load/backpressure testing.
- Safety invariants: PAPER mandatory for development/tests/CI/demos/unverified workflows; LIVE broker `place_order`, `modify_order`, and `cancel_order` writes remain disabled; no live broker smoke test or production deployment is claimed; PR #9 stays Draft/unmerged; do not update `main`; original Tradepro repository untouched.


## API authorization and cross-tenant audit — 2 November 2026

### Scope and reviewed route inventory

Static review covered the 13 routers registered by `backend/app/api/v1/router.py`, comprising 86 versioned route handlers across auth, users, settings, portfolios, strategies, backtests, market data, broker-charge evidence, reconciliation, Upstox charges, news, instruments and admin. Also reviewed the session dependency, portfolio/strategy ownership helpers, broker credential service, market-data subscription service, and representative HTTP authorization/isolation tests.

### Controls confirmed in the reviewed code

- Access-token requests require a valid JWT access type, UUID subject and session ID, an active user, and a persisted session belonging to that user that is neither revoked nor expired.
- Portfolio child routes use authenticated-user portfolio lookup before reading or mutating positions, orders, executions, analytics, broker snapshots or strategies. Strategy access additionally binds the strategy to the requested portfolio.
- Broker credential reads/writes and Analytics Token operations are passed the authenticated user ID; broker connection allocation and snapshot routes additionally constrain connection and allocation rows by that user.
- Market-data stream state is keyed by authenticated user ID; subscription persistence scopes queries by both user ID and that user's broker connection.
- Backtest repository access is scoped by user ID. Reconciliation list services receive the authenticated user ID. Broker-charge evidence lookup binds evidence to a broker connection owned by the user; cross-user contract-note/component/reconciliation regression coverage is recorded in the prior checkpoint.
- Platform settings, admin statistics, news-source management/ingestion and instrument seed/sync routes use the administrator dependency. Regular-user denial is covered by HTTP tests.
- Existing two-user HTTP regressions cover portfolio, order, strategy and backtest isolation; the contract-note and reconciliation cross-tenant regression checkpoint is recorded above in this file.

### Public routes and operational review

- Registration, login, logout and refresh are intentionally callable without an existing access session; MFA enrollment/verification/disable require the authenticated-user dependency.
- `GET /health`, `GET /` and instrument catalog search are currently public by design/code shape. Instrument search exposes catalog data rather than user records. Confirm whether FastAPI OpenAPI/docs endpoints should be disabled or access-restricted in production deployment; this static review does not establish their production network exposure.
- No confirmed cross-tenant read/write path was identified in the reviewed handler/service paths. This is a bounded static review, not proof that all authorization paths are correct.

### Remaining adversarial verification — OPEN

- Add/confirm two-user HTTP tests for broker credential and Analytics Token isolation, OAuth state user/connection binding and replay, market-data stream/subscription isolation, MFA step-up/session revocation, and admin-only news/instrument operations.
- Review every child-resource repository/service query and response schema for indirect identifiers, nested relationships, exports and error side channels.
- Verify public docs/OpenAPI exposure and production proxy/network access; run authenticated and unauthenticated DAST against an isolated staging deployment.
- Continue secret/token log redaction review, broker-write reachability analysis, abuse/load testing, tenant-isolation testing, deployment/restore/incident-response review and independent penetration testing.

**Status: PARTIAL — no blanket security sign-off.** Backend CI #41464532786 and Security analysis #41464532390 passed on the pre-audit documentation head `0ed82cca3c7b0b66087a133230db07764ad903fc`. This audit documentation update requires its own exact-head CI. PAPER mandatory; LIVE broker order writes disabled; PR #9 remains OPEN/Draft/unmerged; original `tarunsharma2610-del/Tradepro` untouched.


## Broker credential/API isolation regression — verified 2 November 2026

- Added HTTP-level two-user regression `test_broker_credentials_and_analytics_tokens_are_isolated_between_users` in `backend/tests/test_api_authorization.py`.
- Test covers User A saving broker credentials and an Upstox Analytics Token; User B sees an empty broker-connection list and an unconfigured token status, cannot delete User A's broker connection or token, and receives no plaintext secret/token in responses.
- Exact test commit: `05f25067fc4a3d2e3e3fdb251aba859b3e668ad5`. Backend CI #41467643061 — SUCCESS; Security analysis #41467643224 — SUCCESS, both on that exact commit. Backend run passed pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore and evidence retention.
- This closes the specifically identified broker credential/Analytics Token API regression gap; it does not complete the full endpoint IDOR sweep, CSRF review, DAST, broker-write reachability audit or penetration testing.
- Current PR #9 remains OPEN/Draft/unmerged; PAPER mandatory; LIVE broker order writes disabled; original `tarunsharma2610-del/Tradepro` untouched.


## Phase 4 dispatcher integration correction — 2 November 2026 (exact-head CI verified)

- Corrective test commit: `4aba13642f1f3bcb4e11f5c6b5def7433e687ca7`. The Redis-to-scanner dispatcher integration test retrieves and acknowledges the dispatcher item in the same asyncio task, preserving task-scoped ownership; production safeguards were not weakened.
- Exact-head Backend CI [#41471120955 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41471120955). Redis setup, full backend pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention all passed.
- Exact-head Security analysis [#41471120975 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41471120975): CodeQL and Python dependency vulnerability audit passed. These are not DAST or penetration-test sign-offs.
- Remaining Phase 4 gates: full Redis → scanner → dispatcher → durable PAPER stop-event → execution → final position/ledger proof; duplicate/out-of-order quote tests; worker crash/cancellation/recovery; concurrent PAPER exits; multi-process load/backpressure; observability/runbooks; production restore evidence.
- Security assessment remains incomplete: full IDOR/authorization matrix, secret/token redaction, broker-write reachability, isolated-staging DAST, abuse/load and tenant-isolation testing, deployment/incident response and independent penetration testing.
- Safeguards: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PAPER mandatory; LIVE broker `place_order`, `modify_order`, `cancel_order` disabled; PR #9 OPEN/Draft/unmerged; no merge/deployment/LIVE activation.


## Phase 4 verification update — 2 November 2026

- Verified code/test head: `4c5b598272e6d99bfb56595eb9d0aad9652e56d8`.
- Exact-head Backend pytest #41482453315: SUCCESS.
- Exact-head CodeQL and dependency audit #41482453362: SUCCESS.
- Dispatcher and Redis coverage includes duplicate/out-of-order quote rejection, bounded queue overflow/backpressure, single-flight processing, cancellation/retry, Redis Pub/Sub reconnect, independent consumer recovery, and real Redis process restart recovery.
- PAPER stop-event coverage includes durable claim retry, crash-after-claim database recovery, stale-token fencing, concurrent PostgreSQL claim/reclaim races, retry exhaustion, and concurrent duplicate PAPER execution with one order/fill.
- These are automated regression tests; they do not constitute production load certification or broker live-order validation.
- Safety invariants unchanged: PAPER mandatory; LIVE broker place/modify/cancel writes disabled; original `tarunsharma2610-del/Tradepro` out of scope; PR #9 remains Draft and unmerged.
- This documentation synchronization is not a green checkpoint until Backend CI, CodeQL, and dependency audit pass on the resulting exact documentation commit.


## Phase 4 authoritative resume checkpoint — 2 November 2026, 23:06 IST

Latest verified implementation head: `29d165395259a73f819bf22327a44e0fe06f1600`. Backend tests [#41492213645](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41492213645) and Security analysis [#41492213677](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41492213677) both PASSED on this exact head. Nifty 500 dated membership snapshots, mapping and admin import are implemented; the active 500-member snapshot now feeds an authenticated Upstox LTPC subscription endpoint with durable desired-state persistence. Remaining: scanner quote ordering/staleness and subscription lifecycle; scanner filters/ranking; full Redis→scanner→dispatcher→durable PAPER stop→execution→ledger proof; multi-process recovery/concurrent exits; realized-P&L reconciliation and read-only UI; load/observability; IDOR/secret/DAST/broker-write reachability/independent penetration test. Next: verify final documentation commit's exact-head CI, then quote-integrity tests and scanner integration. Security audit is NOT COMPLETE. PR #9 Draft/unmerged; original Tradepro untouched; PAPER mandatory; LIVE order writes disabled.


## Latest verified Phase 4 checkpoint — 3 November 2026 (multi-worker metrics hardening)

- Repository: `tarunsharma2610-del/tradepro-improved` only. Branch: `phase4/redis-market-data-publisher`. PR #9 remains OPEN, Draft and unmerged.
- Exact implementation/test head: `15141cdf437419afa2c89ad1f911d4ba863f6ccf`.
- Backend CI [#41597941401 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41597941401): **1,626 passed, 8 warnings**. Broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore drill, and evidence retention passed.
- Security analysis [#41597941400 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41597941400): CodeQL and Python dependency audit passed.
- Metrics correction verified: independent per-worker counter state; atomic, retry-protected Redis aggregation; expiring Redis heartbeat scores with a 60-second activity window; stale-worker removal; admin metrics regression test models the production Redis time/zset interface.
- This does not claim Prometheus integration, production alerting, sustained-load acceptance, deployment readiness, or Phase 4 completion.
- Remaining Phase 4 gates: end-to-end Redis snapshot recovery → scanner/dispatcher → durable stop-event intake → final PAPER ledger/position acceptance; more multi-process/crash-window races; PAPER/LIVE isolation audit; security/authorization/secret-redaction review; sustained-load and backpressure testing; exact-head documentation CI.
- Safety: PAPER mandatory; live broker `place_order`, `modify_order`, `cancel_order` writes disabled; PR #9 Draft/unmerged; no merge/deployment/LIVE activation; original `Tradepro` repository untouched.


## Latest sustained-load and alerting checkpoint — 3 November 2026

- Exact verified benchmark head: `edec040c5bb43ea572419345c5ecd50b76ab1c86` on Draft PR #10.
- Backend CI #41645265983: SUCCESS on this exact head; 1,632 passed, 8 warnings; broker-write boundary guard passed.
- Security CI #41645266170: SUCCESS on this exact head; CodeQL and dependency audit passed.
- Concurrent synthetic PAPER dispatcher smoke test: 5,000 observations, 8 workers, queue capacity 512, 112,920.26 observations/second, p50 3.2393 ms, p95 4.3143 ms, p99 4.4683 ms; 21 bounded-queue rejections were retried and all observations were processed. This is an in-process CI smoke benchmark, not production or end-to-end capacity evidence.
- Full measurements and limitations: `PHASE4_SUSTAINED_LOAD_REPORT.md`.
- Alerting is NOT implemented. Compose currently has PostgreSQL, Redis, backend, worker, frontend and Nginx, but no independent Prometheus/Alertmanager/notification service. Proposed thresholds are design candidates only, not approved production settings.
- Remaining: independent alert delivery/failure recovery; endpoint-by-endpoint IDOR/cross-user authorization review; realistic sustained-load and multi-replica crash-window testing; final documentation synchronization and exact-head CI.
- Safety unchanged: PAPER mandatory; live broker order writes disabled; PR #9 and #10 Draft/unmerged; only `tradepro-improved`; original `Tradepro` untouched.


## Endpoint authorization and PAPER/LIVE audit addendum — 3 November 2026

### Scope and inspected routes

Source-reviewed the versioned API routers for portfolios, strategies, backtests, broker charge evidence, reconciliation, settings, users, and Upstox charge APIs. The review focused on authentication dependencies, owner scoping, child-resource lookups, admin-only operations, and execution-mode checks.

### Verified safeguards in source and existing regression tests

- Portfolio lookup is scoped through `PortfolioRepository.get_for_user(user.id, portfolio_id)`; child position/order/execution and broker snapshot reads occur only after the portfolio ownership check.
- Strategy routes first verify portfolio ownership; strategy reads/updates/deletes/evaluation are constrained to the route's portfolio. Activation also verifies PAPER mode.
- Backtest list/get/trades/delete operations use user-scoped repository methods.
- Broker connection and Analytics Token settings are user-scoped; credential/token values are not returned in API responses.
- Broker charge evidence is joined to the owning broker connection; cross-user access returns not found. Cross-user review is restricted to platform admins, and review also requires a different reviewer from the extractor.
- Reconciliation queries are filtered by the authenticated user's ID.
- Platform settings require the admin dependency.
- Upstox charge operations resolve the connected token through the authenticated user's broker connection.
- Existing API isolation tests cover cross-user portfolio, strategy, backtest, pending-order cancellation, broker evidence/reconciliation, broker credentials/tokens, market-data stream state, and OAuth callback state.
- Existing PAPER/LIVE tests verify immutable trading mode, LIVE order rejection before broker access, LIVE strategy activation denial, fail-closed LIVE positions/balances, and broker allocation constraints.

### MFA defect fixed in separate Draft PR #11

Source review found `mfa_verify` and `mfa_disable` called `response.delete_cookie` without accepting FastAPI's `Response` parameter. The route signatures now inject `Response`, and HTTP-level tests cover cookie clearing after MFA enable and disable.

- PR #11 head: `c11dc9de719a3fb417a0c9760b2cff944aed4d7a`.
- Backend CI #41646429604: SUCCESS; 1,633 tests passed, 8 warnings; broker-write boundary guard passed.
- Security CI #41646429541: SUCCESS; CodeQL and dependency audit passed.
- PR #11 remains Draft and unmerged.

### Audit limits / remaining review

This is a focused source-and-regression-test review, not a formal penetration test, independent security assessment, or certification. It does not establish that every deployment secret, reverse-proxy rule, cloud IAM policy, network ACL, database role, backup, or runtime host is correctly configured. Continue testing authorization against deployed PostgreSQL and multi-user sessions, review rate limits and file upload/storage boundaries, and run independent security testing before any public or LIVE use.

### Safety

PAPER remains mandatory. Live broker `place_order`, `modify_order`, and `cancel_order` writes remain disabled. PRs #9, #10, and #11 remain Draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` is untouched.


## MFA factor replacement hardening — 3 November 2026

A deeper authentication review found that an authenticated user could call MFA enrollment while MFA was already enabled; the service would overwrite the stored encrypted secret without verifying the existing factor. This could permit replacement of an active factor from a compromised authenticated session.

### Correction submitted in Draft PR #11

- `AuthService.start_mfa_enrollment` now rejects replacement when `user.mfa_enabled` is true.
- The API maps the service rejection to HTTP 409 Conflict.
- Existing-factor replacement requires the user to prove the current factor through the password + TOTP disable flow before enrolling again.
- Added service-level regression coverage proving the encrypted original secret is unchanged.
- Added HTTP regression coverage proving an authenticated session cannot replace an already-enabled factor without disabling it through the protected flow.

Latest PR #11 head: `8061500a90ec4a3aeaa52cce51f850773ef0414e`. New backend and security CI are running; do not transfer the previous head's green status to this commit. Previous exact-head verification at `c11dc9de719a3fb417a0c9760b2cff944aed4d7a` passed (1,633 backend tests, 8 warnings; CodeQL and dependency audit passed), but is superseded by the new factor-replacement hardening commit.

### Remaining MFA review

Review enrollment pending-state expiry, TOTP attempt throttling, recovery codes, notification of security-factor changes, and deployment/session revocation behavior. Do not claim MFA security is fully complete based on these fixes alone.


## MFA enrollment password step-up — latest Draft PR #11 update

A third MFA hardening step now requires password reauthentication before initial enrollment. The service validates the password before generating or storing a new TOTP secret; the API returns 401 on incorrect password. Already-enabled factors continue to be non-replaceable from enrollment and return 409; replacement requires the existing password + current TOTP disable flow first.

Regression tests cover wrong-password rejection with no secret persisted, correct-password enrollment, and prevention of replacing an enabled factor. The API enrollment contract now requires a JSON password field.

Latest PR #11 head: `10657cf099aaed17c7d4a18f2878ebd4d48f9f1a`. Backend CI #41648211858 is running and Security CI #41648211953 is queued. Previous green checks apply only to earlier PR #11 heads and do not verify this update. MFA remains under review; recovery codes, pending enrollment expiry, attempt throttling, and security-change notifications are not yet verified.


## Exact-head MFA verification — 3 November 2026

Draft PR #11 MFA hardening is now verified on its latest head `10657cf099aaed17c7d4a18f2878ebd4d48f9f1a`.

- Backend workflow #41648211858: SUCCESS — 1,637 passed, 8 warnings; broker-write boundary guard passed.
- Security workflow #41648211953: SUCCESS — CodeQL and Python dependency vulnerability audit passed.
- PR #11 remains Draft/unmerged.

The changes require password reauthentication for initial MFA enrollment, reject replacement while an MFA factor is enabled, and inject FastAPI Response so MFA enable/disable can clear browser cookies. Earlier failed backend runs on intermediate commits are superseded by this exact-head green result.

Documentation checkpoint before this addendum was verified on `22570af88916ea2c940831051ed429da5a701319` (Backend #41648348189 and Security #41648348210 both SUCCESS). This addendum creates a new documentation commit and therefore requires fresh exact-head CI before it becomes a verified checkpoint.


## Operational alerting implementation — 3 November 2026

Draft PR #12 adds a PAPER worker-fleet alert monitor and admin-configured Telegram delivery. See `PHASE4_OPERATIONAL_ALERTING.md` for conditions, thresholds, configuration, tests, failure semantics, and remaining deployment gates.

- Alerts: dropped unique observations, exhausted dispatch retries, ≥5 handler failures per interval, ≥25 rejected observations per interval, no worker heartbeat for ≥60 seconds, and unavailable shared metrics; recovery notification on heartbeat return.
- Poll interval: 30 seconds; Redis-backed per-fingerprint cooldown: 300 seconds. Process-local cooldown is used if Redis is unavailable; cross-replica dedupe is not guaranteed during Redis outage.
- Admin-only encrypted platform key added: `ops_alert_telegram_chat_id`; configure it alongside `telegram_bot_token` through Settings → Platform.
- Monitor runs as an independent worker task. Delivery is best-effort and must not block/rollback PAPER execution.
- Automated tests cover threshold deltas, aggregate-only content, Telegram delivery/dedupe, invalid destination and missing-worker threshold.

PR #12 head is subject to exact-head Backend and Security CI. A successful CI run does not prove live Telegram delivery; a credentialed deployment smoke test and multi-replica fault-injection remain required. PAPER-only and broker-write restrictions remain unchanged. PR #12 is Draft/unmerged.


### Alerting monitoring boundary clarification

The in-process heartbeat alert measures active Redis metrics-exporter heartbeats, not quote-dispatch worker health independently. Since the monitor itself runs inside the worker container, it cannot report a total crash of that same container. An external uptime/health watchdog is still required for complete worker-process-loss detection. This limitation is explicitly recorded in `PHASE4_OPERATIONAL_ALERTING.md`; do not describe the in-process monitor as a substitute for external infrastructure monitoring.


## Operational alert follow-up — 3 November 2026

Code review found and fixed a cooldown edge case: missing/invalid Telegram configuration previously could leave a Redis dedupe key active for the full five-minute cooldown. The monitor now releases that key so correcting the admin destination allows immediate retry. Added automated tests for two independent monitor instances sharing Redis (only one notification is sent for the same fleet delta) and configuration correction/retry without waiting for cooldown.

See `PHASE4_OPERATIONAL_ALERTING.md`. Latest alert code commit before this documentation sync: `4f7829a8019758b9eb0fc770dcae80d9cbb1c428`. Backend and Security CI are running for the code follow-up; this documentation sync itself will trigger fresh exact-head workflows. Do not treat earlier green CI as verification of these new tests. Worker heartbeat remains an exporter heartbeat only; external monitoring is required to detect total container/process loss.


## External worker watchdog — 3 November 2026

Added host-side watchdog files:
- `ops/worker_watchdog.py` inspects the Compose worker state and Docker restart count from outside the worker container.
- `ops/systemd/tradepro-worker-watchdog.service` and `ops/systemd/tradepro-worker-watchdog.timer` run the check as a root-owned oneshot each minute.
- `ops/worker-watchdog.env.example` documents an optional HTTPS incident webhook; real URLs/credentials must remain in a root-owned 0600 host file.
- `backend/tests/test_host_worker_watchdog.py` covers running/missing/unavailable Docker, state/restart transitions and HTTPS-only webhook enforcement.
- `PHASE4_EXTERNAL_WATCHDOG.md` is the installation runbook; `PHASE4_OPERATIONAL_ALERTING.md` records the integration boundary.

The watchdog only observes Docker state; Docker's existing restart policy remains responsible for restart. It does not call broker APIs. It is not installed on the Oracle VM yet. Without an HTTPS webhook, notifications remain in the host journal. VM/Docker daemon/systemd failure still requires independent cloud-provider instance monitoring. One-minute polling may miss short transient states, although Docker restart-count changes are detected.

Latest implementation commit before documentation synchronization: `996ccbcd9f52d539e17912940ce690ab9b9fa2d5`. Backend and Security CI were triggered on that commit; final documentation synchronization requires its own exact-head CI. Do not mark this checkpoint verified until both workflows pass on the final docs head.

PAPER-only remains mandatory; live broker `place_order`, `modify_order`, and `cancel_order` writes remain disabled. PR #12 remains Draft/unmerged; original `Tradepro` remains untouched.


## Real Redis multi-client alert test — 3 November 2026

Added a CI-backed integration test using two independent Redis clients against the workflow's Redis 7 service. Both concurrently attempt the same unique alert fingerprint via atomic Redis `SET NX EX`; exactly one claim and one Telegram send are required. See `PHASE4_OPERATIONAL_ALERTING.md`. This is stronger than the in-memory fake but does not replace multi-container fault injection or a credentialed Telegram deployment smoke test. Backend and Security CI must pass on the final documentation head before checkpoint verification.


## PostgreSQL worker-loss recovery test — 3 November 2026

Added a PostgreSQL 16-backed recovery-sweeper test for an expired EXECUTING PAPER stop event. It simulates worker loss after the claim transaction is committed, invokes the real expired-event sweeper without Redis redelivery, verifies claim-token rotation, and completes the durable event using the replacement token. The broker-facing execution method is stubbed; this test does not submit orders. See `PHASE4_PAPER_STOP_EVENT_POSTGRES_CONCURRENCY.md`.

This is a DB-backed recovery integration test, not an OS-level worker SIGKILL or a full end-to-end order-fill test. The prior PostgreSQL concurrency cases remain in place. The stop-event model docstring was corrected to reflect worker ownership. Exact-head Backend and Security CI must pass after the final documentation sync.


Follow-up test-harness correction: the stubbed `execute_claimed` method now uses an instance-method-compatible signature, so the PostgreSQL recovery-sweeper test exercises the handler call shape correctly. This creates a new exact-head CI requirement; previous runs on earlier commits do not verify this final correction.


## PostgreSQL recovery verification update — 3 November 2026

- Backend CI run [#41659743611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41659743611) and Security analysis [#41659743654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41659743654) both PASSED on exact commit `319cf01dedd3b8bb861d6d60f010f96b08e9697e`.
- Backend and Security results above validate the lease-timeline harness correction, but do not validate subsequent commits.
- Added an explicit PostgreSQL integration assertion that the original worker's claim token cannot complete the event after recovery and replacement-worker completion. This is committed as `794af153daa6d331d28a5e4aa7b3d3249de1a09e`.
- Exact-head Backend and Security CI for `794af153daa6d331d28a5e4aa7b3d3249de1a09e` and this documentation synchronization are required before declaring a verified checkpoint.
- Scope remains `tarunsharma2610-del/tradepro-improved` only. PAPER-only; live broker order writes disabled; PR #12 OPEN, Draft and unmerged; original `Tradepro` untouched.
- This DB-backed worker-loss simulation is not an OS-level SIGKILL or Oracle VM failure drill. External watchdog installation, real VM failure drill, sustained production-like load, and final security audit remain pending.


## Verified PostgreSQL recovery checkpoint — 3 November 2026

- Exact documentation and implementation head: `49f058614eb8ab02acb9a24b6870aaf7e17a83da`.
- Backend CI [#41664985664 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41664985664): **1,646 passed, 8 warnings**; broker-write boundary guard passed; PostgreSQL 16 migration/restore checks completed successfully.
- Security analysis [#41664985706 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41664985706): CodeQL and Python dependency vulnerability audit passed.
- The PostgreSQL recovery-sweeper test now also asserts that the original claim token cannot complete the event after the replacement worker has completed it.
- The test simulates worker loss by closing the original DB transaction and advancing the persisted lease timeline; it is not an OS-level process kill. Next reliability gate: isolated multi-process worker termination/restart against PostgreSQL 16, with a real SIGKILL/SIGTERM fault window and verification of one durable PAPER outcome, no duplicate ledger mutation, and stale-token rejection.
- Additional pending gates: Redis/worker multi-container failure injection; sustained production-like load with realistic DB handler work; Oracle VM watchdog installation and failure drill; external VM monitoring; final independent security/penetration review.
- Repository scope: `tarunsharma2610-del/tradepro-improved` only. PR #12 is OPEN, Draft and unmerged. PAPER-only remains mandatory; live broker order writes remain disabled; original `Tradepro` untouched.
