<!-- Phase 3 continuation sync: 27 October 2026. Latest verified code/test head: 31ce2a10bcc789c223608c6566082b24aea7358c; Backend CI #40383076131 SUCCESS. Current maintained-doc synchronization head at the time of this update: fbcefc1ae44f863b5d16d5e32fd819d277b0ead8; documentation CI #40384521664 SUCCESS. DP/demat Execution persistence and central charge-total recomputation are implemented; next gate is focused audit of unknown-vs-zero semantics, delivery/non-delivery rules, migration round-trips, idempotency, rollback, and integration with per-fill allocation/reconciliation. GST/IPFT implementation is not being restarted. PR #6/#7 stay Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro repository out of scope. -->

## Authoritative Phase 3 checkpoint — 26 October 2026 (latest verified CI)

- Target repository only: `tarunsharma2610-del/tradepro-improved`; branch `phase3/durable-per-fill-charge-allocation`; implementation/test head `44830ec48b50b4f470ec9ca95dd2d3f4339dd3df`. Do not modify original `Tradepro`.
- Exact-head Backend CI: [run #40294178677 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40294178677), including the test separating NSE/IPFT arithmetic reconciliation from GST taxable-base approval.
- GST estimate helper accepts exactly 18%; tests reject 0%, 5%, 100%, and 100.01%. Rate guard does not approve taxable-base composition; component inclusion needs reviewer and invoice/source evidence.
- ₹307/crore versus ₹306.99/crore transaction charge + ₹0.01/crore IPFT is arithmetic reconciliation only, not GST-base approval.
- Canonical live-fill integration is verified: six independently verified charge snapshots, evidence revalidated under lock, no raw-only fallback; brokerage cap applied once before deterministic paise-exact allocation.
- Remaining Phase 3 gates: effective-dated tariff applicability; component-specific per-fill allocation acceptance; invoice/source-backed GST/IPFT and product/segment evidence; adversarial/migration/recovery review; final exact-head docs/sign-off.
- Upstox public schedules/calculator are estimates; aggregate charges endpoint is not actual per-fill evidence. Null remains unknown, not zero. Synthetic restore is not actual Oracle recovery.
- PAPER mandatory; live broker writes, automatic live-fill promotion and automatic scheduling disabled. PR #6 open/draft/unmerged unless explicitly approved. Defer AI/open-source adaptations until Phase 3 acceptance. Documentation commit needs its own CI.

---

## Canonical checkpoint reconciliation — 26 October 2026 (canonical live-fill integration verified)

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. Never modify original `tarunsharma2610-del/Tradepro`.
- **Latest verified implementation head before this documentation sync:** `255fc208eed4bc8b922977717209d27912055377`. Exact-head Backend CI [run #40286205714 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40286205714): **962 passed, 1 warning**. Broker-write boundary guard, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, and restore-evidence retention all passed. Synthetic restore does not prove actual Oracle Cloud recovery.
- **PR #6:** open, draft, unmerged. Do not merge without explicit user approval.
- **Phase 3 integration completed on this head:** `LiveFillAccountingService` now requires exactly six independently verified canonical charge snapshots. It revalidates each canonical ledger and its source hashes/links/mapping version, reviewed fill manifest and weights, INR totals, durable reconciliation references, and the contract-note reference under lock. There is no fallback to raw-only legacy allocation rows. Extra, unmapped, unlinked, or foreign-connection per-fill allocations fail closed.
- **Integration tests:** canonical snapshot creation → independent review → allocation → reconciliation; direct and combined/split transaction/IPFT source lines canonicalize to one exchange-charge component; exact replay, missing/unreconciled/extra allocations, and PostgreSQL live-fill-versus-ledger promotion race. No live broker order writes are enabled.
- **Remaining Phase 3 gates:** (2) independently reviewed effective-dated tariff applicability; (3) approved component-specific per-fill allocation rules; (4) invoice/source-backed GST/IPFT and product-specific component acceptance; (6) final adversarial, migration and recovery review; (7) exact-head documentation/sign-off. Official public tariff snapshots are research evidence, not proof of account-specific actual charges; candidate rates remain DRAFT until the required review is recorded. Synthetic restore is not a real Oracle recovery test.
- **Upstox controls:** no unused SDK runtime dependency; Agent Skill remains development/static-review-only; brokerage calculator is estimate-only; aggregate charge endpoints are not per-fill actual evidence.
- **Safety invariants:** PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. Keep PR #6 unmerged until explicit approval.
- **Next step:** resume at the remaining Phase 3 tariff/component evidence gates. Do not repeat canonical snapshot integration. Do not begin the separate AI/open-source adaptations until Phase 3 acceptance is complete.
- **Documentation-sync note:** this multi-document commit must pass its own exact-head CI before the next implementation change.

---


---


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



## Authoritative checkpoint — 26 October 2026 (documentation CI verified)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- Latest implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`; exact-head Backend CI [#40287765745 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745).
- Documentation synchronization commit: `f90573d653c7103bf9cfdb1f867da97b176d3240`; its exact-head Backend CI [#40289107666 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40289107666). Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of actual Oracle Cloud recovery.
- Approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries do not supersede this checkpoint.


## GST/API evidence checkpoint — 26 October 2026

- Implementation/test head `149d21fdbb82306ff1b800ff7d3ad33b99058d81`; exact-head Backend CI [#40296745348 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40296745348). Passing CI does not constitute legal approval of GST treatment.
- Source-backed Upstox GST component candidates now cover NSE/BSE equity delivery, equity intraday, equity futures and equity options. All remain `DRAFT`. Delivery includes `demat_charges`; the other categories do not. `exchange_charges` is the canonical combined transaction/IPFT component, so IPFT must not be counted twice. Trade notional is never a GST component.
- Official Upstox `GET /v2/charges/brokerage` calculates a quote for supplied instrument, quantity, product, side and price; response fields include GST, STT, stamp duty, transaction, clearing, IPFT and SEBI turnover. It is an estimate, not proof of actual executed-fill charges: https://upstox.com/developer/api-documentation/get-brokerage/.
- Official Upstox `GET /v2/trade/profit-loss/charges` returns a segment/financial-year date-range breakdown; `ipft` can be null. Treat it as aggregate reconciliation evidence, not per-fill attribution: https://upstox.com/developer/api-documentation/get-trade-charges/. Actual-charge approval still needs contract-note/tax-invoice and account-record reconciliation.
- Upstox's public schedule specifies 18% GST on brokerage + transaction charges + IPFT, with demat additionally for equity delivery, and says IPFT is combined with transaction charges: https://upstox.com/brokerage-charges/. NSE circular `NSE/FA/73061` supports revised combined NSE transaction/IPFT rates effective 1 March 2026: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf.
- CBIC permits exclusion of statutory recoveries such as STT/stamp duty only when pure-agent conditions are met; otherwise apply Section 15 and applicable valuation rules: https://cbic-gst.gov.in/sectoral-faq.html and https://cbic-gst.gov.in/valuation-rules.html. Do not hard-code universal exclusion without evidence.
- No GST candidate is promoted. Missing/null API fields remain unknown, not zero. Any later API ingestion must preserve raw response/hash, retrieval time, query segment/date range, schema version and invoice linkage. Do not use the brokerage calculator as actual-charge evidence or infer per-fill values from aggregate responses.
- Next gate: source-backed GST acceptance/reconciliation using actual invoice/contract-note evidence and per-product component sets, then exact-head CI and documentation verification. PAPER mandatory; live broker order writes disabled; PR #6 remains draft/unmerged; original `Tradepro` untouched.


## Canonical latest Phase 3 checkpoint — 26 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **Verified code/evidence head:** `d287da70ce184c904c6f9ede9e4a0edca5839f8f` (commit: “docs: reconcile public Upstox contract note GST examples”).
- **Exact-head CI:** PASS — [GitHub Actions run #40304398632](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40304398632), commit `d287da70ce184c904c6f9ede9e4a0edca5839f8f`; **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention also passed. This is CI evidence, not proof of a real Oracle recovery or broker-origin authenticity.
- **GST/IPFT research:** Three public third-party historical Upstox note copies were reconciled: 11-Feb-2025 base ₹2.97 / IGST ₹0.53; 21-May-2024 base ₹77.56 / IGST ₹13.96 (IPFT ₹0.11 listed outside that note's printed base); 12-Mar-2025 base ₹2.75 / IGST ₹0.50. Printed-base compositions differ historically. The current official Upstox schedule supports the **estimate-only** base of brokerage + transaction charges + demat where applicable + IPFT, with IPFT represented exactly once because it is combined with transaction charges. Do not add SEBI to this current estimate base without current applicable billing evidence; never calculate GST on trade notional or infer zero from missing/null fields.
- **Tax/accounting approval:** all four GST component candidates remain `DRAFT`. Historical public copies do not prove current actual per-fill billing across products/accounts. Actual-charge promotion stays gated; estimate logic and actual invoice reconciliation are distinct. Follow effective dates and preserve raw API/source evidence.
- **Next action when resuming:** continue Phase 3 from this exact commit and checkpoint. Next gate is component-specific GST acceptance cases for equity delivery, intraday, futures and options, then implementation review and exact-head CI; do not restart from earlier saved checkpoints.
- **Safety / PR:** PAPER mode mandatory; live broker `place_order`/`modify_order`/`cancel_order` and automatic live-fill promotion remain disabled. PR #6 remains open, draft and unmerged. Original `tarunsharma2610-del/Tradepro` is not the work target and must remain untouched.
- This checkpoint supersedes older statements in this document about CI being in progress or requiring verification for the pre-`d287da7` head. Historical notes remain history; this is the canonical resume point.


## Session checkpoint sync — 26 October 2026

- Exact-head Backend CI [#40368554399 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40368554399) passed on code head `9d3f255480da9a71980a9d3819fbb69a34835753`. New documentation-sync commits require their own final exact-head CI check.
- Statutory GST research: CBIC stock-broking FAQ and CGST Act section 15 / CGST Rules Rule 33 and Rule 27 govern valuation; pure-agent exclusion is conditional on evidence, not automatic. IGST Act section 12(12) governs stock-broking place of supply; supplier/place-of-supply state comparison determines IGST vs CGST+SGST. Sources: https://cbic-gst.gov.in/sectoral-faq.html ; https://cbic-gst.gov.in/valuation-rules.html
- GST public-schedule helper/tests remain estimate-only. Statutory GST valuation service and tests are not implemented yet; GST/IPFT acceptance remains open. Next: implement Section 15 inclusion, Rule 33 evidence gates, tax-state split, Decimal/paise rounding and fail-closed handling. IPFT combined/separate and DP/demat persistence/reconciliation remain open.
- No personal contract note available or required. Safety: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER-only; live broker order writes disabled; original Tradepro repository out of scope.


## 27 October 2026 — Phase 3 API-to-accounting continuation

The user has explicitly asked that the existing charge APIs be integrated now rather than reopening GST/IPFT research. Existing read-only client methods are present in `backend/app/brokers/upstox/reconciliation_client.py`: brokerage calculator (`/v2/charges/brokerage`) is estimate-only; trade-charges (`/v2/trade/profit-loss/charges`) is aggregate-only. The remaining work is to trace actual call sites and wire responses into a typed, provenance-preserving orchestration/reconciliation path. Require exact approved endpoint/schema/scope/date mappings; do not fabricate approved mappings. Aggregate data cannot become per-fill actuals. Preserve missing/null/invalid/zero distinctions, prevent transaction/IPFT double count, and fail closed before live accounting when actual per-fill evidence is absent. This is Phase 3 work, not permission to enable live order writes. Exact-head CI must run after implementation and document sync.


### Implementation update — 27 October 2026

Added `app/services/upstox_charge_api_orchestration_service.py` plus focused tests. The service wraps the existing read-only client, preserves scope/status/payload and makes endpoint semantics explicit: brokerage calculator = estimate only; trade charges = aggregate reconciliation only; neither is per-fill actual evidence. This is a safe first integration seam, not completion of UI/API route or accounting-ledger wiring. Next, connect the service to the existing read-only reconciliation path and persist aggregate context without promoting it to per-fill charges. Confirm exact-head CI before marking this increment green.


### Authenticated route wiring — 27 October 2026

Added authenticated read-only routes `GET /api/v1/upstox/charges/brokerage-estimate` and `GET /api/v1/upstox/charges/aggregate`, registered in the API router. The handlers scope broker connection lookup to the authenticated user, decrypt the token server-side, and use the fixed GET-only client. Response classification remains estimate-only versus aggregate reconciliation only; neither endpoint returns per-fill-actual eligibility. No order-write method was added. Route-level tests and latest-head CI remain pending; this is not yet persistence into the charge evidence ledger or accounting promotion.


### Route tests and CI — 27 October 2026

Added route tests for estimate-vs-aggregate response classification, preservation of null IPFT, and invalid-quantity validation. Prior CI run #40473895336 passed on doc head `24b7b9ee728049f26b200cbee54571ae3c22b7bf`; the new test commit `ffb87c9af7c87d921eadf0198b7ba8704be65e76` still requires exact-head CI. Next inspect the evidence/reconciliation model before any persistence; aggregate API output must remain reconciliation-only and must never be spread across fills.


## API-first paper-trade charge estimation decision — 29 October 2026

- User-approved behavior: use Upstox's pre-trade Brokerage Details API for paper-fill charge estimates when it returns a complete, valid, internally consistent breakdown. Keep the existing deterministic local calculator as the automatic fallback if the API is unavailable, expired/unauthorized, incomplete, null/invalid, or inconsistent. This is estimation only, not live-trading/accounting promotion.
- Implementation added on the Phase 3 branch: `backend/app/services/paper_trade_charge_estimator.py` plus deterministic tests. `ExecutionService` now uses API-first estimates for market and matched limit paper fills and records `PAPER_UPSTOX_API_ESTIMATE` versus `PAPER_ESTIMATE` in the existing execution charge-source field. Components are accepted only when paise-exact supported components sum exactly to the API total; transaction, clearing and IPFT are combined once in the existing exchange-charge field. Unknown/incomplete fields fall back rather than block paper trading.
- Existing post-trade Upstox charges endpoint remains aggregate reconciliation evidence, not per-fill actuals. The API route already exists. GST reconciliation remains available without blocking paper-trade P&L.
- Implementation commits: `b90c09dc82a51181bc9eae422cb025eb79c65bcb`; default-enabled setting `UPSTOX_CHARGE_ESTIMATES_ENABLED`. CI disables network estimates only for the broad execution suite; mocked estimator tests cover API and fallback paths.
- Backend CI [#40755234415](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40755234415) — **SUCCESS** on code/test head `778e76d3554a3baedc41f0396276c1cb3dafc38f`: **1,197 passed, 1 warning**; broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence retention passed. Documentation sync head `d57dd476ecd6acebd4dc9e169912b877811a8166` still needs exact-head CI verification before it is called green.
- Next: continue the next uncovered Phase 3 accounting acceptance gate after CI recovery. Do not reopen GST/IPFT from zero or make minor estimate variance a paper-trading blocker. Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original `Tradepro` out of scope.


## Standard Upstox access-token lifecycle — audited 29 October 2026

- The standard OAuth authorization-code access token expires at 03:30 IST the following day; the current adapter records that expiry and `BrokerCredentialsService.get_access_token` refuses expired tokens. A regression test now covers the expired-token path.
- Do **not** invent a silent refresh-token grant or reuse a single-use authorization code. The official standard OAuth flow requires a new authorization-code exchange after user authorization; the documented extended/analytics-token facilities are separate token products with different read-only scopes and eligibility requirements, not a generic refresh token.
- In paper trading, an expired/unavailable token must not block a fill: the charge estimator uses the hardcoded deterministic fallback and records the fallback source. The API-first estimate remains best-effort.
- Live Upstox API calls have not been credential-tested in this CI environment. Do not label the real OAuth handshake or account-specific endpoint entitlements as end-to-end verified until a user-authorized integration test succeeds.
- Official references: https://upstox.com/developer/api-documentation/get-token/ and https://upstox.com/developer/api-documentation/authentication/ .


## Authoritative Phase 3 engineering closure — 29 October 2026

This section supersedes older status/next-step notes above; earlier entries remain as historical audit trail.

**Status: Phase 3 engineering acceptance is complete for the agreed PAPER-mode scope.** Do not confuse this with live-money release approval or actual-charge promotion.

Verified code checkpoint: `3a0c464afcb10261d1590607f8440affd21295a0`, Backend CI [#40878367369 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40878367369), **1,207 passed, 1 warning**. Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic restore, and restore-evidence retention passed. The documentation-sync head must pass its own CI before this sync is considered green.

Engineering closure covers deterministic paise-exact per-fill allocation; integrity-checked/reviewer-controlled evidence; canonical mapping; combined/split transaction/IPFT representation; replay/idempotency/conflict protection; locked total verification and rollback safeguards; explicit DP/demat persistence/completeness; statutory GST and GST/API diagnostic primitives; and Upstox API-first PAPER estimates with hardcoded fallback and standard disclaimer. The post-trade Upstox Trade Charges API remains aggregate-only and cannot be promoted to per-fill actual evidence.

Paper estimate disclaimer: “Estimated charges may differ from actual broker charges. For paper trading only; these are not actual booked charges.”

Operational gates are separate: credentialed Upstox OAuth/API smoke test and real Oracle backup/restore require deployment; any tariff lacking independently approved broker/exchange/segment/product/date evidence remains estimate-only/fail-closed for actual accounting. Historical contract-note fixtures are regression coverage, not a reason to promote estimates to actuals. These gates do not block PAPER engineering closure.

Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6/#7 remain Draft/unmerged; PAPER mandatory; live broker writes disabled. Phase 4 is the next separate increment after exact documentation-head CI passes.


## Resume checkpoint — 29 October 2026 (Upstox response-schema validation)

- **Code/test head:** `404c1e11ef4f2557c791c720c8d9a3fbc4e93bc1`; exact-head Backend CI [#40883660756 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40883660756). The workflow result confirms success; its summary did not expose a reliable pytest count, so no count is asserted here.
- **Concrete fix:** `UpstoxChargeApiOrchestrationService` no longer marks arbitrary successful HTTP JSON as usable. Brokerage estimates require `status == "success"` and `data.charges`; post-trade aggregate charges require `status == "success"` and `data.charges_breakdown`. Wrong/missing schema returns `usable=false`, clears the payload and records `INVALID_RESPONSE_SCHEMA`.
- **Regression coverage:** valid endpoint-specific response fixtures plus incorrect endpoint schema, unsuccessful/missing status, and aggregate wrong-shape payload cases.
- **Evidence boundary:** Brokerage Details remains estimate-only; Trade Charges remains aggregate reconciliation-only and never per-fill actual evidence. Null IPFT must not be silently coerced to zero. This fix validates response shape; it does not approve tariffs or promote accounting.
- **Contract-note continuity:** previously supplied January 2023 Upstox/RKSV contract-note examples remain available as historical regression fixtures; do not ask the user to provide them again. Their scope must be respected when using them for GST totals versus per-fill allocations.
- **Next:** verify CI on the exact synchronized documentation head. Keep PR #6/#7 Draft and unmerged, PAPER mode mandatory, live broker writes disabled, and the original `tarunsharma2610-del/Tradepro` repository untouched.

## Phase 4 API-first market data and token scope — 30 October 2026

- Exact code/test head `3a74fbb788a63ca3b042ceec400dbc7a83f32571` passed Backend CI #41016468736 (1,240 passed, 1 warning), including migration and synthetic restore checks.
- Paper market order pricing now consumes Upstox Full Market Quotes V3 order-book depth: BUY uses asks, SELL uses bids; quantity-weighted fill; snapshot timestamp, instrument identity, price validity and available depth are validated.
- Official Upstox docs distinguish the standard OAuth access token (expires at 3:30 AM IST next day) from Analytics Token, intended for market data and real-time streaming without daily reauthorization. API docs: https://upstox.com/developer/api-documentation/get-token/ ; https://upstox.com/developer/api-documentation?f=K110
- Next implementation: add a separate encrypted Analytics Token field and controlled settings endpoint; route market-data/stream endpoints to Analytics Token only where official docs authorize it. Keep account/portfolio/trading operations on the standard access token as required. Do not expose token values in API responses/logs; do not conflate token types or claim a refresh-token flow.
 
## Upstox Analytics Token implementation — 30 October 2026

- Added separate encrypted `analytics_token_encrypted` and `analytics_token_expires_at` fields to per-user broker connections with migration `202610300031` (down revision `202610270030`).
- Added owner-scoped Settings API to save, inspect status and clear Analytics Token. Token is accepted from the user's Upstox Developer Apps > Analytics page; it is never returned, logged or included in API responses. Expiry is tracked as 365 days from local registration; confirm/renew against the Developer Console's actual expiry date.
- Analytics Token retrieval is independent of standard OAuth `is_connected` state and fails closed when missing/expired. Standard OAuth access-token path remains separate for operations not documented as Analytics Token eligible.
- Routed strategy historical/intraday candle fetch, paper market quote/charge estimation, queued paper limit-order quotes, and market WebSocket reconnects through Analytics Token. Broker order/trade ingestion continues to use standard OAuth until each endpoint's Analytics Token/static-IP eligibility is deliberately enabled.
- Analytics Token is read-only. It cannot place, modify or cancel orders. Live trading remains disabled; PAPER-only guard unchanged.
- Official docs: https://upstox.com/developer/api-documentation/analytics-token/ ; https://upstox.com/developer/api-documentation/announcements/analytics-token-static-ip/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- CI for this new implementation is pending. Do not mark it accepted until exact-head CI passes, including migration round-trip and token isolation tests.

## Verified Analytics Token checkpoint — 30 October 2026

- Implementation head `083ab17a5150ea3be514438a16ea7c6c888c0be3` passed Backend CI #41017833952: 1,243 passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore drill all passed.
- Analytics Token is stored separately encrypted, owner-scoped, expiry-checked and never returned in API output/logs. It is used only for documented read-only market-data/streaming/charge-estimate routes. Standard OAuth remains separate for account endpoints not enabled for Analytics Token or requiring static IP.
- Real token entry and live API smoke test remain a deployment/user setup gate; code CI is not proof of a real broker session.
- PAPER-only and live order-write safeguards unchanged; PR #8 remains Draft/unmerged; do not update main or the original Tradepro repository.


## Upstox option-chain + mode-correct streaming increment — 30 October 2026

- Exact preceding docs head `c00278fb33cc094a0f07d6a61d3ca9827f2dcdcf` passed Backend tests #41018852112 and #41018839615. These runs verify the preceding full-feed/doc checkpoint only, not the new code below.
- Added optional broker-adapter `get_option_chain` capability and Upstox implementation for the documented `GET /v2/option/chain` endpoint. The authenticated API route `GET /api/v1/market-data/option-chain` uses the separately stored Analytics Token only, validates exact ISO expiry or supported relative expiry keywords, and rejects MCX because Upstox documents that exchange as unsupported for this endpoint.
- Upstox's response supplies strike-wise call/put market data, OI, previous OI, volume, bid/ask and Greeks. The application adds `change_oi = oi - prev_oi` only when both source values are present and finite; otherwise the derived field is `null`. Original provider fields are retained and no missing/null value is converted to zero.
- Fixed a scope bug found during audit: the stream manager already retrieves Analytics Token, but the HTTP start route was still gating on daily OAuth. Stream start now correctly requires a valid Analytics Token; it does not require daily OAuth for public market-data streaming. The route reports the actual selected feed mode.
- Added explicit stream mode selection: `ltpc`, `option_greeks`, or `full`, defaulting to `full`. Mode-specific limits are validated before starting: LTPC 5,000; Option Greeks 3,000; Full 2,000. The user-scoped manager runs one stream per user, below Upstox's normal two-connection ceiling. No Plus-only Full D30 assumption.
- Option Greeks mode decodes the documented first-level bid/ask depth, Greeks and IV. Full mode retains D5 depth, OHLC and extended metadata parsing. Regression tests cover adapter endpoint/query/auth, provider errors, option-chain route, MCX rejection, expiry validation, OI delta semantics, Analytics Token-only stream authorization, selected modes and mode-specific limits.
- Code/test head: `42be7ad2a33c2e7a6db08842a5ec9c7c30154af5`. Exact-head CI for this increment is pending; do not claim green until the exact current PR head has passed backend tests and all safety/migration checks.
- Official contracts: https://upstox.com/developer/api-documentation/analytics-token/ ; https://upstox.com/developer/api-documentation/get-pc-option-chain/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ ; official V3 proto: https://assets.upstox.com/feed/market-data-feed/v3/MarketDataFeed.proto . Analytics Token supports Option Chain and WebSocket without static IP; MCX Option Chain is not available.
- Next after exact-head CI: add/verify index + India VIX feed presets and subscription lifecycle management (subscribe/change_mode/unsubscribe) with per-user limits; then test WebSocket recovery and option-chain snapshot/stream consistency. Do not create a duplicate market-data service or Redis bridge without a proven process-boundary need.
- Safety: only `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original Tradepro untouched; PAPER mode mandatory; live broker order writes disabled.


## Upstox V3 subscription lifecycle — 30 October 2026

- Verified the official V3 WebSocket contract directly: methods are `sub`, `unsub`, and `change_mode`; requests must be sent as binary protobuf-feed protocol frames containing JSON bytes. The V3 docs specify normal per-category individual limits of LTPC 5,000, Option Greeks 3,000 and Full 2,000; when categories are mixed, the combined limits are 2,000 for LTPC/Greeks and 1,500 for Full. This implementation deliberately uses one mode per user stream, so it enforces the corresponding individual limit and does not claim mixed-mode capacity.
- Added native live subscription management to the existing streamer: add instrument keys with `sub`, remove keys with `unsub`, and change the mode of the complete user stream with `change_mode`. It preserves the desired subscription set across reconnects and sends the current complete subscription/mode on the next connection.
- Mode changes invalidate cached ticks so depth/Greeks from a previous feed mode cannot be consumed as if they came from the newly selected mode. Unsubscribed ticks are removed. The final key cannot be removed via partial unsubscribe; use DELETE `/market-data/stream` to stop the stream.
- Added authenticated API endpoints: POST `/api/v1/market-data/stream/subscribe`, POST `/api/v1/market-data/stream/unsubscribe`, and POST `/api/v1/market-data/stream/change-mode`. Each is user-scoped, checks the Analytics Token, verifies active instrument keys before subscribing, and rejects requests when there is no running stream. Partial mixed-mode changes are intentionally rejected; change mode applies to all keys in the stream to keep one consistent parser/mode contract.
- Added tests for binary V3 control requests, dynamic subscribe/unsubscribe/change_mode, reconnect replay of updated desired state, per-mode limits, stale tick invalidation, active-instrument validation, and missing-stream conflict responses.
- Exact previous code/test head `e53ac0f9a24bf3a92a409fa548d59b41206a5042` passed Backend CI #41019403337. Current subscription-lifecycle head: `7aecd1e5b9a77a44fe3b0885a89a88e4826c2d33`; exact-head Backend CI #41019804917 is queued, and prior incremental runs are queued/running. Do not mark this lifecycle increment green until the latest exact head passes all backend, broker-write, SQLite/PostgreSQL migration and synthetic restore checks.
- Official source: https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ (method semantics, binary request format, India VIX key, and individual/combined limits).
- Next after exact-head CI: add verified index/India VIX presets based on instrument-master keys, then reconnect/subscribe race tests and end-to-end quote fan-out to the scanner/strategy data path. No second stream service, Redis bridge, or live-order capability is being added without a demonstrated requirement.
- Safety: only `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original Tradepro untouched; PAPER mode mandatory; live broker order writes disabled.


## Verified checkpoint — 30 October 2026 (subscription lifecycle CI green)

- Exact implementation commit `b87245002a24bb0bd002b7e0c7dc5bbc82085357` passed complete Backend CI run #41020300281: backend pytest, broker-write boundary, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL + document-volume restore drill, and restore evidence retention. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41020300281
- The lifecycle-test correction now tests partial mode-change rejection with two subscribed instruments, so the test exercises the actual partial-subscription case instead of incorrectly treating a single-instrument complete-stream mode change as partial.
- Subscription lifecycle implementation includes authenticated user-scoped subscribe/unsubscribe/change-mode routes, active-instrument validation before subscribe, per-mode subscription limits, reconnect replay, and invalidation of cached ticks after mode changes. No live broker order capability was introduced.
- This is the accepted code/test checkpoint. Documentation synchronization is being committed separately; the exact documentation head must receive its own CI verification before the next code increment.
- Next implementation: index feed presets backed by dynamically resolved and locally validated Upstox instrument keys (Nifty 50, Nifty Bank, India VIX). Do not hardcode exchange tokens. Use the official Instrument Search API and Upstox developer documentation; preserve provider identifiers and source timestamps. Then implement freshness/recovery observability and scanner/strategy fan-out.
- Official references: https://upstox.com/developer/api-documentation/instrument-search/ ; https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ ; India VIX key documented as `NSE_INDEX|India VIX`.
- Safety: work only in `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; do not change main or original `Tradepro`; PAPER mode mandatory; all live broker order writes remain disabled. No credentials or tokens in code, logs, docs or chat.


## Verified checkpoint — 30 October 2026 (rich market-data snapshot CI green)

- Exact implementation/test commit `036ad952ced862e94b2c4d3af75b79b43a0bbc28` passed full Backend CI run #41022649412: backend pytest, broker-write boundary, SQLite Alembic upgrade/downgrade/re-upgrade, PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, isolated synthetic PostgreSQL + document-volume restore, and evidence retention. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41022649412
- Corrected the missing-quote stream-status test to apply the normal authenticated-user dependency overrides. Production authentication remains required; the assertion that an absent latest quote is represented as unavailable remains in place.
- The stream status response now exposes the validated fresh tick snapshot fields needed by downstream read-only consumers: instrument key, LTP, exchange timestamp, receive time, depth, option Greeks, OI, traded volume, average traded price, total buy/sell quantities and OHLC. Missing quotes remain null; do not infer freshness from a missing tick.
- Index presets are implemented from the locally synchronized official Upstox instrument master and fail closed for missing/ambiguous matches. Do not hardcode dynamic exchange instrument identifiers.
- Architecture note: the existing WebSocket stream manager is process-local. A worker in a separate process cannot read its in-memory cache. Before scanner/strategy consumers depend on streamed ticks, implement and test a shared cross-process delivery layer using the Redis already present in deployment (or another justified existing shared store). Redis Pub/Sub alone is not durable: pair notification with a TTL-bounded latest-quote cache/snapshot, explicit timestamps, freshness checks, and reconnect/recovery semantics. On Redis loss or stale/missing quote, consumers must fail closed and retain existing candle freshness and PAPER/risk gates.
- Next work: audit current Redis configuration and Redis Python package APIs; define a small versioned quote envelope and namespaced user/instrument keys; implement publisher + cache write in the existing stream lifecycle; implement worker/API consumer with TTL and timestamp validation; test outage, reconnect, expiry, ownership isolation and process restart; only then connect scanner and paper strategy consumers.
- This checkpoint does not certify Redis fan-out, scanner integration or strategy integration as complete. No live broker order capability was introduced.
- Safety: work only in `tarunsharma2610-del/tradepro-improved`; PR #8 remains Draft/unmerged; main and original `Tradepro` untouched; PAPER mode mandatory; live broker order submission/modification/cancellation disabled; no credentials in code, logs, docs or chat.


## Phase 4 Redis market-data bridge checkpoint — 30 October 2026

The existing Upstox Market Data Feed V3 streamer remains the provider-facing WebSocket implementation. Its asynchronous tick callback is now connected to a Redis publisher, rather than introducing another market-data service or duplicating the WebSocket connection. Redis stores per-user versioned latest snapshots with TTL; Pub/Sub carries notification metadata only. Downstream consumers must fetch the snapshot and independently validate user scope, schema/version, TTL and exchange timestamp. The stream callback is not permission to trigger broker orders; all evaluation remains PAPER-only. Exact-head Backend CI #41024607462 passed on `72b22a647f2b9a38ac7afc0aaee9547a67b16fcf`. Consumer, reconnect recovery and cross-process integration remain pending. Continue to prefer official Upstox V3 docs/protobuf/SDK where applicable; do not add a second data service or redundant SDK without a demonstrated need.


## Phase 4 shared market-data transport checkpoint — 30 October 2026

The Upstox V3 WebSocket remains the provider ingress. The existing streamer callback publishes validated ticks to Redis through the user-scoped publisher. Redis Pub/Sub is a notification channel only; the authoritative quote is the versioned, expiring Redis snapshot. The Lua publisher atomically increments version, stores snapshot/TTL, and publishes notification to prevent concurrent write reordering.

Exact-head Backend CI #41026567279 passed on `1c70e17a0ea54f8e8f219ae27d90aa46a02ea16e`, including real Redis 7 integration tests. Still pending: automatic Redis reconnect/resubscription, recovery after Redis server restart, independent-process delivery tests, scanner integration and PAPER strategy integration. No live order API is enabled. Prefer official Upstox APIs/protobuf/SDK contracts; do not introduce a duplicate market-data service.


## Phase 4 Redis version-counter lifecycle checkpoint — 30 October 2026

Exact-head Backend pytest CI #41031153316 passed on `3088e49cf24317f58f7e04a60d6cd54e065143b4`. The Upstox V3 provider ingress remains unchanged. The Redis publisher keeps per-user/per-instrument version counters persistent while quote snapshots retain TTL; real Redis integration coverage verifies the next tick after snapshot expiry receives the next version. Redis remains a cross-process cache/notification transport, not another market-data provider.

This change addresses ordinary snapshot expiry only. Consumer startup/reconnect snapshot reconciliation, Redis restart epochs, independent OS-process delivery, worker lifecycle and multi-user load still require explicit acceptance tests. Persistent counters need an explicit retention policy. Scanner and PAPER strategy integration remain pending; no live order writes are enabled. Prefer the official Upstox V3 API/SDK/protobuf contracts and do not duplicate provider services.


## Phase 4 Redis bounded epoch/version checkpoint — 30 October 2026

Exact-head full Backend CI #41032764754 passed on `7268edd6e7ddb7ef6d472799d1d0164b4210b135`. Upstox V3 remains the provider-facing WebSocket ingress. Redis remains the cross-process quote transport, not a second market-data provider. Snapshots use short TTL; version counters use bounded 24-hour default retention with unique epochs. Atomic Lua allocates epoch/version, writes snapshot and publishes notification. Counter expiry or Redis data loss starts a new epoch; consumers validate epoch plus version. Existing integer-only counter values migrate on the next publish.

Real Redis tests passed for snapshot/counter TTL expiry, new-epoch acceptance, Pub/Sub reconnect, Redis process restart, independent OS-process delivery, two-user isolation and concurrent publishing. The consumer is not yet managed by the background worker; scanner and PAPER strategy do not yet consume Redis quotes. Strategy evaluation still uses the existing candle-based API path. Next implement worker subscription discovery/lifecycle and test load/shutdown before scanner integration. Continue preferring official Upstox V3 APIs, SDK and protobuf schemas; do not introduce duplicate market-data services. Live order writes remain disabled.
