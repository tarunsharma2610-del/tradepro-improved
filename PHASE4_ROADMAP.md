# Phase 4 Roadmap — Audit, Hardening, and Readiness

- Repository scope: `tarunsharma2610-del/tradepro-improved` only.
- Working branch: `phase4/roadmap-progress-checkpoints`.
- Starting checkpoint: `9add7f98ccf89f0c146e4367b79cdd5877104ff3` (Phase 3 checkpoint supplied for continuation).
- Status: ROADMAP CREATED; Phase 4 repository audit not yet completed. Do not mark implementation tasks complete until code and tests confirm them.

## Purpose
Progress from Phase 3 PAPER-mode accounting safeguards into a verified, maintainable application without enabling live broker writes. Audit before editing, preserve existing working functionality, and close only demonstrated gaps.

## Work packages and exit criteria

### P4-0 — Establish baseline and audit (first)
- [ ] Verify branch head, PR states, and exact-head CI.
- [ ] Inspect current Phase 3 checkpoint, instructions, architecture, requirements, progress, handover, and roadmaps.
- [ ] Inventory backend routes/services/models, frontend/UI status, auth, market data, strategy/backtest, risk controls, paper execution, charge flow, persistence, deployment, and tests.
- [ ] Produce a gap matrix: implemented / partial / missing / blocked by deployment or credentials.
- [ ] Do not repeat completed Phase 3 GST/IPFT/API schema work unless a concrete regression is found.
**Exit:** auditable inventory with evidence paths and prioritized findings.

### P4-1 — Risk and paper execution safety
- [ ] Verify risk checks are enforced at the execution boundary and cannot be bypassed by strategies.
- [ ] Test position sizing, capital/exposure limits, invalid/stale market data, rejected orders, partial fills, duplicate events, retries, cancellation, and restart recovery.
- [ ] Verify deterministic position/P&L updates and estimated-charge source labels.
- [ ] Confirm live order submission/modification/cancellation remain disabled and fail closed.
**Exit:** tests prove expected state transitions and broker-write safety.

### P4-2 — Paper-trading lifecycle and accounting integration
- [ ] Trace simulated order → fill → position → P&L → charge estimate → history.
- [ ] Verify estimates are never represented as booked actual charges.
- [ ] Verify replay/idempotency and rollback on failed multi-step updates.
- [ ] Check delivery/DP completeness rules and preserve aggregate API reconciliation-only boundary.
**Exit:** lifecycle regression suite passes without weakening Phase 3 accounting invariants.

### P4-3 — Persistence, security, observability
- [ ] Review database transaction boundaries, migration compatibility, restart behavior, logs, error handling, secrets, and configuration defaults.
- [ ] Confirm no tokens/secrets or sensitive contract-note identifiers leak into logs or docs.
- [ ] Validate health/readiness checks and actionable operational diagnostics.
- [ ] Prepare (but do not claim completion of) production Oracle backup/restore steps.
**Exit:** targeted tests and a documented operational checklist; actual production restore remains deployment-gated.

### P4-4 — Upstox read-only integration readiness
- [ ] Audit OAuth callback/token refresh and expiry/error handling already present.
- [ ] Verify market-data API permissions, WebSocket reconnect, subscription limits, stale-data detection, and rate-limit handling.
- [ ] Keep analytics/market-data access separated from any order-write permission.
- [ ] Define a credentialed smoke-test checklist; run only with authorized credentials in the deployed environment.
**Exit:** read-only integration behavior is tested and documented; no live order writes.

### P4-5 — CI, documentation, checkpoint
- [ ] Add tests only for confirmed gaps.
- [ ] Run targeted tests then the required full backend/security/migration/restore workflow.
- [ ] Synchronize maintained documents to the tested commit.
- [ ] Re-run CI on the exact final documentation/checkpoint head.
- [ ] Save a new checkpoint after every successful CI pass; if CI fails, fix and rerun before marking green.
**Exit:** exact-head CI green and all resume documents agree on the same commit/run.

