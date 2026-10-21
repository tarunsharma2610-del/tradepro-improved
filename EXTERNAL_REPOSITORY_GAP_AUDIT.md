## Current verified checkpoint — 21 October 2026

- **Latest CI-verified `main` HEAD:** `7798f03200ba823d51bdd359539594b38e9830e1`; exact-head backend CI [run 39567592850](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567592850) passed.
- **Latest code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard and SQLite/PostgreSQL 16 reversible migration checks.
- The slow-persistence/lease-race audit is complete: the PostgreSQL row-lock test proves reclaim waits while a fenced write transaction is open; `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` passed 20 concurrent expiry-boundary renewal/reclaim races. Expired owners cannot renew, and ownership generation/token advance is verified.
- Official Upstox V2 order-book and get-trades-for-day endpoints are current-day endpoints without documented pagination parameters. Historical trades are a separate paginated API; that API is not wired into the Phase 2 worker.
- **Current task:** synchronize the remaining historical architecture/roadmap/reference-audit notes. This documentation commit needs its own exact-head CI and a final stale-status scan before Phase 2 is formally closed. Phase 3 remains blocked until then.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

---

# External Repository Gap Audit — Tradepro Improved

Audit date: 2026-10-21
Target: https://github.com/tarunsharma2610-del/tradepro-improved (main)
Protected baseline: https://github.com/tarunsharma2610-del/Tradepro (do not modify)
Purpose: identify genuinely missing capabilities and safe, free-to-use implementation ideas. This is a focused public-repository review, not a legal opinion or a line-by-line security certification of every upstream file.

## 1. Target repository first: current verified position

- Current HEAD observed during this audit: `ffbe3fccf28c572c6e8af43c1862a205fbf3ae7d`, commit message `docs: complete checkpoint audit and reconcile Phase 2 handover`.
- Backend CI for that exact HEAD: run [39558705500](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39558705500), completed successfully.
- The repository has an existing substantial backend/frontend, Alembic migration chain, automated backend tests, two CI workflows, Upstox adapter/OAuth, instrument sync, WebSocket market data, paper execution/accounting, strategy scoring, risk controls, backtesting, transaction costs, and a durable live-order/reconciliation foundation.
- Existing `REFERENCE_REPOSITORY_AUDIT.md`, `AUDIT_REPORT.md`, `MASTER_ROADMAP.md`, and `HANDOVER.md` are part of the target repo. This document supplements the prior four-repository comparison with the additional candidates and a fresh gap assessment.
- Latest code/test evidence recorded in project docs: commit `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`, backend CI passed 466 tests with one warning and SQLite/PostgreSQL 16 migration checks; frontend CI passed TypeScript/build on its recorded commit. Do not conflate that historical evidence with current HEAD's frontend status unless a run for the exact current SHA confirms it.
- Keep live order placement disabled. Do not introduce broker writes, automatic fill-accounting promotion, automatic scheduling, or a wholesale safety-branch merge as part of this research audit.

### Current implementation evidence inspected

- `backend/app/services/backtest_engine.py`: pure bar-by-bar engine, reuses existing strategy scoring, position/fill math and transaction-cost functions, models configurable slippage, computes max drawdown and basic win/loss counts.
- `backend/app/services/strategy_engine.py`: five indicator components (RSI, SMA crossover, MACD, volume spike, momentum) combined by configurable weights into a composite score; decision enum currently represents ENTER_LONG, EXIT, HOLD.
- `backend/app/services/transaction_costs.py`: centralized Decimal-based Indian transaction-cost calculation for equity delivery, intraday, futures and options. The module itself flags some exchange/brokerage inputs as indicative and requiring periodic source verification.
- `backend/tests/test_backtest_engine.py` and `test_transaction_costs.py`: deterministic backtest behavior, slippage direction, capital limits, P&L basics and cost component tests already exist.
- Existing app already has portfolio-level risk controls, order idempotency/outbox records, broker-fill identity, reconciliation leases/run records/issues, a read-only reconciliation worker, and an isolated live-fill accounting service. Do not create duplicate engines or bypass those boundaries.

