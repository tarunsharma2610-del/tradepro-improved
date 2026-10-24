# Upstox API, SDK, Framework and Agent-Skill Usage Policy

**Mandatory for Tradepro Improved. Last reviewed: 2026-10-24.** Scope is only `tarunsharma2610-del/tradepro-improved`; never modify original `tarunsharma2610-del/Tradepro`.

## Rule

Before any Upstox-related design, implementation, or audit, consult the current official Upstox API catalogue and endpoint docs, authentication/developer console, SDK docs/source, official examples and announcements, sandbox, rate limits, and relevant official Agent Skills/MCP docs. Maintain a capability matrix and use every capability relevant to the project and actually available/permitted—not every endpoint blindly. Do not rely on memory, outdated snippets, or forum claims without official corroboration or reproducible tests.

## First-party references

- API catalogue: https://upstox.com/developer/api-documentation/
- SDK installation: https://upstox.com/developer/api-documentation/installing-sdk/
- Official Python SDK: https://github.com/upstox/upstox-python
- Official Node.js SDK: https://github.com/upstox/upstox-nodejs
- Agent Skills docs: https://upstox.com/developer/api-documentation/agent-skills/
- Official Agent Skill repository: https://github.com/upstox/upstox-skills
- Read-only MCP docs: https://upstox.com/developer/api-documentation/mcp-integration/
- Hosted MCP endpoint: https://mcp.upstox.com/mcp
- Sandbox: https://upstox.com/developer/api-documentation/sandbox/
- Rate limits: https://upstox.com/developer/api-documentation/rate-limiting/
- Brokerage estimate API: https://upstox.com/developer/api-documentation/get-brokerage/
- Historical trade-charge API: https://upstox.com/developer/api-documentation/get-trade-charges/
- Historical trades API: https://upstox.com/developer/api-documentation/get-historical-trades/
- Developer community: https://community.upstox.com/c/developer-api
- Tariff page: https://upstox.com/brokerage-charges/

Re-verify current URLs, API versions, permissions, and supported segments during each audit; this list is an initial inventory, not proof of current availability or account entitlement.

## Required API capability inventory

For every relevant capability record: endpoint and API version, purpose, official source, segment/instrument coverage, auth/scope/static-IP/entitlement, rate limits, SDK support or reason for direct REST/WebSocket, schema/version caveats, freshness/retention, retries/errors, tests, status (implemented/missing/restricted/not needed), and last-verified date.

Audit at least:

1. **Authentication/account setup:** OAuth, token lifecycle/expiry, analytics token where appropriate, scopes, developer-console setup, static-IP/regulatory constraints.
2. **Instruments:** instrument master, exchange/segment, symbol/token mapping, expiry, strike, lot size, tick size and contract changes.
3. **Market data:** LTP, quotes/full market quotes, OHLC, historical/intraday candles, WebSocket/Market Data Feed V3, depth, reconnect/resubscribe and stale-feed detection.
4. **Derivatives research:** option contracts/chains, Greeks, OI/PCR/max-pain where officially available, expiries, lot constraints and segment entitlements.
5. **Portfolio/account:** holdings, positions, funds/margins, orders/order history, trade book, order details, profile and P&L views. Reconcile with the local ledger; do not blindly overwrite audited accounting.
6. **Charges (mandatory evaluation):** Brokerage Details/Calculator `/v2/charges/brokerage`; Trade Charges `/v2/trade/profit-loss/charges`; Historical Trades `/v2/charges/historical-trades`. Test null/missing fields, pagination/date limits, DP-plan/minimums, financial-year semantics and actual broker outputs.
7. **Order lifecycle (documentation/tests only while gated):** place/modify/cancel, status, fills/trades, multi-order, GTT, exit/square-off, protection and kill-switch controls. Map to existing idempotency/reconciliation design; never invoke live order writes during coding/tests.
8. **Operations:** sandbox, rate limits/backoff, timeouts, pagination, idempotency, WebSocket recovery, observability and error-code mapping.

## SDKs, frameworks, examples, skills and MCP

- Prefer the maintained official SDK for the backend language when it supports the needed endpoint/version. Evaluate the official Python SDK first for this Python-oriented backend. Add Node SDK only for a concrete Node use case; do not add redundant SDKs.
- Verify endpoint-version support individually. If an SDK is behind or lacks a required endpoint/stream, use a small typed adapter against the documented REST/WebSocket contract with contract tests instead of forcing an obsolete path.
- Use official schemas, enums, sample code, changelog and error codes for fixtures and adapter tests. Pin versions and review licences/security before adoption.
- Inspect the official Upstox Agent Skill's `SKILL.md`, references, scripts and examples as API knowledge and test-design resources. The skill can execute live trades: do not run trading-capable scripts in CI, submit live orders, or allow the skill to bypass this app's safeguards.
- Upstox MCP is described as read-only for account data. Use account-scoped MCP only with explicit user authorization and supported connector setup. Never assume it is connected, expose tokens in chat, or access account data without consent. Public API documentation research does not require connecting an account.
- Check official AI-agent documentation and machine-readable docs index (for example `llms.txt`, if currently published). Agent tools help discover accurate API patterns; they do not authorize changing safeguards.
- Forums can identify edge cases; corroborate against official docs or reproducible sandbox/contract tests.

