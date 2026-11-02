# Phase 4 P4-0 Baseline Audit — 29 October 2026

## Scope and method
- Repository audited: `tarunsharma2610-del/tradepro-improved` only.
- Branch: `phase4/roadmap-progress-checkpoints`.
- Audit commit baseline: `39952e8d091a6ed55d7eff2cb9a48f60c4e1288d` (Phase 4 planning/doc checkpoint head).
- Audit is static inspection of tracked GitHub source and workflows. No runtime tests or deployed credentialed smoke tests were executed in this audit.
- Original `tarunsharma2610-del/Tradepro` repository was not accessed or modified.

## Executive result
The repository already contains substantial backend functionality: authenticated Upstox OAuth/API adapter, a user-scoped Market Data Feed V3 streamer with reconnect/stale-data handling, strategy/backtest services, portfolio risk checks, paper order/fill accounting, charge/GST/IPFT services, extensive backend tests, and CI checks for broker-write boundaries and SQLite/PostgreSQL migration round-trips plus synthetic restore.

Therefore Phase 4 should harden existing functionality rather than rewrite it. The most important confirmed follow-up is to make the PAPER-only configuration an enforceable fail-closed invariant at startup and to strengthen regression coverage around every route that could reach broker order-write methods. Existing code already labels `TRADING_MODE=LIVE` as not implemented, and the paper execution service writes `trading_mode="PAPER"`; nevertheless, `main.py` currently only logs a warning if the mode is LIVE, so configuration alone does not fail startup. The adapter contains an HTTP `place_order` implementation; current static guard limits unapproved call references, but dynamic/reflection bypasses are explicitly not fully proven safe by the scanner. Treat this as defense-in-depth hardening, not evidence that live orders have been sent.

## Evidence-based gap matrix

| Area | Current evidence | Audit status | Next action |
|---|---|---|---|
| Branch/checkpoint | Phase 4 roadmap, progress and checkpoint records created | Present; exact-head CI still unverified | Establish a green exact-head CI checkpoint before claiming green |
| Paper execution | `ExecutionService.place_order` sets new orders to `trading_mode="PAPER"`; risk checks apply to MARKET and LIMIT paths | Implemented in inspected path; full acceptance not re-run in this audit | Add/retain tests proving mode configuration cannot route orders to broker writes |
| Broker-write boundary | `backend/scripts/check_broker_write_boundary.py` AST guard and `test_broker_write_boundary_guard.py`; backend workflow runs guard | Present, with documented static-analysis limitation | Add a startup hard stop for non-PAPER mode and targeted tests; preserve the guard |
| Upstox OAuth | Adapter exchanges auth code, computes next 03:30 IST expiry; credential service is used for tokens | Present; account-specific refresh/reconnect remains operationally unverified | Audit token refresh/expiry paths and test expired-token failure behavior |
| Upstox market data | `upstox_market_data_streamer.py` uses V3 authorize handshake, user-scoped token provider, bounded reconnect and stale tick rejection | Implemented in code; live credentials not tested | Verify streamer lifecycle/authorization error cases in tests; real smoke test remains deployment-gated |
| Strategy and risk | Strategy execution routes through shared ExecutionService; portfolio risk checks include open/pending exposure | Present | Verify emergency stop and entry/exit asymmetry under direct/manual evaluation |
| Paper lifecycle | Execution, position, cost estimator and charge-total modules/tests exist | Present; Phase 4 full lifecycle review pending | Trace order→fill→position→P&L→estimated charges, including failure rollback/replay |
| Accounting | Phase 3 per-fill allocation, evidence, GST/IPFT and reconciliation modules/tests exist | Preserve; do not reopen without regression | Regression-test estimates/aggregate API never become per-fill actual evidence |
| Persistence/migrations | Backend CI has SQLite + PostgreSQL 16 upgrade/downgrade/re-upgrade and synthetic restore drill | CI coverage present; production Oracle restore is not evidenced | Keep production backup/restore as post-deployment gate |
| Frontend | Next.js app routes exist for admin, backtests, login, news, portfolios, reconciliation, register and settings; CI workflow typechecks/builds | Present; UI acceptance not part of P4-0 | Keep major UI build changes for planned UI phase unless hardening requires them |
| CI trigger coverage | Backend workflow triggers on push to main, pull_request, workflow_dispatch; frontend workflow triggers on main/path changes, pull_request/path changes, workflow_dispatch | Push to the Phase 4 branch alone does not trigger backend workflow; frontend workflow is path-filtered | Use an authorized PR/workflow dispatch to obtain exact-head checks; never call empty status “passed” |

## Prioritized Phase 4 actions
1. **P4-0A (safety first) — IMPLEMENTED, CI PENDING:** `backend/app/core/config.py` now normalizes `TRADING_MODE` and rejects every value other than `PAPER` using Pydantic validation at settings load. Added `backend/tests/test_trading_mode_safety.py` for lowercase/whitespace normalization, default PAPER, and LIVE/invalid-mode rejection. The change is not accepted until backend CI passes on the exact head.
2. **P4-0B:** review all references to adapter `place_order`, `modify_order`, `cancel_order`, dynamic dispatch and order routes. Ensure tests demonstrate no application execution path can submit live writes.
3. **P4-0C:** inspect automated-entry kill switch, strategy exit behavior, stale market-data checks and service-boundary risk checks.
4. **P4-0D:** paper order/fill/P&L/charge lifecycle and persistence failure/restart/replay tests.
5. **P4-0E:** Upstox token expiry/streamer lifecycle and deployment checklist.
6. **P4-0F:** full CI on exact head, update all Phase 4 resume/checkpoint records and continue at the first unchecked item.

