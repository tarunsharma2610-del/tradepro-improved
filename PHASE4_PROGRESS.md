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

## Verified Analytics Token checkpoint — 30 October 2026

- Implementation head `083ab17a5150ea3be514438a16ea7c6c888c0be3` passed exact-head Backend CI run #41017833952: **1,243 tests passed, 1 warning**.
- Passed broker-write boundary enforcement; SQLite upgrade/downgrade/re-upgrade; PostgreSQL 16 migration round-trips; isolated synthetic PostgreSQL/document-volume restore drill.
- New Analytics Token implementation is accepted at code/test level: separately encrypted per-user token, owner-scoped save/status/clear endpoints, expiry fail-closed retrieval, and routing for market data, strategy candles, paper quote/charge calls and WebSocket reconnects.
- This does not mean a real user token has been entered or live Upstox connectivity has been validated. User must generate/copy the Analytics Token from Developer Apps > Analytics and configure it in Settings once UI is available.
- PAPER-only, live writes disabled, PR #8 Draft/unmerged, main untouched, original Tradepro untouched.


## Upstox option-chain + mode-correct streaming increment — 30 October 2026

- Exact preceding docs head `c00278fb33cc094a0f07d6a61d3ca9827f2dcdcf` passed Backend tests #41018852112 and #41018839615. These runs verify the preceding full-feed/doc checkpoint only, not the new code below.
- Added optional broker-adapter `get_option_chain` capability and Upstox implementation for the documented `GET /v2/option/chain` endpoint. The authenticated API route `GET /api/v1/market-data/option-chain` uses the separately stored Analytics Token only, validates exact ISO expiry or supported relative expiry keywords, and rejects MCX because Upstox documents that exchange as unsupported for this endpoint.
- Upstox's response supplies strike-wise call/put market data, OI, previous OI, volume, bid/ask and Greeks. The application adds `change_oi = oi - prev_oi` only when both source values are present and finite; otherwise the derived field is `null`. Original provider fields are retained and no missing/null value is converted to zero.
- Fixed a scope bug found during audit: the stream manager already retrieves Analytics Token, but the HTTP start route was still gating on daily OAuth. Stream start now correctly requires a valid Analytics Token; it does not require daily OAuth for public market-data streaming. The route reports the actual selected feed mode.
- Added explicit stream mode selection: `ltpc`, `option_greeks`, or `full`, defaulting to `full`. Mode-specific limits are validated before starting: LTPC 5,000; Option Greeks 3,000; Full 2,000. The user-scoped manager runs one stream per user, below Upstox's normal two-connection ceiling. No Plus-only Full D30 assumption.
- Option Greeks mode decodes the documented first-level bid/ask depth, Greeks and IV. Full mode retains D5 depth, OHLC and extended metadata parsing. Regression tests cover adapter endpoint/query/auth, provider errors, option-chain route, MCX rejection, expiry validation, OI delta semantics, Analytics Token-only stream authorization, selected modes and mode-specific limits.
- Code/test head: `42be7ad2a33c2e7a6db08842a5ec9c7c30154af5`. Exact-head CI for this increment is pending; do not claim green until the exact current PR head has passed backend tests and all safety/migration checks.
- Official contracts: https://upstox.com/developer/api-documentation/analytics-token/ ; https://upstox.com/developer/api-documentation/get-pc-option-chain/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ ; official V3 proto: https://assets.upstox.com/feed/market-data-feed/v3/MarketDataFeed.proto . Analytics Token supports Option Chain and WebSocket without static IP; MCX Option Chain is not available.
- Next after exact-head CI: add/verify index + India VIX feed presets and subscription lifecycle management (subscribe/change_mode/unsubscribe) with per-user limits; then test WebSocket recovery and option-chain snapshot/stream consistency. Do not create a duplicate market-data service or Redis bridge without a proven process-boundary need.
- Safety: only `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original Tradepro untouched; PAPER mode mandatory; live broker order writes disabled.


## Upstox V3 subscription lifecycle — 30 October 2026

- Verified the official V3 WebSocket contract directly: methods are `sub`, `unsub`, and `change_mode`; requests must be sent as binary protobuf-feed protocol frames containing JSON bytes. The V3 docs specify normal per-category individual limits of LTPC 5,000, Option Greeks 3,000 and Full 2,000; when categories are mixed, the combined limits are 2,000 for LTPC/Greeks and 1,500 for Full. This implementation deliberately uses one mode per user stream, so it enforces the corresponding individual limit and does not claim mixed-mode capacity.
- Added native live subscription management to the existing streamer: add instrument keys with `sub`, remove keys with `unsub`, and change the mode of the complete user stream with `change_mode`. It preserves the desired subscription set across reconnects and sends the current complete subscription/mode on the next connection.
- Mode changes invalidate cached ticks so depth/Greeks from a previous feed mode cannot be consumed as if they came from the newly selected mode. Unsubscribed ticks are removed. The final key cannot be removed via partial unsubscribe; use DELETE `/market-data/stream` to stop the stream.
- Added authenticated API endpoints: POST `/api/v1/market-data/stream/subscribe`, POST `/api/v1/market-data/stream/unsubscribe`, and POST `/api/v1/market-data/stream/change-mode`. Each is user-scoped, checks the Analytics Token, verifies active instrument keys before subscribing, and rejects requests when there is no running stream. Partial mixed-mode changes are intentionally rejected; change mode applies to all keys in the stream to keep one consistent parser/mode contract.
- Added tests for binary V3 control requests, dynamic subscribe/unsubscribe/change_mode, reconnect replay of updated desired state, per-mode limits, stale tick invalidation, active-instrument validation, and missing-stream conflict responses.
- Exact previous code/test head `e53ac0f9a24bf3a92a409fa548d59b41206a5042` passed Backend CI #41019403337. Current subscription-lifecycle head: `7aecd1e5b9a77a44fe3b0885a89a88e4826c2d33`; exact-head Backend CI #41019804917 is queued, and prior incremental runs are queued/running. Do not mark this lifecycle increment green until the latest exact head passes all backend, broker-write, SQLite/PostgreSQL migration and synthetic restore checks.
- Official source: https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ (method semantics, binary request format, India VIX key, and individual/combined limits).
- Next after exact-head CI: add verified index/India VIX presets based on instrument-master keys, then reconnect/subscribe race tests and end-to-end quote fan-out to the scanner/strategy data path. No second stream service, Redis bridge, or live-order capability is being added without a demonstrated requirement.
- Safety: only `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original Tradepro untouched; PAPER mode mandatory; live broker order writes disabled.


