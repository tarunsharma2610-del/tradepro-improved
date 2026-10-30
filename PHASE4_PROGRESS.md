# Phase 4 Progress

- Repository: `tarunsharma2610-del/tradepro-improved` only.
- Branch: `phase4/roadmap-progress-checkpoints`.
- Starting commit: `9add7f98ccf89f0c146e4367b79cdd5877104ff3`.
- Starting Phase 3 CI: [Backend CI #40885193019](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40885193019) — reported successful in the handover context.
- Current Phase 4 status: **Planning/checkpoint scaffolding only. Audit not yet performed; no Phase 4 feature implementation claimed.**

## Completed in this checkpoint
- [x] Created dedicated Phase 4 branch `phase4/roadmap-progress-checkpoints` from the specified Phase 3 checkpoint commit.
- [x] Wrote Phase 4 roadmap and progress/checkpoint records.
- [ ] Run an exact-head CI on the new Phase 4 documentation commit(s).
- [ ] Verify the latest branch head and CI status after documentation updates.
- [x] Perform P4-0 static baseline audit and publish `PHASE4_P0_BASELINE_AUDIT.md`.
- [x] Implement fail-closed `TRADING_MODE=PAPER` validation in `backend/app/core/config.py`.
- [x] Add `backend/tests/test_trading_mode_safety.py` for PAPER normalization and LIVE/invalid-mode rejection.
- [ ] Obtain backend CI on the exact final Phase 4 head; no green status claimed yet.
- [ ] Continue P4-0B broker-write boundary call-path audit after CI.

## Work packages
- P4-0 baseline/audit: STATIC AUDIT DONE; safety config hardening committed, CI pending.
- P4-1 risk and paper execution safety: NOT STARTED; audit before deciding what is missing.
- P4-2 paper lifecycle/accounting integration: NOT STARTED; preserve Phase 3 invariants.
- P4-3 persistence/security/observability: NOT STARTED.
- P4-4 Upstox read-only integration readiness: NOT STARTED.
- P4-5 CI/docs/checkpoint: IN PROGRESS; exact-head CI pending.

## Non-negotiable safeguards
- Only `tarunsharma2610-del/tradepro-improved`; never modify `tarunsharma2610-del/Tradepro`.
- Do not update `main` or merge PR #6 / PR #7; keep Draft PRs unmerged absent explicit authorization.
- PAPER mode mandatory. Live broker order writes (`place_order`, `modify_order`, `cancel_order`) remain disabled.
- Do not promote brokerage estimates or aggregate post-trade API results into per-fill actual charges.
- Keep unsupported or unverified tariff scopes estimate-only/fail-closed for actual accounting.
- Production OAuth smoke tests and real Oracle restore remain deferred until deployment and authorized credentials/backups exist.

## Resume protocol
At the start of each continuation: verify the branch head, read this file and `PHASE4_LATEST_CI_CHECKPOINT.md`, inspect exact-head CI, then continue at the first unchecked item. Never infer success from a prior commit's CI. If CI fails, fix the failure and rerun before checkpointing green.


## Phase 4 resume checkpoint — 29 October 2026 (latest verified code CI)

- Repository: `tarunsharma2610-del/tradepro-improved` only; branch: `phase4/roadmap-progress-checkpoints`.
- Draft PR #8: https://github.com/tarunsharma2610-del/tradepro-improved/pull/8; base is `phase3/cross-broker-gst-ipft-resolution`. PR remains unmerged. `main` has not been updated. PR #6/#7 remain unmerged.
- **Latest verified code/test head:** `13bcb6c6b25387916b8e653cb0ba8dd3ad3c31ad`.
- **Backend CI #40898908339: SUCCESS** on that exact head: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40898908339. Backend pytest, broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, and synthetic PostgreSQL/document-volume restore/evidence retention all passed.
- CI failure on earlier run #40896927805 was traced to the Upstox Brokerage Details test fixture asserting IPFT under the wrong field. Corrected fixture/assertion uses `data.charges.otherTaxes.ipft`, preserving null distinctly; the retry passed.
- P4-0 static audit saved in `PHASE4_P0_BASELINE_AUDIT.md`. PAPER-only config validation added in `backend/app/core/config.py`; tests added in `backend/tests/test_trading_mode_safety.py`.
- **Next step on resume:** verify the current branch head and latest CI (documentation updates can trigger a newer head/run); then continue P4-0B broker-write call-path audit and add targeted tests for every route into broker write methods, automated-entry kill switch, stale market data, and risk checks. Fix any failure and re-run before checkpointing green.
- Safeguards: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` untouched; do not update `main` or merge PR #8/#7/#6 without explicit authorization; PAPER mode mandatory; live `place_order`, `modify_order`, `cancel_order` writes disabled; Upstox Brokerage Details remains estimate-only and aggregate Trade Charges remains reconciliation-only; no credentialed live smoke test or production Oracle restore claimed.

## User-directed engineering principle — 30 October 2026

Use Upstox Developer Console, official current API documentation, supported APIs, SDKs, and schema/proto files whenever they are the right tool. Audit existing implementation first; do not build bespoke polling, duplicate services, or workaround layers before checking provider-supported solutions. Custom fallbacks need a stated reason and tests. Local freshness checks are defense-in-depth, not a substitute for wiring the supported live stream and REST recovery path into strategy data.

Official docs checked: https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ ; https://upstox.com/developer/api-documentation/v3/get-intra-day-candle-data/ ; https://upstox.com/developer/api-documentation/installing-sdk/.

Audit finding: V3 streamer and REST methods exist, but strategy execution is not yet consuming a shared stream/candle pipeline, and candle parsing is explicitly marked BEST-EFFORT. Next priority: verify response ordering/timestamp/field contracts against official examples; connect existing WebSocket + REST recovery to strategy candles; add integration tests for disconnect/gap recovery and instrument identity. Do not enable live order writes.

## 30 October 2026 — supported intraday API integration

Implemented the first direct API correction rather than adding more stale-data heuristics:
- Added a broker-level optional intraday-candle capability and Upstox V3 implementation using the official current-session candle endpoint.
- Strategy candle loading now combines historical V3 candles with current-session V3 intraday candles using Asia/Kolkata date boundaries and timestamp deduplication; intraday rows win on overlap.
- Fail-closed behavior remains if either required source is unavailable or malformed.
- Added tests for the exact endpoint/auth contract, historical+intraday merge, source failure, and strategy fixture compatibility.
- Exact current code head: d7c786fc164ed297df42f26493c994ceacd337a7. CI pending for this head; previous successful run #41014529152 was on the earlier head 58e6674dab5c02f725f76401af358397fd47c161.
- Next: verify exact-head CI, fix failures, then assess WebSocket integration into the worker. Don't aggregate these as complete yet. No live account test has been performed.

## 30 October 2026 — timestamped quote validation

- Confirmed Upstox LTP V3 supplies last_price but not last_trade_time; Full Market Quotes V3 supplies both last_price and last_trade_time plus instrument_token.
- Added optional full-quote broker capability and Upstox V3 endpoint. Paper execution now prefers a fresh subscribed WebSocket tick, otherwise uses Full Market Quotes V3 and validates instrument identity and exchange last-trade time (<=15 seconds old; <=60 seconds future skew).
- Missing, stale or mismatched quote fails closed; no fallback to stale candle close or guessed LTP.
- Added endpoint and quote-validation tests; updated strategy/execution fixtures.
- Latest head 65f8070e344eaa4cd8cb82c876732662d02cc3a3; exact-head CI queued/running. Prior exact-head checkpoint d2662b05d4910d9bf93e307fb08f10a1609405ee passed backend and migration CI.

## 30 October 2026 — WebSocket tick integrity

- Diagnosed five CI failures on earlier quote integration: all were test assertions requiring "price" wording; invalid prices were correctly rejected. Clarified message without relaxing validation.
- Audited Upstox V3 streamer: removed unsafe fallback from missing LTPC last-trade time to packet currentTs. Missing LTT or non-finite/non-positive LTP is no longer cached; latest_tick requires a positive exchange timestamp and validates exchange age plus local monotonic receive age.
- Added regression tests for non-finite LTP and missing LTT.
- Current code head 4dd8420d4d787be049c956204e15bfdff9586f3e. CI #41015772900 is running on this test head; prior code/message runs #41015756833 and #41015671461 are also running. No green claim until exact-head result.

## CI result — 30 October 2026

Backend pytest passed on code/test head 4dd8420d4d787be049c956204e15bfdff9586f3e (run #41015772900). The WebSocket code head d7c74a20a4a46741123ebbf4809176e90199643c passed run #41015756833; the rejection-message correction head 90bb1f5bf9d43767043a653e68a55b374bf0c599 passed run #41015671461. Latest documentation head 2589db1e0a6446ea60d12a075d58ce43fa19ed93 is in CI run #41015946896; await exact-head result.

## 30 October 2026 — market-depth execution and CI checkpoint

- Exact code/test head `3a74fbb788a63ca3b042ceec400dbc7a83f32571`; Backend CI #41016468736 passed: 1,240 tests, 1 warning, including broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore drill.
- Paper market fills use fresh Full Market Quotes V3 depth, consuming asks for BUY and bids for SELL, calculating a depth-weighted average, and rejecting stale snapshots, wrong instruments, invalid prices or insufficient depth.
- Test fixtures updated to V3 depth contract; obsolete LTPC-only stream monkeypatch removed. CI fixes changed test fixtures/wording only, not safety semantics.
- OAuth audit: standard Upstox access token expires at 3:30 AM IST next day; expired token fails closed. Official docs identify a distinct Analytics Token for market data and streaming without daily reauthorization. Next: separately encrypted analytics-token persistence and scope-correct market-data routing.
 
## Upstox Analytics Token implementation — 30 October 2026

- Added separate encrypted `analytics_token_encrypted` and `analytics_token_expires_at` fields to per-user broker connections with migration `202610300031` (down revision `202610270030`).
- Added owner-scoped Settings API to save, inspect status and clear Analytics Token. Token is accepted from the user's Upstox Developer Apps > Analytics page; it is never returned, logged or included in API responses. Expiry is tracked as 365 days from local registration; confirm/renew against the Developer Console's actual expiry date.
- Analytics Token retrieval is independent of standard OAuth `is_connected` state and fails closed when missing/expired. Standard OAuth access-token path remains separate for operations not documented as Analytics Token eligible.
- Routed strategy historical/intraday candle fetch, paper market quote/charge estimation, queued paper limit-order quotes, and market WebSocket reconnects through Analytics Token. Broker order/trade ingestion continues to use standard OAuth until each endpoint's Analytics Token/static-IP eligibility is deliberately enabled.
- Analytics Token is read-only. It cannot place, modify or cancel orders. Live trading remains disabled; PAPER-only guard unchanged.
- Official docs: https://upstox.com/developer/api-documentation/analytics-token/ ; https://upstox.com/developer/api-documentation/announcements/analytics-token-static-ip/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- CI for this new implementation is pending. Do not mark it accepted until exact-head CI passes, including migration round-trip and token isolation tests.
