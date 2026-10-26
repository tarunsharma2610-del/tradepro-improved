# Reuse-First Integration Plan — Tradepro Improved

**Status:** Decision and execution plan; not evidence that integrations are already implemented  
**Prepared:** 26 October 2026  
**Planning branch:** `planning/ai-research-desk-post-phase3`  
**Implementation target:** `tarunsharma2610-del/tradepro-improved` only  
**Deadline target:** 48 hours from execution start; this is a prioritization target, not permission to bypass acceptance gates.

## 1. Executive decision

Do not rebuild the application and do not import entire trading platforms blindly. Keep Tradepro Improved as the system of record and integrate the smallest proven pieces that close a real gap.

1. **Upstox APIs remain the authoritative broker/data integration.** Keep the existing async HTTP/WebSocket implementation unless a narrow SDK compatibility spike proves a specific benefit. Reuse official endpoints, schemas, API examples, SDK and Agent Skills as reference material.
2. **Finish Phase 3 before promoting broker fills into live accounting.** The canonical allocation/reconciliation path is the immediate implementation task. Do not invent per-fill charge splits, tariff mappings, GST/IPFT treatment, or broker field semantics when source evidence is missing.
3. **Build the AI Research Desk inside the existing FastAPI/frontend architecture.** Reuse the agent roles, workflow patterns and safe research utilities from Vibe-Trading and TradingAgents. Do not deploy a separate full desktop application as the core product.
4. **Use Bhav as the first backtesting reuse candidate.** Audit its engine, Indian charge model, expired-option data support, test fixtures and strategy contract; reuse/adapt isolated MIT-licensed components only after compatibility and correctness checks. Do not replace Tradepro's backtest service wholesale.
5. **Use OpenAlgo as a broker-abstraction and workflow reference, not a blind dependency.** Its AGPL-3.0 license and overlap with the existing broker layer make code import a deliberate license/architecture decision.
6. **Do not integrate NautilusTrader into the 48-hour target.** Evaluate it later as a research spike only if the current engine demonstrably cannot meet a requirement. The current upstream is LGPL-3.0 and Python 3.13+ in its v2 transition; it adds significant compatibility and operational surface for a 2-CPU/approximately-1-GB VM.
7. **Treat Trading Agents Lab as a UX/workflow reference, not a runtime dependency.** The project is AGPL-3.0; its documentation says the desktop is tested on macOS and requires Python 3.13/Node 20. Borrow the debate/report ideas, not its full application, unless a separate license and runtime decision approves it.

## 2. What Tradepro Improved is building

The target is a personal-use Indian-market trading/research application with:

- Upstox-first OAuth, read-only account/portfolio and market data, quotes, candles, instruments, WebSocket streams and order/trade reconciliation.
- Nifty 500/equity scanning; NSE/BSE/MCX coverage only where supported data and instrument masters are verified.
- Strategy configuration, historical backtests, options/futures analysis, charts and risk/performance reporting.
- P&L that distinguishes actual broker charges from estimates and includes supported taxes/fees without double-counting.
- Paper trading first, explicit human approval and hard risk controls; live order writes remain disabled until separately authorized and safety-reviewed.
- A research desk that gathers cited evidence, analyses fundamentals/technicals/news/events, compares bull/bear cases, tests strategy hypotheses and produces a transparent report before any paper-trade proposal.
- Later alerts/notifications and scheduled research only after the existing worker, permissions, cost limits and recovery behavior are verified.

This plan does **not** claim all of these capabilities are complete. The repository's code, migrations, tests, docs and current CI—not roadmap wording—determine implementation status.

## 3. Repository self-audit and immediate checkpoint

The last authoritative Phase 3 checkpoint retrieved from the implementation branch records:

