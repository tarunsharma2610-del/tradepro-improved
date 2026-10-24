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

## Public tariff source archive and candidate rules — 2026-10-24 (CI verified)
Added a dated normalized excerpt from Upstox and official NSE references at `docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md`; canonical payload SHA-256 is `c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420`. Eighteen effective-dated STT/exchange-charge candidate rows are DRAFT and non-selectable. The excerpt is not original HTML; stamp duty source needs current corroboration and exchange/IPFT composition needs review. Exact-head CI run `40065979244` passed (**760 passed, 1 warning**).


## Fixed-order brokerage entrypoint regression — 24 October 2026

- Audit found that `calculate_charge_for_trade` routed percentage-based `ORDER_NOTIONAL` brokerage through `calculate_order_brokerage`, but flat-fee `ORDER_FIXED` brokerage fell through to the generic calculator, which intentionally rejects that basis.
- Fixed the shared entry point to route both `ORDER_NOTIONAL` and `ORDER_FIXED` brokerage through the guarded order-level calculator. Added regression test `test_trade_charge_entrypoint_supports_flat_fixed_order_brokerage` asserting a flat INR 20 fee is returned through the full scope-selection entry point.
- Implementation commit: `1634989d29734f1d5ffdcfee826384a512eaafe7`; regression-test commit: `928c0207ff8de5f4852225ab6b9e0fabe97f6e12`.
- Exact-head backend CI run 40066706304 was in progress at documentation time; do not mark this fix green until that run completes. Recheck CI after these documentation updates because they change the branch head.
- No tariff candidate was activated, no charge was promoted to the actual ledger, and no live broker order was sent. Original `tarunsharma2610-del/Tradepro` remains out of scope.


## Brokerage basis/unit validation hardening — 24 October 2026

- Latest verified prior head: Backend pytest workflow run [40066838844](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40066838844) passed for the flat fixed-order brokerage entry-point regression.
- Additional fail-closed hardening now rejects inconsistent brokerage rule shapes at construction: `ORDER_FIXED` requires `INR_FIXED`, and `ORDER_NOTIONAL` requires `PERCENT`. This prevents invalid basis/unit combinations from surviving registry validation and failing only during calculation.
- Implementation commit: `4faa6a062264b2396cb00e380c5cbbe16449ec91`; regression-test commit: `26ea299b78be463651768b2ab93fa6443d5350c5`.
- CI for these new commits is pending and must be checked on the exact latest branch head before this change is considered verified. Do not reuse the earlier green run as evidence for these commits.
- No official tariff rate was activated, no estimate was promoted to actual per-fill accounting, and no live broker order was sent. PR #6 remains draft/unmerged; work stays in `tarunsharma2610-del/tradepro-improved`, not the original `Tradepro` repository.


## Brokerage rule validation CI correction — 24 October 2026

- Backend CI run [40067041722](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40067041722) failed with 2 tests failing and 762 passing. The failure exposed that generic rate-unit arithmetic tests used a default `brokerage/ORDER_NOTIONAL` rule while intentionally testing `INR_PER_CRORE` and `INR_FIXED`; the new brokerage shape guard correctly rejected those inconsistent test fixtures.
- Corrected the generic unit test matrix to use semantically appropriate component/basis pairs: `brokerage/ORDER_NOTIONAL/PERCENT`, `sebi_turnover/TURNOVER/INR_PER_CRORE`, and `other_fee/ORDER_FIXED/INR_FIXED`. This preserves the guard rather than weakening production validation.
- Test-fix commit: `6ba333fe0339838042ffd25a141c4805318418bc`. A new CI result for this exact commit has not yet been observed; do not mark it green until confirmed.
- No tariff rules were activated and no charge allocations or live broker orders were created. PR #6 remains draft/unmerged; original `tarunsharma2610-del/Tradepro` remains out of scope.


## Generic tariff test basis correction — 24 October 2026

- Backend CI run [40067217326](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40067217326) completed with 763 passed and 1 failed. The remaining failure was the generic unit-arithmetic test using `ORDER_FIXED`, which is intentionally excluded from generic calculation bases and must use the specialized brokerage entry point.
- Corrected the test fixture to use supported generic basis `NOTIONAL` for the generic `INR_FIXED` arithmetic case. The production guard is unchanged. Test correction commit: `7c7dadff65885918fc0e01d0aa8deaf1b6d1bb16`.
- CI for this correction and subsequent documentation updates must be checked on the exact latest PR head. No green result is claimed until verified.
- No tariffs were activated; no actual charges were promoted or per-fill ledger writes made; no live broker orders were sent. PR #6 remains draft and unmerged. Work is limited to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.


## Official tariff-source recheck — 24 October 2026

