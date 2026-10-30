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
