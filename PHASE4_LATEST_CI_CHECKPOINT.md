# Phase 4 Latest CI Checkpoint

## Current checkpoint state
- Repository: `tarunsharma2610-del/tradepro-improved` only.
- Branch: `phase4/roadmap-progress-checkpoints`.
- Base commit: `9add7f98ccf89f0c146e4367b79cdd5877104ff3`.
- Base Phase 3 workflow: [Backend CI #40885193019](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40885193019) — reported successful for the Phase 3 checkpoint.
- Latest code/test commits: `791ae9858d80ddf5554db71f134db273e55be29b` (PAPER-only config enforcement) and `1517b2947709f96083dc48e06edfebe32152d37f` (regression tests). Latest documentation/audit commit before checkpoint update: `082956a3fe1e9643510b18054e8f7333a578a091`.
- Exact-head CI for the current Phase 4 head: **PENDING VERIFICATION**. No passing run is claimed. The repository's backend workflow runs on pull requests or workflow_dispatch; branch pushes alone do not trigger it.

## Scope of this checkpoint
This checkpoint creates Phase 4 planning/resume records only. It does not claim that the repository audit, deployment, OAuth smoke test, production Oracle backup/restore, or Phase 4 implementation has been completed.

## Next required actions
1. Verify the new branch's latest commit and the CI workflow triggered by the documentation commits.
2. If the workflow is running, wait/check the exact run. If failed, inspect job logs, fix on this Phase 4 branch, and rerun.
3. Once green, record exact commit SHA, run URL/ID, job outcomes, and any warnings here and in `PROGRESS.md` / `HANDOVER.md`.
4. Open/verify a draft Phase 4 PR to trigger backend CI without merging; inspect failures and fix them on this branch. Then continue P4-0B broker-write boundary call-path audit from the first green checkpoint.

## Safety checklist
- [x] Only the `tarunsharma2610-del/tradepro-improved` repository is in scope.
- [x] Original `tarunsharma2610-del/Tradepro` is out of scope.
- [x] No `main` update or PR merge authorized/performed by this checkpoint.
- [x] PAPER mode remains mandatory; live broker writes remain disabled.
- [x] Upstox brokerage API is estimate-only; post-trade charge API is aggregate reconciliation-only.
- [x] PR #6 and PR #7 must remain Draft/unmerged unless explicitly authorized.
- [x] Static P4-0 audit published.
- [x] Non-PAPER configuration rejected at settings load; regression tests added.
- [ ] Exact-head Phase 4 backend CI verified green.


## Phase 4 resume checkpoint — 29 October 2026 (latest verified code CI)

- Repository: `tarunsharma2610-del/tradepro-improved` only; branch: `phase4/roadmap-progress-checkpoints`.
- Draft PR #8: https://github.com/tarunsharma2610-del/tradepro-improved/pull/8; base is `phase3/cross-broker-gst-ipft-resolution`. PR remains unmerged. `main` has not been updated. PR #6/#7 remain unmerged.
- **Latest verified code/test head:** `13bcb6c6b25387916b8e653cb0ba8dd3ad3c31ad`.
- **Backend CI #40898908339: SUCCESS** on that exact head: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40898908339. Backend pytest, broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, and synthetic PostgreSQL/document-volume restore/evidence retention all passed.
- CI failure on earlier run #40896927805 was traced to the Upstox Brokerage Details test fixture asserting IPFT under the wrong field. Corrected fixture/assertion uses `data.charges.otherTaxes.ipft`, preserving null distinctly; the retry passed.
- P4-0 static audit saved in `PHASE4_P0_BASELINE_AUDIT.md`. PAPER-only config validation added in `backend/app/core/config.py`; tests added in `backend/tests/test_trading_mode_safety.py`.
- **Next step on resume:** verify the current branch head and latest CI (documentation updates can trigger a newer head/run); then continue P4-0B broker-write call-path audit and add targeted tests for every route into broker write methods, automated-entry kill switch, stale market data, and risk checks. Fix any failure and re-run before checkpointing green.
- Safeguards: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` untouched; do not update `main` or merge PR #8/#7/#6 without explicit authorization; PAPER mode mandatory; live `place_order`, `modify_order`, `cancel_order` writes disabled; Upstox Brokerage Details remains estimate-only and aggregate Trade Charges remains reconciliation-only; no credentialed live smoke test or production Oracle restore claimed.

## Phase 4 checkpoint — 30 October 2026: P4-0B static reflection guard

- Latest code/test head: `24c34dac47e273f9377485dc697f9fa510808a72`.
- Exact-head Backend CI: [#41012821073 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41012821073).
- The backend pytest job passed, including the broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, and synthetic PostgreSQL/document-volume restore drill.
- Change: AST guard now rejects literal `getattr(adapter, "place_order"/"modify_order"/"cancel_order")` dispatch; regression tests verify literal write methods are blocked and ordinary read-method reflection is allowed.
- An intermediate run #41012807565 failed because the first test version wrote literal backslash-n characters into its synthetic source file, causing a SyntaxError. The fixture escaping was corrected; run #41012821073 passed on the corrected exact head.
- PR #8 remains Draft/unmerged; `main` was not updated. PR #6/#7 remain unmerged.
- Next: P4-0C, test automated-entry kill-switch behavior and verify exit paths remain available, then audit stale-market-data handling and risk checks at service boundaries.
- Static-analysis limit remains explicit: dynamically computed method names and arbitrary reflection cannot be fully proven safe by this AST guard.
- Safety invariants unchanged: only `tradepro-improved`; PAPER mandatory; live broker writes disabled; no live order, deployment, credentialed smoke test, or production Oracle restore claimed.

## Engineering directive and next integration correction — 30 October 2026

User direction: work smarter, not by layering workarounds. Prefer Upstox Developer Console, official current API docs, official SDKs, and supplied schemas/proto wherever applicable. Audit existing integration first; explain any custom workaround and why it is needed. Local freshness validation is defense-in-depth, not the primary data-freshness architecture.

Official contracts checked:
- Market Data Feed V3: https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- Intraday Candle Data V3: https://upstox.com/developer/api-documentation/v3/get-intra-day-candle-data/
- Official SDK installation: https://upstox.com/developer/api-documentation/installing-sdk/

Repo audit finding: backend/app/services/upstox_market_data_streamer.py already implements V3 authorization/reconnect/protobuf tick intake; backend/app/brokers/upstox/adapter.py has V3 quote and historical candle REST calls; backend/app/services/candle_parsing.py still labels response validation BEST-EFFORT; strategy execution fetches candles independently rather than consuming a shared stream/candle pipeline. Next task: verify documented contracts and design a shared data/candle pipeline with REST warm-up/gap recovery and WebSocket updates, not more isolated stale-data workarounds. Do not add/switch SDKs without checking dependency compatibility and actual endpoint coverage.

Prior exact-head Backend CI #41013144850 passed on c8704cf97af3b2a31cd19114ae56f51dd796b08. Instruction/document changes in this continuation require new exact-head CI before a new green checkpoint is claimed. PR #8 stays Draft/unmerged; main remains untouched; PAPER-only/live-write safeguards remain mandatory.

## Upstox candle API integration continuation — 30 October 2026

- Verified official Upstox V3 intraday candle endpoint and schema: https://upstox.com/developer/api-documentation/v3/get-intra-day-candle-data/
- Added optional BrokerAdapter.get_intraday_data(...) capability with an explicit unsupported result for adapters that do not implement it.
- Implemented Upstox V3 /historical-candle/intraday/{instrument_key}/{unit}/{interval} call with encoded instrument key and bearer authorization.
- Strategy candle loading now requests historical and current-session intraday candles concurrently, uses exchange-local (Asia/Kolkata) date boundaries, merges by UTC-normalized timestamp, and prefers intraday candles on overlap. If either source fails or returns malformed/empty candle data, it fails closed instead of inventing partial history.
- Added endpoint contract test and candle-source merge/failure regression tests; updated strategy test adapter fixture to model both endpoints.
- Current code head after this work: d7c786fc164ed297df42f26493c994ceacd337a7. CI for this exact head and subsequent docs is pending; do not label it green until verified.
- Prior CI run #41014529152 passed on earlier head 58e6674dab5c02f725f76401af358397fd47c161. This does not prove the new API integration.
- Still not complete: wiring WebSocket tick state into the running strategy worker; live Upstox account/Developer Console verification unavailable in this session. The official Python SDK was reviewed, but not added because the current V3 streamer already uses Upstox protobuf schema and SDK addition has not been shown to improve this path.
- Safeguards unchanged: only tarunsharma2610-del/tradepro-improved; PR #8 Draft/unmerged; main untouched; PAPER mandatory; live broker writes disabled.

## Timestamped quote validation — 30 October 2026

- Exact prior checkpoint verified green: commit d2662b05d4910d9bf93e307fb08f10a1609405ee; backend CI #41014929096 and migration CI #41014916708 both passed.
- New API-first improvement: Upstox LTP V3 response contains last_price but no last-trade timestamp. The Full Market Quotes V3 endpoint supplies last_price, instrument_token and last_trade_time (epoch milliseconds), so the paper execution price path now prefers a fresh WebSocket tick and otherwise requests the timestamped Full Market Quote V3 endpoint.
- REST fallback validates exact instrument_token, finite positive price, present last_trade_time, maximum 15-second trade age, and rejects timestamps more than 60 seconds in the future. Missing/mismatched/stale quote rejects the paper market order rather than silently using an old LTP.
- Added optional broker full-quote capability, Upstox V3 adapter implementation, endpoint contract test, timestamp validation test, and updated execution/strategy fixtures.
- Latest code head: 65f8070e344eaa4cd8cb82c876732662d02cc3a3. Exact-head CI is queued/running; do not mark green until it completes.
- Official docs: https://upstox.com/developer/api-documentation/get-full-market-quote-v3/ and https://upstox.com/developer/api-documentation/ltp-v3/
- Architecture finding: API-started WebSocket manager is process-local; worker has its own process. However, paper order execution already has a REST LTP fallback. Timestamped Full Market Quotes V3 now strengthens that fallback. No Redis bridge or second worker stream is justified yet for the current five-minute strategy cadence; keep WebSocket integration scoped to real-time use cases that demonstrably need it.
- Safeguards unchanged: only tarunsharma2610-del/tradepro-improved; PR #8 Draft/unmerged; main untouched; PAPER mandatory; live broker writes disabled.

## WebSocket tick integrity and CI correction — 30 October 2026

- Investigated CI failures on commit 6212723741425e970fe62b712659d4739dd6df6f. All five failures were assertions expecting the rejection reason to contain "price"; invalid NaN, Infinity, negative and zero prices were already rejected. Updated only the rejection wording in commit 90bb1f5bf9d43767043a653e68a55b374bf0c599; no validation was weakened.
- Further audit found a real edge case in Upstox WebSocket parsing: it fell back from missing LTPC last-trade time to packet currentTs, which could make an old trade look newly traded. Removed that fallback; a tick is cached only when LTP is finite and positive and exchange LTPC LTT is present/positive. latest_tick now rejects missing exchange timestamps and checks both receive monotonic age and exchange timestamp age/future skew.
- Added regression coverage for NaN/Infinity LTP and missing LTT. Current code head: 4dd8420d4d787be049c956204e15bfdff9586f3e.
- CI runs: #41015671461 on message-only correction 90bb1f5; #41015756833 on WebSocket code d7c74a20; #41015772900 on tests 4dd8420d. At checkpoint writing, all were still running; do not mark any as green until completed.
- Official API docs confirm Full Market Quotes V3 returns instrument_token, last_price, last_trade_time (milliseconds); Market Data Feed V3 LTPC provides ltp and ltt. Sources: https://upstox.com/developer/api-documentation/get-full-market-quote-v3/ and https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- Stream architecture remains intentionally simple: API process uses fresh WebSocket ticks when available; separate worker process cannot share the in-memory registry and therefore uses timestamped REST full quotes. No Redis bridge added without a concrete need.
- Safeguards unchanged: only tarunsharma2610-del/tradepro-improved; PR #8 Draft/unmerged; main untouched; PAPER mandatory; live broker writes disabled.

## CI result correction — 30 October 2026

- Exact code/test head 4dd8420d4d787be049c956204e15bfdff9586f3e passed Backend pytest in run #41015772900.
- WebSocket implementation head d7c74a20a4a46741123ebbf4809176e90199643c passed Backend pytest in run #41015756833.
- Rejection-message correction head 90bb1f5bf9d43767043a653e68a55b374bf0c599 passed Backend pytest in run #41015671461.
- Latest documentation head at this update: 2589db1e0a6446ea60d12a075d58ce43fa19ed93; exact-head CI #41015946896 is running. Older doc-head runs #41015887638 and #41015931607 are also running; only the newest exact head should be used for final green status.

## Exact-head correction and market-depth pricing — 30 October 2026

- Latest code/test head: `3a74fbb788a63ca3b042ceec400dbc7a83f32571`.
- Exact-head Backend CI run **#41016468736 passed**: 1,240 tests passed, 1 warning. The run also passed broker-write boundary enforcement, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trips, and the isolated synthetic PostgreSQL/document-volume restore drill.
- Earlier failing runs were traced to obsolete LTPC-only test monkeypatches, strategy fixtures missing the new V3 market-depth shape, and rejection wording. These were corrected; no production safety validation was weakened.
- Paper market orders now price from fresh Full Market Quotes V3 snapshot depth: BUY consumes ask levels, SELL consumes bid levels, and the fill price is volume-weighted across levels. The snapshot timestamp is validated independently of last_trade_time; an old last trade alone does not invalidate a fresh book. Insufficient depth, stale snapshot, mismatched instrument or invalid price fails closed.
- Strategy execution fixtures now include the documented market-depth response. Removed obsolete test monkeypatch for the old LTPC stream path.
- New Upstox authentication finding: official docs distinguish daily standard access tokens from Analytics Tokens, which are intended for market data and real-time streaming without daily reauthorization. Next package: add separately encrypted Analytics Token storage and route only supported market-data/stream calls through it; keep standard OAuth access token for account/trading permissions. Do not reuse either token across scopes.
- Official docs: https://upstox.com/developer/api-documentation/get-full-market-quote-v3/ ; https://upstox.com/developer/api-documentation/get-token/ ; https://upstox.com/developer/api-documentation?f=K110
- Safeguards unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #8 Draft/unmerged; main untouched; PAPER mandatory; live broker writes disabled.
 
## Upstox Analytics Token implementation — 30 October 2026

- Added separate encrypted `analytics_token_encrypted` and `analytics_token_expires_at` fields to per-user broker connections with migration `202610300031` (down revision `202610270030`).
- Added owner-scoped Settings API to save, inspect status and clear Analytics Token. Token is accepted from the user's Upstox Developer Apps > Analytics page; it is never returned, logged or included in API responses. Expiry is tracked as 365 days from local registration; confirm/renew against the Developer Console's actual expiry date.
- Analytics Token retrieval is independent of standard OAuth `is_connected` state and fails closed when missing/expired. Standard OAuth access-token path remains separate for operations not documented as Analytics Token eligible.
- Routed strategy historical/intraday candle fetch, paper market quote/charge estimation, queued paper limit-order quotes, and market WebSocket reconnects through Analytics Token. Broker order/trade ingestion continues to use standard OAuth until each endpoint's Analytics Token/static-IP eligibility is deliberately enabled.
- Analytics Token is read-only. It cannot place, modify or cancel orders. Live trading remains disabled; PAPER-only guard unchanged.
- Official docs: https://upstox.com/developer/api-documentation/analytics-token/ ; https://upstox.com/developer/api-documentation/announcements/analytics-token-static-ip/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- CI for this new implementation is pending. Do not mark it accepted until exact-head CI passes, including migration round-trip and token isolation tests.

## CI correction — 30 October 2026

- Latest implementation/test head: `083ab17a5150ea3be514438a16ea7c6c888c0be3`.
- Previous exact-head run #41017634485 had 1,242 passed and one test-only failure caused by SQLite returning a naive datetime in the expiry assertion. Corrected the test to normalize that value to UTC; production expiry checks already normalize it.
- Exact-head run #41017833952 is running. Acceptance remains pending until the exact head passes pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore drill.
- PAPER-only guard remains enforced; PR #8 remains Draft/unmerged; no main update; original Tradepro repository untouched.


## Upstox V3 full market feed increment — 30 October 2026

- Audited the existing V3 streamer before changing it; retained the existing authorized-URL flow, TLS validation, protobuf decoder, reconnect loop, stale-tick rejection and callback contract.
- Extended `UpstoxMarketDataStreamer` to subscribe in official V3 `full` mode by default (five-level depth; Upstox documentation calls this `full`, not `full_d5`). LTPC and `option_greeks` remain explicit supported modes. `full_d30` is deliberately rejected because it is a Plus entitlement and not assumed available.
- Full-mode tick model now exposes bid/ask depth, option Greeks, OI, traded volume, average traded price, total buy/sell quantity and OHLC snapshots. Optional provider fields remain `None` when not supplied; proto3 scalar default zero is not represented as confirmed data. Existing freshness validation remains unchanged.
- Applied documented individual subscription limits: LTPC 5,000; option Greeks 3,000; full 2,000. The V3 docs also specify a 1,500 combined limit when mixing categories and per-user connection limits; cross-connection aggregate enforcement belongs in a user-scoped subscription manager and remains a follow-up, not claimed complete here.
- Added regression tests for full-feed decoding, absent-field semantics, mode-specific limits, and exact binary subscription request mode.
- Code/test head: `8ba7009ef478ec256ba8b882351bdf514a9e324e`. Exact-head CI is pending verification; no green status is claimed for this increment.
- Official contract checked: https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ . The official documentation describes `full` as LTPC + five market levels + metadata + Greeks, and confirms India VIX instrument key `NSE_INDEX|India VIX`.
- Next: verify exact-head CI and fix any failures; then implement the official Option Chain REST endpoint using `oi`, `prev_oi`, volume and Greeks, with missing/null/zero kept distinct. Follow with a subscription manager and shared worker/API market-data pipeline.
- Safety: only `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original Tradepro untouched; PAPER mode mandatory; live broker order writes disabled.


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


## Redis publisher checkpoint — 30 October 2026 (exact-head CI passed)

- Repository: `tarunsharma2610-del/tradepro-improved` only. Implementation branch: `phase4/redis-market-data-publisher`; Draft PR #9 targets `phase4/roadmap-progress-checkpoints`. PR #9 remains open, Draft and unmerged.
- **Exact verified head:** `72b22a647f2b9a38ac7afc0aaee9547a67b16fcf`.
- **Backend CI #41024607462: SUCCESS on that exact SHA** — https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41024607462. Backend pytest job completed successfully. This checkpoint records the job conclusion; no test count or unreported workflow checks are inferred.
- Added `backend/app/services/redis_market_quote_publisher.py`: per-user Redis namespace, versioned latest-quote snapshots, TTL, timestamp/price/instrument validation, and Pub/Sub notification. Latest snapshot is the source of truth; Pub/Sub is a wake-up signal. Version counter receives expiry.
- Connected the existing Upstox V3 stream manager's asynchronous `on_tick` callback to the publisher in `backend/app/services/market_data_stream_manager.py`. Redis publishing failure is logged and returns unavailable; there is no in-memory fallback for downstream consumers.
- Added publisher unit tests and corrected the fake Redis pipeline context-manager and expiry behaviour. Earlier CI failures were confined to the test double; production auth and market-data validation were not weakened.
- **Not yet complete:** independent Redis consumer, snapshot schema/user/version validation at consumer boundary, reconnect recovery, cross-process tests, scanner integration and paper-strategy integration. No live Upstox credentialed smoke test or Redis production deployment is claimed.
- Next: update this seven-document checkpoint set and verify docs CI on its exact resulting head; then implement the consumer with recovery by reading the latest snapshot after subscription/reconnect. Consumer must fail closed on missing/expired/stale/mismatched snapshots and must not trust Pub/Sub payloads as quote data.
- Safeguards: PAPER mandatory; live broker writes disabled; PR #8 and PR #9 remain Draft/unmerged; do not update main or merge without explicit approval; original `tarunsharma2610-del/Tradepro` remains out of scope.


## Phase 4 Redis atomic publisher checkpoint — 30 October 2026

- Repository: `tarunsharma2610-del/tradepro-improved` only; working branch: `phase4/redis-market-data-publisher`; PR #9 remains Draft/open and unmerged. No main-branch update. Original `tarunsharma2610-del/Tradepro` remains out of scope.
- **Latest verified code/test head:** `1c70e17a0ea54f8e8f219ae27d90aa46a02ea16e`.
- **Exact-head Backend CI #41026567279: SUCCESS:** https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41026567279. Backend pytest, broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore and evidence retention passed.
- Earlier atomic-publisher run #41026517896 failed because the concurrent Redis integration test omitted `import json`; corrected on the exact head above. The failure was a test import error, not a production publisher failure.
- Real Redis 7 integration tests cover publisher/consumer snapshots, tenant isolation, TTL, Pub/Sub notification followed by authoritative snapshot reads, consumer-instance restart recovery, and concurrent publishing. Atomic Lua publisher now allocates version, writes expiring snapshot, and publishes notification in one Redis script.
- The Redis consumer remains a standalone service: scanner/strategy integration is NOT complete. Actual Redis-server restart/reconnect and independent OS-process tests remain pending. Do not treat mocked/unit tests or consumer-instance restart as proof of Redis server restart recovery.
- **Next:** implement and test Redis consumer reconnect/resubscribe and snapshot recovery after Redis restart; then independent-process tests; then scanner integration; then PAPER strategy integration. Preserve quote expiry, exchange timestamps, user isolation, version monotonicity, and fail-closed behaviour.
- Safety: PAPER mandatory; live broker order writes remain disabled; PR #8/#9 remain Draft/unmerged; no main update; only Tradepro Improved may be modified.


## 30 October 2026 — Redis quote version-counter lifecycle checkpoint

- **Latest verified code/test head:** `3088e49cf24317f58f7e04a60d6cd54e065143b4`.
- **Exact-head Backend pytest workflow #41031153316: SUCCESS:** https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41031153316.
- Publisher version counters no longer receive a TTL; authoritative quote snapshots continue to expire. This prevents a quiet instrument's counter resetting while a long-running consumer retains a higher local version.
- Added real Redis integration coverage for snapshot deletion/expiry followed by a subsequent publish retaining the incremented version.
- This checkpoint does NOT by itself prove all Redis recovery/production lifecycle gates. The earlier real Redis process-restart integration test is present, but independent OS-process publisher/consumer testing and sustained multi-user/multi-instrument load remain pending.
- Scanner and PAPER strategy integrations remain NOT complete. Do not advance them until transport acceptance gates are met.
- **Next:** audit consumer startup/reconnect snapshot sweep and worker lifecycle; add independent OS-process delivery tests and sustained isolation/load tests; then integrate scanner, followed by PAPER strategy.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #9 Draft/unmerged; no main update; PAPER mandatory; live broker writes disabled; original Tradepro untouched.


## 30 October 2026 — Redis bounded epoch/version lifecycle accepted

- **Latest verified code/test head:** `7268edd6e7ddb7ef6d472799d1d0164b4210b135`.
- **Exact-head Backend CI #41032764754: SUCCESS:** https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41032764754. The full job passed pytest, broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document restore, and evidence retention.
- Redis publisher now uses a bounded version-counter retention (default 24 hours) and a unique epoch identifier. Quote snapshots retain their short configured TTL (15 seconds by default). Lua atomically allocates epoch/version, writes the snapshot, and publishes notification.
- When the version key expires or Redis loses volatile data, the next publisher creates a new epoch and starts at version 1. Consumers compare (epoch, version), accepting a reset only when the epoch changes. Existing integer-only version keys are migrated on the next publish.
- Real Redis tests cover actual snapshot TTL expiry while the counter remains in the same epoch; actual counter TTL expiry followed by a new epoch and consumer acceptance; Pub/Sub connection kill/reconnect; Redis process restart; independent publisher/consumer OS processes; two-user isolation; and concurrent version ordering.
- Intermediate epoch commit `85d8c30` failed five consumer unit tests because the fixture snapshots did not yet include the required epoch. The fixtures and tests were corrected in `cb52cb8`; the final exact-head CI above passed.
- **Not complete:** multi-user/multi-instrument load testing at scale; a managed long-running consumer registry in the worker; scanner integration; PAPER strategy consumption of Redis quotes. The current worker still evaluates strategies through its existing candle path.
- **Next:** define durable user/instrument subscription discovery and lifecycle for the worker consumer; add cancellation, restart, shutdown and scale tests; then connect scanner; only then evaluate PAPER strategy integration.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #9 Draft/unmerged; no main update; PAPER mandatory; live broker writes disabled; original Tradepro untouched.



## 30 October 2026 — durable subscription fixture fix and SDK/CAS audit

- Verified exact-head Backend CI #41036389075: SUCCESS on 2212be0e094bb41423193b4384b6c07511ff3d62. Backend pytest, broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document restore and evidence retention all passed.
- Fixed three market-stream API test failures by seeding the persisted Upstox broker-connection owner row required by durable subscription persistence. No production validation was weakened.
- SDK audit: UPSTOX_SDK_COMPATIBILITY_AUDIT.md. No SDK dependency added because current async adapter/streamer outperforms the SDK's synchronous/callback interfaces for our lifecycle. Official V3 protobuf schema matches the checked-in schema.
- Follow-on CAS field propagation code head: fe76751c54a720ffa5fcec7b4f3728b137447090. This adds CAS numeric fields and eligibility to tick parsing, Redis snapshots, stream status and tests. Exact-head CI is pending; the prior successful CI does not certify this newer code.
- Do not merge PR #9 or update main. PAPER mandatory; live order writes disabled; original Tradepro untouched.


## SDK comparison — additional mixed-mode finding

The official SDK source tracks separate instrument sets by feed mode and resubscribes each set on connection open. Our current streamer has one mode per user connection. This is a genuine gap for mixed scanner workloads. Borrow the mode-indexed subscription registry and reconnect replay logic after CAS-field CI passes; retain our async transport and token-provider refresh. Audit detail is in UPSTOX_SDK_COMPATIBILITY_AUDIT.md. This is planned work, not yet implemented or accepted.


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


## Phase 4 checkpoint — 30 October 2026: independent feed-mode subscription persistence

- Repository: `tarunsharma2610-del/tradepro-improved` only.
- Branch: `phase4/redis-market-data-publisher`; Draft PR #9 remains open and unmerged.
- Exact verified code/test head: `ef80d792c4d89abda1850b73f54f7b81bf16bbf7`.
- Exact-head Backend CI [#41057600440 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41057600440).
- All required workflow steps passed: backend pytest, Redis restart-recovery integration environment, broker-write boundary guard, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence retention.
- Subscription persistence now replaces the desired instrument set for the requested feed mode only; subscriptions in other modes remain active. Regression tests cover independent `ltpc`/`full` desired sets and reactivation of a prior mode identity.
- CI run #41057234551 failed because an existing test still expected the old single-active-mode behaviour. The test expectation was updated in `ef80d792c4d89abda1850b73f54f7b81bf16bbf7`; exact-head retry passed.
- Important scope limit: this verifies persistence semantics only. It does not yet prove mixed-mode Upstox V3 WebSocket subscribe/unsubscribe frames, per-instrument mode tracking, reconnect replay, or end-to-end live feed delivery.
- Next: audit the current V3 streamer and subscription manager against the official Upstox feed-mode contract; implement mixed-mode WebSocket lifecycle and mode-scoped unsubscribe with regression tests. Then verify Redis consumer lifecycle before scanner/PAPER strategy integration.
- Safeguards unchanged: PAPER mandatory; live broker `place_order`, `modify_order`, and `cancel_order` writes disabled; no PR merge, main update, deployment, live-order test, or production Oracle restore authorized/performed. Original `tarunsharma2610-del/Tradepro` remains out of scope.


## Phase 4 checkpoint — Redis consumer recovery hardening — 30 October 2026

- Repository/branch: `tarunsharma2610-del/tradepro-improved`, `phase4/redis-market-data-publisher`; Draft PR #9 remains open and unmerged.
- Latest implementation head: `a5e352bef2c78f27141b61bca5893fdfa0fd049a`.
- Exact-head Backend CI #41061518847 is running; no pass is claimed for this head yet.
- Prior exact-head Backend CI #41060945704 passed on `f7c863977ed17a3d705b83db8dcc6b7ba421cccf`, including fresh Upstox Analytics Token retrieval and fresh authorized V3 WebSocket URL on reconnect.
- Added Redis consumer regression coverage for Redis volatile-data loss: a new epoch may restart at version 1 after the prior epoch reached a higher version. Added idle Pub/Sub PING/PONG heartbeat coverage.
- Existing Redis consumer behaviour audited: authoritative snapshot reads, TTL/freshness validation, user isolation, reconnect/resubscribe, snapshot sweep after reconnect, Pub/Sub heartbeat, and fail-closed handling. Existing real-Redis CI integration covers server restart and independent process delivery; newly added tests specifically cover consumer epoch rollover and idle heartbeat.
- Worker-managed Redis consumer lifecycle and scanner/PAPER strategy consumption remain incomplete. Do not claim end-to-end scanner delivery.
- Next: wait for exact-head CI; then design worker lifecycle with single-owner/lease semantics, graceful cancellation and durable per-user subscription discovery before enabling consumers. Keep scanner integration behind that gate.
- Safety: PAPER mandatory; live broker order writes disabled; no PR merge/deployment/live credential test; original `tarunsharma2610-del/Tradepro` remains out of scope.


## Phase 4 checkpoint — Redis consumer epoch and heartbeat recovery — 30 October 2026

- Latest implementation/test head: `a5e352bef2c78f27141b61bca5893fdfa0fd049a`.
- Exact-head Backend CI [#41061518847 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41061518847). The Backend pytest job, Redis restart-recovery integration environment, broker-write boundary guard, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore, and evidence retention all completed successfully.
- Regression coverage verifies recovery from Redis volatile-data loss when the new epoch restarts at version 1 after the prior epoch reached version 8, and verifies Pub/Sub PING/PONG on an idle listener connection.
- The preceding token-refresh test remains covered by exact-head CI #41060945704 on `f7c863977ed17a3d705b83db8dcc6b7ba421cccf`: each reconnect calls the token provider again and obtains a fresh authorized V3 WebSocket URL.
- Redis consumer validates authoritative snapshots and supports reconnect/resubscribe, snapshot sweep, heartbeat, tenant isolation and fail-closed freshness checks. These tests do not certify production Redis deployment or sustained production load.
- Not complete: managed worker consumer lifecycle, durable subscription discovery/ownership coordination, scanner integration, and PAPER strategy consumption of Redis quotes. Existing strategy execution still uses its candle path.
- Next: design and test worker-managed consumer lifecycle (single-owner/lease semantics, startup discovery, cancellation, graceful shutdown, replica coordination and isolated failure handling). Only after that gate passes, connect the scanner, then evaluate PAPER strategy consumption.
- Safety unchanged: PR #9 remains Draft/open/unmerged; PAPER mandatory; live broker order writes disabled; no deployment or credentialed live smoke test claimed; original `tarunsharma2610-del/Tradepro` remains out of scope.


## Latest verified checkpoint — 30 October 2026

- Implementation commit `6ac3882a98f3c66abb4cd62848971b6277ab3be7` passed exact-head Backend CI [#41080156436](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41080156436); Backend pytest success, no failed steps.
- Added transactional `PaperStopEventClaimService`: ownership validation; portfolio → strategy → position locks; open position requirement; ambiguous shared portfolio/instrument ownership fails closed; unique quote-event identity; claim token/lease/attempt metadata; duplicate insert protected by nested savepoint.
- Claim service is not connected to dispatcher or order execution. Caller owns transaction commit/rollback.
- Next: PostgreSQL 16 multi-session claim race tests; explicit state transitions and lease reclaim; crash recovery; shared-position allocation decision; only then controlled dispatcher-to-PAPER execution.
- Do not enable live writes, merge PR #9, or deploy. PR #9 remains Draft/unmerged; PAPER mandatory.
- The documentation synchronization commit is separate and requires exact-head CI.
