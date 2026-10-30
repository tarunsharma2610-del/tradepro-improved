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
