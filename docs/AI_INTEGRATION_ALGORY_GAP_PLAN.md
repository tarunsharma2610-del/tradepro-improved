<!-- Phase 3 DP per-fill accounting checkpoint — 27 Oct 2026. Implemented optional demat_transaction_charges in LiveFillChargeBreakdown validation, Execution.total_charges, status, API completeness, and exact replay comparison. Equity-delivery SELL now requires a reviewed/reconciled DP canonical snapshot plus allocation for that fill; other fills reject an extra DP allocation. Snapshot materialization permits component-specific reviewed fill manifests so DP can target only eligible delivery sells. DP canonical allocations can now be independently reviewed and promoted to RECONCILED. Synthetic delivery-sell test verifies KNOWN DP amount and total charges; separate tests cover missing DP, paise precision, and subset manifests. Backend CI #40455767684 on prior code/test head c2ed99843368bd7716f03983219ab048d095cbf2 had 1 assertion-message mismatch and 1,076 passed; updated the assertion in commit 855fcf68cb3202f09e3a2f98cecb99ce57240728. Exact-head CI is pending; do not mark green until it passes. Prior successful safety/migration/restore gates: #40455290232. GST/IPFT not restarted; invoice-level acceptance and independent tariff approval remain separate gates. PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original Tradepro out of scope. -->

# AI Integration Plan — Research Agents and Algory.app Gap Audit

**Status:** Planned only; intentionally deferred until Phase 3 is accepted.  
**Target repository:** `tarunsharma2610-del/tradepro-improved` only.  
**Safety:** Keep PR #6 draft/unmerged unless explicitly approved. PAPER mode remains mandatory; live broker order writes and autonomous live activation remain disabled.

## Purpose

When AI integration starts, use this document as the required intake checklist. Explicitly include **Algory.app** and the gap findings below so the audit is not lost between sessions. This is a planning artifact, not approval to start implementation during Phase 3.

## Existing Tradepro Improved foundation to reuse

Repository audit notes identify existing components that must be inspected and extended rather than duplicated:

- `backend/app/services/strategy_engine.py`: weighted composite signals using RSI, SMA crossover, MACD, volume spike and momentum.
- `backend/app/services/backtest_engine.py`: bar-by-bar backtesting, existing position/fill math, transaction-cost functions, configurable slippage and basic drawdown/win-loss reporting.
- `backend/app/services/ai_assistant_service.py`: LLM contextual assistant using portfolio positions, recent orders and related news; this is not yet a complete research-agent system.
- Existing portfolio risk controls, Upstox integration, paper execution, order idempotency/outbox, broker-fill identity, reconciliation records/workers, and isolated live-fill accounting.

First inspect current source, tests and docs at the Phase 3 completion checkpoint. Treat this inventory as a lead, not a claim that every listed capability is complete or production-ready.

## Algory.app audit: capability-by-capability gap matrix

Algory.app is a strategy discovery and validation reference, not a platform to copy wholesale. Re-verify current product capabilities and terms when this stage begins.

| Capability / finding | Current Tradepro Improved position from prior audit | Required action during AI stage |
|---|---|---|
| Indicator-based strategy signals | Weighted indicator score already exists | Reuse and test; do not create a parallel signal engine |
| Historical backtesting | Bar-by-bar engine and transaction-cost hooks exist | Audit data quality, no-lookahead, fill realism, fees/taxes/slippage and reproducibility |
| Comprehensive performance report | Basic drawdown and win/loss reporting exists; completeness not established | Verify and add only missing metrics: equity curve, CAGR, Sharpe/Sortino, expectancy, profit factor, average win/loss, drawdown duration and fee/slippage breakdown |
| Out-of-sample / walk-forward validation | Not confirmed as complete | Verify; add chronological train/validation/test splits and walk-forward evaluation if missing |
| Genetic/evolutionary strategy discovery | Not confirmed; not to be assumed implemented | Evaluate bounded candidate generation/evolution only after deterministic validation is reliable |
| Candidate versus random/baseline strategies | Not confirmed | Add robust baselines and multiple-testing safeguards if missing |
| Monte Carlo / trade-sequence stress testing | Not confirmed | Test sequence resampling, drawdown tails and robustness if missing |
| Parameter sensitivity / overfitting checks | Not confirmed | Add parameter stability and sensitivity analysis if missing |
| Portfolio diversification and strategy correlation | Risk controls exist, full strategy-level correlation not confirmed | Audit correlation, concentration, overlap and portfolio-level drawdown before recommending combinations |
| Strategy library, provenance and candidate “passport” | Not confirmed as complete | Persist candidate source, data window, parameters, code/version, metrics, validation status and rejection reasons |
| Backtest-to-paper/broker parity and decay monitoring | Not confirmed as complete | Compare predicted versus paper/actual fills; monitor drift, decay and alert/retire candidates under explicit rules |
| Scheduled re-evaluation | Automatic scheduling is currently disabled by safety policy | Consider only after Phase 3 acceptance and explicit approval; no autonomous live activation |
| MT5 export | Algory-specific capability; Tradepro is Upstox-first | Defer unless a concrete user need justifies it |

