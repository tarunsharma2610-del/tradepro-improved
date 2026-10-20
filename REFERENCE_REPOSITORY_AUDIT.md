# Reference Repository Audit — Tradepro Improved

Audit date: 2026-10-20
Target repository: https://github.com/tarunsharma2610-del/tradepro-improved
Protected baseline: https://github.com/tarunsharma2610-del/Tradepro
Scope: targeted source/tree/README/architecture/test/license review of four candidate projects. This is not a line-by-line audit of every file in each external repository, and README claims are not treated as proof of production readiness.

## Non-negotiable repository safeguard

All future code and documentation changes for this upgrade must target `tarunsharma2610-del/tradepro-improved` only. Do not modify the original `tarunsharma2610-del/Tradepro` repository. Verify target repository, branch and current HEAD before every write. External repositories are references; do not replace Tradepro Improved or copy code without reviewing its licence and dependencies.

## Executive conclusion

Do not replace Tradepro Improved with any candidate. Tradepro Improved already contains substantial application-specific work: Upstox adapter and OAuth, multi-segment instrument-master reconciliation, WebSocket market data, paper order accounting and portfolio controls, durable live-order intents/outbox/audit records, strict order matching, a read-only reconciliation client/worker with leases, persisted run summaries/issues, owner-scoped review API/UI, broker-fill identity records, and an isolated live-fill accounting service with charge provenance. The latest commits on 2026-10-18 added an isolated atomic live-fill accounting contract and tests. The older PROGRESS.md/AUDIT_REPORT.md/ROADMAP.md checkpoint text is dated 2026-10-17 and must be reconciled against current HEAD before further implementation.

The best savings are **design patterns, targeted tests and selected MIT-licensed components after file-level review**, not wholesale repository merges. The current high-priority work remains to complete and verify the existing reconciliation/accounting lifecycle safely. Live submission remains disabled; no external project is evidence that Tradepro is ready for live trading.

## Candidate findings

### 1. AI Trading Platform
Repository: https://github.com/afnanadil2007-design/AI-Trading-Platform
License: MIT (reviewed LICENSE). README describes a paper-only platform, FastAPI + Next.js, PostgreSQL/TimescaleDB, Redis events, layered domain architecture, typed strategy definitions, risk gates, portfolio accounting, broker adapters, and tests. It explicitly says live execution is not enabled and lists known limitations. The public repository page showed only two commits at the time checked; treat its architecture as useful, not as independently established production maturity.

Useful patterns to adapt:
- Keep core trading/domain rules independent from API, ORM, broker and LLM frameworks; enforce import boundaries in CI.
- Model AI-generated strategies as validated structured data/drafts, never executable generated code; require human activation.
- Use Decimal for prices/money and preserve charge provenance.
- Model broker outcomes as accepted/rejected/unknown; ambiguous network outcomes must trigger reconciliation rather than blind retry.
- Use contract tests and explicit adapter ports; never allow strategy code to bypass risk gates.

Tradepro overlap/gap:
- Tradepro Improved already has Decimal/cost accounting, broker abstractions, strategy and risk services, idempotency records and reconciliation concepts. Do not duplicate these.
- A domain-boundary/import-linter pass and stronger tests for order-state transitions may be useful later.
- AI strategy generation is optional and should not delay safe order reconciliation; if added, it must produce a validated draft only, with cost limits and no autonomous activation.

Decision: **high-value architecture reference; selective MIT code reuse only after exact module and dependency review.** Do not import its overall stack wholesale.

### 2. Algo Options Platform
Repository: https://github.com/iamadarsha/algo-options-platform
License: MIT (reviewed LICENSE). README describes FastAPI + React, SQLite, Upstox, paper-first intraday options, candle/option-chain ingestion, strategy modules, risk limits and vectorized backtesting. Its architecture document includes useful options-specific flows. Its Upstox guide contains TODOs around confirming exact endpoint behavior and describes fallback to paper on API errors; that behavior must not be copied into any live-order path. Public repository history showed a small number of commits, so validate implementation and tests before relying on claims.

Useful patterns to inspect:
- Options-chain and expiry data ingestion, strategy-specific configuration, intraday session handling and market-close exit planning.
- Walk-forward/Monte Carlo backtest design and reporting, after confirming the implementation actually avoids look-ahead bias and models costs correctly.
- Explicit live-disable configuration and broker contract tests.

Tradepro overlap/gap:
- Tradepro Improved already imports the official multi-segment Upstox instrument master and supports live LTP streaming; do not add a second market-data stack.
- Audit current backtesting and strategy coverage before adding options-specific metrics, Greeks/chain snapshots, expiry/lot-size validation or more realistic execution simulation.
- Keep the existing PostgreSQL/Alembic and user-scoped repository design; do not introduce a parallel SQLite order database.

Decision: **best domain-specific reference for Indian options research; selectively port algorithms/tests only after checking contracts, licensing and integration cost.**