## Verified checkpoint — 30 October 2026 (subscription lifecycle CI green)

- Exact implementation commit `b87245002a24bb0bd002b7e0c7dc5bbc82085357` passed complete Backend CI run #41020300281: backend pytest, broker-write boundary, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL + document-volume restore drill, and restore evidence retention. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41020300281
- The lifecycle-test correction now tests partial mode-change rejection with two subscribed instruments, so the test exercises the actual partial-subscription case instead of incorrectly treating a single-instrument complete-stream mode change as partial.
- Subscription lifecycle implementation includes authenticated user-scoped subscribe/unsubscribe/change-mode routes, active-instrument validation before subscribe, per-mode subscription limits, reconnect replay, and invalidation of cached ticks after mode changes. No live broker order capability was introduced.
- This is the accepted code/test checkpoint. Documentation synchronization is being committed separately; the exact documentation head must receive its own CI verification before the next code increment.
- Next implementation: index feed presets backed by dynamically resolved and locally validated Upstox instrument keys (Nifty 50, Nifty Bank, India VIX). Do not hardcode exchange tokens. Use the official Instrument Search API and Upstox developer documentation; preserve provider identifiers and source timestamps. Then implement freshness/recovery observability and scanner/strategy fan-out.
- Official references: https://upstox.com/developer/api-documentation/instrument-search/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ ; India VIX key documented as `NSE_INDEX|India VIX`.
- Safety: work only in `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; do not change main or original `Tradepro`; PAPER mode mandatory; all live broker order writes remain disabled. No credentials or tokens in code, logs, docs or chat.


## Verified checkpoint — 30 October 2026 (rich market-data snapshot CI green)

- Exact implementation/test commit `036ad952ced862e94b2c4d3af75b79b43a0bbc28` passed full Backend CI run #41022649412: backend pytest, broker-write boundary, SQLite Alembic upgrade/downgrade/re-upgrade, PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, isolated synthetic PostgreSQL + document-volume restore, and evidence retention. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41022649412
- Corrected the missing-quote stream-status test to apply the normal authenticated-user dependency overrides. Production authentication remains required; the assertion that an absent latest quote is represented as unavailable remains in place.
- The stream status response now exposes the validated fresh tick snapshot fields needed by downstream read-only consumers: instrument key, LTP, exchange timestamp, receive time, depth, option Greeks, OI, traded volume, average traded price, total buy/sell quantities and OHLC. Missing quotes remain null; do not infer freshness from a missing tick.
- Index presets are implemented from the locally synchronized official Upstox instrument master and fail closed for missing/ambiguous matches. Do not hardcode dynamic exchange instrument identifiers.
- Architecture note: the existing WebSocket stream manager is process-local. A worker in a separate process cannot read its in-memory cache. Before scanner/strategy consumers depend on streamed ticks, implement and test a shared cross-process delivery layer using the Redis already present in deployment (or another justified existing shared store). Redis Pub/Sub alone is not durable: pair notification with a TTL-bounded latest-quote cache/snapshot, explicit timestamps, freshness checks, and reconnect/recovery semantics. On Redis loss or stale/missing quote, consumers must fail closed and retain existing candle freshness and PAPER/risk gates.
- Next work: audit current Redis configuration and Redis Python package APIs; define a small versioned quote envelope and namespaced user/instrument keys; implement publisher + cache write in the existing stream lifecycle; implement worker/API consumer with TTL and timestamp validation; test outage, reconnect, expiry, ownership isolation and process restart; only then connect scanner and paper strategy consumers.
- This checkpoint does not certify Redis fan-out, scanner integration or strategy integration as complete. No live broker order capability was introduced.
- Safety: work only in `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original `Tradepro` untouched; PAPER mode mandatory; live broker order submission/modification/cancellation disabled; no credentials in code, logs, docs or chat.