## 2. Candidate repository findings

### A. AI Trading Platform
Repository: https://github.com/afnanadil2007-design/AI-Trading-Platform
License: MIT, as declared by GitHub/repository.
Public README describes FastAPI, Next.js, PostgreSQL/TimescaleDB, a typed strategy DSL, paper trading, risk gates, layered/hexagonal architecture, and AI-assisted strategy drafting. README also lists unfinished items such as equity curve visualization, tradable position rounding, visible metric caveats, and walk-forward validation. Its feature claims are not independently proven by this focused review.

Potentially useful:
- Architecture/import-boundary checks in CI.
- A validated strategy-draft format rather than executing generated Python/code.
- Explicit backtest metric caveats and out-of-sample/walk-forward reporting.
- Handling an unknown broker outcome by reconciling instead of blindly retrying.

Disposition: use patterns and test ideas; no wholesale stack replacement. Strategy-generation features are lower priority than verified execution/accounting safety.

### B. Algo Options Platform
Repository: https://github.com/iamadarsha/algo-options-platform
License: MIT, recorded in the target repository's prior audit.
Public description focuses on Upstox, paper-first intraday options, options-chain/candle ingestion, risk controls and backtesting. Prior audit noted endpoint TODOs and fallback behavior that must not be copied into any live-order path.

Potentially useful:
- Options-specific data/expiry/lot-size validation and strategy test cases.
- Intraday session/market-close rules and option-chain snapshots.
- Walk-forward and Monte Carlo test ideas, but only after verifying implementation and costs.

Disposition: relevant options reference. Preserve Tradepro's existing PostgreSQL/Alembic data model, broker adapter, and risk gates; do not add a second SQLite order database or second market-data stack.

### C. OpenAlgo
Repository: https://github.com/marketcalls/openalgo
License: AGPL-3.0, confirmed on repository/project documentation.
Large multi-broker platform; documentation describes normalized broker APIs, per-broker capabilities, symbol mapping, market-data interfaces, rate limits, alerts and options analytics. It is a separate Flask/React self-hosted platform and is not a drop-in module.

Potentially useful without source copying:
- Broker capability matrix and adapter contract checklist.
- Documented broker-specific symbol mapping, rate-limit, connection-health and streaming edge cases.
- Feature inventory for a future broker-agnostic roadmap.

Disposition: documentation/behavior reference only by default. Do not copy/adapt its server source into Tradepro unless AGPL obligations are deliberately accepted after legal review. No dependency on OpenAlgo is required for the suggested improvements.

### D. Kite Algo Bot
Repository: https://github.com/KoshIndia/kite-algo-bot
License: MIT, confirmed in the target repository's prior audit.
Public README describes a Zerodha-specific rule-based engine with shared backtest/paper/live logic, order admission gates, kill switches, signal scoring, decision logs, event/intermarket context and strategy tests. The repository history is small; features must be validated before relying on them.

Potentially useful:
- Explainable setup scorecard showing factor scores and allow/block reasons.
- Structured decision/rejection logs.
- Tests for stop-distance position sizing, daily-loss caps, API-health blocks and no-lookahead.
- Same deterministic strategy decisions across backtest and paper execution.

Disposition: design/test reference only. Do not transplant Kite-specific broker code or add a second risk engine.

### E. SYSTRA — Systematic Trading Engine
Repository: https://github.com/Akshaypa91/Systematic-Trading-Engine
Public README describes NSE/BSE rules-based strategies, isolated paper/live modes, Upstox OAuth, sandbox-first order placement, charges preview and risk/emergency controls. A LICENSE file is present, but its precise SPDX identity/terms were not independently verified during this pass.

Potentially useful:
- Compare Upstox order/quote/funds/positions capability coverage against our adapter.
- Compare paper/live separation and explicit environment/sandbox safeguards.
- Consider a broker capability/contract test checklist.

Disposition: inspect its exact license and implementation before any code reuse. Until then, architecture/behavior reference only. Do not use claimed live readiness as evidence that our live-order lifecycle is ready.

