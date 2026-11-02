# Phase 4 — PAPER Quote-Driven Stop Monitor Design Audit

Date: 30 October 2026
Repository: `tarunsharma2610-del/tradepro-improved`
Implementation branch: `phase4/redis-market-data-publisher`
Status: design gate only; no quote-driven order trigger has been enabled.

## Verified baseline

- Exact code/test head: `d6fd555d17faa02beff229a04acd3dfcd4cf86c5`.
- Backend CI #41076913522 passed on that exact SHA: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41076913522
- PR #9 remains open, Draft and unmerged; target branch `phase4/roadmap-progress-checkpoints`.
- PAPER mode only. Live broker order submission/modification/cancellation remains disabled.
- Scanner observations are held in process memory, keyed by (user_id, instrument_key), and expire after 15 seconds based on local monotonic receive time.
- Redis quote consumer callback currently calls `MarketScanner.process_quote`; it is synchronous and performs no database/order work.
- Strategy worker runs candle-based evaluations every 300 seconds. It fetches 5-minute historical + intraday candles, checks candle freshness, computes indicators, then may use a fresh scanner LTP for a trailing-stop check.
- `ExecutionService.place_order` is the shared PAPER execution/accounting path. MARKET PAPER fills require a separate fresh Full Market Quotes V3 depth snapshot; LTPC WebSocket messages do not contain executable depth.

## Findings that block a safe tick-driven stop monitor

1. **No idempotency key for a stop event.** Repeated quote versions, Redis redelivery, callback retries, or two worker replicas could submit repeated exit orders unless a durable event claim is introduced.
2. **Strategy state is not locked by the current evaluator.** `StrategyExecutionService.evaluate` reads/writes `current_watermark` without a strategy-row lock. Portfolio locking inside order placement does not by itself prove that two stop callbacks cannot both decide to exit.
3. **Multiple strategies can share a portfolio/instrument.** Position quantity is portfolio+instrument scoped, while trailing-stop watermark is strategy scoped. Multiple strategies could each attempt to close the same shared position. The ownership/allocation rule must be explicit before automation.
4. **A quote is a trigger observation, not an execution price.** The LTPC quote must never be used to simulate a fill. A triggered exit must go through existing PAPER order execution, fresh depth, portfolio risk validation, virtual cash/position accounting and transaction-cost handling.
5. **The scanner's 15-second TTL is based on local receipt time.** It does not independently prove that the exchange timestamp is within an allowed age. The monitor must enforce both exchange timestamp and receive-time bounds, reject future/skewed timestamps, and bind epoch/version to a per-subscription lifecycle.
6. **Redis listener isolation and backpressure matter.** Do not perform slow DB or broker calls inside the quote callback. Do not spawn an unbounded async task for every tick. Use a bounded/coalescing queue keyed by user+instrument and explicit overflow metrics/fail-closed behavior.
7. **Reconnect/lease handoff can replay data.** Epoch changes, version resets, duplicate/out-of-order messages and stale consumers must not reuse old stop claims or create duplicate orders.
8. **Existing worker cadence is not real time.** A 300-second candle evaluation cannot be described as tick-by-tick stop monitoring. The new monitor must be an independent worker path and must not redownload candles on each quote.

## Required architecture before implementation

- Keep `MarketScanner.process_quote` as a fast validation/cache callback only.
- Publish accepted observations to a bounded, coalescing dispatcher keyed by (user_id, instrument_key); retain only the newest accepted (epoch, version) per key.
- Resolve active strategies by exact portfolio owner and instrument key; never use a global instrument-only lookup.
- Define one explicit position-exit ownership model for multiple strategies sharing a portfolio/instrument. Until then, fail closed for ambiguous shared-position ownership rather than allowing each strategy to independently liquidate it.
- Introduce durable stop-event idempotency, preferably a persisted event/claim with a unique key covering strategy (or position owner), subscription epoch and quote version. The claim and transition to an exit-in-progress state must be transactionally coordinated.
- Lock the authoritative strategy/position/portfolio rows in a consistent order. PostgreSQL concurrency tests must prove that two replicas cannot create duplicate exit orders for one stop event.
- Trigger only after a fresh, valid quote crosses the configured stop using the strategy's persisted watermark. Update watermark monotonically and transactionally; do not regress it on out-of-order ticks.
- Submit exits only through the existing PAPER `ExecutionService.place_order` path. WebSocket LTP is trigger-only; full-depth quote remains the execution input.
- If full-depth quote, analytics token, risk validation, accounting, or DB transaction fails, retain a recoverable state and do not mark the stop event complete. Define retry policy and alerting before release.
- Ensure no new code path can select LIVE mode or call broker order-write endpoints.

## Test gates (all required)