## CI status
- The Phase 3 baseline run cited in prior checkpoint records is not CI evidence for the new Phase 4 documentation head.
- At the time of the initial audit, commit `39952e8d091a6ed55d7eff2cb9a48f60c4e1288d` returned no combined status entries; that is **not a pass**. Safety hardening was subsequently committed at `791ae9858d80ddf5554db71f134db273e55be29b` and its tests at `1517b2947709f96083dc48e06edfebe32152d37f`; exact-head CI is still pending.
- The repository's backend workflow is configured for pull requests and workflow_dispatch, not arbitrary branch pushes. No Phase 4 green run is claimed here.

## Safeguards confirmed for this work
- Only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope.
- No `main` update and no merge of PR #6/#7.
- PAPER mode remains mandatory; live `place_order`, `modify_order`, `cancel_order` writes remain disabled.
- Brokerage Details estimates remain estimates; aggregate Trade Charges responses remain reconciliation-only.
- No live broker write, credentialed smoke test, production deployment or real Oracle restore was performed.

## User-directed integration principle — 30 October 2026

Use official Upstox APIs/SDKs and Developer Console where applicable, after auditing existing code. Avoid workaround-first design and duplicate integrations. Current source audit indicates the V3 streamer and V3 REST endpoints already exist, while strategy candle retrieval is separate and parser documentation remains BEST-EFFORT. This is an integration/contract-verification gap to address before adding more freshness heuristics. Official references:
- https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- https://upstox.com/developer/api-documentation/v3/get-intra-day-candle-data/
- https://upstox.com/developer/api-documentation/installing-sdk/

## Market-data API audit update — 30 October 2026

Confirmed the supported V3 current-session candle endpoint from official documentation. The strategy previously requested only the historical-candle endpoint for a date range that included today. Added a direct Upstox V3 intraday candle call and combined its parsed output with historical candles, deduplicated by UTC-normalized timestamp with intraday preferred on overlap. Both sources must succeed; no synthetic candle fallback is used. Added API URL/auth and merge/failure tests. Current head d7c786fc164ed297df42f26493c994ceacd337a7 is pending CI. WebSocket is still not wired to the worker; its API-process registry is process-local, so the process boundary must be handled intentionally rather than assumed away.
Official reference: https://upstox.com/developer/api-documentation/v3/get-intra-day-candle-data/

## Quote freshness/API contract audit — 30 October 2026

LTP V3 returns last_price, ltq, volume and cp but no last_trade_time. Full Market Quotes V3 returns last_price, instrument_token and last_trade_time. Paper execution's REST fallback now uses the latter, validates exact instrument identity and exchange trade age, and rejects missing/stale/future-invalid quotes. Fresh WebSocket ticks remain preferred when present in the same process. Current head 65f8070e344eaa4cd8cb82c876732662d02cc3a3 is awaiting exact-head CI.
Official docs: https://upstox.com/developer/api-documentation/get-full-market-quote-v3/ ; https://upstox.com/developer/api-documentation/ltp-v3/

## Exchange timestamp source audit — 30 October 2026

Official Upstox docs distinguish exchange last-trade time (LTPC LTT) from packet currentTs. The streamer previously substituted currentTs if LTT was absent; this could make stale last-trade price appear fresh. Removed the fallback, require finite positive LTP and positive LTT, and validate exchange and receive age. Full Market Quotes V3 REST fallback independently checks last_trade_time and exact instrument_token. Current test head 4dd8420d4d787be049c956204e15bfdff9586f3e is awaiting CI.

## Verification status correction — 30 October 2026

WebSocket timestamp validation and its regression tests passed Backend pytest on exact code/test head 4dd8420d4d787be049c956204e15bfdff9586f3e (run #41015772900). Latest synchronized documentation head 2589db1e0a6446ea60d12a075d58ce43fa19ed93 is awaiting exact-head CI #41015946896.

## Market-depth and token-scope audit — 30 October 2026

Exact code/test head `3a74fbb788a63ca3b042ceec400dbc7a83f32571` passed Backend CI #41016468736 (1,240 tests, 1 warning). Paper market fills use fresh Full Market Quotes V3 depth with side-aware depth consumption and quantity-weighted pricing; stale snapshot, invalid/mismatched instrument or insufficient depth fails closed. Next integration audit: distinguish Upstox Analytics Token (market-data/streaming) from standard daily OAuth access token (account/trading). Add separate encrypted storage and route by documented endpoint scope; never assume a refresh token.


## 2026-11-01 — Current Phase 4 status (supersedes older resume pointers)

- Latest verified green implementation head: `d0d26eb98ff5d77ce4f3ed1baee943bccaca51e4`; Backend CI [#41316803274 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41316803274). Checks: backend pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL and documentation-volume restore.
- LIVE balance-source protection and its fixture corrections passed CI #41315704407 on `9314703f31ff3ad31f2b97090cbfa1a5d4096a8c`.
- Mode-aware analytics implementation and regression tests are included in `d0d26eb` and passed #41316803274.
- Remaining: fail-closed LIVE positions API; explicit broker-account/LIVE-portfolio allocation; verified funds and positions sync; realized and freshness-gated unrealized P&L; Redis-to-execution and multi-worker end-to-end recovery/isolation; frontend mode selector; security/load/operational review.
- Current documentation synchronization commit is being validated separately; do not call the documentation head green until its exact-head CI succeeds.
- PR #9 remains Draft/unmerged. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `tarunsharma2610-del/Tradepro` remains untouched. LIVE broker place/modify/cancel writes remain disabled.
- Next code gate: inspect LIVE positions route and tests, then enforce mode-aware fail-closed behavior with regression coverage.



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