## Planned research-agent roles

Assess integration of these eight roles against existing services before creating anything new:

1. Fundamentals and financial-statement researcher.
2. Technical/market-structure researcher.
3. Corporate actions, earnings and event-calendar researcher.
4. News and sentiment researcher.
5. Macro and sector-context researcher.
6. Quantitative strategy discovery and validation researcher (including the Algory.app gap matrix).
7. Risk, portfolio exposure and downside researcher.
8. Research coordinator/orchestrator that reconciles evidence, flags disagreement, and produces a traceable report.

Agents should provide sourced, timestamped evidence and structured proposals. Missing data, stale sources and disagreements must be visible; an LLM must not invent market facts or silently fill missing values.

## Architecture and safety boundaries

- Deterministic code—not an LLM—owns signals, backtest execution, fill simulation, costs/taxes, portfolio accounting and risk limits.
- AI may research, summarize, propose candidate strategies and explain results; it may not bypass validation, risk controls, accounting review or broker-write guards.
- Generated strategies remain drafts until they pass reproducible tests, data-leakage checks, out-of-sample/walk-forward evaluation, transaction-cost-aware backtests, robustness/stress checks and human approval.
- No automatic activation or live order placement. PAPER mode remains mandatory; live broker writes stay disabled unless separately reviewed and explicitly authorized.
- Preserve Upstox-first design. Review licences, maintenance, dependencies, data rights, API terms and security before adopting external code/services. Prefer selective ideas and compatible open-source components over wholesale replacement.
- Apply cost/rate limits, logging, source citations, secret redaction, prompt-injection resistance and deterministic fallbacks to all research-agent calls.

## Required workflow when Phase 3 is accepted

1. Verify the latest Tradepro Improved branch, exact commit, CI and project docs; do not rely on stale checkpoint text.
2. Re-audit current strategy, backtest, market-data, risk and AI services with tests.
3. Revisit Algory.app's current official product material and terms; mark each matrix item **implemented / partial / missing / not applicable**, citing repository files/tests or authoritative product sources.
4. Review candidate reference projects and broker/API capabilities; check licence and provenance before any reuse.
5. Produce a prioritized design with dependencies, acceptance tests, cost controls and rollback plan before implementation.
6. Implement in small increments, add regression tests, update all relevant project checkpoint/roadmap documents, commit to this repository, and verify exact-head CI.
7. Keep Phase 3 accounting/tariff evidence gates separate; AI research must not be used as evidence to approve brokerage, GST, IPFT or other tax treatment.

## Acceptance checklist

- [ ] Phase 3 is explicitly accepted and its latest exact-head CI/docs checkpoint is verified.
- [ ] Existing functionality and tests mapped before proposing new modules.
- [ ] Algory.app capability matrix refreshed and every gap dispositioned.
- [ ] Eight research-agent roles mapped to existing or planned services.
- [ ] Backtest realism, no-lookahead, out-of-sample validation and metrics gaps resolved or explicitly deferred.
- [ ] Candidate provenance, human approval, risk limits and paper-only boundaries tested.
- [ ] Licence, API/data terms, privacy, cost and security reviews recorded.
- [ ] Relevant docs synchronized and exact-head CI passes.

## Explicit deferral

Do not begin this AI/Algory implementation while Phase 3 is still in progress. Resume this plan only after Phase 3 acceptance; the next Phase 3 task remains the current documented tariff/component evidence gates, not AI work.