## Execution rules
1. Start every session by verifying this branch's latest commit and its CI; resume from the last completed checkpoint, not an older failed run.
2. Audit before edits; never redo completed work without a concrete defect.
3. Work only in `tarunsharma2610-del/tradepro-improved`. The original `tarunsharma2610-del/Tradepro` repository is strictly out of scope.
4. Do not merge PR #6 or PR #7, do not update `main`, and do not merge Phase 4 work unless the user explicitly authorizes it.
5. PAPER mode remains mandatory. Live broker `place_order`, `modify_order`, and `cancel_order` writes remain disabled. No live-write flags, credentials, endpoints, or shortcuts may bypass this boundary.
6. Upstox Brokerage Details remains estimate-only; post-trade Trade Charges remains aggregate reconciliation-only, never per-fill actual-charge evidence.
7. Public/estimated tariffs without independently reviewed scope/date/source evidence stay estimate-only or fail closed for actual accounting.
8. Historical contract-note fixtures are regression evidence, not authorization to promote estimates or aggregate values to booked actuals.
9. Production OAuth smoke tests and real Oracle backup/restore are operational gates for after deployment; do not invent results or let their absence block ordinary PAPER-mode engineering.
10. Keep AI/open-source integrations and UI work in the previously agreed sequence; do not mix them into this audit unless the roadmap explicitly calls for it.

## Phase 4 completion definition
Phase 4 is complete only when each applicable work-package exit criterion is supported by tests or documented operational evidence, all safety invariants hold, exact-head CI passes, and the user-facing progress/handover/checkpoint files identify the same verified head. Deployment-only gates must be explicitly labelled deferred, not falsely passed.

## Execution update — 30 October 2026

- [x] P4-0B initial static hardening: literal `getattr` dispatch to broker write methods is rejected; targeted tests added.
- [x] Exact-head Backend CI #41012821073 passed on `24c34dac47e273f9377485dc697f9fa510808a72`.
- [ ] P4-0B broader call-path review: dynamically computed method names and arbitrary reflection remain limitations; continue auditing routes/services and don't overstate static guard coverage.
- [ ] P4-0C: test kill switch blocks new strategy entries while exits remain possible; inspect stale market-data/candle handling and risk checks at shared execution boundary.
- [ ] P4-1: continue order lifecycle, partial/rejected/replay/restart tests only after the P4-0C findings are addressed.

## Revised data-integration priority — 30 October 2026

- [x] Record user directive: use Upstox Developer Console, official APIs, SDKs, and schemas when useful; avoid unnecessary workaround-first engineering.
- [x] Check official docs for Market Data Feed V3, Intraday Candle Data V3, and SDK installation.
- [ ] Audit actual response contracts and installed dependency compatibility; replace unsupported BEST-EFFORT assumptions with schema-backed tests.
- [ ] Connect existing V3 WebSocket streamer to the shared strategy market-data/candle pipeline; retain REST intraday/historical endpoints for warm-up and gap recovery.
- [ ] Preserve five-minute strategy semantics; test candle timestamp/order, instrument-key matching, partial/current candle handling, reconnect and missing-candle recovery.
- [ ] Keep freshness/invalid-data checks as defense-in-depth only; they must not replace correct API integration.
- [ ] Run exact-head backend CI after code/docs changes and checkpoint only the exact passing head.

Engineering rule: check provider-supported capability and existing implementation before writing custom workarounds. Explain and justify any remaining workaround. PAPER/live-write/repository boundaries remain unchanged.

## Upstox API-first market-data work — 30 October 2026