- Rechecked the official Upstox charges page on 2026-10-24 and recorded the findings in `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`. It lists 1 April 2026 STT/CTT changes and 1 March 2026 NSE transaction-charge changes, and states IPFT is combined with transaction charges while separately listing ₹0.01/crore (options on premium) plus GST. Current candidate rows represent transaction charges only; IPFT composition/effective-date treatment must be resolved before approval.
- The same page's ₹10/order API-order brokerage note is explicitly valid only through 31 December 2025 (excluding GTT); do not treat it as current pricing. Current authenticated API-order-specific terms remain unverified.
- NSE's official stamp-duty page is still marked updated 03/10/2023, so it is not a fresh 2026 publication. Independent current statutory corroboration remains a release gate.
- No tariff candidate was approved or activated, no estimate was promoted to actual per-fill accounting, and no live broker order was sent. Source excerpt remains normalized rather than byte-for-byte HTML. Exact-head CI must be checked after these documentation changes; prior green CI does not cover the new head.


## Brokerage tariff effective-date gate — 24 October 2026

- Reconfirmed the official Upstox public page lists current brokerage examples: equity delivery/options ₹20 per executed order; equity intraday ₹20 or 0.1% (whichever lower); equity futures ₹20 or 0.05% (whichever lower). The current source excerpt does not establish a precise effective_from date for these brokerage terms.
- A trial draft-registry addition was reverted because populating the required `effective_from` with the retrieval date would falsely imply a published effective date. No brokerage candidates with guessed effective dates remain in the tariff registry. Before registering these rows, obtain a source that establishes the effective date or explicitly model an evidence-backed “current as observed” rule state without pretending the retrieval date is the tariff effective date.
- Existing calculation helpers can model flat per-order brokerage and capped percentage brokerage (`maximum_inr`), but helper capability is not source approval. The published “whichever lower” semantics must have a regression test before a reviewed rule is eligible for use.
- The preceding verified Backend pytest run was [40067742361](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40067742361), successful on the then-current head. Later registry/documentation commits need exact-head CI confirmation; do not reuse that run as proof for later commits.
- No rates were activated, no estimates were promoted into actual accounting, and no live broker order was sent. PR #6 remains draft/unmerged and the original `Tradepro` repository remains out of scope.


## Order-brokerage cap regression coverage — 24 October 2026

- Added regression coverage for percentage brokerage below/at the maximum cap, minimum-floor behavior, simultaneous minimum/maximum bounds, and flat `ORDER_FIXED/INR_FIXED` brokerage. Tests call the specialized order-level calculation helper and assert paise-precise outputs; flat order fees reject percentage caps.
- Test commit: `48447dafb11d7d83a09f4f64a55020405fa167a4`. This is not yet CI-verified; run and inspect CI for the exact latest PR head before treating the tests as passing.
- This covers arithmetic only. It does not approve any live tariff row, define the allocation of one order's brokerage across multiple fills, or establish that public examples match a particular authenticated account plan. Per-fill allocation and actual-charge promotion remain blocked pending policy/evidence and durable accounting acceptance tests.
- PR #6 remains draft/unmerged; no live broker orders were sent; original `Tradepro` remains out of scope.

## CI follow-up — fixed-fee cap regression test — 24 October 2026