- Repo: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- PR #6 is open/draft/unmerged. Never merge without explicit user approval.
- The 25 October checkpoint recorded commit `075b16af03cf6be4897c381378f68db76a6cbba6` and successful exact-head Backend CI run [#40211145592](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40211145592). A later documentation commit was also reported as `383ccde7dad187d2d9ddeec30b712bbf3ede3ca5`, with Backend CI run [#40212469240](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40212469240). Re-check the current branch head and checks before implementation; do not assume either SHA is still the latest.
- The immediate next code task is to connect canonical snapshot allocation/reconciliation to `live_fill_accounting_service`, including reviewed source evidence, combined/split transaction/IPFT representation, exact replay, complete totals and rejection of extra/unmapped components.
- The existing SDK audit states that backend dependencies include `httpx`, `websockets` and `protobuf`, but not `upstox-python-sdk`. Existing code has async REST calls, a custom V3 protobuf/WebSocket streamer, a read-only reconciliation client and validated charge parsing. Do not replace those paths without an evidence-backed compatibility result.
- Existing Upstox brokerage calculator results are estimates, and aggregate charge endpoints are not per-fill actual evidence. Contract-note/source authenticity and product/date/invoice-specific tariff/GST/IPFT semantics remain separate acceptance requirements.
- The planning branch contains the checkpointed project documents; it is not the implementation branch. This plan must not cause accidental changes to the original `Tradepro` repository or bypass the active Phase 3 branch.

## 4. Reuse decision matrix

| Candidate | Reuse target | Decision | Why / guardrail |
|---|---|---|---|
| [Official Upstox API docs](https://upstox.com/developer/api-documentation) | Current endpoint contracts, auth, rate limits, quotes, candles, fundamentals/news, WebSockets, portfolio and charges | **P0 — authoritative** | Verify exact API version, token class, entitlement, rate limit and response schema. Never infer per-fill accounting from an aggregate endpoint. |
| [Official Upstox Python SDK](https://github.com/upstox/upstox-python) | Supported request/response models and examples; isolated endpoint compatibility spike | **P0 — selective** | Do not add as a dependency until one real call path uses it and async, timeouts, error redaction and testability remain intact. Do not call real-money order methods. |
| [Upstox Agent Skills](https://github.com/upstox/upstox-skills) | API-reference/development guidance for coding agents | **P0 — development-only** | Static review, source links and generated-code guidance only. Skills are not production authorization and cannot override broker-write guards. |
| [Bhav](https://github.com/rajmaurya0904/bhav) | NSE options backtest mechanics, Upstox expired-option retrieval, Indian cost model, deterministic Parquet outputs, metrics and test patterns | **P1 — audit then selectively adapt** | README identifies MIT license, Python 3.11+, and optional Node 20 UI. Verify license file, actual code/tests, time-series assumptions, charge rules, data licensing and runtime cost. Reconcile its cost model with Tradepro's audited rules before reuse. |
| [Vibe-Trading (HKUDS)](https://github.com/HKUDS/Vibe-Trading) | Research autopilot, hypothesis → deterministic backtest → evidence report, data bridge, strategy generation and reusable skills | **P1 — inspect modules and reuse patterns** | Public repo reports MIT license. Audit dependency graph, execution hooks, prompt/tool boundaries and current maintenance. Do not import its whole stack or let generated strategies execute arbitrary code. |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) | Analyst roles, bull/bear debate, tool-based evidence collection, risk/portfolio-manager synthesis | **P1 — preferred AI architecture reference** | Public repo reports Apache-2.0. Reuse modular ideas/components with attribution and license notice as required. Adapt data tools to Indian sources; do not treat LLM output as an execution signal. |
| [Trading Agents Lab](https://github.com/RBJGlobal/TradingAgentsLab) | Research report UX, debate transcript, provider selection, local model support and cost guard | **P2 — UX/reference only** | AGPL-3.0 fork; docs list Python 3.13/Node 20 and macOS-tested desktop. Do not copy code into the app without explicit license review. Do not run the desktop app as the server's core. |
| [OpenAlgo](https://github.com/marketcalls/openalgo) | Broker capability matrix, normalized adapter contracts, option tools, Analyzer/paper mode, API/UI patterns | **P2 — reference first** | AGPL-3.0 and overlaps with the existing broker subsystem. Do not vendor/import its implementation or expose its execution service as a shortcut. Consider standalone use only after license, API and safety review. |
| [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) | Future event-driven backtest/live parity research | **P3 — defer** | Upstream currently identifies LGPL-3.0 and Python 3.13+ for its v2 line. Resource/adapter integration is too broad for the 48-hour critical path. No wholesale engine replacement. |
| [OpenBB](https://github.com/openbq-org/OpenBB) | Potential financial-data adapter/fundamental research connector | **P2 — compare before adoption** | Audit current license, Indian-market coverage, provider availability, payload provenance and dependencies. Prefer direct official sources when they are sufficient; avoid adding a broad data platform just for one endpoint. |
| Official exchange/company sources and public filings | Corporate announcements, results, shareholding, filings, events and official reference data | **P0 — evidence sources** | Store source URL, publication/effective time, retrieved time and content hash. Respect site terms/rate limits. Scraped forum/social content is sentiment context, never verified company fact. |
| Forums, Reddit, StockTwits, news publishers | Discovery and sentiment context | **P2 — secondary evidence** | Label as unverified/user-generated, timestamp it, link the original source and guard against prompt injection. No rumor alone may create a trade. |

**License policy:** before copying any code, record repository URL, commit/tag, license, files copied, required notices, local modifications, dependencies and intended use in a third-party reuse register. “Open source” does not mean license-free. If the license is incompatible or uncertain, use the public documentation as inspiration and implement an independent adapter.

## 5. Target architecture: reuse the existing application

Keep one system of record. Add adapters and services behind existing application boundaries rather than introducing multiple competing apps.

1. **Market/broker adapters:** current Upstox client remains canonical. Add a typed adapter only where an endpoint is missing or the existing parser is demonstrably inadequate. Store raw-response provenance with normalized data where policy permits.
2. **Research data layer:** normalized entities for instrument, quote/candle, company metric, announcement/event, news item and source citation. Each fact includes source/provider, timestamp, freshness and confidence/verification label.
3. **Deterministic analytics:** existing scanner, indicator, strategy and backtest services perform numeric calculations. Agents may request calculations; they must not fabricate numeric values or silently replace computed results with prose.
4. **Research orchestration:** one bounded workflow service coordinates specialised roles. Use structured input/output schemas, persisted run IDs, timeouts, cancellation, retries and token/cost ceilings. Avoid a long-running agent swarm or separate microservice unless the existing worker cannot host it.
5. **AI roles:** (a) fundamentals, (b) technicals, (c) news/events, (d) bull case, (e) bear case, (f) quant/backtest, (g) independent skeptic/source checker, (h) risk officer/final synthesis. These are roles in a workflow, not necessarily eight independent deployed agents. Start with sequential calls and shared cited evidence to reduce cost and resource use.
6. **Output:** evidence-backed report with thesis, counter-thesis, catalysts, risks, valuation/metrics with source dates, technical context, event calendar, backtest limitations, confidence/unknowns and explicit invalidation conditions. Include source links and agent disagreements; never present an LLM confidence score as a calibrated probability unless empirically calibrated.
7. **Paper-trade proposal:** deterministic strategy/risk engine validates instrument, lot size, capital, margin, max loss, liquidity, data freshness and paper-mode settings. Human confirmation remains required. AI agents cannot call broker write endpoints directly.
8. **Observability:** record run inputs, prompt/template versions, model/provider, token/cost estimate, source citations, tool calls, deterministic calculation versions, result and failure reason. Add daily/weekly budget caps and cancellation.
9. **Security:** treat all web/news/forum text as untrusted data, not instructions. Tool allowlists, schema validation, secrets redaction, SSRF protection, bounded fetch sizes, safe HTML/PDF parsing and no arbitrary code execution are required. No agent-generated Python runs in the backend without a separate sandbox and human review.

## 6. Two-day execution sequence

### Day 1 — Phase 3 correctness first; build the research vertical slice

**Gate 0 — first 30–60 minutes**
- Verify current implementation branch head, PR #6, exact-head CI and pending failures.
- Read the Phase 3 checkpoint and existing charge component-set/allocation/reconciliation services.
- Compare existing tests before writing new tests; identify only missing integration cases.
- Freeze unrelated refactors and do not restart completed work.

**Gate 1 — Phase 3 allocation integration**
- Wire the canonical snapshot allocation/reconciliation path into `live_fill_accounting_service`.
- Preserve atomicity, idempotent replay, rollback, exact decimal/paise handling and source-total reconciliation.
- Test combined vs split transaction/IPFT, partial fills, exact replay, missing/extra/unmapped components, conflicting replay, rollback and PostgreSQL concurrency as appropriate.
- Keep unknown or unauthenticated source evidence rejected. If authentic tariff/invoice evidence is unavailable, leave that rule DRAFT and record the blocker; do not invent evidence or claim the full accounting gate passed.
- Run targeted tests, full relevant backend CI, safety-boundary checks and migration/recovery gates. Commit and verify CI against the exact new head.

**Gate 2 — source inventory and integration spike**
- Inventory existing quote, candle, news, fundamentals, instrument, backtest and risk services and identify the smallest missing capability.
- Compare current Upstox endpoints against the official docs; only use a narrow read-only SDK spike if it fills a gap.
- Inspect Bhav's engine/cost/tests and Vibe-Trading/TradingAgents orchestration code; record exact reusable files/commit/license and compatibility.
- Do not add all projects as dependencies.

**Gate 3 — minimum AI Research Desk slice**
- Add a single research-run API/service and persisted result schema using existing app conventions.
- Implement one end-to-end flow: instrument → source-backed quote/metrics/news/events → deterministic technical summary → bull/bear analysis → skeptical evidence check → risk summary → cited report.
- If model credentials are absent, provide a deterministic “data collected / AI unavailable” result and make the missing configuration visible; never fake an AI response.
- Run tests with recorded/synthetic fixtures, no external credentials and no live broker writes.

### Day 2 — connect, harden and verify

**Gate 4 — enrich and integrate**
- Add missing research sources only where a verified API/source exists and terms allow it.
- Reuse suitable Bhav backtest logic only after mapping it to Tradepro's strategy contract, Indian cost accounting and test suite. If the engine is incompatible, preserve it as a separate offline benchmark and do not destabilize the existing backtester.
- Add report history, source citations, freshness labels, failure states, budget/time limits and UI access through the current frontend.
- Add a paper-trade proposal path only through existing deterministic strategy/risk controls; no agent gets direct broker write access.

**Gate 5 — adversarial tests**
- Missing/stale data, source conflicts, duplicate events, market holiday/time-zone edges, API throttling/timeouts, malformed pages, prompt injection, malicious links, model refusal/provider outage, cost-cap exhaustion and cancellation.
- Verify an AI report cannot bypass risk controls or trigger real broker actions.
- Verify charge estimates are labelled estimates and actual charges are source-backed and reconciled.
- Test migrations, rollback, idempotency, restore procedure and low-resource operation.

**Gate 6 — release candidate**
- Run full applicable CI on the exact final commit and inspect every failed/queued/running job.
- Update the canonical roadmap, progress, handover, architecture, integration/audit and change-log documents that are affected; do not mechanically duplicate stale checkpoint blocks into unrelated files.
- Record actual feature status as PASS / FAIL / BLOCKED with evidence and test links.
- Keep PR #6 draft/unmerged pending user authorization. Keep PAPER mode mandatory and all live broker writes disabled.

## 7. Acceptance checklist

- [ ] Current implementation branch/head and exact-head CI verified before edits.
- [ ] Phase 3 canonical allocation/reconciliation integrated end-to-end; unsupported or unauthenticated charges fail closed.
- [ ] Evidence-backed tariff/GST/IPFT rules are independently verified, or explicitly remain blocked/DRAFT—not falsely marked complete.
- [ ] Existing Upstox integration reused; any SDK addition has a narrow test and a documented reason.
- [ ] AI research run produces a structured report with source citations, timestamps, data freshness and explicit unknowns.
- [ ] Bull/bear/skeptic/risk roles run under bounded time/cost and provider failure is handled visibly.
- [ ] Numeric metrics/backtests come from deterministic services; AI cannot invent or alter their values.
- [ ] Paper-trade proposals pass deterministic risk controls and require the existing human approval path.
- [ ] No AI tool can call live order placement/modification/cancellation.
- [ ] Reuse register records provenance and license obligations for copied code.
- [ ] Full relevant CI, broker-write safety, migrations and recovery checks pass on the exact final head.
- [ ] Documentation reflects verified facts; no stale counts, unverified claims or duplicate work.
- [ ] PR #6 remains unmerged without explicit user approval; original `Tradepro` remains untouched.

## 8. Explicitly out of scope for the 48-hour critical path

- Replacing the entire platform with OpenAlgo or NautilusTrader.
- Integrating every candidate repo or installing multiple overlapping agent frameworks.
- Enabling autonomous live trading, automatic live-fill promotion or automatic scheduling before their gates pass.
- Claiming Nifty 500, all NSE/BSE/MCX derivatives, comprehensive event coverage or production recovery without test/data evidence.
- Treating forum posts, LLM outputs, aggregate brokerage APIs or estimated charges as verified facts.
- Sacrificing safety, source attribution, reproducibility or exact-head CI to meet a calendar deadline.

## 9. Source links consulted

- Upstox API overview and Agent Skills: https://upstox.com/developer/api-documentation
- Upstox authentication: https://upstox.com/developer/api-documentation/authentication/
- Official Upstox Python SDK: https://github.com/upstox/upstox-python
- Official Upstox Skills: https://github.com/upstox/upstox-skills
- Bhav (MIT per repository README): https://github.com/rajmaurya0904/bhav
- Vibe-Trading (MIT per GitHub repository metadata): https://github.com/HKUDS/Vibe-Trading
- TradingAgents (Apache-2.0 per repository metadata): https://github.com/TauricResearch/TradingAgents
- Trading Agents Lab (AGPL-3.0 fork): https://github.com/RBJGlobal/TradingAgentsLab
- OpenAlgo (AGPL-3.0): https://github.com/marketcalls/openalgo
- NautilusTrader (LGPL-3.0): https://github.com/nautechsystems/nautilus_trader
- OpenBB data platform: https://github.com/openbq-org/OpenBB

**Review note:** repository metadata and README statements are initial screening, not a substitute for checking the exact commit's LICENSE file and applicable dependencies before code is copied or deployed.