## Latest verified Phase 4 progress — 30 October 2026

- **Latest verified code/test commit:** `72b22a647f2b9a38ac7afc0aaee9547a67b16fcf`.
- **Exact-head Backend CI #41024607462: SUCCESS** — https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41024607462. Backend pytest job passed on the exact commit.
- Redis publisher implemented and connected to the Upstox V3 stream manager callback. Features: per-user key/channel namespace, versioned quote snapshot, TTL, exchange/receive timestamp and positive finite LTP validation, Pub/Sub notification, and no stale in-memory fallback.
- Publisher unit tests added; fake Redis pipeline context-manager and version-key expiry behaviour corrected after CI identified test-double issues.
- Status: publisher and callback wiring implemented; exact-head CI passed. Consumer, reconnect recovery, cross-process delivery tests, scanner and paper-strategy integration remain pending. Docs sync CI for this checkpoint remains pending.
- Resume next: verify docs sync commit's exact-head CI; then implement Redis consumer. Consumer should treat Pub/Sub as notification only and retrieve/validate the latest Redis snapshot, including user ID, schema version, version monotonicity, TTL and exchange timestamp.
- No live broker write path was added or enabled. PAPER remains mandatory. PR #9 remains Draft/unmerged; main is not to be updated without explicit user authorization. Work only in `tradepro-improved`; original `Tradepro` is out of scope.


## 30 October 2026 — Redis atomic publisher exact-head checkpoint