### 3. OpenAlgo
Repository: https://github.com/marketcalls/openalgo
License: AGPL-3.0 (reviewed License.md and public project documentation). README describes a large self-hosted broker-agnostic platform with many broker plugins, normalized REST endpoints, market-data streaming, symbol mapping, rate limits and extensive broker-integration documentation. It is a different stack and broader execution platform, not a drop-in module.

Useful patterns to study without copying code:
- A broker capability matrix (quotes, history, stream, order book, trades, positions, holdings, margins and supported order types).
- A consistent normalized broker contract and per-broker mapping/contract-test checklist.
- Broker-specific rate-limit handling, symbol mapping, connection health and WebSocket normalization.

License/architecture warning:
- Do not copy, adapt, or link OpenAlgo server source into Tradepro Improved unless the project deliberately accepts AGPL-3.0 obligations after legal review. Reading public docs and independently implementing compatible behavior is the safer default.
- Its Python 3.12+ / Flask + React platform, deployment model and broad dependency surface are not suitable for wholesale transplant into the current FastAPI/Next.js application and constrained Oracle host.

Decision: **documentation and behavior reference only by default; no source-code transplantation.**

### 4. Kite Algo Bot
Repository: https://github.com/KoshIndia/kite-algo-bot
License: MIT (reviewed LICENSE). README and tests describe a Zerodha Kite-focused rule-based system with a shared backtest/paper/live pipeline, risk gates, sizing, kill switches, signal scoring, event/intermarket context, decision logs and strategy tests. The public page showed a very small commit history at the time checked; validate every claimed feature and its limitations. It is Zerodha-specific, not an Upstox adapter.

Useful patterns:
- Explainable signal funnel with per-factor scores and a recorded allow/block reason.
- Position sizing based on stop distance and maximum capital deployment, with tests for risk/reward and daily-loss/consecutive-loss/API-health gates.
- Shared deterministic strategy evaluation for backtests and paper simulation, with explicit differences only at data/execution adapters.
- Event and intermarket context as optional filters, never substitutes for hard risk gates.

Tradepro overlap/gap:
- Portfolio-level risk caps and strategy daily-loss controls already exist in Tradepro Improved. Reuse only missing tests or independently adapt useful sizing/decision-reporting ideas; do not create a second risk engine.
- Review the current backtest implementation for a reproducible shared decision pipeline, fees/slippage, look-ahead prevention, walk-forward evaluation, and explainable rejection logs before implementing enhancements.
- Keep Upstox and the existing broker abstraction; do not transplant Kite-specific code.

Decision: **good MIT-licensed design/test reference for risk and explainability; selective adaptation only.**

## Feature comparison

| Capability | Tradepro Improved current evidence | Most useful reference | Action |
|---|---|---|---|
| Upstox connection / OAuth | Existing Upstox adapter, encrypted per-user credentials, OAuth state protections | Algo Options docs; OpenAlgo broker docs | Keep existing implementation; contract-check official Upstox APIs |
| Instrument master / streaming | Multi-segment completeness-gated sync and Upstox V3 streaming; live OAuth session still unverified | OpenAlgo normalized symbol/streaming docs | Improve capability matrix and stream operational checks; do not duplicate stack |
| Paper trading / accounting | Shared paper execution path, transaction-cost engine, portfolio controls | AI Trading Platform, Kite Algo Bot | Review current behavior; add missing regression tests, not a second engine |
| Live order safety | Durable intent/idempotency/outbox/events, versioned status persistence, read-only reconciliation worker, leases, review queue/UI | AI Trading Platform's unknown-outcome rules; OpenAlgo docs as behavior reference | Complete current work; no blind retry; live submission remains disabled |
| Broker fills / live accounting | Broker fill identity and isolated `LiveFillAccountingService`; latest tests check duplicate fill and paper/live separation | AI Trading Platform Decimal/accounting patterns | Audit integration boundaries and atomicity; do not connect to worker until gates/tests are complete |
| Portfolio risk | Configurable daily loss, exposure, order value, open/pending positions and daily order count; strategy daily-loss gate | Kite Algo Bot risk tests; Algo Options limits | Audit gaps: mark-to-market, margin-aware exposure, global account kill switch and thresholds |
| Backtesting | Existing backtest phase; full current behavior needs code-level comparison | AI Trading Platform and Algo Options Platform | Audit fill model, costs, look-ahead bias, walk-forward and Monte Carlo before porting anything |
| Strategy builder / signals | Existing typed no-code strategy form and five-indicator scoring | Kite Algo Bot explainable scoring; AI Trading Platform validated DSL | Add per-signal explanation only if absent; consider validated draft generation later, not now |
| Broker expansion | Broker abstraction/registry currently Upstox-first | OpenAlgo's broker capability matrix (docs only) | Design capability flags and adapter contract tests before adding another broker |
| SaaS/auth isolation | User-scoped repositories and per-user broker credentials already present | AI Trading Platform auth/ownership patterns | Audit cross-user isolation and authorization coverage; do not replace current auth stack |

