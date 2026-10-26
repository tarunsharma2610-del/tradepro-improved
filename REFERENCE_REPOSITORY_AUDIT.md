## Authoritative Phase 3 checkpoint — 26 October 2026

- Work only in `tarunsharma2610-del/tradepro-improved`, branch `phase3/durable-per-fill-charge-allocation`; implementation head `eeea33a11303d03bee508be2f5af887dd5ee26e0`; exact-head Backend CI [#40290116323 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40290116323).
- Latest code change applies the order-level brokerage cap once before deterministic paise-exact distribution by reviewed fill weights; added coverage for caps, unequal weights, stable tie rounding, invalid weights, and DRAFT tariff rejection.
- Phase 3 is NOT complete. Continue with effective-dated tariff review, component-specific allocation acceptance, invoice/source-backed GST/IPFT and product/segment evidence, adversarial/migration/recovery review, then final exact-head sign-off. Do not redo canonical live-fill integration.
- Public tariff snapshots remain estimate-only; no inferred approval for actual account charges, GST composition, stamp duty or unsupported segment mappings. PAPER mandatory; live order writes, automatic live-fill promotion and scheduling disabled. PR #6 remains open/draft/unmerged unless explicitly approved. Defer AI/open-source adaptation until Phase 3 acceptance. Documentation commit must pass its own CI.

---

## Current Phase 3 checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `3963c2bf4e6ffe2bb33d327b10e2995cd243d003`. Exact-head [Backend CI run 39607630055](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39607630055) passed **484 tests, 1 warning in 29.34s**; the broker-write boundary guard passed, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- New Phase 3 guard: broker-reported live-fill charge references are trimmed for storage and rejected when longer than the `Execution.charge_reference` 200-character column limit. This prevents a predictable storage error from being misreported as a concurrent promotion conflict. Regression coverage is included in the 484-test result.
- The existing Phase 3 safety gates remain active: replay must match the accounted fill and exact charge evidence; only broker-reported, internally consistent charges with a non-empty audit reference are accepted; durable staged trade quantities must match broker-confirmed child fills before promotion; exchange-time ambiguity/out-of-order fills fail closed; paper positions and cash remain isolated.
- **Phase 3 remains in progress, not complete.** Remaining review includes coordinator/identity boundaries, charge provenance/allocation semantics, full partial-fill and crash/restart acceptance criteria, and any explicitly selected bridge design. Keep `BrokerFillIdentity` separate from manual `BrokerTradeRecord` unless a reviewed Phase 3 design explicitly authorizes a narrow bridge.
- Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. The original `tarunsharma2610-del/Tradepro` repository remains untouched. Phase 2 remains closed.
- This checkpoint describes the verified code commit above. The documentation synchronization commit will trigger its own CI; do not treat that documentation commit as green until its exact-head run passes. Older checkpoint entries below are historical audit trail, not current status.

---

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


## Cumulative live-fill guard and intake-architecture finding — 2026-10-21

- Current main now includes a cumulative per-child accounting guard in `LiveFillAccountingService`; a new staged trade is rejected if its quantity plus already-accounted executions would exceed the broker-confirmed child fill total. Regression test included.
- Exact code/test checkpoint `5ad579f60e78dcb5fdee14dcdb17dc4c9d8956a1`, [run 39480669799](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480669799): **432 passed, 1 warning**, including SQLite and PostgreSQL 16 reversible migration checks.
- Important unresolved architecture split: `LiveOrderReconciliationWorker` writes trade identities to `BrokerFillIdentity`, while `BrokerTradeIngestionService` stages `BrokerTradeRecord` and `LiveFillAccountingService` promotes that second model. These must not be treated as one source of truth without an explicit migration/bridge plan. Keep the accounting service unregistered and live writes disabled.


## Child-order reconciliation port — 2026-10-21

- Added the child-order reconciliation service and tests with current-main schema adaptations; broker-reported filled quantity must equal the sum of durable staged trades, weighted average price must match, and terminal state/fill quantity cannot regress. Only `BrokerOrder.status` and `filled_quantity` are updated.
- Exact-head [run 39481385581](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581) passed **438 tests, 1 warning**, including SQLite and PostgreSQL 16 reversible migration checks.
- Main has 38 test modules; the safety branch has 48, with 20 safety-only modules remaining. See `SAFETY_BRANCH_PORT_MATRIX.md`.
- Next gate is to document whether the intent-based `BrokerFillIdentity` path and manual Order `BrokerTradeRecord` path are distinct by design or need a safe bridge. Do not merge their records implicitly; keep live writes and automatic promotion disabled.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Resolver now checks that the payload field name matches the terminal field in the selected approved mapping path. This closes a semantic mismatch where a caller could select `charges.ipft` but normalize another payload field.
- Implementation commit: `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression test commit: `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI for latest commits is pending; previous green runs apply only to earlier heads.
- Existing accounting tests cover lock ordering, replay idempotency, conflicting evidence and rollback. A genuine concurrent two-session verification-versus-promotion race is not demonstrated in the inspected live-fill test file; verify other integration coverage before marking complete.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Latest resolver CI and PostgreSQL concurrency suite verified

- Latest implementation/documentation checkpoint `ed346e823cbfae8448fae0134c4ff864bfcc60ac` passed Backend pytest workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654): **872 passed, 1 warning**, with the broker-write boundary guard also passing.
- Dedicated PostgreSQL concurrency tests are present in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`, including source verification vs allocation promotion and live-fill promotion vs ledger verification. The successful CI summary reports no skipped tests, so this run exercised the collected suite; the race tests are part of that test set.
- This confirms test execution and safeguards in the synthetic PostgreSQL test environment; it does not establish production broker tariff correctness or approve any real Upstox field mapping.
- PR #6 remains draft/unmerged. Live broker order submission and automatic quantity/notional allocation remain disabled. Work only in `tradepro-improved`; original `Tradepro` remains untouched.


## Authoritative checkpoint — 26 October 2026 (documentation CI verified)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- Latest implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`; exact-head Backend CI [#40287765745 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745).
- Documentation synchronization commit: `f90573d653c7103bf9cfdb1f867da97b176d3240`; its exact-head Backend CI [#40289107666 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40289107666). Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of actual Oracle Cloud recovery.
- Approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries do not supersede this checkpoint.