- Redis consumer implementation accepted on exact-head Backend CI #41025805338 (commit `a9e5cb59fde15dd273cde51b78acf063fd8ebe8c`).
- Added Redis 7 service to backend CI and real Redis integration tests for publisher/consumer round-trip, tenant isolation, snapshot TTL, Pub/Sub notification semantics, and consumer-instance restart recovery.
- Atomic Lua publisher commit `47e9108937270b288bf70a269d3dc89941884af2` was followed by correction commit `1c70e17a0ea54f8e8f219ae27d90aa46a02ea16e` adding missing JSON import in concurrency integration test.
- **Latest exact-head Backend CI #41026567279 PASSED** on `1c70e17a0ea54f8e8f219ae27d90aa46a02ea16e`: pytest, broker-write boundary, SQLite/PostgreSQL 16 migrations, synthetic restore, and evidence retention all passed.
- Atomic publisher performs version increment, snapshot write/expiry, and Pub/Sub publish in one Lua script. Real Redis concurrent publishing coverage added.
- Pending: automatic Redis reconnect/resubscribe, Redis server restart recovery, independent OS-process tests, scanner consumption, and PAPER strategy consumption. No scanner/strategy integration is claimed.
- Next implementation gate: reconnect/resubscription with bounded backoff and a post-reconnect authoritative snapshot sweep; add real Redis failure/restart tests before wiring scanner.
- PR #9 remains Draft/unmerged; no main update. PAPER mandatory; live broker writes disabled; original Tradepro untouched.


## 30 October 2026 — Redis version-counter lifecycle checkpoint

- **Exact-head Backend pytest CI #41031153316 PASSED** on `3088e49cf24317f58f7e04a60d6cd54e065143b4`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41031153316.
- Publisher no longer expires the per-user/per-instrument version counter; quote snapshots retain their configured TTL. This preserves monotonic versions when a quiet instrument's snapshot expires and later receives another tick.
- Added real Redis coverage verifying snapshot absence followed by a new publish produces the next version, not a reset version.
- Redis process-restart test exists and previously passed in #41029973040. Do not conflate that test with independent OS-process publisher/consumer validation or full production readiness.
- Pending: inspect startup/reconnect authoritative snapshot sweep, worker lifecycle and shutdown; independent OS-process delivery tests; multi-user/multi-instrument load and isolation tests; scanner consumption; PAPER strategy consumption.
- PR #9 remains Draft/unmerged; main untouched; PAPER mandatory; live broker writes disabled; original Tradepro out of scope.


## 30 October 2026 — Redis bounded epoch/version lifecycle checkpoint

- **Exact-head Backend CI #41032764754 PASSED** on `7268edd6e7ddb7ef6d472799d1d0164b4210b135`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41032764754. All workflow steps passed: backend pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore and evidence retention.
- Redis quote snapshots retain their configured short TTL; version counters use a bounded 24-hour default retention and carry a unique epoch. Atomic Lua allocates epoch/version, writes the snapshot and publishes the notification in one operation.
- Counter expiry or Redis data loss creates a new epoch; consumers validate epoch plus version, so a new epoch's version 1 is not rejected as regression. Legacy integer counters migrate on next publish.
- Real Redis suite covers snapshot TTL expiry, counter TTL expiry/new epoch, Pub/Sub disconnect recovery, Redis process restart, independent OS-process publisher/consumer delivery, two-user isolation and concurrent atomic version ordering.
- Intermediate commit `85d8c30` failed five unit tests because consumer fixtures lacked the new epoch field; corrected in `cb52cb8`, with final exact-head CI passing on `7268edd6e7ddb7ef6d472799d1d0164b4210b135`.
- Still pending: multi-user/multi-instrument scale/load tests; worker-managed consumer registry and graceful lifecycle; scanner integration; PAPER strategy consuming Redis snapshots. Strategy worker currently retains its candle-based evaluation path.
- PR #9 remains Draft/unmerged; main untouched; PAPER mandatory; live broker writes disabled; original Tradepro out of scope.



## Upstox SDK compatibility and CAS feed increment — 30 October 2026

