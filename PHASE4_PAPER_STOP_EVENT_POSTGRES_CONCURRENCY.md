# Phase 4 — PostgreSQL 16 PAPER stop-event claim concurrency

Date: 30 October 2026

## Test scope

Added PostgreSQL-only multi-session tests in `backend/tests/test_paper_stop_event_claim_postgres_concurrency.py`. Both tests use independent SQLAlchemy sessions, a two-worker thread pool and a synchronization barrier. They use the CI-provisioned PostgreSQL 16 service via `TEST_POSTGRES_URL`, create uniquely identified fixtures, and delete only their own rows. They do not drop shared database tables.

1. **Same quote identity race:** two workers race the same strategy/event/epoch/version. Required outcome: exactly one durable CLAIMED row and one duplicate/no-claim result; no unexpected exception; persisted claim token and attempt count exactly one.
2. **Distinct quote versions:** two workers race different quote versions for the same strategy/epoch. Required outcome: both durable claims survive serialization, with distinct versions and tokens.

## Existing lock behavior under test

The claim service locks portfolio → strategy → position. The portfolio row is the common serialization point for claims in one portfolio, while the database unique constraint remains the final duplicate identity guard. This test provides PostgreSQL evidence for those two properties; it is not a proof of multi-host production reliability or lease recovery.

## CI

Backend CI already provisions PostgreSQL 16 and exports `TEST_POSTGRES_URL`; the new file is auto-discovered by pytest. A successful exact-head CI run is required before accepting the concurrency milestone.

## Safety

Tests create only synthetic PAPER-domain database rows. No dispatcher integration, order creation, broker API call, live write, deployment or PR merge is included.


## Lifecycle and lease-recovery concurrency extension — 1 November 2026

Verified on exact head `aaf64fcf1431f7fa998d61c9cc3efd9b251437a6`, Backend CI #41097352266 SUCCESS.

Additional PostgreSQL 16 independent-session tests cover:

1. Two workers racing to reclaim one expired claim: exactly one rotates the token; the other loses without error.
2. Two workers racing an event at its retry limit: neither can exceed the attempt budget; the event is terminalized as FAILED.
3. Caller rollback after CLAIMED → EXECUTING restores the prior durable state and token.
4. Recovery of an expired EXECUTING lease rotates ownership; the stale worker cannot complete, while the new token can proceed.
5. Retryable delay and stale-token behavior are also covered by service-level tests.

These tests prove the implemented database state transitions under the CI PostgreSQL 16 service; they do not prove production multi-host reliability or authorize dispatcher/order integration.



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