1. Quote freshness: receive-time TTL, exchange timestamp age, future timestamp/skew, invalid timestamp, missing timestamp, and exact 15-second boundary.
2. Ordering/lifecycle: duplicate version, lower version, epoch rotation, lease handoff, delayed old-epoch quote, reconnect and replay.
3. Isolation: wrong user, wrong instrument, inactive strategy, deleted strategy, portfolio ownership mismatch.
4. Multiple strategies: same user/instrument, same portfolio/instrument, different portfolios, explicit shared-position ownership, and no duplicate aggregate close.
5. Concurrency: simultaneous callbacks across two worker replicas on PostgreSQL 16; exactly one durable claim and at most one exit order.
6. Execution: LTPC never used as fill price; fresh depth required; risk checks, kill switch semantics, PAPER-only mode, fees, GST/IPFT accounting and position/cash ledgers unchanged.
7. Failure recovery: Redis outage, bounded queue overflow, DB outage, token expiry, depth quote failure, process restart after claim, process restart after order creation but before acknowledgement.
8. Regression: existing 5-minute indicator calculations and scheduled strategy evaluation unchanged; no repeated candle downloads per tick.

## Implementation decision

Do **not** implement tick-triggered exits by simply calling `StrategyExecutionService._exit` from the Redis callback. That would lack durable event idempotency, bounded dispatch, shared-position ownership and proven concurrency control. First implement and test the dispatcher/claim state machine and ownership policy; only then connect it to the existing PAPER execution service.

## Current completion state

- Scanner TTL, Redis worker lifecycle and first scanner-to-PAPER trailing-stop evaluation slice: implemented and CI-verified at the baseline above.
- True quote-driven/tick-by-tick PAPER stop monitor: not implemented; design and concurrency gates remain.
- Production deployment, sustained-load testing and credentialed Upstox smoke tests: deferred.


## Latest follow-up — 30 October 2026

Transactional PAPER stop-event claim service commit `6ac3882a98f3c66abb4cd62848971b6277ab3be7` passed exact-head Backend CI #41080156436. Claims validate tenant/strategy/instrument ownership, lock portfolio → strategy → position, reject ambiguous shared-position ownership and duplicate quote identity, and store a bounded lease. The dispatcher remains disconnected from the claim service and order execution. Next gates are PostgreSQL 16 multi-worker concurrency, event transitions/lease reclaim, crash recovery, explicit shared-position ownership, then controlled PAPER integration. PR #9 Draft/unmerged; PAPER mandatory; live broker writes disabled.


## Implementation status correction — 1 November 2026

This dated addendum supersedes the earlier "findings that block" where the gaps have since been implemented and CI-verified. The original audit remains intact as a historical record of the risks identified at design time.

### Safeguards now implemented and covered by tests
- Durable PAPER stop-event identity is stored with a unique strategy/event/epoch/version key, claim token, bounded lease, attempt counter and constrained state vocabulary.
- Claim service validates user/portfolio/strategy/instrument ownership and rejects ambiguous shared portfolio/instrument position ownership. It locks portfolio → strategy → position.
- Lifecycle supports token-fenced CLAIMED → EXECUTING → COMPLETED/RETRYABLE/FAILED transitions and atomic expired-lease reclamation with token rotation.
- PAPER execution orchestration validates ownership and lease, uses the shared ExecutionService with caller-owned transaction, and commits order, execution/accounting, position/cash, watermark and event completion atomically.
- Completed-event redelivery returns the existing matching filled PAPER order. Failure injection verifies rollback when completion fails after the order/accounting work has been flushed.
- PostgreSQL 16 tests cover concurrent claims/reclaimers, retry-limit exhaustion, expired EXECUTING lease recovery, rollback, and two workers concurrently executing the same event. The last case verifies one order, one execution, one position close and same-order replay.
- Exact-head Backend CI #41289810206 passed on 6db7dcfa3d46c11c844733e571ea6f90dda999d6; the current code checkpoint and its docs are tracked in PHASE4_LATEST_CI_CHECKPOINT.md.

### Still not implemented / still blocks dispatcher activation
- MarketQuoteDispatcher remains isolated and is not wired into RedisMarketQuoteWorker or the durable claim/execution services.
- There is no supervised quote-driven PAPER stop-monitor consumer yet. Callback must remain validation/cache/dispatch only; DB and execution work belongs in a separate bounded consumer.
- Consumer cancellation, in-flight acknowledgement/requeue, retry backoff, shutdown and multi-replica handoff need explicit semantics and tests before activation.
- Freshness must include both scanner receive-time TTL and exchange timestamp age/skew checks at the final stop-trigger boundary. A WebSocket LTPC tick is trigger data only; fills still require fresh Full Market Quotes V3 depth through existing PAPER execution.
- Multi-user/multi-instrument load, Redis outage/reconnect, queue overflow, stale quote, missing depth, kill-switch, and deployment/credentialed Upstox tests remain required or deferred as applicable.

### Correct next sequence
1. Harden dispatcher acknowledgement/cancellation and supervised consumer lifecycle; add tests for cancellation before work, during work, and shutdown with pending/in-flight keys.
2. Add a PAPER-only consumer service that resolves exact owner/instrument strategy subscriptions, applies final exchange-time and receive-time freshness checks, then uses durable claim + atomic execution services. Do not perform DB or order work in the Redis callback.
3. Test the integrated flow with PostgreSQL 16 multi-worker races, duplicate/out-of-order versions, epoch replacement, cross-tenant isolation, stale/future timestamps and queue overflow.
4. Run full exact-head CI before recording another checkpoint.
5. Keep LIVE mode isolated and all live broker writes disabled until the separate live-readiness stages are independently completed and explicitly approved.