- Official SDK compatibility audit saved in UPSTOX_SDK_COMPATIBILITY_AUDIT.md. Decision: do not add upstox-python-sdk as a runtime dependency now. Its generated REST client is synchronous (urllib3) and its WebSocket feeder is callback-based (websocket-client); our async httpx/websockets adapter has better fit for FastAPI lifecycle, dynamic token-provider refresh on reconnect, bounded exponential retry, freshness enforcement and application-owned Redis pipeline.
- Compared official SDK v2.30.0 V3 protobuf with our checked-in schema: exact schema match. No protobuf dependency replacement needed.
- Identified a real decoder gap: CAS fields already in our schema were not surfaced. Added indicative equilibrium price, reference price, indicative equilibrium quantity, total/market indicative quantities and CAS eligibility to MarketTick, Redis snapshots and stream status; added populated/absent-field tests.
- Exact-head Backend CI #41036389075 PASSED on 2212be0e094bb41423193b4384b6c07511ff3d62 after adding required broker-connection records to durable-subscription test fixtures.
- CAS implementation code head: fe76751c54a720ffa5fcec7b4f3728b137447090. Its exact-head CI is running/pending verification; do not mark CAS accepted until it passes. Earlier intermediate CAS commits also triggered runs; acceptance is tied only to final exact head.
- Newer SDK API coverage worth a later scanner/research roadmap review: v2.27 Fundamentals and Market Information APIs; v2.30 CAS quote/feed fields. Do not duplicate SDK methods where our adapter is already superior.
- Safety unchanged: only Tradepro Improved; PR #9 Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro untouched.


## SDK mixed-mode subscription finding — 30 October 2026

- Source-level SDK comparison found a real capability gap: official MarketDataStreamerV3 maintains separate LTPC/full/option_greeks/full_d30 subscription sets and replays each mode on socket open; Tradepro currently uses one mode for the whole user stream.
- Decision: borrow the per-mode registry and reconnect replay design, not the SDK's callback/websocket-client transport. Keep our asyncio transport, token-provider refresh on every reconnect, bounded exponential retry, protobuf validation and Redis delivery.
- Implementation is gated on the current CAS field propagation exact-head CI passing. Then extend durable subscription reconciliation to preserve per-instrument feed modes and enforce current official per-mode/combined limits. Scanner integration remains blocked until these tests pass.


## PAUSED — next implementation plan to resume here (30 October 2026)

**Do not restart from an older checkpoint. Resume from the latest Phase 4 branch head and the sequence below.**

### Gate 0 — repair the current exact-head CI failure

- Latest code head: 0cd3e2273f831b9e7d4968899ef8fc6a5d14a59d.
- Workflow #41037359835 FAILED in pytest: 1,304 passed, 2 failed. Both failures are in tests/test_upstox_option_chain_api.py because the test FakeStreamer fixture does not define the newly exposed market_info attribute. Production parser/API work is not the failure identified by CI.
- On resume, inspect the FakeStreamer fixture and add a safe default market_info=None (and a focused assertion if appropriate). Do not weaken/remove the production market status field or its tests.
- Rerun full backend pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic restore drill. Only checkpoint after all exact-head checks pass.

### Gate 1 — mixed feed-mode subscription implementation (next feature)

Borrow the useful design from official Upstox Python SDK v2.30.0, not its transport:

1. Replace the current one-mode-per-user stream assumption with a mode-indexed subscription registry for LTPC, full, option_greeks and full_d30 where officially supported.
2. Permit a user connection to carry different instruments in different feed modes concurrently, subject to current official Upstox limits.
3. Replay each mode's instrument set after every reconnect, using our own asyncio streamer and fresh token-provider call on reconnect.
4. Update durable subscription service/API reconciliation so subscribing, unsubscribing or changing one instrument's mode does not deactivate unrelated mode subscriptions.
5. Preserve user/broker ownership isolation, validate instrument keys and feed modes, and enforce per-mode plus combined connection limits from current official docs.
6. Restore mixed-mode desired subscriptions after API/worker restart.
7. Add tests for mixed modes, mode-specific changes, duplicate requests, limits, reconnect replay, token refresh, startup recovery, Redis delivery and tenant isolation.
8. Benchmark/verify against the official SDK's behaviour and record the comparison; do not add SDK dependency unless a separately proven benefit emerges.

### Gate 2 — only after mixed-mode tests and CI are green

