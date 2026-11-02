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


## Latest Phase 4 verification — 30 October 2026

- Transactional PAPER stop-event claim implementation: `6ac3882a98f3c66abb4cd62848971b6277ab3be7`.
- Exact-head Backend CI #41080156436 passed: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41080156436.
- Claims validate user/portfolio/strategy/instrument ownership, lock portfolio → strategy → position, reject flat or ambiguously shared positions, and persist unique quote identity, claim token and bounded lease. Duplicate claims fail closed.
- No claim consumer or order path is enabled by this slice. PAPER-only remains mandatory; live broker order writes remain disabled; PR #9 remains Draft/unmerged; original Tradepro repository is out of scope.
- Next: PostgreSQL 16 multi-worker claim tests, safe lease reclamation and crash recovery, then controlled PAPER dispatcher integration only after those gates.


## Lifecycle extension — 1 November 2026

The claim service is now complemented by `PaperStopEventLifecycle` (verified at exact head `aaf64fcf1431f7fa998d61c9cc3efd9b251437a6`, Backend CI #41097352266 SUCCESS).

- Claim-token-fenced conditional updates implement CLAIMED → EXECUTING → COMPLETED, EXECUTING → RETRYABLE, and EXECUTING → FAILED.
- Execution and retry leases are bounded; reclaim rotates the claim token and increments attempts; exhausted attempts become terminal FAILED.
- A stale worker cannot complete or advance an event after another worker has reclaimed it.
- The lifecycle never commits, creates an order, or calls a broker; caller owns the SQLAlchemy transaction.
- PostgreSQL 16 tests cover concurrent reclaim, retry-budget exhaustion, rollback atomicity and recovery of an expired EXECUTING event.
- This remains a state-coordination primitive only. It is not connected to the dispatcher or order execution.



## Phase 4 authoritative audit/status — 2 November 2026
This section supersedes older Phase 4 resume pointers where they conflict; older entries remain historical.
- Scope only tarunsharma2610-del/tradepro-improved, branch phase4/redis-market-data-publisher. PR #9 targets phase4/roadmap-progress-checkpoints and remains OPEN, Draft, unmerged. Original tarunsharma2610-del/Tradepro remains untouched.
- Latest verified code/test head before this docs repair: 654b0a5d2cb898a0b6dcd4dcb6556b0af6c2ccc2. Exact-head Backend CI #41398555424 PASSED on that SHA, including stale LIVE broker-position snapshot regression. Preceding commit 502303d2f2d9be1ed0ece0ecb5b280ed5f7db2e4 passed #41398528946.
- Earlier API/Redis safeguards passed: #41397210305 (3281618), #41397227429 (a65c463), #41397602437 (d01146f), #41397616502 (147d59b). Prior docs CI #41398105822 passed on 027850d; this docs sync needs its own exact-head CI.
### Completed, CI-backed Phase 4 scope
- PAPER is the only enabled execution path. Broker place_order/modify_order/cancel_order writes remain disabled; AST broker-write boundary runs in Backend CI.
- Mode-aware portfolio analytics and ownership/isolation checks are implemented. LIVE balance does not fall back to simulated starting capital; LIVE positions fail closed rather than exposing PAPER positions.
- Read-only Upstox LIVE funds, positions and holdings sync uses the allocated owner-scoped broker connection and immutable portfolio/user/connection-bound snapshots. Failed sync retains the prior snapshot and does not mutate PAPER accounting.
- Analytics Token storage/ownership/expiry controls, Upstox V3 stream lifecycle, feed-mode subscription/reconnect/startup recovery and SDK compatibility review have prior green CI.
- Redis publisher/consumer has user-scoped TTL snapshots, schema/version and epoch/version checks, atomic publishing, Pub/Sub notifications, real Redis tests, restart/recovery and independent process delivery tests.
- Worker-managed Redis consumer lifecycle, lease/replica coordination, scanner intake and 15-second scanner TTL are implemented. Scanner-to-PAPER trailing-stop evaluation consumes fresh user/instrument-scoped LTP while five-minute candles remain the indicator source.
- Durable PAPER stop-event claim/state/lease/retry/recovery, PostgreSQL 16 concurrency tests, bounded dispatcher and PAPER worker wiring have prior green CI. Full end-to-end market-to-ledger acceptance remains outstanding.
- Read-only LIVE unrealized P&L API GET /api/v1/portfolios/{portfolio_id}/live-unrealized-pnl checks owner/mode/current allocation/snapshot binding, reads exact instrument keys through user-scoped Redis consumer, fails closed on stale/missing/invalid quotes and Redis outage, and does not mutate accounting.
- LIVE position snapshots missing timestamps, future-dated or older than 120 seconds are rejected. Exact-head CI #41398555424 passed.
### Remaining gates
1. Full authenticated LIVE P&L API integration test using real ephemeral Redis publisher/consumer in the same test flow (component-level Redis tests already exist).
2. Internal realized-P&L ledger and broker fill/trade reconciliation; keep broker daily P&L, broker realized P&L and internal lifetime realized P&L distinct.
3. Frontend LIVE read-only P&L display with separate realized/unrealized values, freshness and unavailable states.
4. Full Redis→scanner→dispatcher→durable stop claim→PAPER fill→ledger/position/cash end-to-end tests, including crashes, retries, duplicate/out-of-order events and competing exits.
5. Multi-user/multi-instrument load/backpressure, metrics/alerts, runbooks, worker recovery; production Oracle restore and credentialed Upstox smoke tests remain deployment gates.
6. LIVE order readiness is not achieved; any future write gateway needs separate design, deny-by-default authorization, idempotency, audit and explicit approval.
### Security audit status
- PHASE4_P0_BASELINE_AUDIT.md exists (29 Oct) but is a static source/workflow audit; it explicitly did not perform runtime or credentialed smoke testing.
- Existing controls include broker-write AST enforcement, ownership/mode checks, encrypted Analytics Token handling, Redis tenant namespacing/freshness, PostgreSQL concurrency, migration/restore CI and audit logging.
- Comprehensive Phase 4 security assessment is NOT COMPLETE. No verified full IDOR sweep, SAST/DAST report, dependency vulnerability scan, authenticated/independent penetration test or production configuration review is evidenced. Do not claim penetration-tested or production security-approved.
- Remaining security: endpoint authorization matrix and adversarial IDOR tests; secret redaction/storage review; rate-limit/abuse tests; dependency/SAST; DAST on safe staging; broker-write reachability tests; tenant isolation/load; backup/restore and incident response.
### Safeguards
PAPER only; LIVE place/modify/cancel writes disabled; PR #9 Draft/unmerged; no deployment or LIVE gateway activation authorized. After docs sync, run CI on exact new docs head before saving a green checkpoint.



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

Historical entries above are retained as historical evidence. Current authoritative state:
- Repository: `tarunsharma2610-del/tradepro-improved` only; branch `phase4/redis-market-data-publisher`; PR #9 targets `phase4/roadmap-progress-checkpoints`, remains OPEN/Draft/unmerged.
- Code/test head before this docs sync: `3ad06a045c16251b6daf1e2ec429837ddd390c59`. Exact-head Backend CI #41402165142 PASSED: **1,550 passed, 1 warning**; Redis-backed pytest, broker-write guard, SQLite/PostgreSQL 16 migration round-trips and synthetic restore/evidence retention passed.
- Authenticated LIVE unrealized-P&L API is now tested end-to-end against a real Redis publisher/user-scoped snapshot; expected ₹40.00 result asserted without mutating accounting.
- Rate-limit Redis outage fail-closed (HTTP 503) and MFA-disable password+TOTP step-up fixes passed CI #41400727799.
- Comprehensive security audit remains **NOT COMPLETE**. Static baseline audit is not penetration testing. IDOR/authorization matrix, cross-tenant adversarial tests, SAST/dependency scan, DAST, secret review, broker-write reachability, load/abuse testing, deployment hardening and independent penetration testing remain open.
- Remaining product gates: realized-P&L ledger and broker-fill reconciliation; LIVE P&L frontend; complete Redis→scanner→dispatcher→durable PAPER stop→ledger E2E; multi-user load/backpressure, observability/runbooks; credentialed Upstox smoke test and production Oracle restore.
- PAPER only; LIVE broker `place_order`, `modify_order`, `cancel_order` writes disabled; PR #9 not to be merged; original `Tradepro` repository untouched.
- This docs synchronization requires a new exact-final-head Backend CI before it is a green checkpoint.


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