- [x] Confirm the official current-session V3 intraday candle endpoint and documented seven-field candle schema.
- [x] Add optional adapter capability and Upstox V3 intraday REST implementation.
- [x] Combine historical and intraday candle sources in strategy evaluation; use Asia/Kolkata session date and timestamp-normalized deduplication.
- [x] Add API contract, source merge, and fail-closed regression tests.
- [ ] Verify CI on exact current head d7c786fc164ed297df42f26493c994ceacd337a7; resolve failures before checkpointing green.
- [ ] Audit how to consume the existing V3 WebSocket stream inside the actual strategy worker process. The current API-process stream registry is process-local; do not assume it is shared with the worker container.
- [ ] Only integrate WebSocket data where it improves a defined requirement (e.g. current LTP for paper valuation/stop decisions); preserve five-minute candle indicator semantics and use official candle endpoints for OHLC history.
- [ ] Verify current Upstox SDK endpoint coverage/dependencies before deciding whether it adds value. Do not add it just for appearance.
- [ ] Keep all paper/live safeguards and original repository boundary intact.

## Timestamped paper-execution quotes — 30 October 2026

- [x] Verify official Upstox Full Market Quotes V3 response includes instrument_token, last_price and last_trade_time.
- [x] Add optional full-quote adapter capability and Upstox V3 endpoint.
- [x] Require exact instrument identity and a fresh exchange last-trade timestamp for REST paper-fill pricing; prefer fresh subscribed WebSocket tick where available.
- [x] Add endpoint contract and timestamp-validation tests.
- [ ] Verify exact-head CI for 65f8070e344eaa4cd8cb82c876732662d02cc3a3 and fix any failures.
- [ ] Revisit worker-owned WebSocket subscriptions only if the five-minute strategy cadence or user requirements need streaming beyond the existing REST fallback; avoid unnecessary Redis or duplicated stream infrastructure.

## Market-data integrity follow-up — 30 October 2026

- [x] Confirm Upstox Full Market Quotes V3 carries exact instrument token, last price and last-trade time.
- [x] Confirm Upstox Market Data Feed V3 LTPC includes last-trade time (LTT) distinct from packet currentTs.
- [x] Remove packet-timestamp fallback when exchange LTT is missing; reject invalid LTP and missing exchange timestamp.
- [x] Validate both monotonic receive age and exchange timestamp age on cached ticks.
- [x] Add regression tests for NaN/Infinity and missing LTT.
- [ ] Verify exact-head CI on 4dd8420d4d787be049c956204e15bfdff9586f3e; repair failures before next checkpoint.

## Verification status — 30 October 2026

