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
