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