- [x] Backend pytest passed on market-data code/test head 4dd8420d4d787be049c956204e15bfdff9586f3e (run #41015772900).
- [x] WebSocket code passed on d7c74a20a4a46741123ebbf4809176e90199643c (run #41015756833).
- [ ] Verify exact-head CI for latest synchronized documentation head 2589db1e0a6446ea60d12a075d58ce43fa19ed93 (run #41015946896).

## Verified checkpoint — 30 October 2026

- [x] Use Full Market Quotes V3 snapshot timestamp and executable order-book depth for paper market fills.
- [x] BUY consumes ask levels; SELL consumes bid levels; calculate quantity-weighted fill price across levels.
- [x] Reject stale snapshots, mismatched instruments, invalid depth/prices and insufficient liquidity.
- [x] Correct strategy fixtures and remove obsolete LTPC-only monkeypatch.
- [x] Exact-head CI passed on `3a74fbb788a63ca3b042ceec400dbc7a83f32571`, run #41016468736: 1,240 passed, 1 warning; broker-write boundary, SQLite/PostgreSQL 16 migrations and synthetic restore drill passed.
- [ ] Implement separately encrypted Upstox Analytics Token storage and use it for market-data/stream APIs only. Retain standard OAuth token for account/trading scope; verify endpoint permissions and tests before use.
- [ ] Add token health/expiry status to broker connection UX; never invent automatic refresh for the daily standard token.
 
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


## Roadmap checkpoint update — 30 October 2026

### Completed
- [x] Add user-isolated Redis quote publisher with versioned latest snapshots and TTL.
- [x] Validate instrument key, finite positive LTP, exchange timestamp and receive timestamp before publishing.
- [x] Publish per-user Pub/Sub notifications after writing the latest snapshot.
- [x] Connect Upstox V3 stream manager's `on_tick` callback to Redis publisher.
- [x] Add publisher tests and pass exact-head Backend CI #41024607462 on `72b22a647f2b9a38ac7afc0aaee9547a67b16fcf`.

### Remaining sequence
1. Synchronize the seven Phase 4 checkpoint documents and pass docs-triggered CI on the exact resulting commit.
2. Implement an independent Redis quote consumer. Pub/Sub is notification only; read authoritative snapshot from Redis.
3. Enforce user isolation, schema/version checks, TTL, exchange timestamp freshness, and monotonic version handling in consumer.
4. Implement startup/reconnect recovery by re-reading latest snapshots; add missed-notification and Redis outage tests.
5. Add real Redis integration tests (including separate publisher/consumer processes) before declaring cross-process delivery complete.
6. Integrate scanner only after consumer acceptance.
7. Integrate PAPER strategy evaluation only after scanner and consumer acceptance; preserve existing candle freshness and risk gates.

No step is complete merely because a service or test double exists. Do not enable live trading or merge Draft PRs.


## Redis delivery milestone update — 30 October 2026

- [x] Redis quote consumer and unit tests; exact-head CI #41025805338 passed.
- [x] Redis 7 service in backend CI and real Redis integration tests.
- [x] Atomic publisher version/snapshot/notification sequence using Redis Lua.
- [x] Concurrent publish test and corrected integration-test import.
- [x] Exact-head CI #41026567279 passed on `1c70e17a0ea54f8e8f219ae27d90aa46a02ea16e`.
- [ ] Consumer reconnect and resubscribe after Redis connection loss.
- [ ] Recovery sweep after Redis server restart; prove expired/missed quotes fail closed.
- [ ] Independent publisher/consumer OS-process integration tests.
- [ ] Scanner consumes only validated user-scoped fresh quotes.
- [ ] PAPER strategy evaluation consumes validated quotes and retains candle/risk freshness checks.
- [ ] Update checkpoint after each exact-head CI pass.

Do not skip gates or mark downstream integrations complete based on publisher/consumer unit tests. Keep PR #9 Draft/unmerged and live broker writes disabled.


## Redis version-counter lifecycle update — 30 October 2026

- [x] Keep Redis version counters persistent across ordinary quote snapshot expiry.
- [x] Real Redis integration test: delete/expire snapshot, publish next quote, verify version increments rather than resetting.
- [x] Exact-head Backend pytest CI #41031153316 passed on `3088e49cf24317f58f7e04a60d6cd54e065143b4`.
- [ ] Audit consumer startup/reconnect authoritative snapshot sweep and fail-closed behaviour.
- [ ] Verify dedicated worker lifecycle, cancellation and graceful shutdown.
- [ ] Add independent publisher/consumer OS-process integration tests.
- [ ] Add multi-user/multi-instrument concurrency, isolation and recovery tests.
- [ ] Integrate scanner only after transport gates pass.
- [ ] Integrate PAPER strategy only after scanner acceptance; retain candle freshness and risk gates.

Persistent version keys require an explicit retention/cleanup policy for instruments no longer subscribed; do not reintroduce TTL-based counter resets without an epoch-safe design. Keep PR #9 Draft/unmerged and live broker writes disabled.


## Redis bounded epoch/version lifecycle update — 30 October 2026

- [x] Add bounded version-counter retention (24-hour default) and unique epoch identifier.
- [x] Atomically allocate epoch/version, write snapshot and publish notification through Lua.
- [x] Migrate existing integer-only counters on next publish.
- [x] Verify actual quote snapshot expiry while version remains in the same epoch.
- [x] Verify actual counter expiry starts a new epoch and an existing consumer accepts the reset safely.
- [x] Verify Pub/Sub connection kill/reconnect and real Redis process restart.
- [x] Verify independent OS-process publisher/consumer delivery, two-user isolation and concurrent atomic version order.
- [x] Exact-head full Backend CI #41032764754 passed on `7268edd6e7ddb7ef6d472799d1d0164b4210b135`.
- [ ] Multi-user/multi-instrument scale and sustained-load testing.
- [ ] Implement worker-managed consumer registry with durable subscription discovery, dynamic add/remove, cancellation, graceful shutdown and restart recovery.
- [ ] Integrate scanner only after worker consumer lifecycle acceptance.
- [ ] Integrate PAPER strategy evaluation only after scanner acceptance; retain candle freshness and risk gates unless a separately reviewed quote-based execution design is approved.

Do not claim scanner or strategy integration: `app/worker.py` currently uses its existing candle-based strategy path and does not run a Redis quote-consumer registry. Keep PR #9 Draft/unmerged and live broker writes disabled.



## SDK compatibility audit and next implementation gate — 30 October 2026

1. [x] Compare official Upstox Python SDK v2.30.0 with the existing REST adapter, OAuth flow, V3 streamer, protobuf, Redis publisher/consumer and instrument master.
2. [x] Record decision not to add the SDK as a dependency: generated synchronous REST client and callback WebSocket feeder do not improve our async architecture; existing token refresh, reconnect, validation and Redis handling remain application-owned.
3. [x] Compare official SDK V3 protobuf with local schema; schemas match.
4. [ ] Verify exact-head CI for CAS-field propagation (fe76751c54a720ffa5fcec7b4f3728b137447090). The decoder now carries IEP/reference price/indicative quantities/CAS eligibility into MarketTick, Redis snapshots and stream status.
5. [ ] After CAS CI passes, proceed with the worker-managed Redis consumer lifecycle and durable subscription recovery/validation before scanner integration.
6. [ ] Add a later scanner/research design review for official Fundamentals and Market Information APIs introduced in SDK v2.27.0. Prefer official endpoints where useful; do not add SDK runtime dependency by default.

No live broker writes. PAPER remains mandatory; PR #9 remains Draft/unmerged.


### SDK-derived implementation improvement — mixed feed modes

- [x] Compare SDK v2.30.0 subscription implementation against our streamer.
- [x] Identify missing capability: mixed per-instrument LTPC/full/option_greeks modes on one user stream.
- [ ] After CAS exact-head CI passes, borrow the SDK's per-mode subscription-set design and reconnect replay semantics in our async streamer.
- [ ] Update durable subscription service/API to reconcile multiple feed modes without deactivating unrelated modes.
- [ ] Enforce current official per-mode and combined connection limits; add mode transition, reconnect, startup restore and user-isolation tests.
- [ ] Only then wire scanner consumers.


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


## Current Phase 4 checkpoint — 30 October 2026

The older Gate 0/Gate 1 notes above are historical. Mixed-mode persistence, V3 WebSocket lifecycle/reconnect replay, startup recovery and token refresh have since been implemented and have passing exact-head CI checkpoints. See `PHASE4_LATEST_CI_CHECKPOINT.md`.

- Latest code/test head: `a5e352bef2c78f27141b61bca5893fdfa0fd049a`; Backend CI #41061518847 is running, not yet accepted.
- Added tests for Redis consumer epoch rollover after volatile data loss and idle Pub/Sub heartbeat. Prior exact-head head `f7c863977ed17a3d705b83db8dcc6b7ba421cccf` passed Backend CI #41060945704.
- Next: (1) exact-head CI pass; (2) worker-managed Redis consumer lifecycle with durable per-user subscription discovery, single-owner/lease coordination, cancellation and shutdown; (3) multi-user/multi-instrument delivery and recovery; (4) scanner and PAPER strategy integration only after those gates.
- Do not interpret Redis publisher/consumer unit tests as scanner integration or production deployment validation.
- PR #9 remains Draft/unmerged. PAPER mandatory; live order writes disabled; original Tradepro out of scope.


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