### F. Bhav
Repository: https://github.com/rajmaurya0904/bhav
License: MIT, confirmed in repository README.
Public README describes a Python bar-by-bar NSE options backtester using Upstox historical and expired-option endpoints, cached one-minute data, deterministic Parquet outputs, warm-up replay, partial/tranche closes, Indian costs and metrics including CAGR, Sharpe/Sortino, drawdown, expectancy, profit factor and Monte Carlo summaries. Bundled sample data allows offline demonstration, but real/full data requires broker API access.

Potentially useful:
- Options-specific research/backtest design and expired-contract data coverage.
- Deterministic run manifests/checksums and cached datasets.
- Warm-up period and partial-close regression tests.
- Additional performance/risk metrics and Monte Carlo uncertainty reports.

Disposition: strongest candidate for an options-research gap study. Do not copy the separate engine wholesale; first design a small adapter around Tradepro's existing backtest services and verify whether its data licence/API permissions permit intended use. Historical data is not automatically free just because code is MIT.

### G. Dhan NIFTY Algo Trading Lab
Repository: https://github.com/builditwithgk/dhan-nifty-algo-trading-lab
License: MIT, declared in README.
Public README describes a paper-only v1, equity and NIFTY-options research, full Indian charge model, stop-distance risk sizing, centralized veto/kill controls, no-lookahead backtesting, out-of-sample validation and a local dashboard. Its v1 does not ship a live-order broker. It uses Dhan-oriented market-data integrations and SQLite/Streamlit, not our app's stack. The README itself notes that example strategies did not pass profitability gates after costs.

Potentially useful:
- Mandatory-stop and lot-rounding edge-case tests.
- Unbypassable risk-gate test patterns.
- Out-of-sample validation and honest reporting of strategies that fail after costs.
- Durable audit journal and restart-frozen kill-switch behavior as design references.

Disposition: useful MIT test/design reference. Reimplement the missing tests/behavior in our own architecture; do not copy the Dhan adapter or introduce its SQLite/Streamlit stack. Its reported strategy results are a reminder that code correctness does not establish profitability.

### H. NSE/BSE Algo Trading System
Repository: https://github.com/vijaxx/algo-trading-system
License: MIT, declared in README.
Public README describes five Indian intraday strategies, deterministic synthetic data, an explicit no-lookahead test/proof, Indian equity cost modelling and pre-trade risk guards. It is paper/backtest only; the README explicitly warns that synthetic results do not indicate live-market edge, slippage is simplified, and partial fills/order-book effects are not modelled.

Potentially useful:
- No-lookahead and future-data-leakage regression tests.
- Deterministic fixtures and risk-cap concurrency tests.
- Clear limitations on synthetic data and simplified fill assumptions.

Disposition: strong low-cost test-design reference, not a source of real-market signals or evidence of profitability. MIT reuse would still require preserving the licence/copyright notice if code is copied; independent reimplementation of ideas avoids copying expression.

## 3. Gap assessment: what is actually missing or worth strengthening

Priority is based on Tradepro's current architecture and the inspected services, not on feature counts advertised by upstream projects.

### P0 — Continue existing safety work; do not duplicate it
1. **Completed 21 October 2026:** Phase 2 slow-persistence and high-volume lease-expiry/renewal race audit passed CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386). No additional production-code change was required.
2. Keep broker submission disabled until order lifecycle, broker reconciliation, partial fills, charge provenance, duplicate prevention, recovery, kill switch and end-to-end tests are complete.
3. Verify cost rates against current primary Upstox/NSE/BSE sources and add a clear “last verified” mechanism; the cost module itself flags some rates as indicative.

