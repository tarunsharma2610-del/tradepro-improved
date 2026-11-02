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


## Verified checkpoint — PostgreSQL 16 PAPER stop-event claim concurrency (30 October 2026)

- **Implementation SHA:** `0d3700f0a12add3239457bc4009eb019d77c78a0`
- **Backend CI:** [#41090051358](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41090051358) — **SUCCESS**, exact SHA.
- Full workflow passed: backend pytest, broker-write boundary, SQLite migration upgrade/downgrade/re-upgrade, isolated PostgreSQL 16 migration database upgrade/downgrade/re-upgrade, and synthetic PostgreSQL/document-volume restore drill with retained evidence.
- PostgreSQL 16 concurrency tests cover same quote identity races (one durable claim, one duplicate) and distinct quote versions (both accepted). Strategy and Position locks are scoped to their respective tables to avoid nullable-side outer-join locking errors.
- PostgreSQL migration validation now uses isolated `tradepro_migration_check`; the concurrency suite retains `tradepro_test`.
- **Next:** implement and test claim-token-owned event lifecycle transitions (CLAIMED → EXECUTING → COMPLETED; explicit RETRYABLE/FAILED), then lease expiry/reclamation and crash recovery. Do not connect to PAPER order execution until lifecycle/idempotency gates pass.
- **Safety:** only `tarunsharma2610-del/tradepro-improved`; PR #9 remains Draft/open/unmerged; PAPER mandatory; live broker order writes disabled; no deployment or live trading.


## Latest verified checkpoint — PAPER stop-event lifecycle and PostgreSQL 16 recovery (1 November 2026)

- Repository: `tarunsharma2610-del/tradepro-improved` only; branch: `phase4/redis-market-data-publisher`; Draft PR #9 remains open and unmerged.
- Exact PR/code head verified: `aaf64fcf1431f7fa998d61c9cc3efd9b251437a6` (commit: caller-owned watermark transaction test correction).
- Exact-head Backend CI [#41097352266 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41097352266). Backend pytest, Redis restart-recovery integration setup, broker-write boundary guard, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore and evidence-retention steps all completed successfully.
- The previously planned claim-token-owned lifecycle is now implemented in `paper_stop_event_lifecycle.py`: CLAIMED → EXECUTING → COMPLETED; EXECUTING → RETRYABLE or FAILED; expired CLAIMED/EXECUTING/RETRYABLE claims can be reclaimed with a rotated token and bounded attempt count. Conditional updates fence stale claim tokens; caller retains transaction commit/rollback ownership.
- PostgreSQL 16 tests now cover simultaneous lease reclaim (exactly one new token wins), exhausted retry-budget races, rollback atomicity, expired EXECUTING recovery, and stale-worker completion rejection. Unit tests cover retry delay, terminal failure and lease expiry.
- Latest watermark test correction explicitly commits the caller-owned transaction before asserting persisted watermark state; this preserves the service's transaction ownership contract.
- Important boundary: lifecycle tests validate durable event state only. No lifecycle transition authorizes an order, no dispatcher-to-execution connection is accepted by this checkpoint, and no live broker writes are enabled.
- Next gate: review lifecycle semantics and transaction boundaries, decide/implement explicit strategy allocation for shared portfolio/instrument positions (currently fail-closed), then design a crash-safe PAPER consumer that coordinates claim → existing PAPER risk/depth/kill-switch/accounting path with idempotent execution evidence. Add failure-injection tests before connecting the bounded dispatcher.
- Deployment, sustained-load testing, credentialed Upstox smoke tests and production Oracle restore remain deferred.
- Safety: PAPER mandatory; live `place_order`, `modify_order`, and `cancel_order` writes disabled; PR #9 Draft/unmerged; no main update or merge; original `tarunsharma2610-del/Tradepro` untouched.


## Execution integration safety audit — 1 November 2026

- Documentation-only audit at head `5208b19ca07cb8bf1b32fe9944760d5d9e2e522d`; exact-head documentation CI #41284535086 passed.
- Shared-position policy: retain fail-closed rejection when multiple active strategies share a portfolio/instrument position. `Position` is keyed by portfolio+instrument, not strategy; no allocation ledger exists. Do not guess ownership or let multiple strategies exit the same net position.
- Critical execution-path finding: `ExecutionService._fill()` is not currently one atomic unit of work. It calls `OrderRepository.create()`, `PositionRepository.get_or_create()/save()`, and `PortfolioRepository.save()`, whose repository methods commit internally, before the final `Execution` insert/commit. A crash or exception between those commits can leave a filled order without matching position/cash/execution evidence, or partially applied accounting.
- Therefore do NOT call the current `ExecutionService.place_order()` as the consumer's event-completion transaction yet. A lifecycle event cannot safely be marked COMPLETED atomically with the existing fill; a retry after an intermediate commit risks duplicate or inconsistent accounting.
- Required implementation gate before dispatcher integration:
  1. Refactor PAPER fill persistence so order, position, portfolio cash, execution/charges and event completion share one caller-owned SQL transaction; repositories used in that path must flush, not commit.
  2. Add durable event idempotency to the order/execution boundary (unique stop-event reference, or equivalent unique idempotency key) and recovery lookup. A retry must return the prior committed outcome, never create a second fill.
  3. Lock/revalidate portfolio, strategy, position and event in a documented global lock order; recheck open position, direction/quantity, kill switch and risk immediately before fill.
  4. Add failure-injection tests after each persistence stage, transaction rollback tests, duplicate-consumer races, and PostgreSQL 16 concurrent tests proving one fill and one accounting effect.
  5. Keep ambiguous shared strategy ownership fail-closed until explicit position allocation exists.
- No source execution code was changed in this audit. Dispatcher remains unconnected to stop-event execution. PAPER-only; all live broker order writes remain disabled.


## 1 November 2026 — atomic PAPER fill CI and stop-order idempotency schema

- Backend CI #41284932565 SUCCESS on exact commit `a9dd7174f9a075d130a78a9046d434dcb97838f2`; includes caller-owned PAPER fill transaction and rollback regression.
- Added migration `202611010034` introducing nullable `orders.paper_stop_event_id`, FK to `paper_stop_events.id` (RESTRICT), and unique constraint `uq_orders_paper_stop_event`.
- Added model/schema test for nullable unique reference and FK.
- This constraint prevents more than one order from referencing a given event, but it does not itself implement recovery or authorize event execution. Consumer remains disconnected pending token/lease validation, existing-order recovery and atomic event completion.
- PR #9 remains Draft/unmerged; PAPER-only; live broker order writes disabled; original Tradepro untouched.


## 1 November 2026 — CI green and execution-boundary replay recovery added

- Backend CI #41285290161 passed on exact schema/migration commit `b8be854040ffa672ed5da26fd821984ec074c232`, including pytest, broker-write boundary, SQLite and PostgreSQL 16 migration cycles, and synthetic restore drill.
- Added order lookup by `paper_stop_event_id` and a constrained `ExecutionService.place_order(..., paper_stop_event_id=...)` path for strategy-owned PAPER MARKET orders only.
- After locking the user-owned portfolio, repeated matching event delivery returns the existing order; mismatched replay parameters fail closed.
- Added tests for replay without a second quote/accounting mutation and rejection of LIMIT/manual event-linked orders.
- These changes do not yet complete event lifecycle atomically. Next: event/portfolio/strategy/position lock-order orchestration; claim-token and unexpired lease validation; existing-order recovery; complete/fail transition in the same transaction; fault-injection and PostgreSQL 16 concurrency tests.
- PAPER only; live broker order writes disabled; PR #9 remains Draft/unmerged; original Tradepro untouched.


## 1 November 2026 — atomic stop-event execution implementation (CI pending)

- Previous exact-head Backend CI #41285643789 passed on `7b12c9522941f5ac3237f4f659055863687cca31`, including stop-event order idempotency/replay tests.
- Added `PaperStopEventExecutionService`: validates user/portfolio/strategy/instrument ownership, active strategy, open position, claim token and unexpired lease; locks portfolio -> strategy -> position -> event.
- Calls the existing PAPER MARKET ExecutionService with caller-owned transaction (`commit=False`), then transitions the event to COMPLETED in the same commit as order, execution, cash, position and strategy watermark. Rejected orders become terminal FAILED; duplicate completed delivery returns the original filled order.
- Added success, replay, invalid-token and forced-completion-failure rollback tests.
- New exact-head CI is required before acceptance. Dispatcher remains disconnected; no live broker order writes; PR #9 Draft/unmerged; original Tradepro untouched.
- Next after green CI: PostgreSQL 16 concurrent duplicate-consumer race and process-crash/failure injection around commit; then review whether dispatcher activation is safe.


## 1 November 2026 — atomic execution CI failure diagnosed; fixture fix committed

- CI #41286034683 failed at pytest setup: 1,383 passed, four errors because the new test module referenced non-shared `portfolio` and `instrument` fixtures defined only in another test module.
- Added local `portfolio` and `instrument` fixtures following existing repository patterns. This is a test-only correction; no production code changed.
- Rerun exact-head CI is mandatory. Do not proceed to PostgreSQL concurrency tests or dispatcher integration until green.


## 1 November 2026 — timezone bug fixed after atomic execution CI

- CI #41286342961: 1,384 passed, 3 failed. All three failures shared a naive/aware datetime comparison at claim-lease validation; PostgreSQL migration and later CI gates were skipped because pytest failed first.
- SQLite strips timezone metadata from DateTime(timezone=True). Added UTC normalization at the execution boundary and tests for naive UTC plus non-UTC aware offsets.
- New commit awaits exact-head full CI. Do not mark atomic execution green until pytest, broker-write boundary, SQLite/PostgreSQL 16 migration cycles and restore drill all pass.


## 1 November 2026 — completed-event redelivery fix; CI rerun pending

- CI #41286561712 on `f3ef675d0085c87658408cdd2841d8d859dc96e3`: 1,388 passed, one failed.
- Root cause: duplicate delivery checked for a non-flat position before checking COMPLETED state. The first successful stop fill correctly flattened the position, so replay was incorrectly rejected rather than returning the existing order.
- Reordered validation/locks: portfolio -> strategy -> event; a completed event returns its existing matching filled PAPER order. Only active claimed events then lock/check the open position and proceed.
- Exact-head CI required. PostgreSQL concurrency and dispatcher remain blocked.


## 1 November 2026 — narrow PAPER execution call allowlist added; CI pending

- CI #41286886564: pytest passed; broker-write AST gate failed on the intended shared `self.execution.place_order` call inside the PAPER stop-event orchestration service.
- Narrowly allowed that exact receiver and function in that exact file. Added positive regression test for shared ExecutionService delegation and negative test proving direct adapter.place_order remains blocked.
- No live broker-write exemption added. Await full exact-head CI including SQLite/PostgreSQL 16 migrations and restore drill.


## Live-trading readiness policy — 1 November 2026

Product direction: Tradepro Improved is intended to support both PAPER and LIVE trading. PAPER remains the default and mandatory mode for development, automated tests, CI, demos and all unverified workflows. This direction supersedes older roadmap wording that described the product as permanently PAPER-only; it does NOT authorize live broker writes today.

### Current operational status
- LIVE broker order submission, modification and cancellation remain DISABLED. This roadmap update does not enable any production live order writes.
- The current CI work concerns PAPER stop-event orchestration and static broker-write boundary tests. Enabling LIVE mode would not resolve these failures and must not be used to bypass the guard.
- Existing live-order intent/reconciliation code, if present, is not proof that broker writes are ready or authorized.
- PR #9 remains Draft/unmerged. Original `tarunsharma2610-del/Tradepro` remains out of scope and must not be modified.

### Required stages before any LIVE enablement
1. **Mode separation:** explicit per-account/environment mode, secure default PAPER, and no environment variable or API request that silently switches a PAPER account to LIVE.
2. **Broker authorization:** verify official Upstox OAuth scopes and account permissions; keep the read-only Analytics Token separate from trading OAuth credentials; encrypt credentials and enforce owner isolation, expiry and revocation.
3. **Central live-write gateway:** all live place/modify/cancel operations pass through one narrowly scoped service. No direct adapter calls from routes, strategies, workers, stop-event services or AI agents.
4. **Human authorization:** explicit confirmation for live orders, or a separately reviewed, revocable automation authorization with quantity/notional/instrument/segment limits, expiry and kill switch. No AI agent may grant itself live authority.
5. **Pre-trade risk controls:** market/session checks, instrument/lot/tick validation, price collars, maximum order/notional/position/day-loss limits, duplicate/idempotency protection, fresh quotes and exposure checks.
6. **Failure safety:** reconcile broker timeouts and unknown states before retry; never blindly resubmit. Keep durable audit records with actor, request hash, broker response and correlation ID; test cancel/modify races.
7. **Security testing:** authorization/IDOR, replay, concurrency, secret handling, rate limits, dependency/SAST/DAST review; prove PAPER paths cannot reach the live gateway and PAPER credentials cannot activate live writes.
8. **Operational readiness:** supported broker sandbox tests where available, monitoring/alerts, kill-switch drill, backup/restore drill, incident runbook and a restricted low-limit pilot.
9. **Separate release approval:** exact-head green CI, independent review, explicit user authorization for the target deployment, and a documented rollback. Green CI alone never enables LIVE.

### Immediate next steps
- Correct malformed newline escapes in the broker-write AST regression fixtures; retain the negative test that rejects direct adapter writes.
- Run full exact-head CI: pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore evidence.
- Only after green CI, continue PostgreSQL 16 concurrent PAPER stop-event tests.
- In parallel, audit existing live-intent and broker-adapter call paths against the stages above. Record gaps; do not enable writes during this audit.


## Phase 4 verified checkpoint — 1 November 2026 — PostgreSQL concurrent PAPER stop execution

- Latest branch head: `6db7dcfa3d46c11c844733e571ea6f90dda999d6` (PR #9 head; Draft/unmerged).
- Exact-head Backend CI [#41289810206 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41289810206). Backend pytest, broker-write boundary enforcement, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore and evidence retention all completed successfully.
- PostgreSQL 16 concurrent duplicate stop-event execution regression is included. Two independent workers race the same durable claim; the test verifies one PAPER filled order, one execution, one position close, a single quote fetch, and the same completed order returned to both workers.
- Initial concurrency CI #41289482098 exposed a SQLAlchemy identity-map stale-state race after a worker waited on row locks. The locked event query now uses `.populate_existing()` to refresh persisted state under lock. The fix is recorded in `PHASE4_PAPER_STOP_EVENT_EXECUTION_SAFETY.md`.
- Atomicity remains enforced: PAPER order, execution/accounting, position/cash, strategy watermark and event completion share one transaction. Failure injection verifies rollback if completion cannot be committed; completed redelivery returns the existing order.
- Direction check: this is the correct Phase 4 order of work—prove persistence, idempotency and multi-worker safety before connecting quote dispatch. It is not production-readiness certification.
- Product target remains PAPER + LIVE with independent balances/orders/positions/P&L and mode-isolated execution. PAPER is the default for development and CI. LIVE broker place/modify/cancel remain disabled pending the separately gated readiness stages in this document and `MASTER_ROADMAP.md`.
- Safety: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` untouched; PR #9 Draft/unmerged; no deployment or credentialed Upstox trading smoke test claimed.

### Next implementation sequence
1. Add PostgreSQL 16 concurrent expired-lease reclamation tests, proving only one reclaimer rotates the claim token and stale workers cannot execute.
2. Add process-interruption/restart tests around claim, execution and acknowledgement; verify transaction rollback leaves a reclaimable claim and post-commit redelivery returns the existing completed order.
3. Review dispatcher cancellation/acknowledgement behavior and define a supervised consumer loop that always acknowledges or safely releases in-flight work.
4. Connect the bounded dispatcher to the durable claim service for PAPER only; keep scanner callbacks free of DB, broker and order work.
5. Add multi-user/multi-instrument, Redis outage/reconnect, stale quote, depth and kill-switch tests; then run exact-head full CI.
6. Continue the separate PAPER/LIVE mode-isolation and live-write gateway audit. Do not enable LIVE broker writes as part of Phase 4 dispatcher work.


## 1 November 2026 — dispatcher cancellation recovery tests CI green

- Exact PR #9 head `1e37ad6e52a3c94a35a5519cc496ab3000f3f44f`; Backend CI [#41290374836 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41290374836).
- All workflow gates passed: full backend pytest, broker-write boundary enforcement, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore, and evidence retention.
- Dispatcher now exposes same-consumer-task `release()` for cancellation/interruption. It requeues the in-flight observation unless a newer coalesced observation exists; newest observation wins. Successful processing continues to use `task_done()`.
- Added regression tests for cancellation recovery and newest-value preference. These are in-process handoff semantics only; process death loses this in-memory queue, so durable recovery must continue to rely on Redis replay plus PostgreSQL claim/lease state. Do not describe dispatcher memory as durable.
- PR #9 remains Draft/unmerged. Product target is PAPER + LIVE with strict separation; PAPER is default for CI. LIVE broker place/modify/cancel remain disabled. Original `tarunsharma2610-del/Tradepro` untouched.

### Next steps
1. Add supervised consumer lifecycle tests for worker shutdown, cancellation before/during handling, retry/backoff, queue drain and no leaked in-flight keys.
2. Wire the Redis quote callback to a non-blocking dispatcher publish only; it must not await strategy/DB/execution work.
3. Add a separately supervised PAPER consumer that validates receive-time and exchange-time freshness, resolves user/strategy ownership, obtains durable claim/lease and delegates to the existing atomic PAPER stop-event execution service.
4. Test multi-worker PostgreSQL idempotency, Redis disconnect/reconnect/replay, queue overflow, stale/future quotes, depth, kill switch and cross-tenant isolation.
5. Exact-head full CI before each accepted checkpoint. No LIVE writes until independent readiness gates and explicit approval.


## Architecture review after dispatcher recovery CI — 1 November 2026

The green dispatcher-recovery CI is necessary but not sufficient to activate quote-driven stop execution. A source review of `backend/app/worker.py`, `redis_market_quote_worker.py`, `market_scanner.py`, `strategy_execution_service.py`, and the stop-event services identified the following integration boundary:

- The existing worker currently wires `RedisMarketQuoteWorker(on_quote=scanner.process_quote)`. `MarketScanner.process_quote` is synchronous, validates/builds an in-memory observation, and does not execute orders. This is safe for the current scanner role.
- The Redis worker awaits async `on_quote` callbacks inline. Therefore the future dispatcher publish callback must be synchronous/non-blocking; it must not perform DB reads, strategy evaluation, broker calls or await execution.
- The dispatcher is bounded and process-local. Its cooperative `release()` recovers task cancellation only. Hard process death requires upstream Redis snapshot recovery and durable PostgreSQL claim/lease recovery; the in-memory queue is not a durable event log.
- Existing trailing-stop behavior is currently evaluated inside the 5-minute `StrategyExecutionService.evaluate` cycle using the latest scanner observation and persisted `current_watermark`. The stop-event claim/execution services provide idempotent durable execution, but the quote-driven consumer still needs an explicit, transactionally safe per-tick stop-evaluation/watermark policy.
- Do not simply connect dispatcher items directly to `claim_trailing_stop` or `execute_claimed`. First define and test how active strategy/portfolio/position ownership is resolved; how watermark is advanced or a trigger is calculated under row locks; how stale/future exchange timestamps are rejected at the final boundary; and how quote epochs/replay are handled.
- A dedicated supervised PAPER consumer must own bounded DB sessions, retry/backoff and shutdown semantics. Redis callbacks remain dispatch-only. The consumer must call the existing shared `check_trailing_stop` logic, not reimplement its math, and then use the existing durable claim + atomic execution services.
- The current strategy/portfolio schema and execution path are not yet evidence of completed user-selectable PAPER/LIVE balance and order isolation. That remains a separate product requirement and live-readiness gate. All live broker order writes stay disabled.

### Revised immediate next slice (before order integration)
1. Specify a quote-driven trailing-stop evaluation service: lock order, owner resolution, watermark advancement, trigger boundary, quote age/skew policy and duplicate event key.
2. Add pure/unit tests for long/short watermark evolution, epoch reset, duplicate/out-of-order quote, stale/future quote and no-position/no-strategy cases.
3. Add PostgreSQL 16 concurrency tests proving two ticks/workers cannot race watermark updates or generate duplicate stop events.
4. Add supervised dispatcher consumer tests for handler failure/backoff, cancellation during handler/backoff, graceful shutdown and pending/in-flight accounting.
5. Only then wire the synchronous scanner→dispatcher publish callback and the PAPER-only consumer. Keep it disabled until integrated exact-head CI passes.


## 1 November 2026 — quote freshness test correction (not yet CI-verified)

- Backend CI #41290692856 FAILED on commit `4224d08da1cd71173ceace6a0bcb2aa0ea4f2d99`. The failure was isolated to `test_scanner_accepts_exchange_timestamp_within_future_clock_skew`: the test generated its receive timestamp using a later wall-clock call than the injected `now`, so the scanner correctly rejected a receive timestamp slightly in the future. This was a test-fixture clock mismatch, not evidence that the future exchange-time skew policy failed.
- Corrected the fixture to set `received_at=now.isoformat()` using the same injected clock. Fix commit: `fe6d86a4c662512a891d40be45aafd441b144430`.
- The correction is NOT accepted until full CI passes on this exact head. Do not rely on the previous green CI #41290374836 for the later scanner freshness changes.
- Next action: inspect the new exact-head workflow result. If it fails, diagnose the actual failing test/log before changing implementation. No dispatcher/consumer integration until quote freshness tests and full CI are green.


## 1 November 2026 — trailing-stop pure-math hardening (CI pending)

- Latest verified baseline: Backend CI #41290966001 passed on `e13c3d16bd00031b9b8e5259cf1b4df2457fb473`; this is the last fully green exact-head checkpoint before the following edits.
- Added pure unit coverage for long and short trailing-stop watermark seeding, monotonic ratcheting, and trigger thresholds using the existing shared `check_trailing_stop` helper. No separate implementation of stop math was introduced.
- Hardened `check_trailing_stop` to reject zero positions, non-positive/non-finite prices or watermarks, and stop percentages outside the supported strategy schema range (>0 and <=50%). This avoids silently interpreting a flat position as short or accepting corrupted configuration.
- New code/test commits are not yet CI-verified. Do not connect quote dispatch to stop execution until full exact-head CI passes and a transactional quote-evaluation policy (including watermark/epoch handling) is designed and tested.
- Product target remains a single app with selectable PAPER/LIVE modes and isolated balances/orders/positions/P&L. Current CI and automated execution remain PAPER-only; LIVE broker place/modify/cancel remain disabled. PR #9 stays Draft/unmerged and original `tarunsharma2610-del/Tradepro` remains untouched.

### Next
1. Verify this exact head through full Backend CI; diagnose any failure from logs before changing code.
2. Design the transactional per-quote evaluator: lock portfolio → strategy → position; validate tenant/mode and quote freshness; handle epoch/version ordering; update watermark and create durable stop event atomically.
3. Add PostgreSQL 16 concurrency tests for watermark races and duplicate/out-of-order quote delivery.
4. Add supervised consumer retry/shutdown tests, then connect Redis callback → bounded dispatcher → PAPER-only consumer. No LIVE writes.

## 1 November 2026 — bounded dispatch retry and integrated PAPER runtime checkpoint

- Latest code/test head: `3ca26594cf3a711be624cf2836079caac352a897`.
- Exact-head Backend CI [#41302875861 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41302875861). All workflow steps completed: backend pytest; broker-write boundary; SQLite upgrade/downgrade/re-upgrade; isolated PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL/document-volume restore and evidence retention.
- Runtime worker wiring is present: Redis quote ingress → scanner/dispatcher → four PAPER dispatch workers; independent five-second durable stop-event recovery.
- Dispatcher handler retries are capped at five attempts. On exhaustion, scanner high-water state is cleared to allow authoritative Redis snapshot replay; newer coalesced quotes are retained. PostgreSQL quote/event/order identities provide replay protection.
- Shared PAPER execution rechecks the current position under portfolio/position locks and rejects a stale reduce-only exit if the position is flat, direction mismatched, or requested quantity exceeds the remaining position.
- This checkpoint verifies backend CI, not production operation or sustained market-load behaviour. No production deployment or live broker write is authorized.

### Remaining gates
1. End-to-end integration proof from Redis snapshot through scanner, dispatcher, stop intake, durable claim, PAPER fill, ledger and final position/cash state.
2. Multi-process/multi-replica tests for simultaneous quote delivery, worker death, lease expiry/reclaim, uncertain commits, Redis restart and periodic indicator-exit versus event-stop races.
3. PAPER/LIVE mode separation audit and central live-write gateway review; current build remains PAPER-only.
4. Security, dependency, load/backpressure, monitoring/alerting, backup/restore operations and runbook review.
5. Synchronize all maintained docs and run exact-head CI on the final docs/code commit.

PR #9 remains Draft/open/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` untouched. Live broker place/modify/cancel remain disabled.

## PAPER/LIVE isolation audit finding — 1 November 2026

A source review of the current models and shared execution service confirms that the present Phase 4 runtime is PAPER-only, not yet a selectable dual-mode implementation:
- `ExecutionService.place_order` explicitly creates orders with `trading_mode="PAPER"` and the current market execution/fill path is simulated accounting; it does not route order writes to Upstox.
- `Order` has a `trading_mode` column, but `Portfolio` does not own a mode and `Position` is scoped only by `(portfolio_id, instrument_id)`. Therefore the desired separate PAPER/LIVE balances and positions are not yet proven by the current schema.
- Before enabling LIVE, design and test a mode boundary at portfolio/account scope: mode-bound portfolio ownership, order/position/ledger queries constrained to that mode, strategy-to-portfolio mode binding, and a separate explicit live broker execution gateway with deny-by-default authorization and idempotency.
- Switching modes must select a different isolated portfolio/account; it must never mutate an existing order's mode, move positions/cash, or route PAPER strategies to a live gateway.
- Keep LIVE broker place/modify/cancel disabled until this design, migrations, API authorization, UI selection, adversarial tests and independent safety audit are complete.

This is a verified outstanding product requirement, not a claim that LIVE mode is implemented.


## 2026-11-01 — Superseding Phase 4 status (verified through Backend CI #41316803274)

This section is the current-status authority as of 2026-11-01 and supersedes older undated or stale “current status/next step” statements elsewhere in this document. Earlier entries remain historical records and must not be interpreted as the current implementation state.

- Latest verified green implementation commit: `d0d26eb98ff5d77ce4f3ed1baee943bccaca51e4` on `phase4/redis-market-data-publisher`.
- Exact-head Backend CI: [#41316803274 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41316803274). Verified stages: backend pytest, broker-write safety boundary, SQLite migration round-trips, PostgreSQL 16 migration round-trips, synthetic PostgreSQL restore and documentation-volume restore drill.
- The LIVE balance-source implementation and corrected fixtures passed CI #41315704407 on commit `9314703f31ff3ad31f2b97090cbfa1a5d4096a8c`.
- Mode-aware portfolio analytics now joins executions to owning orders, constrains portfolio identity and trading mode, and receives the portfolio mode from the API. Regression tests cover PAPER/LIVE separation and unsupported modes. Verified by CI #41316803274.
- LIVE portfolios do not treat simulated starting capital as broker funds; balance source remains unavailable until verified broker sync. PAPER simulated balances remain supported.
- Green CI does not establish production LIVE readiness. LIVE broker place/modify/cancel writes remain disabled; no LIVE gateway activation or deployment is authorized.
- Outstanding: LIVE positions API fail-closed behavior; broker-account-to-LIVE-portfolio allocation; verified LIVE funds/positions sync; realized and freshness-gated unrealized P&L; Redis-to-execution and multi-worker end-to-end isolation/recovery; frontend mode selection; security/load/operational review; final docs-head CI.
- PR #9 remains Draft/unmerged, targeting `phase4/roadmap-progress-checkpoints`. Only `tarunsharma2610-del/tradepro-improved` is in scope. Original `tarunsharma2610-del/Tradepro` must remain untouched.
- Next implementation gate: inspect the LIVE positions route and tests, then add fail-closed mode-aware behavior with regression tests. Do not start broker allocation or UI work until this boundary is proven.


## 2026-11-01 — LIVE broker snapshot synchronization checkpoint (supersedes older outstanding-status notes)

- Funds V3 synchronization and LIVE positions snapshot synchronization are implemented as read-only broker-data paths. Positions validation, immutable snapshot persistence, owner-scoped LIVE migration 042, latest-snapshot API and audit logging are in place.
- Exact-head Backend CI #41321796027 PASSED on `3090d7518dfcebaad3dad69967b861f9e3fb3e14`. Verified stages: backend pytest, broker-write safety enforcement, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL restore and documentation-volume restore.
- Decimal normalization canonicalizes signed zero to `0.00`; regression coverage added.
- Latest broker Positions and Funds reads are now scoped to the broker connection currently allocated to the LIVE portfolio. Regression coverage verifies old snapshots are not returned after allocation removal/replacement. The test respects the database's unique one-connection-per-user-per-broker constraint by using distinct broker providers for the replacement scenario.
- Failed synchronization retains the prior snapshot; PAPER positions and accounting are not mutated; broker-reported realized and unrealized P&L remain distinct; unknown instrument identities are not guessed; broker daily P&L is not represented as lifetime P&L.
- This is read-only LIVE data synchronization, not LIVE order execution. Broker place/modify/cancel writes remain disabled; PAPER execution remains the only enabled execution path. No deployment or LIVE gateway activation is authorized.
- PR #9 remains Draft and unmerged. Work is restricted to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository remains out of scope and must not be modified.
- Next implementation sequence: holdings synchronization; broker instrument identity reconciliation; separate realized P&L ledger; freshness-gated unrealized P&L using market prices; stale-data detection; multi-worker synchronization recovery; end-to-end security/isolation and operational review.
- Documentation update itself must pass exact-head Backend CI before this documentation checkpoint is considered green.


## 1 November 2026 — LIVE portfolio unrealized P&L projection checkpoint

- Current Phase 4 branch: `phase4/redis-market-data-publisher`.
- Latest code/test head: `18588c18f550f6dc5a4953f90229e05f31e14269`.
- Exact-head Backend CI [#41328649301 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41328649301). The immediately preceding service-only commit `290bae0fb963ddb37382d91d6f961fbfd5db27b2` also passed CI #41328642939. The final CI #41328649301 covers the latest head including duplicate-position regression tests.
- Fresh-quote LIVE unrealized P&L calculation is implemented in `backend/app/services/live_unrealized_pnl_service.py`; tests cover long/short profit and loss, flat positions, stale/future quotes, invalid/non-finite values and paise rounding. This calculation service passed exact-head CI #41327228865 on `f84834a163e9f8acdd59898e07865f7b226db07d`.
- Read-only portfolio projection is implemented in `backend/app/services/live_portfolio_pnl_view_service.py`; tests cover combined long/short results, missing/stale quotes, flat rows, malformed broker rows, unknown instrument identities and duplicate broker position identity handling.
- The projection requires exact broker instrument keys, uses fresh quote timestamps (default maximum age 15 seconds), and withholds the portfolio total if any open position cannot be valued. Duplicate (instrument, product) rows fail closed; same instrument across distinct products remains separate.
- Important integration boundary: this is a tested pure projection service, not yet connected to the authenticated portfolio API or Redis quote consumer. No frontend integration or broker/internal realized-P&L reconciliation is complete. Do not claim it is end-to-end LIVE portfolio P&L.
- Main-branch cleanup after two accidentally placed files was completed; latest cleanup CI #41328271380 passed on main. The Phase 4 files are present on the intended Phase 4 branch.
- Next session: (1) inspect Redis consumer snapshot schema and exact instrument-key mapping; (2) add a read-only adapter that reads authoritative Redis snapshots and converts timestamps/prices safely; (3) integrate the projection behind owner-scoped LIVE portfolio authorization and LIVE snapshot availability checks; (4) add API tests for stale/missing quotes, duplicate rows, ownership and PAPER isolation; (5) keep realized and unrealized P&L separate; (6) add broker-vs-internal reconciliation only after authoritative fill/ledger mapping is established; (7) update frontend only after API contract is stable.
- After next code milestone, synchronize all maintained docs and run Backend CI on the exact final documentation head before marking the documentation checkpoint green.
- Safety: PAPER execution remains the only enabled execution path. LIVE broker place/modify/cancel remain disabled. PR #9 remains Draft/open/unmerged. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `tarunsharma2610-del/Tradepro` must remain untouched.


## Phase 4 checkpoint synchronization — 2 November 2026

- Verified PR #9 branch head before this documentation repair: `62eac41ce86577082b7e78c976de9c72b746464e`.
- Exact-head Backend CI run [#41329154167](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41329154167) completed successfully on that head. All workflow stages passed: backend pytest, broker-write boundary enforcement, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration upgrade/downgrade/re-upgrade, and synthetic PostgreSQL/document-volume restore drill with evidence retention.
- This successful run is the verified baseline for this documentation synchronization. The documentation commit created from this update must receive its own exact-head Backend CI run before it is called a green documentation checkpoint.
- November 1 Phase 4 progress recorded in this branch includes PAPER/LIVE portfolio isolation guards, read-only LIVE funds/positions synchronization, and fail-closed LIVE unrealized-P&L calculation/projection. The projection is not yet end-to-end: authoritative Redis quote-consumer integration, owner-scoped portfolio API integration, API-level stale-data/ownership/PAPER-isolation coverage, frontend display and realized-ledger reconciliation remain pending.
- Resume sequence: inspect the authoritative Redis snapshot schema and exact instrument-key mapping; build a timestamp/Decimal-safe adapter; integrate behind owner-scoped LIVE portfolio authorization and snapshot-availability gates; add stale/missing/future quote, duplicate-row, ownership and PAPER-isolation tests; keep realized and unrealized P&L separate; then proceed to UI and broader multi-worker/security/operational verification.
- Safeguards: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` remains untouched; PAPER remains the only enabled execution path; LIVE broker place/modify/cancel writes remain disabled; PR #9 remains Draft/open/unmerged.


## Phase 4 checkpoint repair — 2 November 2026 (supersedes earlier pending-integration notes)

### Verified implementation
- Owner-scoped read-only endpoint is implemented: GET /api/v1/portfolios/{portfolio_id}/live-unrealized-pnl.
- Endpoint requires an owned LIVE portfolio, the currently allocated broker connection owned by the same user, and the latest position snapshot bound to that portfolio, user, and connection. PAPER portfolios are rejected; missing allocation/snapshot is not treated as zero.
- Reads quotes through the existing user-scoped RedisMarketQuoteConsumer using exact broker instrument_key values; no symbol-based guessing. Quote freshness is bounded to 15 seconds and the P&L projection rejects missing/stale/future/malformed quote data, invalid position rows and duplicate instrument/product rows. Aggregate P&L is withheld if any open position cannot be valued.
- Redis is pinged before reads so an unavailable Redis service returns HTTP 503; Redis client is closed in finally. This prevents Redis outages being misreported as an ordinary missing quote.
- Calculation is read-only and keeps realized ledger, executions, PAPER positions, cash and broker writes untouched. This is not end-to-end LIVE trading readiness and no frontend P&L display is claimed.

### Exact successful CI evidence
- CI #41397210305 PASSED on 32816181c890877736b6d3324d542f8208141026 (API endpoint).
- CI #41397227429 PASSED on a65c463b862b858b899bccd68f7e1eada6483e93 (API ownership and PAPER-mode regression tests).
- CI #41397602437 PASSED on d01146f3384594c6a8443f1f0daa0b1fa4d635db (Redis availability fail-closed safeguard).
- CI #41397616502 PASSED on 147d59be787124a04c44748dcf051784f0cf9f4e (Redis outage regression test).
- Previous documentation repair CI #41396779042 PASSED on fd15b4a4d609597d9123b36f9c02190f422de083.
- The documentation synchronization in this commit must itself pass Backend CI on its exact resulting head before this checkpoint is called green.

### Next gates
1. Add end-to-end API tests with a real ephemeral Redis service/snapshot writer and assert a fully-valued response from a fresh user-scoped quote.
2. Add API tests for stale/missing/future quotes, stale or malformed broker position snapshots, Redis outage, tenant isolation and PAPER isolation.
3. Review rate limiting, bounded Redis reads and large-position response behavior before enabling UI polling.
4. Add frontend display only after the API contract and freshness semantics are verified; label unrealized P&L separately from realized P&L.
5. Complete broker-vs-internal reconciliation and operational/security review before considering any LIVE execution capability.

### Non-negotiable safeguards
- Work only in tarunsharma2610-del/tradepro-improved; original tarunsharma2610-del/Tradepro remains out of scope and untouched.
- PAPER remains the only enabled execution path. LIVE place_order, modify_order and cancel_order writes remain disabled.
- PR #9 remains Draft/open/unmerged. Do not merge or enable LIVE order writes without explicit authorization.



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

- Added authenticated two-user regression coverage for unauthorized contract-note upload/download, source-component create/review/reject, reconciliation run/issue access, and broker-settings connection scoping. The test exercises foreign broker-connection identifiers and verifies no cross-user data access.
- Exact PR-head Backend CI [#41404633900 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41404633900) on `e8f8783fc32a96e43e710289721992e077dc4d82`; PR #9 head matches this SHA. All workflow steps passed: pytest, broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention.
- This verifies the added regression coverage and existing workflow safeguards; it does not establish a complete IDOR sweep or penetration test. Comprehensive security assessment remains NOT COMPLETE.
- Next security gates: continue endpoint-by-endpoint authorization matrix, secret/token redaction/storage review, dependency scan/SAST, isolated-staging DAST, broker-write reachability, abuse/load testing, deployment/incident-response review and independent penetration test.
- PAPER remains mandatory; LIVE broker place/modify/cancel writes disabled; PR #9 remains OPEN/Draft/unmerged; original `tarunsharma2610-del/Tradepro` remains out of scope.


## Security scanning and dependency remediation checkpoint — 2 November 2026

- Added GitHub Actions security workflow `.github/workflows/security-analysis.yml` with CodeQL Python static analysis and `pip-audit` over `backend/requirements.txt`. CodeQL and dependency audit both completed successfully on exact commit `8be6a0369c81a519c00712d69095b2ab3ceb5faa`: [CodeQL run #41406851928](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41406851928), [dependency audit #41406857558](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41406857558). Dependency audit reported zero known vulnerabilities for the resolved backend dependency set.
- Dependency remediation upgraded FastAPI to the compatible `0.143.x` line; CI resolved FastAPI `0.143.5` and Starlette `1.10.0`. This replaced the previously vulnerable Starlette `0.46.2` resolution. Compatibility was verified by the full backend workflow, not assumed from version numbers.
- Full Backend CI [#41406857547 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41406857547) on the same exact SHA. Pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, and synthetic restore/evidence-retention checks passed.
- Security scope remains incomplete: CodeQL and pip-audit are automated static/dependency checks, not DAST or penetration testing. Continue endpoint-by-endpoint authorization/IDOR matrix, secret/token redaction review, authenticated API negative tests, broker-write reachability, staging DAST, abuse/load testing, deployment hardening and independent penetration test. Review new CodeQL findings on every run; a successful workflow does not imply no security defects outside its rules.
- Prior rate-limit fail-closed, MFA step-up, and cross-tenant contract-note/reconciliation regression protections remain recorded in prior checkpoints.
- PAPER remains mandatory; LIVE broker place/modify/cancel writes disabled; PR #9 remains OPEN/Draft/unmerged; original `tarunsharma2610-del/Tradepro` remains out of scope.


## Authentication hardening and security verification — 2 November 2026

- Hardened JWT creation: optional extra claims can no longer override reserved `sub`, `type`, `iat`, or `exp` claims. Added parameterized regression tests for each reserved claim and a positive test proving non-reserved claims remain supported.
- Corrected stale rate-limiter documentation: Redis outage behavior is fail-closed with HTTP 503; it is not fail-open.
- Exact code commit verified: `4ebc24c0ae129cf53614cd58c46c41cc55a204ab`. Backend CI [#41408254466 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41408254466); CodeQL and Python dependency audit [#41408254462 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41408254462). All three checks completed successfully on the exact same SHA.
- Dependency audit reported zero known vulnerabilities for the resolved backend dependency set; prior FastAPI/Starlette compatibility remediation remains in place.
- Security assessment is still INCOMPLETE. These checks do not establish absence of vulnerabilities or replace the remaining endpoint authorization/IDOR matrix, secret/token redaction and storage review, staging DAST, broker-write reachability review, abuse/load tests, deployment hardening and independent penetration testing.
- Existing rate-limit fail-closed, MFA step-up, cross-tenant contract-note/reconciliation regressions and CodeQL/pip-audit workflow remain in scope and must not be regressed.
- PAPER mode remains mandatory; LIVE broker place/modify/cancel writes remain disabled; PR #9 remains OPEN/Draft/unmerged; original `tarunsharma2610-del/Tradepro` remains strictly out of scope.


## Authoritative Phase 4 checkpoint — 2 November 2026, 18:30 IST

- Repository: `tarunsharma2610-del/tradepro-improved` only. Working branch: `phase4/redis-market-data-publisher`. Latest code/test commit: `d6619a58cd585ef35b79126d866c90bb903cb890`.
- Exact-head Backend tests [#41410058905 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41410058905): Backend pytest passed on the exact commit above.
- Exact-head Security analysis [#41410058894 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41410058894): CodeQL static analysis and Python dependency vulnerability audit both passed on the same commit. This does not establish absence of vulnerabilities or replace DAST/penetration testing.
- Latest security test addition: production settings reject missing explicit `SECRET_KEY` and `MASTER_ENCRYPTION_KEY`; explicit valid secrets are accepted; development fallback remains available. Earlier 2 Nov JWT reserved-claim hardening and fail-closed Redis rate-limit documentation are retained.
- PR #9 is OPEN, Draft and unmerged; head is the exact commit above; base is `phase4/roadmap-progress-checkpoints`. Do not merge or mark ready without explicit authorization.
- Already implemented and not to be repeated: user-scoped Redis quote snapshots/TTL/epoch-version ordering and Pub/Sub; Upstox V3 WebSocket reconnect/subscription recovery; Redis consumer recovery; scanner freshness/dispatcher; durable PAPER stop-event claims and atomic PAPER execution; PostgreSQL concurrency/rollback tests; worker runtime wiring and PAPER reduce-only protections.
- Remaining Phase 4 engineering: full end-to-end Redis snapshot → scanner → dispatcher → durable stop-event → PAPER ledger/position tests; multi-process/multi-replica races and crash-window tests (especially indicator exits versus stop-event exits); complete PAPER/LIVE data and API/UI isolation audit; operational observability/alerting and sustained load/backpressure tests.
- Remaining security audit: endpoint-by-endpoint authorization/IDOR matrix, secret/token storage and redaction review, authenticated negative tests, broker-write reachability proof, staging DAST, abuse/load tests, deployment hardening and independent penetration testing. CodeQL and pip-audit are baseline automated checks only.
- Safeguards: PAPER mandatory for development/tests/CI/unverified workflows; live broker `place_order`, `modify_order`, and `cancel_order` writes remain disabled; no live smoke test or production deployment is claimed; original `tarunsharma2610-del/Tradepro` remains strictly out of scope.
- This checkpoint records the latest verified code head. Documentation synchronization commits that follow require their own exact-head Backend + Security CI before being called green. Continue from the remaining work above; do not repeat completed items.


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

- Latest verified implementation head: `29d165395259a73f819bf22327a44e0fe06f1600`; Backend tests [#41492213645](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41492213645) and Security analysis [#41492213677](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41492213677) both PASSED on this exact head.
- Nifty 500 dated/validated membership snapshots, exact NSE mapping, atomic replacement, retained history, admin import and regression tests are implemented. `POST /api/v1/market-data/stream/universe/nifty-500` connects the active complete snapshot to the authenticated user's existing Upstox LTPC stream; Analytics Token required, compatible subscriptions preserved, conflicting feed modes rejected, subscription state persisted. No order writes.
- Completed earlier Phase 4 work includes Redis quote/dispatcher/recovery safeguards; durable PAPER stop-event claims/leases/retries/fencing and PostgreSQL concurrency coverage; persisted auth sessions, refresh rotation/replay rejection, logout revocation, JWT claim protections, MFA step-up, transactional key-rotation implementation; HTTPS/CORS and two-user broker credential/Analytics Token isolation regression.
- Remaining: scanner quote ordering/staleness and subscription lifecycle; scanner filters/ranking; full Redis→scanner→dispatcher→durable PAPER stop→execution→position/ledger proof; multi-process crash/recovery and concurrent exits; realized-P&L/fill reconciliation; read-only LIVE P&L UI; load/backpressure/observability/runbooks; remaining IDOR/secret review/DAST/broker-write reachability/independent penetration test; authorized read-only Upstox smoke test and production restore evidence.
- Next session (3 Nov): verify exact-head CI on the final docs commit first; then continue quote ordering/staleness and subscription lifecycle tests. Documentation commit itself is not green until its Backend CI, CodeQL and dependency audit pass.
- PR #9 OPEN/Draft/unmerged; only `tradepro-improved`; original Tradepro untouched; PAPER mandatory; LIVE broker order writes disabled; no merge/deploy/LIVE activation.