## Integration plan, ordered by value and risk

### Immediate: finish existing Phase 2 before broad feature expansion
1. Reconcile current HEAD (2026-10-18) against stale progress/roadmap/audit docs, including the new isolated live-fill accounting service, charge provenance and current test checkpoint.
2. Continue the existing reconciliation checklist: official Upstox order/trade history window and pagination semantics; stale RUNNING-run recovery; crash/restart boundaries; repeated/out-of-order observations; cross-user and cross-connection isolation.
3. Review the exact atomicity boundary between `LiveOrderReconciliationWorker`, broker fill records, `LiveFillAccountingService`, broker-reported charge provenance and live positions. Do not automatically invoke accounting until intent matching, order state, charge source, ownership and idempotency are verified in one safe orchestration.
4. Verify the exact current GitHub Actions run for the current HEAD. Earlier green runs do not prove the current commit passed. No real orders and no production migrations.

### After reconciliation hardening
5. Add a broker capability matrix and contract tests based on OpenAlgo's documentation (independent implementation; no AGPL source copy).
6. Audit backtest correctness against the AI/Kite/Options designs; implement only demonstrated gaps (fees/slippage, no look-ahead, repeatability, walk-forward/out-of-sample and explainable rejection reasons).
7. Audit portfolio/account-level safety gaps: mark-to-market/open P&L and margin-aware exposure if supported by reliable broker data, account-wide live kill switch, session/holiday handling, stale data and API-health blocks.
8. Add options-specific features only after current data/strategy/backtest paths are understood: option-chain snapshots, expiry/lot-size validation, liquidity/spread checks and Greeks if data is reliable and entitlement/cost is acceptable.
9. Consider AI strategy assistance last: structured validated draft, hard schema limits, no generated executable code, no auto-activation, and human approval.

## Explicit non-goals
- Do not replace Tradepro Improved with another repository.
- Do not modify the original Tradepro repository.
- Do not blindly copy whole folders, database models, migrations, Docker setup, broker adapters or dependencies.
- Do not copy OpenAlgo code under AGPL-3.0 without an intentional licensing decision.
- Do not enable live submission, place test orders, silently downgrade a live request to paper, or treat a passing unit test as broker/deployment certification.
- Do not introduce Docker or a heavyweight service stack solely to imitate another project.

## Verification limitations
- This was a targeted repository/source/license audit of the relevant README, architecture/integration documents, tests, selected source files, repository trees and commit history. It was not an exhaustive line-by-line review of every file in all external repositories.
- External repository feature statements are maintainer claims until independently validated. Two candidates had very small visible commit histories at the time checked.
- This audit changed no application code, database schema, production data or broker state. No real broker request or order was made.


## Current-head blocker discovered during audit — 2026-10-20

The latest code/test commit reviewed, `c9273b6e19f2d2854ee311353f5579b586c24969`, has a failed GitHub Actions check: [Backend pytest run 39113589752](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39113589752/job/117634693349). Collection stops with `ModuleNotFoundError: No module named 'app.models.broker_order'` from `backend/tests/test_live_fill_accounting_service.py`.

The current `main` tree also lacks `backend/app/models/broker_order.py`, `broker_trade_record.py`, `live_position.py` and migration revisions `202610180006` / `202610180007`, while `live_fill_accounting_service.py` imports those models and migration `202610180008_execution_charge_provenance.py` declares `down_revision = "202610180007"`. This indicates the latest live-accounting work is incomplete in the checked-in tree and the migration chain is currently broken. Do not integrate external features or describe this checkpoint as green until this is reconciled and the exact current commit passes CI. No live order was placed.


## Superseding current-main verification — 2026-10-21

The 20 October blocker note above is historical and is superseded by subsequent commits and verified CI. The current main tree now contains `BrokerOrder`, `BrokerTradeRecord`, live-fill accounting foundations and the migration chain; the 18 October 2026 chain audit verified one linear chain ending at `202610180008`. Do not use the earlier missing-file observation as the current status.

- Upstox response parser and regression tests were ported; [run 39477976464](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39477976464) passed 406 tests.
- Broker trade staging and adapted tests were ported with mainline schema constraints; [run 39480002328](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480002328) passed **431 tests, 1 warning**, including SQLite and PostgreSQL 16 reversible migrations.
- The 18 October safety branch's 456-pass result and the mainline 406/431-pass results belong to different source/test trees. The dependency map in `SAFETY_BRANCH_PORT_MATRIX.md` identifies 21 remaining safety-only test modules; this is not evidence of 50 deleted tests.
- Broker trade staging remains isolated and is not connected to accounting promotion or automatic live execution. No real broker order was submitted. Next step is child-order/parent-fill reconciliation with replay, rollback and isolation tests; live writes stay disabled.