### P1 — Highest-value functional gaps to investigate and implement after tests/design
1. **Backtest report quality:** inspect whether persisted API/UI exposes complete equity curve, CAGR, Sharpe, Sortino, expectancy, profit factor, average win/loss, drawdown duration, fees/slippage breakdown and metric caveats. The inspected engine currently exposes only basic trade counts and max drawdown directly; extend the result/report layer if the full reporting path is absent.
2. **Out-of-sample / walk-forward validation:** add a chronological split with strict prevention of future-data leakage, only if not already implemented elsewhere. Do not tune on the final holdout.
3. **Explainable signal ranking:** the existing engine has a composite score but decisions are long-entry/exit/hold. Investigate a read-only ranked scanner output with factor scores and explicit rejection reasons before adding it. No orders should be generated by the scanner.
4. **Options research completeness:** verify whether current backtests support actual option instruments, strike/expiry/lot constraints, expired contracts, spread/tranche exits and option-specific fees. If missing, build a separate research-only extension behind existing interfaces rather than importing another whole engine.
5. **Broker capability contract:** document current Upstox features (quotes, candles, stream, instruments, orders, trades, positions, holdings, funds, rate limits) and add contract tests for implemented endpoints only.

### P2 — Valuable after P1 and current Phase 2
- Monte Carlo trade-sequence/drawdown/risk-of-ruin report, clearly labelled as scenario analysis, not a forecast.
- Regime/event/intermarket filters as optional research features, not hard-coded strategy truth.
- Architecture/import-boundary checks if they catch real coupling in the current tree.
- Structured strategy draft generation only if requested; generated output must be schema-validated and manually activated, never arbitrary code execution.

### Do not add
- A second strategy/risk engine, second order database, duplicate Upstox stream, or wholesale external app.
- New paid market-data/LLM/hosting services just to implement these ideas.
- Live-order submission, automatic reconciliation scheduling, or fill-accounting promotion as a side effect of the research audit.
- Claims that any external repository or strategy is profitable based on README claims or synthetic backtests.

## 4. Copyright and “free” rules

- “Free to use” does not mean “public code can be copied without conditions.” Keep an exact source URL, pinned commit, licence identifier, copied-file list and required copyright/license notices for any code reuse.
- MIT-licensed code can generally be reused with its copyright and licence notice retained, subject to the actual file and dependency licences.
- OpenAlgo is AGPL-3.0; do not transplant its source into this repository under the current plan.
- SYSTRA code reuse is blocked until its exact license terms are verified.
- Review each dependency's licence separately. Repository-level MIT does not automatically relicense bundled assets, generated files, broker SDKs, indicators, or market data.
- Prefer independent implementations of general ideas/algorithms, based on documented behavior, with original code and new tests. This reduces copying risk but is not a substitute for legal advice where provenance is uncertain.
- Upstox/broker API access, hosting, notifications and market-data entitlements may still have costs. Bundled sample data is not a replacement for licensed historical market data.

## 5. Recommended implementation order

1. **Completed:** persistence/lease race tests passed CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386); current docs CI must be verified against its own HEAD.
2. Add missing backtest metrics/report fields and no-lookahead/walk-forward tests after confirming which metrics are already exposed end-to-end.
3. Add a read-only explainable signal-ranking/scan result using existing indicators and risk rules; do not route it to order placement.
4. Add an options research/backtest gap only after validating the current data model, supported instruments, data entitlements and expected performance on the current host.
5. Re-audit tests, migration behavior, frontend checks, documentation and exact-head CI; commit all changes only to `tradepro-improved`.

## Source links

- [Tradepro Improved](https://github.com/tarunsharma2610-del/tradepro-improved)
- [AI Trading Platform (MIT)](https://github.com/afnanadil2007-design/AI-Trading-Platform)
- [Algo Options Platform](https://github.com/iamadarsha/algo-options-platform)
- [OpenAlgo (AGPL-3.0)](https://github.com/marketcalls/openalgo)
- [Kite Algo Bot](https://github.com/KoshIndia/kite-algo-bot)
- [SYSTRA](https://github.com/Akshaypa91/Systematic-Trading-Engine)
- [Bhav (MIT)](https://github.com/rajmaurya0904/bhav)
- [Dhan NIFTY Algo Trading Lab (MIT)](https://github.com/builditwithgk/dhan-nifty-algo-trading-lab)
- [NSE/BSE Algo Trading System (MIT)](https://github.com/vijaxx/algo-trading-system)