- Integrate Redis quote consumers with the scanner's broad LTPC universe, selected full-depth instruments and selected option-Greeks contracts.
- Validate freshness, stream silence, mode correctness and missing-field behaviour at the scanner boundary.
- Keep PAPER mode mandatory and all live broker order writes disabled.

### Preserved architecture decision

Keep the existing async httpx/websockets adapter, application OAuth/token lifecycle, V3 protobuf decoder, Redis snapshot/version/epoch delivery, freshness validation and domain-level safeguards. Do not add upstox-python-sdk as a runtime dependency merely for parity; selectively borrow proven SDK capabilities. See UPSTOX_SDK_COMPATIBILITY_AUDIT.md.

### Safety and repository boundary

Work only in tarunsharma2610-del/tradepro-improved on phase4/redis-market-data-publisher. PR #9 remains Draft/unmerged. Do not modify tarunsharma2610-del/Tradepro. No live broker place/modify/cancel calls.


## Phase 4 update — 30 October 2026

- Latest verified code/test commit: `ef80d792c4d89abda1850b73f54f7b81bf16bbf7`.
- Exact-head Backend CI [#41057600440 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41057600440), including pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore/evidence checks.
- Feed-mode subscription persistence now replaces only the selected mode's desired instrument set; other modes remain active. Regression coverage added for independent `ltpc` and `full` subscriptions.
- CI failure #41057234551 was an outdated single-mode test expectation; corrected on the verified head.
- Next: implement and test mixed-mode V3 WebSocket subscribe/unsubscribe, reconnect replay, and Redis consumer lifecycle. Persistence tests do not yet prove end-to-end mixed-mode streaming.
- PR #9 remains Draft/unmerged. PAPER mode mandatory; live broker writes disabled; original `Tradepro` repository out of scope.


## Phase 4 update — Redis consumer recovery hardening — 30 October 2026

- Prior exact-head Backend CI #41060945704 passed on `f7c863977ed17a3d705b83db8dcc6b7ba421cccf`, including the reconnect token-refresh regression.
- New head `a5e352bef2c78f27141b61bca5893fdfa0fd049a` adds Redis consumer tests for Redis data-loss epoch rollover (old epoch version 8 -> new epoch version 1) and idle Pub/Sub PING/PONG heartbeat. Exact-head CI #41061518847 is running; acceptance is pending.
- Audited the Redis consumer: it validates authoritative snapshots, user/instrument identity, TTL, exchange and receive timestamps, epoch/version, and ignores Pub/Sub payloads except as wake-up signals. It resubscribes and sweeps authoritative snapshots after reconnect; heartbeat detects a silent dead Pub/Sub socket.
- Worker currently does not manage Redis consumer instances; strategy evaluation remains on the existing candle path. Scanner/PAPER strategy Redis consumption is not implemented.
- Next gate: exact-head CI; then implement a controlled worker consumer lifecycle with durable subscription discovery, single-owner coordination, graceful shutdown/cancellation and reconnect tests. Only then connect scanner/PAPER evaluation.
- PR #9 Draft/unmerged; PAPER-only; live broker writes disabled; original Tradepro repository untouched.


## Latest verified checkpoint — 30 October 2026

- Implementation commit `6ac3882a98f3c66abb4cd62848971b6277ab3be7` passed exact-head Backend CI [#41080156436](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41080156436); Backend pytest success, no failed steps.
- Added transactional `PaperStopEventClaimService`: ownership validation; portfolio → strategy → position locks; open position requirement; ambiguous shared portfolio/instrument ownership fails closed; unique quote-event identity; claim token/lease/attempt metadata; duplicate insert protected by nested savepoint.
- Claim service is not connected to dispatcher or order execution. Caller owns transaction commit/rollback.
- Next: PostgreSQL 16 multi-session claim race tests; explicit state transitions and lease reclaim; crash recovery; shared-position allocation decision; only then controlled dispatcher-to-PAPER execution.
- Do not enable live writes, merge PR #9, or deploy. PR #9 remains Draft/unmerged; PAPER mandatory.
- The documentation synchronization commit is separate and requires exact-head CI.