## Brokerage estimate vs actual charge accounting

The brokerage calculator is an **estimate for a proposed order**, not executed-charge evidence. The Trade Charges API returns a historical segment/date/financial-year breakdown; Historical Trades returns trade-level references within documented retention/pagination limits. None automatically replaces a reviewed contract note or eligible-fill manifest.

Keep distinct:
- **Estimated charges:** calculator response, parameters, assumptions, source/version and retrieval time.
- **Broker-reported historical charges:** aggregate breakdown with its segment/date/financial-year scope recorded.
- **Executed trade/fill identity:** stable broker order/trade/fill identifiers, side, quantity and time.
- **Reviewed actual evidence:** accepted contract note/source, reviewer, hashes, component values and eligible-fill manifest.
- **Per-fill allocation ledger:** idempotent, auditable allocations from verified actual components under explicit tested allocation rules.

Never silently allocate an aggregate total across fills without an explicit rule; do not double-count estimates and historical charges. Preserve raw/normalized response provenance, retrieval timestamp, effective date when applicable, and response hash—but never bearer tokens. STT/CTT event-specific logic, DP/demat daily per-scrip minimums, conditional lesser-of pricing and other unsupported models remain fail-closed until modelled and tested. Variance comparison remains audit-only and cannot mutate allocations, positions or P&L.

## Safety, privacy and licensing

- PAPER mode remains mandatory; live broker order submission stays disabled. Sandbox availability is not permission to enable live trading.
- Never place, modify, cancel, or square off a live order during research, audit, tests, MCP/skill runs, or coding.
- Keep credentials in secret storage/environment; never commit tokens, OAuth codes, client secrets, identifiers or raw sensitive account data. Redact fixtures/logs.
- Follow Upstox terms, entitlements, user consent, rate limits and current regulatory/static-IP requirements. Do not bypass access controls.
- For external code/skills/dependencies record repository, pinned version/commit, licence, copied/adapted files and security review. Prefer first-party SDK/docs and small adapters over importing an entire trading framework.
- Only modify `tarunsharma2610-del/tradepro-improved`. Audit before editing, add tests, update the nine required project docs, commit, and verify CI on the exact latest head. PR #6 remains draft/unmerged unless the user explicitly changes that instruction.

## Required audit deliverables

Every Upstox audit must deliver: (1) current official-source capability matrix; (2) SDK/framework/Agent Skill/MCP adopt/defer/reject assessment; (3) brokerage estimate vs historical charges vs contract-note/per-fill analysis; (4) auth/token, rate-limit, static-IP/regulatory, sandbox, retry/reconnect and error review; (5) security/licence assessment and test/CI evidence; (6) prioritized implementation plan that avoids duplicate adapters, streams, ledgers and order engines.

## Implementation/SDK assessment — 2026-10-24
The existing `UpstoxReadOnlyReconciliationClient` now implements fixed GET wrappers for Brokerage Details (`/v2/charges/brokerage`), Trade Charges (`/v2/trade/profit-loss/charges`) and Historical Trades (`/v2/charges/historical-trades`). Exact-head CI run `40064514873` passed (744 passed, 1 warning) with mocked HTTP contract tests. The official Python SDK repository lists release v2.30.0 and documents `ChargeApi.get_brokerage`; however, this narrow feature retains the existing direct-REST façade because it enforces a fixed read-only endpoint allowlist, validates scope before network access, sanitizes upstream error bodies, and avoids adding a generated dependency that also exposes order-write APIs. This is a scoped decision, not a blanket rejection of the SDK; reassess if broader typed models or SDK-only capabilities are needed. No real account token was used. Current public tariff-page effective-date notes are in `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`; do not activate rules from page parsing alone.

## Brokerage Details API snapshot integration — 2026-10-24 (CI verified)
The existing fixed-path GET client is paired with `build_upstox_brokerage_api_snapshots`, mapping documented `data.charges` into separate estimate-only component snapshots. It retains sanitized query parameters, API v2 endpoint, UTC retrieval timestamp, canonical full response JSON/digest, total estimate and DP-plan daily minimum as separate metadata. Variance comparison validates response digest and requires request quantity/price/side/instrument to match the exact reviewed fill set. The official docs describe `dp_plan.min_expense` as a daily minimum not included in the calculator total; implementation keeps it separate. No live account calls were made. Exact-head CI run `40065219626` passed (**754 passed, 1 warning**).

## Flat per-order brokerage modeling — 2026-10-24 (CI verified)
The guarded tariff engine now represents flat per-executed-order brokerage as `ORDER_FIXED`/`INR_FIXED`, separately from percentage-of-notional brokerage with an order cap. This supports the documented Upstox charge shape without encoding a flat fee as a percentage. No live API call or rate activation occurred. Exact-head CI run `40065607232` passed (**756 passed, 1 warning**).
