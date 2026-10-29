<!-- Phase 3 checkpoint update — 27 Oct 2026. Latest code/test head 8feeb0cbb0c35e1e37012302c9075d43f1f33eb1 passed Backend CI #40458822529: 1,097 passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed. DP completeness checks require a consistent KNOWN + explicit valid finite nonnegative paise-exact amount, or NOT_APPLICABLE + no amount; invalid status, UNKNOWN-with-amount, KNOWN-without-amount, NOT_APPLICABLE-with-amount, NaN, negative and fractional-paise amounts fail closed. DP canonical manifests are checked against persisted broker trade → child order → local order mappings; only mapped equity-delivery SELL fills are accepted. Delivery SELL still requires reviewed/reconciled DP evidence and durable per-fill allocation; DP is included once in total and replay identity. Maintained docs are being synchronized after the green code run; exact-head CI on the final docs/checkpoint commit must pass before it is called green. PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original Tradepro repository out of scope. -->

# Bhav Open-Source Framework Audit — 25 October 2026

## Scope and provenance

- Audited public repository: https://github.com/rajmaurya0904/bhav
- Audited upstream default branch: `main`, tree commit `562dc214416fd974eb41082b05e131c523e49023`.
- Repository metadata reports an MIT licence; the upstream `LICENSE` file grants permission to use, modify, and redistribute subject to preserving the copyright and licence notice.
- This is a source-level preliminary audit of selected files, not a complete security review or independent verification of market/tax rates.
- This document is for the `tarunsharma2610-del/tradepro-improved` repository only. Do not change the original `tarunsharma2610-del/Tradepro` repository.

## Useful capabilities

The README and source indicate that Bhav provides:
- Python-based NSE index-options historical backtesting using Upstox data.
- A pluggable strategy interface and bar-by-bar simulation.
- A local Parquet cache and sample offline dataset.
- A basic Indian options cost model.
- Portfolio accounting with partial/tranche closes.
- Metrics and Monte Carlo reporting.
- A FastAPI + Next.js backtesting interface and a strategy-upload AST safety validator.

These capabilities may be useful as a reference or as a separately evaluated optional tool. They are not proof that Bhav is production-ready for Tradepro Improved.

## Findings requiring caution

### 1. Cost rates and product coverage are not suitable for direct adoption

In `bhav/engine/costs.py`, `IndianCostModel` labels its numbers as current as of 2025 and hard-codes rates for brokerage, STT, exchange transaction charges, SEBI, stamp duty, and GST. Tradepro Improved already uses effective-dated, source-reviewed tariff rules; replacing that system with these constants would regress tariff provenance and date/product-specific applicability.

The code's GST formula is 18% of brokerage + exchange transaction charges + SEBI charges. It does not model IPFT as a distinct component. Tradepro Improved's source review already warns that Upstox may describe IPFT as combined with transaction charges and that double counting must be avoided. Do not copy these rate values or component assumptions as official current rates.

The method computes turnover as `price * qty`. For the `exercised_itm` branch, the code applies `stt_exercised_rate` to that same turnover, although its docstring describes STT on settlement value. This requires investigation against current official product/contract rules before any use.

The model is an NSE options-oriented example, not a verified general-purpose calculator for every equity, futures, options, exchange, product, and transaction type.

### 2. Brokerage is applied at each portfolio open/close call

`Portfolio.open()` and `Portfolio.close()` call `cost_model.costs()` for each invocation, and `IndianCostModel.costs()` applies a brokerage amount/cap for that invocation. A portfolio method invocation is not necessarily identical to a broker order or contract-note charge line. Multiple fills belonging to one broker order could therefore be charged differently from the actual order-level tariff unless order/fill aggregation is modelled explicitly.

Tradepro Improved should continue to use its durable source-component and per-fill allocation ledger; do not import Bhav's per-call fee logic into that ledger.

### 3. Monetary arithmetic uses binary floating point

The selected cost model and portfolio accounting use Python `float` values for prices, rates, amounts, and totals. That can be acceptable for exploratory backtesting with documented tolerances, but it is not a substitute for Tradepro Improved's deterministic paise-level allocation and exact source-total reconciliation.

### 4. Portfolio mutation before direction validation

In `Portfolio.open()`, cash and `_total_costs` are changed before the existing-position opposite-side check raises `OppositeSideError`. A caller that catches the exception can be left with mutated cash/cost state despite the rejected operation. This is a concrete reason not to embed this portfolio implementation into the production accounting path without a fix and regression test.

### 5. Runtime and operational footprint

Bhav's `pyproject.toml` requires Python 3.11+ and includes `httpx`, `polars`, `pyarrow`, `pydantic`, `typer`, `rich`, FastAPI, Uvicorn, multipart parsing, and Excel support in the base dependency set. The web UI also requires Node.js 20+. This is a meaningful dependency and memory footprint for Tradepro Improved's small Oracle VM. Reuse should be selective; do not deploy a second full web stack just to gain a cost calculator or backtest helper.

## Recommendation for Tradepro Improved

**Decision: reuse as a research/reference framework; do not directly merge or install the full framework at this stage.**

1. Preserve Tradepro Improved's effective-dated, source-reviewed tariff rules, provenance, paise-level allocation, replay/conflict checks, and fail-closed reconciliation.
2. Use Bhav to derive additional synthetic regression scenarios for partial closes, slippage direction, stale marks, option exercise, and backtest look-ahead prevention.
3. Independently verify any rate or tax formula against current official Upstox/NSE/SEBI/CBIC sources and the applicable effective date. A GitHub README or hard-coded example is not tariff authority.
4. If an algorithm is later reused, isolate it behind our existing interfaces, retain MIT notices, add attribution, pin the upstream commit, review transitive dependencies, and add tests that prove it cannot bypass our ledger or broker-write safeguards.
5. Keep all live broker order submission disabled and paper trading mandatory.