## Phase 4 authoritative audit/status — 2 November 2026
This section supersedes older Phase 4 resume pointers where they conflict; older entries remain historical.
- Scope only tarunsharma2610-del/tradepro-improved, branch phase4/redis-market-data-publisher. PR #9 targets phase4/roadmap-progress-checkpoints and remains OPEN, Draft, unmerged. Original tarunsharma2610-del/Tradepro remains untouched.
- Latest verified code/test head before this docs repair: 654b0a5d2cb898a0b6dcd4dcb6556b0af6c2ccc2. Exact-head Backend CI #41398555424 PASSED on that SHA, including stale LIVE broker-position snapshot regression. Preceding commit 502303d2f2d9be1ed0ece0ecb5b280ed5f7db2e4 passed #41398528946.
- Earlier API/Redis safeguards passed: #41397210305 (3281618), #41397227429 (a65c463), #41397602437 (d01146f), #41397616502 (147d59b). Prior docs CI #41398105822 passed on 027850d; this docs sync needs its own exact-head CI.
### Completed, CI-backed Phase 4 scope
- PAPER is the only enabled execution path. Broker place_order/modify_order/cancel_order writes remain disabled; AST broker-write boundary runs in Backend CI.
- Mode-aware portfolio analytics and ownership/isolation checks are implemented. LIVE balance does not fall back to simulated starting capital; LIVE positions fail closed rather than exposing PAPER positions.
- Read-only Upstox LIVE funds, positions and holdings sync uses allocated owner-scoped broker connection and immutable portfolio/user/connection-bound snapshots. Failed sync retains prior snapshot and does not mutate PAPER accounting.
- Analytics Token storage/ownership/expiry controls, Upstox V3 stream lifecycle, feed-mode subscription/reconnect/startup recovery and SDK compatibility review have prior green CI.
- Redis publisher/consumer has user-scoped TTL snapshots, schema/version and epoch/version checks, atomic publishing, Pub/Sub notifications, real Redis tests, restart/recovery and independent process delivery tests.
- Worker-managed Redis consumer lifecycle, lease/replica coordination, scanner intake and 15-second scanner TTL are implemented. Scanner-to-PAPER trailing-stop evaluation consumes fresh user/instrument-scoped LTP while five-minute candles remain indicator source.
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


## 2 November 2026 — security checkpoint reconciliation

- Session-security implementation verified on PR #9 head `77f44c7299f5e7157a4cdb2f8dfe7fbbfb6c08c6`: Backend CI #41460334989 and Security analysis #41460334979 passed on that exact head. Persisted sessions, refresh-token rotation/replay rejection, logout revocation and reserved JWT `sid`/`jti` handling are covered by tests.
- Transactional key-rotation service implementation commit `960c099b53d4c8e41daeb4f5691bc0972d5fb7b2`: Backend CI #41456734039 and Security analysis #41456734074 passed. It covers encrypted broker credentials, OAuth access tokens, Upstox Analytics Tokens, platform settings and MFA secrets; unreadable ciphertext fails closed. No production keys/data were rotated or accessed.
- Docs CI on the final documentation head is still required before calling this checkpoint green.
- Security assessment remains incomplete: endpoint IDOR authorization matrix, secret/token redaction review, broker-write reachability, staging DAST, abuse/load and tenant-isolation tests, deployment/restore/incident-response review and independent penetration testing remain.
- PAPER mandatory; LIVE broker `place_order`, `modify_order`, `cancel_order` writes disabled; PR #9 OPEN/Draft/unmerged; original `tarunsharma2610-del/Tradepro` untouched.


## Phase 4 dispatcher integration correction — 2 November 2026 (exact-head CI verified)

- Corrective test commit: `4aba13642f1f3bcb4e11f5c6b5def7433e687ca7`. The Redis-to-scanner dispatcher integration test retrieves and acknowledges the dispatcher item in the same asyncio task, preserving task-scoped ownership; production safeguards were not weakened.
- Exact-head Backend CI [#41471120955 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41471120955). Redis setup, full backend pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention all passed.
- Exact-head Security analysis [#41471120975 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41471120975): CodeQL and Python dependency vulnerability audit passed. These are not DAST or penetration-test sign-offs.
- Remaining Phase 4 gates: full Redis → scanner → dispatcher → durable PAPER stop-event → execution → final position/ledger proof; duplicate/out-of-order quote tests; worker crash/cancellation/recovery; concurrent PAPER exits; multi-process load/backpressure; observability/runbooks; production restore evidence.
- Security assessment remains incomplete: full IDOR/authorization matrix, secret/token redaction, broker-write reachability, isolated-staging DAST, abuse/load and tenant-isolation testing, deployment/incident response and independent penetration testing.
- Safeguards: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PAPER mandatory; LIVE broker `place_order`, `modify_order`, `cancel_order` disabled; PR #9 OPEN/Draft/unmerged; no merge/deployment/LIVE activation.