- Latest documentation head before this correction, `5b155c4b3f75606b426262f938b420f7a2217d74`, failed backend pytest: **768 passed, 1 failed**. Failure was isolated to `test_fixed_order_brokerage_is_flat_and_rejects_caps`: the test expected calculation-time rejection, but `TariffRule` correctly rejects an invalid fixed-fee rule at construction time.
- Corrected the regression test to assert the rule-construction `ValueError` using the actual validation message. Test-only commit: [47aa91e2696bb6388af73ede568dfe89c4cbead7](https://github.com/tarunsharma2610-del/tradepro-improved/commit/47aa91e2696bb6388af73ede568dfe89c4cbead7).
- CI for this correction and the resulting documentation head is **pending verification**; do not describe the latest head as green until the exact SHA has a successful run. This is a test correction, not a production guard relaxation.
- PR #6 remains draft/unmerged. Live broker order submission remains disabled. All work is confined to `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.

## Exact-head CI passed — 24 October 2026

- Verified successful GitHub Actions backend workflow [40081403001](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40081403001) against exact head `ff9675f5489f4148079b3ee7cd4a97810e352b4b`: **769 passed, 1 warning in 44.10s**. Broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trips passed; synthetic PostgreSQL/document-volume restore drill passed and evidence artifact was uploaded.
- The preceding test-only correction [47aa91e](https://github.com/tarunsharma2610-del/tradepro-improved/commit/47aa91e2696bb6388af73ede568dfe89c4cbead7) asserts that a fixed-fee tariff rule with a maximum cap is rejected at rule construction. This does not weaken production validation.
- The single pytest warning is a Starlette/AnyIO deprecation warning. GitHub Actions also logged Node.js 20 action-runtime deprecation warnings. These did not fail the run.
- Aggregate `ORDER_FILL_SET` variance tests and the variance-only persistence service are present; this successful suite includes their tests. Variance records remain audit-only and do not promote charges or create per-fill allocations. Source-backed effective tariff applicability, charge composition, and durable accounting acceptance remain open gates.
- Synthetic restore is not actual Oracle Cloud recovery. PR #6 remains draft/unmerged. Live broker order execution and automatic accounting promotion remain disabled. All work stays in `tarunsharma2610-del/tradepro-improved`; never modify original `tarunsharma2610-del/Tradepro`.


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


## 2026-10-24 — Official tariff/API source audit

- Upstox's `GET /v2/trade/profit-loss/charges` accepts segment, financial year and optional date bounds; documented output is aggregate `charges_breakdown`, not a per-fill schema. Example `charges.ipft` is null. Treat it as aggregate reconciliation evidence only, and never coerce null to zero. https://upstox.com/developer/api-documentation/get-trade-charges/
- NSE circular NSE/FA/73061 dated 27-Feb-2026 applies from 1-Mar-2026: combined member outflow ₹307/crore cash, ₹183/crore equity futures and ₹3,553/crore equity-options premium; included IPFT contribution is ₹0.01/crore each side. Use effective-dated rate versioning and guard against double counting. This circular does not establish Upstox-specific contract-note JSON field semantics. https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- Upstox's public charges page shows newer effective-date summary values alongside historical tables and lists a STT/CTT change effective 1-Apr-2026. Use the matching date/scope and prefer official exchange/statutory notices for rate authority. https://upstox.com/brokerage-charges/
- Acceptance: aggregate API response, null IPFT, stale tariff, combined-vs-split IPFT and effective-date boundary must fail closed when actual per-fill evidence is required. Production mappings and tariffs remain DRAFT/non-selectable.
- Latest prior implementation head `ee1b2a74d2a9f6141b9afbb6e06562b5cf263a9b` passed workflow #40110597753; rerun CI on the resulting documentation head.
- PR #6 remains draft/unmerged; live order submission and automatic quantity/notional allocation remain disabled; original `Tradepro` remains untouched.


## 2026-10-24 — Aggregate endpoint hard guard added; CI pending

- Upstox `/v2/trade/profit-loss/charges` is now explicitly blocked from `PER_FILL_ACTUAL` resolution regardless of a misleading mapping semantic. Its published schema is aggregate `charges_breakdown`, not per-fill evidence.
- Regression test `test_official_upstox_aggregate_charges_endpoint_cannot_be_promoted_to_per_fill` covers the guard. Implementation `cdc07afdd8cc0c8d0b37d7e4aa8cdf1bf6eac651`; test `8ae749017a8ba0016f2c9adeb77eaff41fb5ae70`. Latest test CI must pass before verification is complete.
- Keep production mappings/tariffs unapproved; null distinct from zero; automatic quantity/notional allocation and live order submission disabled. PR #6 draft/unmerged; original `Tradepro` out of scope.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` takes proposed instrument, quantity, product, transaction type and price, returning a charge calculation; this is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver now blocks `/v2/charges/brokerage` from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use even if a mapping is misleadingly labelled. Existing guard still blocks `/v2/trade/profit-loss/charges` from per-fill actual use. New regression tests cover both misuse cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. Prior head `6cc8b58f635fcb4f1b1cb3e5997099d074800a28` passed workflow #40111501429. CI for the new commits must be verified.
- Production mappings/tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live broker order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.

## Repository audit result — 24 October 2026

The current implementation was audited and recorded in [`docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md`](docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md). The backend currently uses async `httpx` for REST, a custom protobuf/WebSocket V3 market-data service, and a narrow read-only reconciliation client; `backend/requirements.txt` does not declare `upstox-python-sdk`. The existing brokerage estimate parser and charge semantic guard already distinguish estimates and segment/FY aggregates from per-fill actuals.

**Decision:** do not add an unused SDK dependency or replace current clients wholesale. Perform a version-pinned, isolated compatibility spike first, beginning with read-only Brokerage Details API method/schema compatibility. Preserve timeout/error-redaction, async behavior, parser validation, accounting semantic gates and the broker-write guard. The Agent Skill is development-only guidance, not a production dependency; inspect its scripts before use and never run order examples with live credentials. No live request, account access, or order was used in this audit.

## SDK/Agent Skill static review result — 2026-10-24

See [`docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md`](docs/UPSTOX_SDK_API_REPOSITORY_AUDIT.md) and [`docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md`](docs/UPSTOX_AGENT_SKILL_SECURITY_REVIEW.md). The official Python SDK tag `v2.30.0` uses generated clients; the documented `ChargeApi.get_brokerage` method is synchronous by default and has a thread-based `async_req` mode. Existing async `httpx` and validated parsing already cover this endpoint, so no runtime dependency was added. Only adopt the SDK for a concrete capability/correctness benefit, behind existing service interfaces. The upstream skill contains live order/GTT examples; treat it as development-only reference, never execute examples with live credentials, never trust its confirmation prompt as our app's safety boundary, and do not copy its config-token fallback or raw API-body logging into our app.