## Audit status

- [x] Confirm upstream repository and MIT licence.
- [x] Inspect README, `pyproject.toml`, `bhav/engine/costs.py`, `bhav/engine/portfolio.py`, `tests/test_portfolio.py`, and `tests/test_engine.py`.
- [x] Record concrete reuse risks and candidate test ideas.
- [ ] Full dependency vulnerability and licence inventory.
- [ ] Full upstream test-suite execution in an isolated environment.
- [ ] Any integration into Tradepro Improved (not approved by this audit alone).

## References

- Upstream repository: https://github.com/rajmaurya0904/bhav
- Upstream MIT licence: https://github.com/rajmaurya0904/bhav/blob/main/LICENSE
- Cost model: https://github.com/rajmaurya0904/bhav/blob/main/bhav/engine/costs.py
- Portfolio: https://github.com/rajmaurya0904/bhav/blob/main/bhav/engine/portfolio.py
- Portfolio tests: https://github.com/rajmaurya0904/bhav/blob/main/tests/test_portfolio.py
- Project's current Upstox evidence and tariff research: `docs/UPSTOX_CONTRACT_NOTE_AND_API_EVIDENCE.md`


## Canonical latest Phase 3 checkpoint — 26 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **Verified code/evidence head:** `d287da70ce184c904c6f9ede9e4a0edca5839f8f` (commit: “docs: reconcile public Upstox contract note GST examples”).
- **Exact-head CI:** PASS — [GitHub Actions run #40304398632](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40304398632), commit `d287da70ce184c904c6f9ede9e4a0edca5839f8f`; **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention also passed. This is CI evidence, not proof of a real Oracle recovery or broker-origin authenticity.
- **GST/IPFT research:** Three public third-party historical Upstox note copies were reconciled: 11-Feb-2025 base ₹2.97 / IGST ₹0.53; 21-May-2024 base ₹77.56 / IGST ₹13.96 (IPFT ₹0.11 listed outside that note's printed base); 12-Mar-2025 base ₹2.75 / IGST ₹0.50. Printed-base compositions differ historically. The current official Upstox schedule supports the **estimate-only** base of brokerage + transaction charges + demat where applicable + IPFT, with IPFT represented exactly once because it is combined with transaction charges. Do not add SEBI to this current estimate base without current applicable billing evidence; never calculate GST on trade notional or infer zero from missing/null fields.
- **Tax/accounting approval:** all four GST component candidates remain `DRAFT`. Historical public copies do not prove current actual per-fill billing across products/accounts. Actual-charge promotion stays gated; estimate logic and actual invoice reconciliation are distinct. Follow effective dates and preserve raw API/source evidence.
- **Next action when resuming:** continue Phase 3 from this exact commit and checkpoint. Next gate is component-specific GST acceptance cases for equity delivery, intraday, futures and options, then implementation review and exact-head CI; do not restart from earlier saved checkpoints.
- **Safety / PR:** PAPER mode mandatory; live broker `place_order`/`modify_order`/`cancel_order` and automatic live-fill promotion remain disabled. PR #6 remains open, draft and unmerged. Original `tarunsharma2610-del/Tradepro` is not the work target and must remain untouched.
- This checkpoint supersedes older statements in this document about CI being in progress or requiring verification for the pre-`d287da7` head. Historical notes remain history; this is the canonical resume point.


## Phase 3 CI synchronization — 26 October 2026 (GST/IPFT resolver)

- Latest verified code head: `13e201661d26b04c9bf75bb7e3aaf567ad1e69c4`; exact-head Backend CI [#40378072884 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40378072884): **1,056 passed, 1 warning**. Broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill and retained restore evidence passed.
- Added scope/effective-date-selected GST policy resolution for `COMBINED`, `SEPARATE`, and `NOT_APPLICABLE` IPFT representation. It rejects double representation, wrong-exchange reuse, missing/extra components, and unapproved or out-of-window policies. This is estimate-policy plumbing, not actual invoice reconciliation or tariff approval.
- Next Phase 3 gate: persist optional DP/demat charges safely, migrate canonical accounting/persistence and total-charge recomputation, then integrate statutory GST valuation only through reviewed source-backed policy paths. Actual per-fill invoice acceptance remains evidence-gated; no personal contract note is required.
- Safety unchanged: PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; original `tarunsharma2610-del/Tradepro` untouched and out of scope.


## Phase 3 CI synchronization — 26 October 2026 (DP/demat snapshot gate)

- Latest verified code head: `6a6a3560aff18bb94d34b77640058a17d2a208b8`; exact-head Backend CI [#40381396722 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40381396722): **1,057 passed, 1 warning**. Broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore drill and retained restore evidence passed.
- Optional `demat_transaction_charges` can now be represented as a distinct pending canonical snapshot and allocated into the durable per-fill allocation ledger when source rows are independently reviewed. Migration expands the canonical snapshot vocabulary. It does **not** authorize final accounting: DP/demat reconciliation promotion deliberately fails closed until Execution persistence and total-charge recomputation are implemented.
- Next Phase 3 gate: add dedicated optional Execution DP/demat persistence and a single verified total-charge recomputation path, with migration/idempotency/rollback and delivery-vs-non-delivery tests. Keep actual invoice/per-fill acceptance evidence-gated; no personal contract note is required.
- Safety unchanged: PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; original `tarunsharma2610-del/Tradepro` untouched and out of scope.
