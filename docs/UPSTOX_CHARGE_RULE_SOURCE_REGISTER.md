<!-- Phase 3 continuation sync: 27 October 2026. Latest verified code/test head: 31ce2a10bcc789c223608c6566082b24aea7358c; Backend CI #40383076131 SUCCESS. Current maintained-doc synchronization head at the time of this update: fbcefc1ae44f863b5d16d5e32fd819d277b0ead8; documentation CI #40384521664 SUCCESS. DP/demat Execution persistence and central charge-total recomputation are implemented; next gate is focused audit of unknown-vs-zero semantics, delivery/non-delivery rules, migration round-trips, idempotency, rollback, and integration with per-fill allocation/reconciliation. GST/IPFT implementation is not being restarted. PR #6/#7 stay Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro repository out of scope. -->

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


# Upstox charge-rule source register

Research checkpoint: 23 October 2026
Repository scope: `tarunsharma2610-del/tradepro-improved`

## Purpose and evidence hierarchy

This register identifies public source material for implementing charge rules. It does not authorize live trading or automatic accounting promotion. Public pricing pages can change; production rules must be versioned by effective date and reviewed before activation. Preserve retrieval date, URL, relevant excerpt/hash, applicability dimensions, and reviewer decision for each rule version.

## Official Upstox sources

### 1. Brokerage Charges page
URL: https://upstox.com/brokerage-charges/
Reviewed: 23 October 2026.

The page publishes brokerage and component-specific examples: equity brokerage terms, statutory charges, GST bases, stamp-duty categories, exchange transaction charges, IPFT and DP charges. It distinguishes STT/CTT rates effective from 1 April 2026 and NSE transaction charges from 1 March 2026. It is not a universal tariff for all exchanges, products or account plans.

Implementation notes:
- Store each rule with effective_from/effective_to, exchange, segment, instrument/product, side, calculation base, rate unit and source URL.
- The page contains historical as well as current sections. Select by effective date; do not use the first rate found.
- Equity examples do not establish the correct MCX commodity or currency-derivative tariff.
- BSE charges may depend on scrip group; do not substitute NSE rates.
- DP/demat charges can follow a daily-per-scrip/order rule and must not be treated as turnover charges without an approved attribution policy.

### 2. Brokerage Details API
URL: https://upstox.com/developer/api-documentation/get-brokerage/
Endpoint: authenticated GET /v2/charges/brokerage.
Reviewed: 23 October 2026.

Inputs include instrument token, quantity, product, transaction type and price. The response documents brokerage, GST, STT, stamp duty, transaction, clearing, IPFT, SEBI turnover and DP-plan information. This is a broker-calculation cross-check for supported requests, but requires OAuth and is not a static public tariff feed or proof of per-fill allocation. Record request parameters and response provenance when used in a connected-account workflow. Never store access tokens in fixtures or logs.

### 3. Get Trades Charges API
URL: https://upstox.com/developer/api-documentation/get-trade-charges/
Endpoint: authenticated GET /v2/trade/profit-loss/charges.
Reviewed: 23 October 2026.

Returns a charge breakdown for a segment and financial year, including total, brokerage, GST, STT, stamp duty, transaction, clearing, IPFT, other charges, SEBI turnover and demat transaction. Treat it as an aggregate reconciliation source, not proof of the charge attributable to every fill. Preserve segment, financial year and date range; never invent per-fill source values from aggregates.

### 4. Contract-note guidance
- https://upstox.com/help-center/how-can-i-access-and-download-the-contract-note-248457/
- https://upstox.com/help-center/understanding-the-contract-note-248458/

These pages explain how to obtain a real contract note and its role as a legal trade/charge record. Third-party examples in docs/UPSTOX_CONTRACT_NOTE_AND_API_EVIDENCE.md are not independently authenticated; use only for format research and synthetic fixtures. A personal note is optional for ongoing engineering, not a prerequisite to implement the generic engine.

## Public schedule estimate-only review decision — 26 October 2026

- Decision record: `docs/UPSTOX_TARIFF_REVIEW_DECISION.md`.
- Exact allowlist: `backend/app/services/upstox_public_estimate_rules.py`; it promotes only the reviewed 18 STT/exchange-charge identities from the DRAFT candidate registry to APPROVED copies for **public-schedule estimates only**.
- Public estimate snapshots are labelled `PUBLIC_SCHEDULE_ESTIMATE_ONLY`. The allowlist is bound to canonical source-payload SHA-256 `c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420`; changed identities, effective dates, source URLs or hashes fail closed.
- This approval does not authorize account-specific brokerage assumptions or actual-charge promotion. GST/tax composition, stamp duty, SEBI, DP/demat, clearing/other, BSE cash scrip groups, BSE futures, MCX and currency remain unapproved/unsupported.
- Actual per-fill accounting still requires reviewed contract-note evidence and the canonical reconciled allocation path. The estimate registry is not imported by `LiveFillAccountingService`.

## Rule status and known gaps

- Brokerage arithmetic helper/tests exist, but effective-dated product/order-specific rules must be selected before use.
- GST helper accepts an explicit taxable base and rate; the engine needs a reviewed component composition policy for each charge category.
- Stamp-duty helper rejects non-BUY side, but rate/base must be selected by effective date and product/segment.
- STT/CTT helper accepts caller-provided base/rate; it does not distinguish every statutory transaction class, exemption or option-exercise case.
- Exchange and SEBI helpers perform percentage arithmetic only. Exchange rates vary by exchange/segment/product/date; SEBI fees may be expressed per crore rather than as a percent. Normalize units explicitly.
- Commodity/currency, BSE scrip groups, option premium versus futures turnover, exercise/assignment and other special cases require separate sourced rules.
- Public aggregate charge outputs can support reconciliation when authorized, but cannot prove per-fill breakdown if the API returns only aggregates.

## Required executable-rule schema

Each rule must identify:
1. Component code and normalized unit.
2. Broker/exchange and segment.
3. Instrument/product and transaction side, including exception class.
4. Calculation base definition (turnover, premium, brokerage/service-charge base, per-order, per-scrip/day, etc.).
5. Rate or fixed amount, precision/rounding policy, minimum/cap if applicable.
6. effective_from and optional effective_to.
7. Source URL, retrieval date, excerpt/hash and reviewer/approval state.
8. Applicability test cases and expected results.

No rule becomes active from a web scrape alone. Require review and regression fixtures around every effective-date boundary. Unknown or ambiguous cases remain pending manual review.

## Safety

This research does not authorize live orders. PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Work only in tradepro-improved; do not modify the original Tradepro repository.

## Official Upstox tariff-page recheck — 2026-10-24
Source reviewed: https://upstox.com/brokerage-charges/ (retrieved 2026-10-24). The page contains legacy tables as well as newer effective-date rows; do not use the legacy rows as current rates.

The current page states these rows for evaluation:
- Brokerage: equity delivery ₹20 per executed order; equity intraday ₹20/order or 0.1% (whichever lower); equity futures ₹20/order or 0.05% (whichever lower); equity options flat ₹20/order.
- STT/CTT row effective 1 April 2026: equity delivery 0.1% buy and sell; equity intraday 0.025% sell-side; equity futures 0.05% sell-side; equity options 0.15% sell-side on premium, with a separate 0.15% line for sales of exercised options.
- Exchange transaction-charge row effective 1 March 2026: NSE equity delivery/intraday 0.00307%; NSE equity futures 0.00183%; NSE equity options 0.03553% on premium; BSE equity options 0.0325%; BSE scrip-group-specific equity charges and BSE futures nil as shown on the page.
- IPFT is stated to be combined with transaction charges; the page lists ₹0.01 per crore of traded value plus GST (options on premium value). GST base is described as brokerage + transaction + demat + IPFT for delivery, and brokerage + transaction + IPFT for intraday/futures/options. DP charge is ₹20 per scrip per day on sell-side equity delivery; SEBI is listed at ₹10/crore.

Official references: Upstox tariff page above; Upstox Brokerage Details API https://upstox.com/developer/api-documentation/get-brokerage/; NSE levy page https://www.nseindia.com/static/invest/first-time-investor-sebi-turnover-fees-stt-other-levies. The Upstox Brokerage Details API accepts instrument token, quantity, product, BUY/SELL and price; its response provides total/brokerage/tax/other-charge breakdown plus DP-plan daily minimum metadata, which the docs state is not included in the calculation. Trade Charges is an aggregate segment/FY view, and Historical Trades has a documented three-financial-year window and pagination. These API outputs are estimate/reconciliation/reference data, not actual contract-note/per-fill evidence.

**Activation status:** research only. This recheck did not archive/hash the full source page or obtain independent reviewer approval, and it does not activate tariff rules. Before any rate becomes executable, capture a dated source snapshot/hash, corroborate statutory rates against current official exchange/regulatory sources, define segment/product/side/base and effective-date boundaries, add boundary tests, and obtain review. Current automatic QUANTITY/NOTIONAL allocation remains fail-closed for unsupported components.

## API estimate evidence boundary — 2026-10-24 (CI verified)
The Brokerage Details API is used as a calculator estimate source only. Each normalized component snapshot preserves documented request scope and canonical response payload/digest, with API retrieval time, total and DP-plan minimum metadata. `dp_plan.min_expense` remains outside the calculator total and component allocation. Historical aggregate charge data and historical trade references remain separate source types. No API estimate is treated as contract-note actual evidence, and tariff rates above remain research-only until source archival, independent corroboration, review and effective-date tests are complete. Code commit `2c23ebfeb9d0d843620dc6dcf54b7279bb112662` passed exact-head CI run `40065219626` (**754 passed, 1 warning**).

## Brokerage rule-shape implementation note — 2026-10-24
The tariff engine supports flat per-order brokerage via `ORDER_FIXED`/`INR_FIXED` and capped percentage brokerage via `ORDER_NOTIONAL`/`PERCENT` with rule-bound maximums. These shapes match the distinctions shown on the current Upstox public tariff page; no live rates have been activated. The next research artifact should archive the current Upstox/NSE charge-page excerpts and a reproducible SHA-256 digest, then encode candidate rows as DRAFT until source review and effective-date tests are complete. Exact-head CI run `40065607232` passed (**756 passed, 1 warning**).

## Dated source excerpt and candidate registry — 2026-10-24
Added `docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md`. Its canonical extracted-payload SHA-256 is `c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420`. This is a normalized excerpt, not a byte-for-byte copy of live source HTML. NSE's official derivatives STT page corroborates the 1 April 2026 futures/options/exercised-option rates. `backend/app/services/upstox_tariff_candidates.py` now lists 18 effective-dated STT and exchange-charge candidates; all remain DRAFT and are not selectable. The published NSE combined-rate arithmetic and included ₹0.01/crore IPFT contribution are documented for the specified NSE scopes; Upstox API/contract-note representation semantics remain unresolved. The NSE stamp-duty page date is a separate evidence gap, so no rates are activated. Exact-head CI run `40065979244` passed on `f76ecde4ac785123de2980539138ce89ff660294` (**760 passed, 1 warning**).


## Official-source recheck — 2026-10-24 (no tariff activation)

- Rechecked the live official Upstox charges page on 2026-10-24. It explicitly lists STT/CTT changes effective 1 April 2026 (NSE futures 0.05% sell-side; options 0.15% sell-side on premium; exercised-option sales 0.15%) and NSE transaction-charge changes effective 1 March 2026 (equity 0.00307%, futures 0.00183%, options 0.03553% on premium; BSE options 0.0325% and BSE futures nil). Source: https://upstox.com/brokerage-charges/.
- The same page says IPFT is combined with transaction charges and lists ₹0.01 per crore of traded value (options on premium) plus GST. For the documented NSE equity scopes, the published transaction-charge schedule and circular establish a combined exchange outflow that already includes the stated ₹0.01/crore IPFT contribution effective 1 March 2026. Do not add a second IPFT amount to those combined rates. This does not establish Upstox API or contract-note field semantics; verify endpoint/schema and actual contract-note evidence before approving a production mapping.
- The page also lists “Brokerage on API Orders” at ₹10/order as valid only through 31 December 2025 (excluding GTT). Since that date has passed, this historical promotional/API-order rate must not be treated as current. Obtain current authenticated broker terms before modeling API-order-specific brokerage.
- NSE's official stamp-duty reference remains marked updated 03/10/2023 at https://www.nseindia.com/static/invest/first-time-investor-stamp-duty-charges-taxes. It lists buyer-side rates but is not a fresh 2026 publication; independent current statutory corroboration remains an open approval gate.
- These findings corroborate research candidates only. No candidate was promoted from DRAFT, no rate was activated, no actual charge was allocated, and no live broker order was sent. The 2026-10-24 snapshot remains a normalized excerpt rather than byte-for-byte source HTML; capture original page bytes or an independently reproducible archived representation before approval.


## Brokerage tariff effective-date gate — 24 October 2026

- Reconfirmed the official Upstox public page lists current brokerage examples: equity delivery/options ₹20 per executed order; equity intraday ₹20 or 0.1% (whichever lower); equity futures ₹20 or 0.05% (whichever lower). The current source excerpt does not establish a precise effective_from date for these brokerage terms.
- A trial draft-registry addition was reverted because populating the required `effective_from` with the retrieval date would falsely imply a published effective date. No brokerage candidates with guessed effective dates remain in the tariff registry. Before registering these rows, obtain a source that establishes the effective date or explicitly model an evidence-backed “current as observed” rule state without pretending the retrieval date is the tariff effective date.
- Existing calculation helpers can model flat per-order brokerage and capped percentage brokerage (`maximum_inr`), but helper capability is not source approval. The published “whichever lower” semantics must have a regression test before a reviewed rule is eligible for use.
- The preceding verified Backend pytest run was [40067742361](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40067742361), successful on the then-current head. Later registry/documentation commits need exact-head CI confirmation; do not reuse that run as proof for later commits.
- No rates were activated, no estimates were promoted into actual accounting, and no live broker order was sent. PR #6 remains draft/unmerged and the original `Tradepro` repository remains out of scope.

## Upstox API charge-component coverage gap — 24 October 2026

- Official Upstox Brokerage Details and Trade Charges examples expose component fields beyond the currently supported allocation allowlist, including IPFT, clearing, other charges and demat transaction charges. These API responses are estimates or aggregate reconciliation data; they are not per-fill actual evidence.
- The persistence service intentionally does not accept those components until duplicate-counting rules, source provenance, allocation basis, daily/per-scrip semantics and reconciliation behavior are specified and tested. In particular, Upstox describes IPFT as combined with transaction charges on the public tariff page; do not add both components without resolving whether the broker response represents them separately or combined for the applicable endpoint/product.
- Added fail-closed regression coverage for the unsupported component names. This prevents an upstream/API component from being silently omitted or persisted using an unreviewed allocation rule.
- Follow-up: design a versioned normalized API-component mapping, preserve nullable-versus-zero distinctions and response digests, define component-specific allocation policies (including daily DP/demat), and test aggregate totals against API response fixtures. Keep unsupported components blocked until those gates pass.
- No tariff activated, no actual charge promoted, no per-fill accounting side effect added by this test. Live broker writes remain disabled; PR #6 stays draft/unmerged.

## Upstox component provenance checkpoint — 24 October 2026

- Upstox estimate normalization preserves `transaction`, `clearing`, `ipft`, and `sebi_turnover` as distinct components; it does not collapse them into a generic exchange-charge value.
- The component-separation regression test passed on exact PR head [0112f92](https://github.com/tarunsharma2610-del/tradepro-improved/commit/0112f92f065156e93069332be0a3665c601ab940), via [Backend tests run #40083185015](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40083185015). Pytest, broker-write boundary guard, SQLite/PostgreSQL migration round-trips, synthetic restore drill, and evidence-retention steps passed.
- Estimate normalization is not tariff activation or actual-charge evidence. Do not map aggregate trade-charge outputs to individual fills or enable automatic transaction/clearing/IPFT allocation without reviewed component-specific semantics, source evidence, and an exact eligible-fill manifest.
- Open item: verify effective-dated component composition and GST taxable-base rules from official sources and reviewed fixtures; prevent IPFT double-counting where the tariff presentation combines it with transaction charges.
- PR #6 remains draft/unmerged; live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`, never the original `tarunsharma2610-del/Tradepro`.

## PostgreSQL allocation concurrency CI — 24 October 2026

- Corrected PostgreSQL concurrency test fixture now creates valid portfolio, instrument, application-order, and broker-order prerequisites before broker fills. The initial fixture failed on a foreign-key constraint because it used random, non-persisted broker-order IDs; fixed in [fc0c539](https://github.com/tarunsharma2610-del/tradepro-improved/commit/fc0c539dc24f87a705207a16a98789fd63d928f8).
- Exact corrected head passed [Backend CI #40084015153](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40084015153): **777 passed, 1 warning**. CI set `TEST_POSTGRES_URL`; the PostgreSQL concurrency integration ran, alongside broker-write boundary checks, SQLite/PostgreSQL migration round-trips, and synthetic database/document restore with retained evidence.
- This verifies allocation persistence/concurrency only; it does not authorize tariff activation or automatic charge allocation. Keep transaction, clearing, IPFT and SEBI components distinct until official component-composition and GST taxable-base rules are reviewed; prevent IPFT double-counting.
- PR #6 remains draft/unmerged; live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`, never the original `tarunsharma2610-del/Tradepro`.


## GST and Upstox API component cross-check — 24 October 2026

- Rechecked the current official [Upstox brokerage and charges page](https://upstox.com/brokerage-charges/). It explicitly lists GST at 18% on brokerage + transaction + demat charges + IPFT for equity delivery, and brokerage + transaction + IPFT for intraday, futures and options. It separately lists SEBI turnover charges and does not explicitly include them in that displayed GST base. Keep GST composition as a dedicated guarded calculation; do not apply 18% to every charge component by default.
- The official [CBIC stock-broking FAQ](https://cbic-gst.gov.in/sectoral-faq.html) says STT, stamp duty and other taxes are not included in the value of supply where the stock broker satisfies the pure-agent conditions; otherwise valuation follows Section 15 and Rule 27. This is a conditional tax rule, not permission to infer pure-agent treatment for every broker/account. Preserve source evidence and have the applicable tax treatment reviewed before approval.
- The authenticated [Upstox Get Trades Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/) documents separate response fields for transaction, clearing, IPFT, others, SEBI turnover and demat transaction charges, as well as brokerage and taxes. These are aggregate/selected-period charge data and must not be treated as per-fill actuals without an exact source scope and reviewed allocation basis.
- Upstox's public page says IPFT is combined with transaction charges, yet also displays an IPFT rate and the API response schema exposes an `ipft` field. Preserve both raw API fields and response digest; do not add a second IPFT amount to a tariff value that already includes it. Resolve endpoint/product semantics with authenticated fixtures before approving component composition.
- Brokerage examples such as “₹20 per order or 0.1% (whichever is lower)” are representable as a percentage rule with a reviewed maximum cap. Existing cap tests exercise below-cap and at-cap amounts; the source does not provide a precise effective-from date for current brokerage terms, so candidate rules remain unregistered/unapproved until effective-date evidence is established.
- No tariff candidate was activated, no estimate was promoted into actual accounting, and no live broker order was sent. PR #6 remains draft/unmerged; live broker order writes remain disabled. All work remains in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.


## Component coverage matrix and activation blockers — 24 October 2026

The dated public Upstox page and the authenticated Charges API are complementary sources, not interchangeable tariff truth. The public page describes rate/application rules; the API provides broker-calculated totals and a component breakdown for a requested segment/financial-year/date range. Neither the API schema nor an aggregate total alone proves per-fill actuals.

| Component | Current source evidence | Safe implementation status / blocker |
|---|---|---|
| Brokerage | Public page has per-order and percentage/cap examples; other page variants may show different price wording. | Cap-aware calculation helpers and tests exist. No production Upstox brokerage rule is approved until the current account/product terms and effective-from date are evidenced. API-order pricing must not be inferred from expired offers. |
| STT/CTT | Upstox public page and NSE STT page document side/product-specific rates, including the 1 April 2026 changes. | DRAFT candidates exist for selected NSE equity/F&O cases. Complete scope matrix and statutory-source review before approval; do not extrapolate NSE rates to BSE, MCX, currency or uncovered products. |
| Stamp duty | Upstox page has buyer-side product-specific rates; statutory corroboration and current source capture remain incomplete. | No approved automatic rules. Validate instrument/segment scope and effective date against current statutory/exchange sources. |
| Exchange transaction charges | Public page distinguishes exchange, segment, product, and effective date; BSE equity-group applicability is not a single generic rate. | DRAFT candidates cover selected NSE EQ/F&O and BSE F&O option rows only. BSE scrip groups, other exchanges/segments, and precise effective-date evidence remain gaps. |
| IPFT / clearing | Public page says IPFT is combined with transaction charges while also showing an IPFT schedule; API exposes transaction, clearing and IPFT fields separately. | Keep raw fields distinct. Do not sum an IPFT amount twice; resolve whether the tariff table's transaction rate is inclusive or exclusive for each scope using official documentation and authenticated read-only fixtures. |
| SEBI turnover | Upstox page states ₹10/crore; API exposes `sebi_turnover` separately. | Add only after exact eligible turnover base, rounding and effective-date evidence is reviewed. Do not assume it is part of the displayed GST base. |
| GST | Upstox page explicitly enumerates brokerage + transaction + IPFT for intraday/F&O and adds demat charges for delivery. | Use an explicit guarded taxable-component set, not 18% of all fees. Reconcile with current tax guidance and the actual broker charge note; no broad default composition. |
| DP / demat | Upstox page lists delivery sell-side per-scrip-per-day DP charges and API field `demat_transaction`. | Do not allocate an aggregate DP charge evenly to fills without a reviewed per-scrip/day allocation basis. Verify GST treatment and applicable scope. |
| Other / service fees | API has an `others` field; public page lists several non-trading service charges. | Keep outside standard trade tariffs unless a specific service/event rule and source are identified. |

### Next tariff acceptance sequence

1. Preserve the current dated source snapshot and record the retrieval timestamp and content hash; where feasible, archive and hash original source bytes separately from the normalized excerpt.
2. Build a coverage matrix for every supported exchange/segment/product/side/basis and effective-date interval. Missing or ambiguous tuples must remain non-selectable.
3. Add source-backed boundary fixtures for rate transitions, GST composition, IPFT inclusion, brokerage caps and DP per-scrip/day aggregation.
4. Compare read-only API breakdowns against matching date/segment scope; store the raw response digest and distinguish broker aggregate actuals from fill-level allocations.
5. Require independent review and explicit approval before activating any rule. Until then, keep estimates visibly provisional and actual-ledger reconciliation evidence-driven.

**Gate outcome:** no new rule approved or activated by this audit. Automatic tariff-driven per-fill allocation remains disabled for unreviewed components; live broker order writes remain disabled.


## Public-page IPFT discrepancy — source reconciliation status, 24 October 2026

The Upstox public page displays an older IPFT table (₹0.10/lakh for cash/futures and ₹0.50/lakh for options premium) and a newer table saying IPFT is combined with transaction charges and lists ₹0.01/crore. These should not be interpreted as two simultaneously additive charges.

NSE Circular **NSE/FA/73061 (27 February 2026)**, effective 1 March 2026, explains the newer combined schedule and states that the transaction component plus ₹0.01/crore IPFT contribution preserves the relevant total outflow: ₹307/crore cash market, ₹183/crore equity futures, and ₹3,553/crore equity options premium. See the detailed table and scope restrictions in the section “IPFT/transaction-charge reconciliation using NSE circular” below/above in this register and the [official circular PDF](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).

**Status: partially reconciled, not fully approved.** For the listed NSE schedules, the newer combined transaction rate already includes the ₹0.01/crore IPFT contribution; never add the legacy ₹10/₹50-per-crore IPFT values to those combined rates. Preserve API fields separately for audit, but reconcile their actual semantics against authenticated account-specific API/contract-note evidence. The circular does not establish BSE/MCX or every product tuple.

**Remaining gate:** independent review of effective dates and all product/side/basis scopes, and read-only API/contract-note fixture verification before any candidate is approved. GST taxable-component mapping remains a separate gate. No IPFT candidate or GST rule is approved by this source review.

## API source-type boundary and promotion guard — 24 October 2026

The two Upstox API surfaces must not be conflated:

| Source | Documented scope | Permitted use in this project |
|---|---|---|
| [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/) | A request for a specified instrument, quantity, product, transaction type and price; returns an order charge estimate/breakdown | Cross-check an estimate for the exact request. Preserve request parameters, API version and response digest. Not automatically a fill-level actual or a tariff approval. |
| [Get Trade Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/) | Segment + financial year and optional date range; reports trade/P&L charges across the selected scope, with component fields | Aggregate reconciliation only. Do not divide or spread its totals across fills without a separately reviewed, documented allocation basis. |
| Reviewed contract note / bill evidence | Actual charge evidence with source document, component locator and reviewer provenance | Required source type for the current allocation-verification/promotion workflow; still requires exact fill-set, component and allocation-basis checks. |

The Get Trade Charges schema has distinct fields for brokerage, GST, STT, stamp duty, transaction, clearing, IPFT, other charges, SEBI turnover and demat transaction. Separate fields are a reason to preserve each raw field, not proof that a public tariff's transaction rate is exclusive of IPFT. Keep raw API fields and response digest; never add IPFT twice or silently infer an absent field as zero.

A regression test now asserts that evidence tagged `UPSTOX_TRADE_CHARGES_API` cannot pass the contract-note allocation verification path, and that pending allocations remain unpromoted. This protects the source-type boundary; it does not prevent a future, separately designed aggregate reconciliation workflow from comparing scoped totals.

**Still blocked:** resolving the public IPFT schedule discrepancy, approving product-specific GST component sets, and enabling automatic per-fill allocation from API estimates or aggregate totals.


## IPFT/transaction-charge reconciliation using NSE circular — 24 October 2026

**Updated finding:** the two Upstox page tables are not sufficient on their own. An authoritative NSE Finance & Accounts circular explains the newer “combined with transaction charges” presentation. NSE Circular **NSE/FA/73061 dated 27 February 2026**, effective **1 March 2026**, splits member outflow into transaction charges and contribution to NSE IPFT while preserving the overall total.

| NSE segment | Revised transaction component | Revised IPFT contribution | Combined total, each side |
|---|---:|---:|---:|
| Cash market | ₹306.99/crore | ₹0.01/crore | ₹307/crore |
| Equity futures | ₹182.99/crore | ₹0.01/crore | ₹183/crore |
| Equity options (premium) | ₹3,552.99/crore | ₹0.01/crore | ₹3,553/crore |

The circular explicitly states the previous totals were ₹297 + ₹10 = ₹307/crore for cash market, ₹173 + ₹10 = ₹183/crore for futures, and ₹3,503 + ₹50 = ₹3,553/crore for options. From 1 March 2026 it revises these to ₹306.99 + ₹0.01 = ₹307/crore, ₹182.99 + ₹0.01 = ₹183/crore, and ₹3,552.99 + ₹0.01 = ₹3,553/crore, respectively. The circular says the change has no impact on overall outflow for these schedules. Primary source: [NSE Circular NSE/FA/73061 (PDF)](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf), dated 27 February 2026, table and effective-date statement.

This explains the likely cause of the public-page conflict: Upstox still displays an older IPFT schedule (₹10/crore cash/futures and ₹50/crore options) alongside a newer section saying IPFT is combined with transaction charges and showing ₹0.01/crore. Do not add the legacy IPFT rates to the post-1-March-2026 combined rates. The public Upstox transaction table's options rate of 0.03553% corresponds to the combined ₹3,553/crore outflow, while the current component split from the NSE circular is ₹3,552.99 + ₹0.01.

### Implementation decision

- Keep IPFT as a separately captured source/API field for audit and reconciliation, but do **not** add the legacy ₹10/₹50 per-crore amount on top of post-1-March-2026 combined Upstox transaction rates.
- For reviewed NSE-only reconciliation, the expected combined rates are ₹307/crore/side for cash market, ₹183/crore/side for equity futures, and ₹3,553/crore/side on options premium. Preserve the component split and cited source rather than collapsing the audit trail.
- The official circular covers NSE cash/equity derivatives only. It does not establish BSE or MCX rules or every Upstox product tuple. Broker-specific API/contract-note evidence is still needed to verify how each field is represented in the actual-account response.
- No tariff candidate is approved by this documentation update. Automatic activation remains blocked pending exact product/scope/effective-date mapping, authenticated read-only response/contract-note reconciliation, and independent review.


## GST taxable-component evidence review — 24 October 2026

Sources reviewed:
- Upstox [Brokerage Charges](https://upstox.com/brokerage-charges/) states GST at 18% on brokerage + transaction charges + IPFT for equity intraday/futures/options, adding demat charges for equity delivery.
- CBIC [Stock Broking Services FAQ, Q77–78](https://cbic-gst.gov.in/sectoral-faq.html) states brokerage is taxable, while STT, stamp duty and other central/state tax recoveries are excluded only when the pure-agent conditions under Rule 33 are satisfied; otherwise valuation is under CGST Act Section 15 read with Rule 27.
- CBIC [Valuation Rules / Rule 33](https://cbic-gst.gov.in/valuation-rules.html) lists conditions including contractual pure-agent relationship, recipient liability/authorization, separate invoice indication, recovery of only the actual third-party amount, and that the expenditure is additional to the supplier's own service.

### Implementation boundary

1. Do not implement “GST = 18% of every charge” or use a blanket exclusion list. The Upstox page's named base is a broker-published product-specific component list; CBIC's pure-agent test is conditional and depends on the actual transaction/invoice facts.
2. Represent the GST base as a versioned, product-scoped component set only after reconciliation with an actual Upstox tax invoice/contract note. At minimum, verify brokerage, transaction charges, IPFT, and delivery demat components; separately establish treatment of SEBI turnover, clearing, “others,” and any taxes/recoveries from invoice evidence rather than guessing.
3. Keep STT and stamp duty as separate tax components. Do not include them in GST base merely because they are present in a total charge response; do not exclude a recovery solely because it is called a tax unless the relevant pure-agent treatment is supported.
4. Add boundary fixtures that check each product's exact component inclusion, exclusion, missing-field behavior, and rounding against reviewed invoices. Preserve raw source amounts and invoice/API digest; fail closed on unknown component semantics.

**Gate status:** official high-level text is available, but the component mapping for this app remains unapproved until a dated, account-specific invoice/contract-note fixture is reviewed. No GST calculator rule or tariff was activated by this audit.

## Upstox charge APIs — reconciliation evidence (24 October 2026)

Official API documentation reviewed:

- [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/) and [example code](https://upstox.com/developer/api-documentation/example-code/charges/brokerage-details/): `GET /v2/charges/brokerage` accepts an instrument token, quantity, product, transaction type, and price. It returns an order-charge estimate with total, brokerage, taxes (GST, STT, stamp duty), other charges (transaction, clearing, IPFT, SEBI turnover), and DP-plan fields where applicable.
- [Get Profit and Loss on Trades API](https://upstox.com/developer/api-documentation/get-trade-charges/): exposes component fields in the selected-scope P&L charge report (aggregate, not per-trade), including brokerage, GST, STT, stamp duty, transaction, clearing, IPFT, other charges, SEBI turnover, and demat transaction charges. This is the preferred API-side comparison for realized trade charges when the endpoint's documented segment/financial-year/date inputs and data availability requirements are met.
- [Upstox Brokerage Charges](https://upstox.com/brokerage-charges/) lists product-specific public schedules, including revised NSE transaction-charge totals effective 1 March 2026 and GST component descriptions. [NSE Circular NSE/FA/73061](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf) independently supports the NSE cash/equity-derivatives transaction/IPFT split and effective date.

### Integration and approval boundary

1. Use the Brokerage Details API for pre-trade estimate/reconciliation fixtures, not as proof of the final charge on a filled order.
2. Use the selected-scope P&L charge breakdown only for aggregate reconciliation; use an actual broker-issued contract note/tax invoice as realized-charge evidence. Preserve the raw response, request dimensions, retrieval time, API/version, response digest, and matching contract-note reference.
3. Do not sum the public-page legacy IPFT table on top of the current combined NSE transaction rates. Keep raw `ipft` API fields separately for reconciliation, but account for the documented combined-rate schedule and check actual response semantics against contract-note evidence to avoid double counting.
4. The API response's field names do not by themselves prove the GST taxable base or the legal classification of every component. Do not infer GST base from `total`, `other_charges`, or public text alone; approve the component mapping only after reviewing a dated actual invoice/contract-note fixture for the specific segment, instrument, product, and effective date.
5. These sources do not establish BSE/MCX rules for every instrument/product combination. Unsupported or conflicting scope must remain unapproved and fail closed; keep candidate tariffs inactive until reviewed by an independent authorized reviewer.

**Gate status:** API documentation provides useful estimate and realized-charge comparison paths, but no account-specific Upstox response/contract-note fixture was supplied or verified in this audit. No tariff/GST rule is approved or activated by this entry.

## Trade-wise P&L report API — distinct from charges endpoint (24 October 2026)

Official documentation: [Get Profit Loss Report](https://upstox.com/developer/api-documentation/get-profit-and-loss-report/), authenticated `GET /v2/trade/profit-loss/data`.

- The endpoint returns paginated trade-wise realized P&L rows (including quantity, instrument identity/name, trade type, buy/sell dates, averages and amounts), scoped by segment and financial year, with optional dates.
- It does **not** document per-row brokerage/tax/charge components. Do not mistake a trade-wise P&L row for a fill record or per-fill charge evidence.
- The separate [Get Trades Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/) returns a selected-scope aggregate component breakdown. Use it for aggregate reconciliation only.
- The read-only reconciliation client now exposes `get_profit_loss_report` with fixed endpoint path, required pagination, segment/FY validation and date-range validation. Regression tests verify endpoint parameters, pagination bounds and that returned P&L rows are not assumed to contain `charges_breakdown`.
- Use P&L rows only as matching context alongside order/trade history. Contract notes remain the required source evidence for charge-component allocation/promotion; never synthesize per-fill charges from aggregate P&L charge totals.

**Gate status:** API coverage is expanded, but no personal authenticated response or contract-note fixture has been reviewed in this audit. No tariff or accounting promotion gate is changed.

## Effective-date correction for equity STT candidates — 24 October 2026

The current Upstox pricing page's historical section identifies equity-delivery STT (0.1% buy and sell) and equity-intraday STT (0.025% sell side) as rates effective from 1 April 2023. The candidate registry had incorrectly used 1 April 2026 for these unchanged equity rates, which would imply a newer effective date than the source supports. The DRAFT candidates and regression test now preserve 1 April 2023 for these three rows. This is a source-date correction only: candidates remain DRAFT and non-selectable. The distinct futures/options STT transition effective 1 April 2026 remains unchanged.

## P&L report metadata endpoint — 24 October 2026

Official documentation: [Get Report Metadata](https://upstox.com/developer/api-documentation/get-report-meta-data/), authenticated `GET /v2/trade/profit-loss/metadata`. It returns `trades_count` and `page_size_limit` for the selected segment/financial-year and optional date scope. The read-only client now exposes `get_profit_loss_report_metadata` with the same scope/date validation as the P&L report. Use the returned page-size limit when paginating the trade-wise report rather than assuming a preferred page size. Metadata contains no charge components and is not per-fill charge evidence.

## GST source boundary — CBIC and Upstox public schedule — 24 October 2026

Official sources reviewed:
- [Upstox Brokerage Charges](https://upstox.com/brokerage-charges/) states 18% GST on brokerage, transaction charges and IPFT for intraday/futures/options, and additionally demat charges for equity delivery. Its same page says IPFT is now combined with transaction charges, while still listing IPFT as a separate field/table and including it in the GST base. This is a potential double-counting / taxable-base ambiguity, not permission to add the component twice.
- [CBIC Sectoral FAQ, Stock Broking Services, Q77](https://cbic-gst.gov.in/sectoral-faq.html) says STT, stamp duty and other statutory recoveries are outside the broker's GST value only when the pure-agent conditions in Rule 33 are met; otherwise valuation follows section 15 and Rule 27. This means the app must not categorically include or exclude a levy from GST merely by its label.

**Decision:** Keep GST composition and all affected tariff candidates unapproved. A dated account-specific Upstox tax invoice/contract note must establish the actual GST amount and the broker's component mapping for the exact segment/product/effective date; then reconcile it against the public schedule without double-counting combined transaction/IPFT rates. Preserve separate raw source components and mark any unresolved difference for manual review. This note is source research, not tax advice or tariff approval.


## IPFT representation reconciliation — 24 October 2026

### Finding

The primary ambiguity is a **representation/normalization mismatch**, not an unresolved NSE rate for the covered equity segments. NSE Circular NSE/FA/73061 dated 27 February 2026, effective 1 March 2026, states that the member outflow remains unchanged while the split is revised to:
- Cash market: transaction ₹306.99/crore + NSE IPFT ₹0.01/crore = ₹307.00/crore.
- Equity futures: transaction ₹182.99/crore + NSE IPFT ₹0.01/crore = ₹183.00/crore.
- Equity options on premium: transaction ₹3,552.99/crore + NSE IPFT ₹0.01/crore = ₹3,553.00/crore.

Official circular: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf

Upstox's current public page lists the corresponding total rates (0.00307%, 0.00183%, 0.03553%) and says IPFT is combined with transaction charges, while also displaying ₹0.01/crore as the IPFT contribution. Interpret the displayed percentage as the **combined exchange transaction + IPFT total** for these NSE equity/cash, equity futures, and equity options cases. The ₹0.01 line is explanatory component information, not an additional amount to add on top of that combined percentage.

Official page: https://upstox.com/brokerage-charges/

The Upstox Brokerage Details API documents separate response keys `other_charges.transaction` and `other_charges.ipft`; the aggregate Trade Charges API similarly documents transaction and IPFT fields, with IPFT nullable in the published example. This schema alone does not prove that the API's transaction field always represents the pre-IPFT rate or the combined rate for every product/date. The published API examples are not authoritative effective-date fixtures. Preserve the raw response, request scope, null-vs-zero, and digest; verify a live authenticated response against a dated contract note before assigning a canonical meaning to those fields.

API docs:
- https://upstox.com/developer/api-documentation/get-brokerage/
- https://upstox.com/developer/api-documentation/get-trade-charges/

### Required calculation and normalization policy

1. **Public tariff estimate path (NSE equity cash, equity futures, equity options, effective 2026-03-01 onward):** use the published combined total rate (₹307/₹183/₹3,553 per crore respectively). Do not add another ₹0.01/crore to the computed transaction total.
2. **Component-level canonical tariff representation:** if the ledger needs distinct components, represent the official split as transaction-only ₹306.99/₹182.99/₹3,552.99 plus IPFT ₹0.01 per crore on the applicable turnover/premium base. Their sum must equal the combined published rate exactly before final currency rounding. Store a rule-set/representation version so a total-rate rule and split-component rules can never both be applied to the same turnover.
3. **Authenticated Upstox API estimate path:** preserve the returned transaction and IPFT fields as distinct observed fields. Do not overwrite or synthesize one from the public tariff. Until a dated response plus contract-note reconciliation proves the semantics, mark the API-to-canonical mapping as unresolved and fail closed for automatic promotion. If the API's transaction field already equals the combined total and IPFT is also nonzero, do not sum both; raise a representation conflict for review.
4. **GST:** the public Upstox page says GST includes transaction and IPFT for the covered products. Calculate GST from the canonical component set exactly once. The split ₹306.99 + ₹0.01 and combined ₹307.00 have the same pre-GST base; never use ₹307.00 plus a second ₹0.01. Reconcile actual GST to a dated broker-issued invoice/contract note before approving the tax mapping for actual accounting.
5. **Exchange and product scope:** this 1 March 2026 reconciliation covers only NSE cash market, NSE equity futures, and NSE equity options on premium. Do not copy these rates to BSE, MCX, currency derivatives, commodity products, option exercise/assignment, or BSE scrip groups. Upstox's page describes IPFT in its equity table as NSE-specific; BSE rates must use BSE's applicable scrip/product schedule. Currency and commodity schedules require separate current sources.
6. **Evidence status:** the official NSE circular resolves the rate split and total for these three segments. It does not independently prove how every Upstox API response field maps to contract-note components or establish every GST tax-base scenario. Forum posts are useful corroboration of the historical convention that IPFT may be bundled in exchange transaction charges, but are not rate authority. For example, https://tradingqna.com/t/is-zerodha-charging-extra-transaction-charge-on-nse/153935 and https://www.reddit.com/r/IndiaInvestments/comments/17ozqno/ discuss the historical bundling/presentation issue.

### Acceptance tests required before enabling canonical API mapping

- NSE cash/futures/options boundary fixture: component split sums to combined total at ₹306.99 + ₹0.01, ₹182.99 + ₹0.01, and ₹3,552.99 + ₹0.01 per crore.
- Combined-rate mode rejects an additional IPFT amount and prevents double counting.
- Split-component mode rejects a combined rate being stored as transaction-only plus a second IPFT component.
- API mapping tests distinguish `null`, zero, missing field, combined transaction amount, and separate transaction/IPFT amounts.
- GST base is invariant between the split and combined representation for the same taxable total, with rounding applied only according to the reviewed rule.
- BSE/MCX/currency/commodity inputs cannot accidentally select NSE-equity IPFT rules.
- Reconciliation variance remains audit-only and cannot mutate reviewed actual allocations.

### Decision

The **NSE rate arithmetic for these three segments is resolved**. The remaining IPFT gate is API-field semantic mapping, representation-version enforcement, cross-segment scope protection, and actual contract-note/GST corroboration. Candidate tariff rules remain DRAFT/non-selectable until tests, dated evidence, and independent review pass. No tariff has been activated, no actual charge promoted, and no live broker order sent.


### Regression coverage added — 24 October 2026

Test commit: https://github.com/tarunsharma2610-del/tradepro-improved/commit/69945f4854ea8ae7d20e7795b156750406759df7

Added tests in `backend/tests/test_broker_tariff_rules.py` that:
- assert the current DRAFT NSE cash, futures and options exchange-charge candidates use the combined rates 0.00307%, 0.00183%, and 0.03553%;
- assert these candidates remain DRAFT and that no second `ipft` tariff candidate is layered on top of the combined `exchange_charges` candidate set;
- prove the GST helper yields the same ₹307.00 base and ₹55.26 at 18% whether that base is represented as one combined amount or ₹306.99 transaction charges plus ₹0.01 IPFT; and
- assert the NSE rules do not accidentally introduce MCX scope.

These are synthetic rule-consistency tests. They do not establish authenticated Upstox API field semantics, actual contract-note treatment, BSE/MCX rates, or approval of the GST component set. All tariff candidates remain DRAFT/non-selectable. Exact-head CI and independent review remain required.


### Exact-head CI confirmation — 24 October 2026

Verified GitHub Actions Backend tests run #40101310882 against commit `7b63a7dc7669c20e58b2a38cfe04ebf9d250cc89`: successful. Backend pytest reported **805 passed, 1 warning**; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trips passed; synthetic restore drill and evidence retention passed. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40101310882

This confirms the regression tests and documentation recorded at that exact head pass CI. It does not authenticate live Upstox API field semantics, prove account-specific GST treatment, or constitute independent tariff approval. Any subsequent commit requires its own exact-head CI check.


### Exact-head CI confirmation — IPFT checkpoint

GitHub Actions Backend tests run #40101490646 passed on commit `a8166bafe77544bf958d0d393b71432379898b72`. Backend pytest: **805 passed, 1 warning**. Broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic restore drill and restore-evidence retention all passed. Run: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40101490646

This is a successful exact-head result for the source-register update recorded by that commit. Later commits require their own exact-head CI result. No live Upstox API field mapping or account-specific GST treatment is inferred from this CI.


## User-provided historical Upstox statement evidence — 24 October 2026

A user-provided, redacted screenshot of page 2 of a two-page RKSV Securities India Pvt. Ltd. / Upstox Annual Global Transaction Statement was reviewed. The document identifies the period as FY 2022–23 and the segment as Futures & Options. The visible charge summary includes:
- IGST (18% on charges): ₹20.15
- SEBI fees: ₹0.22
- Stamp duty: ₹3.00
- STT-RND: ₹0.32
- STT-SQUP: ₹51.89
- Transaction charges: ₹111.61
- Brokerage charges: ₹1,000.00

The visible summary has no separately labelled IPFT row. This is evidence that this annual summary presented a distinct "TRANSACTION CHARGES" line without a distinct IPFT line; it is **not proof** that IPFT was included in that line. The report may aggregate, omit, or represent charge components differently from a contract note. The screenshot alone does not supply the complete machine-readable trades/turnover bases needed to reproduce the ₹111.61 charge, nor an API response from the same period. Do not infer that historical 2022–23 presentation establishes 2026 API semantics.

### Evidence classification and use

- Classify as user-supplied historical broker statement, not as an independently authenticated original PDF or an individual trade contract note.
- It may support investigation of historical presentation and future reconciliation fixtures, but must not be used as a tariff authority, a live API field mapping, or proof of actual IPFT inclusion.
- If the original PDF and the relevant authenticated Upstox API response are later available, reconcile the same segment/date window and compare underlying exchange turnover/premium, transaction charge, IPFT (including null vs absent vs zero), GST base and rounding.
- Do not promote actual per-fill charge allocations from this summary alone. Existing evidence rules requiring a reviewed contract-note source component and exact eligible-fill manifest remain unchanged.

### Status

The user-provided statement advances historical evidence collection but does not close the IPFT/API normalization or GST approval gates. Candidate rules remain DRAFT/non-selectable. PR #6 remains draft/unmerged and live broker order submission remains disabled.


## Lossless API field-state normalization — 24 October 2026

- Added `backend/app/services/broker_charge_api_normalization.py` with tests distinguishing absent fields, explicit `null`, numeric zero, nonzero numeric values and invalid values while preserving the original raw JSON value.
- This helper intentionally does not map `transaction` to transaction-only vs combined transaction/IPFT, does not interpret aggregate API responses as per-fill actuals, and does not turn `null` into zero. A reviewed mapping must identify API endpoint, response schema/version, field path, semantic meaning, unit, currency, scope and effective date.
- Exact-head CI for the new code/test commits remains required. Tariff candidates remain DRAFT/non-selectable; no API field mapping is approved by this helper alone.


## Reviewed API field mapping gate — 24 October 2026

- Added a generic mapping registry requiring broker, exact endpoint, response schema/version, field path, semantic classification, unit, currency, scope, effective date, source URL/hash and approval state. Selection refuses unapproved, unknown, missing or overlapping mappings.
- This is a software guard, not an approval of `ipft` or `transaction` semantics. No real Upstox mapping is approved yet; sample values in tests are synthetic and must not be interpreted as evidence. The authenticated Brokerage Details endpoint and aggregate Get Trade Charges endpoint remain separate evidence classes.
- Workflow #40106757433 passed for the prior field-state normalizer commit; the mapping module and subsequent docs require their own exact-head CI. Tariff candidates remain DRAFT/non-selectable.


## Official GST/IPFT cross-check — 25 October 2026

- Upstox public charges schedule: https://upstox.com/brokerage-charges/ — lists 2026 effective-dated transaction and STT rates, GST bases by product, and says IPFT is combined with transaction charges while also listing IPFT separately.
- NSE official STT page: https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax — confirms effective 1 April 2026 rates/bases for options sale (0.15% premium), exercised options (0.15% intrinsic value), and futures sale (0.05%).
- CBIC FAQ: https://cbic-gst.gov.in/sectoral-faq.html — STT/stamp duty/other tax recoveries are excluded from GST value only if pure-agent conditions are met; otherwise Section 15/Rule 27 valuation applies.
- Interpretation limit: this does not establish a particular API `transaction` field's semantics or prove per-fill actual charges. No production mapping/tariff is approved; candidates remain DRAFT/non-selectable until endpoint, schema, component, product, effective date, rounding and source evidence are independently reviewed.


## Resolver safety note — 25 October 2026

- Source-level endpoint restrictions remain effective across broker-name casing, trailing slash, query-string and absolute-URL variations for Upstox's aggregate charges and brokerage estimate endpoints.
- These are software controls, not tariff evidence. Keep API field mappings DRAFT/non-selectable until source/schema/product/effective-date semantics are independently reviewed; do not infer per-fill actual charges from estimates or aggregates.


## Expanded source-component vocabulary — 25 October 2026

- The API and persistence vocabulary now accepts separate `transaction_charges`, `clearing_charges`, `ipft`, `other_charges` and `demat_transaction_charges` source rows so those documented labels can be transcribed without collapsing or discarding them.
- Migration `202610250019` expands source-component and allocation constraints. New rows remain pending review; this does not approve any API field mapping or calculation rule.
- Live-fill promotion intentionally still requires exactly the existing six reconciled components. A separate IPFT or extra charge row therefore blocks promotion until a versioned representation/allocation contract is implemented and reviewed.


## Versioned exchange-charge representation contract — 25 October 2026

- Added `backend/app/services/broker_charge_representation_contract.py` with pinned contract version `exchange-charge-representation-v1`. The validator requires an explicit reviewed representation mode, preserves original source labels, validates normalized component names and paise-precision amounts, and rejects combined transaction charges plus a separate IPFT amount to prevent double counting.
- Added `backend/tests/test_broker_charge_representation_contract.py` covering combined versus split representations, equivalent ₹307.00 exchange-charge base, duplicate IPFT rejection, missing components, unknown/inferred modes, invalid amounts, raw-label retention, and unsupported component labels.
- This contract validates representation only. It deliberately returns `accounting_approved: false`; it does not authenticate a source document, approve a broker API mapping, decide GST taxable composition, allocate aggregate amounts to fills, or enable live accounting. Existing promotion remains fail-closed.
- Implementation/test commits: `3c9ac46ea58257ba4c9c87b1b664eee14c6bd35a` and `be505e3dbc0e93eaa25a012d6a9afba81712e9ab`. Exact-head CI for the final documentation head must be checked before this checkpoint is called verified.
- PR #6 remains draft/open/unmerged; PAPER mode remains mandatory; live broker order writes and automatic generic quantity/notional allocation remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Persisted transaction/IPFT representation gate — 25 October 2026

- Added migration `202610250020` and nullable `source_label` / `representation_mode` fields on `broker_charge_source_components`. Existing rows retain their normalized component name as a source-label fallback, but representation mode is deliberately left undeclared rather than inferred.
- Source-component intake now preserves the original label and optional explicit mode. Review of `transaction_charges` / `ipft` rows invokes the versioned representation validator and remains blocked when mode is missing, when combined mode also has a separate IPFT row, when split mode lacks either row, or when sibling rows disagree on mode. Rejected review attempts leave rows pending.
- Added API regression tests for persisted label/mode, combined-plus-separate-IPFT rejection, and missing-mode rejection. Exact-head CI is required before calling this checkpoint verified.
- GST composition, endpoint/schema semantics, authenticated real contract-note evidence, and per-fill allocation approval remain separate gates. No live broker writes or generic quantity/notional allocation were enabled.


## Representation-gate CI correction — 25 October 2026

- The first API regression run exposed two assertion-message mismatches: the validator correctly rejected ambiguous combined-plus-IPFT input and undeclared representation mode, but the tests expected different wording. Updated the tests to assert the validator's actual fail-closed error messages; no safety rule was weakened.
- Follow-up exact-head CI for commit `df344e9c64aeb6ec3f2f01fef01f3c05739d4800` and subsequent documentation synchronization is pending. Do not call the current head green until the full workflow completes.


## Authoritative IPFT/GST decision — 25 October 2026

This section records the settled calculation policy; it must be carried forward, not repeatedly reopened as an undecided research question.

### NSE combined charge includes IPFT

NSE circular NSE/FA/73061 (27 February 2026; effective 1 March 2026) gives combined rates:
- Cash equity: ₹307.00/crore.
- Equity futures: ₹183.00/crore.
- Equity options: ₹3,553.00/crore.

Equivalent split arithmetic:
- Cash equity: transaction charges ₹306.99/crore + IPFT ₹0.01/crore = ₹307.00/crore.
- Equity futures: transaction charges ₹182.99/crore + IPFT ₹0.01/crore = ₹183.00/crore.
- Equity options: transaction charges ₹3,552.99/crore + IPFT ₹0.01/crore = ₹3,553.00/crore.

Use either the explicitly reviewed combined representation or the explicitly reviewed split representation. Never add separate IPFT to a combined amount. Never infer representation from a field name alone. Preserve original source labels, raw values and endpoint/schema/version. Missing, conflicting or ambiguous representations fail closed; null is not zero.

Official circular: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf

### GST taxable-base policy

Apply 18% GST to the applicable, evidence-backed taxable service-charge base using canonical components exactly once. Working Upstox component policy:
- Delivery: brokerage + transaction charges/IPFT + applicable demat transaction charges.
- Intraday, futures and options: brokerage + transaction charges/IPFT.
- Combined transaction charges that already include IPFT enter the base once; split transaction charges excluding IPFT and the separately evidenced IPFT are combined once.
- Apply pure-agent/exclusion treatment only when the applicable tax rule and invoice evidence support it.
- Use product/segment/effective-date-specific rules, documented rounding and invoice reconciliation.

Published broker reference: https://upstox.com/brokerage-charges/

### Approval boundary

Settled: the arithmetic and no-double-counting rule above, component-based GST calculation once, and fail-closed handling of ambiguous representations. Still required for production approval: authentic Upstox API/contract-note field-semantic corroboration, effective-dated mapping and GST-base reconciliation against invoices, per-fill combined/split regression coverage, and exact-head CI. The Upstox Get Trade Charges endpoint is aggregate evidence, not proof of actual per-fill charges. These gates do not reverse the agreed policy.

Safety: PAPER mode mandatory; live broker order writes disabled; PR #6 remains draft/unmerged pending review and user approval. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `tarunsharma2610-del/Tradepro` must remain untouched.


## GST/IPFT checkpoint — 26 October 2026

- Regression test `test_gst_arithmetic_is_invariant_for_combined_vs_split_ipft_representation` verifies equivalent synthetic combined/split components produce ₹307.00 base and ₹55.26 GST at 18%; this is arithmetic coverage only, not approval of real taxable-component mapping. Exact test commit `8b4ae0b431d6aa03f1a8ae347a0b5fa7bda44c4f` passed Backend CI [run 40296066304](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40296066304).
- Source references: NSE circular `NSE/FA/73061` effective 1 Mar 2026 https://nsearchives.nseindia.com/content/circulars/FA73061.pdf; Upstox published charge schedule https://upstox.com/brokerage-charges/; CBIC stock-broking FAQ https://cbic-gst.gov.in/sectoral-faq.html and valuation Rule 33 https://cbic-gst.gov.in/valuation-rules.html.
- Actual GST mapping remains blocked pending product/segment-specific review and reliable invoice/contract-note reconciliation. Never apply GST to trade notional/all charges indiscriminately or count separate IPFT twice; STT/stamp duty exclusion depends on Rule 33 pure-agent conditions. Candidate tariffs remain DRAFT.
- Next gate: product-level GST acceptance cases across equity delivery, intraday and F&O, then exact-head CI. PAPER mode mandatory; live broker order writes disabled; PR #6 draft/unmerged; original `Tradepro` untouched.


## GST/API evidence checkpoint — 26 October 2026

- Implementation/test head `149d21fdbb82306ff1b800ff7d3ad33b99058d81`; exact-head Backend CI [#40296745348 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40296745348). Passing CI does not constitute legal approval of GST treatment.
- Source-backed Upstox GST component candidates now cover NSE/BSE equity delivery, equity intraday, equity futures and equity options. All remain `DRAFT`. Delivery includes `demat_charges`; the other categories do not. `exchange_charges` is the canonical combined transaction/IPFT component, so IPFT must not be counted twice. Trade notional is never a GST component.
- Official Upstox `GET /v2/charges/brokerage` calculates a quote for supplied instrument, quantity, product, side and price; response fields include GST, STT, stamp duty, transaction, clearing, IPFT and SEBI turnover. It is an estimate, not proof of actual executed-fill charges: https://upstox.com/developer/api-documentation/get-brokerage/.
- Official Upstox `GET /v2/trade/profit-loss/charges` returns a segment/financial-year date-range breakdown; `ipft` can be null. Treat it as aggregate reconciliation evidence, not per-fill attribution: https://upstox.com/developer/api-documentation/get-trade-charges/. Actual-charge approval still needs contract-note/tax-invoice and account-record reconciliation.
- Upstox's public schedule specifies 18% GST on brokerage + transaction charges + IPFT, with demat additionally for equity delivery, and says IPFT is combined with transaction charges: https://upstox.com/brokerage-charges/. NSE circular `NSE/FA/73061` supports revised combined NSE transaction/IPFT rates effective 1 March 2026: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf.
- CBIC permits exclusion of statutory recoveries such as STT/stamp duty only when pure-agent conditions are met; otherwise apply Section 15 and applicable valuation rules: https://cbic-gst.gov.in/sectoral-faq.html and https://cbic-gst.gov.in/valuation-rules.html. Do not hard-code universal exclusion without evidence.
- No GST candidate is promoted. Missing/null API fields remain unknown, not zero. Any later API ingestion must preserve raw response/hash, retrieval time, query segment/date range, schema version and invoice linkage. Do not use the brokerage calculator as actual-charge evidence or infer per-fill values from aggregate responses.
- Next gate: source-backed GST acceptance/reconciliation using actual invoice/contract-note evidence and per-product component sets, then exact-head CI and documentation verification. PAPER mandatory; live broker order writes disabled; PR #6 remains draft/unmerged; original `Tradepro` untouched.


## Focused GST/IPFT verification update — 26 October 2026

See [Upstox GST/IPFT evidence review](UPSTOX_GST_IPFT_VERIFICATION_2026-10-26.md) for the source-by-source decision and component matrix. Current conclusion: 18% GST is supported as the public schedule rate; March 2026 NSE combined transaction/IPFT arithmetic is supported; the taxable GST component sets remain DRAFT because the public tariff statement is not equivalent to a verified invoice/tax-base mapping. Public 2024/2025 contract-note copies are unauthenticated historical evidence, not current proof. Do not add IPFT on top of the new combined NSE rate. Null API IPFT remains unknown, not zero. The public Trades Charges API returns a segment/FY/date-range breakdown and may return `ipft: null`; it does not prove per-fill amounts. See the new review document for links and acceptance conditions.


## Historical contract-note GST-base discrepancy — 26 October 2026

A public third-party copy of an Upstox contract note dated 21 May 2024 lists GST taxable value ₹77.56 as brokerage ₹0.01 + SEBI ₹0.11 + turnover charges ₹3.44 + demat ₹74.00, with IGST ₹13.96, while IPFT ₹0.11 is shown separately and excluded from that displayed sum. The arithmetic matches 18% rounded to paise. This conflicts with the current Upstox public schedule's stated GST base (brokerage + transaction + IPFT, plus demat for delivery; no SEBI listed). The copy is unauthenticated and predates the 2026 combined transaction/IPFT schedule, so it is a discrepancy signal—not a rule to copy. Keep GST component sets DRAFT until current treatment is reconciled. Details: [GST/IPFT evidence review](UPSTOX_GST_IPFT_VERIFICATION_2026-10-26.md).


## Evidence-test wording correction — 26 October 2026

The backend test run `40302129087` reported 1,002 passed / 1 failed because an assertion used a phrase not present verbatim in the GST evidence review. The actual evidence describes the historical note as materially different from Upstox's current public pricing page. Corrected the test assertion in commit `f792627fb0ead15551e2506731b183e9b91482bb`; current-head CI remains to be verified. This correction changes no tariff candidate status: all GST component sets remain DRAFT.


## Additional GST-base evidence search — 26 October 2026

Search results for publicly indexed Upstox realized-P&L reports covering FY 2025–26 show separate aggregate GST and IPFT totals but not the taxable-value component breakdown. A 2025 F&O P&L report lists GST, IPFT, SEBI, stamp duty and transaction charges as totals, without explaining the GST base. A July 2026 Reddit post describes GST on brokerage/charges but is anecdotal. These are not authenticated contract-note/tax-invoice evidence. CBIC FAQ Q7/Q77 and Rule 33 valuation guidance mean the tax-base treatment cannot be inferred solely from charge labels; actual contractual/invoice mapping remains unresolved. Keep GST candidates DRAFT.


## Follow-up correction to brittle evidence assertion — 26 October 2026

The first wording-only assertion adjustment still failed because the exact phrase in the evidence document is split by Markdown emphasis (`**materially different**`). Updated the regression test to assert the stable semantic phrase `materially different` rather than formatting-sensitive exact markup. This is a test-only wording fix; the evidence finding and all GST candidate DRAFT statuses are unchanged. The current exact-head CI run must pass before the checkpoint is accepted.


## Contract-note evidence added — 26 October 2026

Public indexed Upstox note copies show three historical GST-base presentations: 11-Feb-2025 brokerage ₹2.96 + turnover ₹0.01 = ₹2.97 base and IGST ₹0.53; 21-May-2024 brokerage ₹0.01 + SEBI ₹0.11 + turnover ₹3.44 + demat ₹74 = ₹77.56 base and IGST ₹13.96, with IPFT ₹0.11 outside the displayed base; 12-Mar-2025 brokerage ₹2.75 base and IGST ₹0.50. Source URLs and arithmetic are recorded in UPSTOX_GST_IPFT_VERIFICATION_2026-10-26.md. These third-party copies show historical billing variation, not a universal rule. For current estimate-only logic, follow the current official Upstox published base (brokerage + transaction charges + demat + IPFT), canonicalizing IPFT inside combined transaction charges once. Actual per-fill GST remains evidence-gated.


## Canonical latest Phase 3 checkpoint — 26 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **Verified code/evidence head:** `d287da70ce184c904c6f9ede9e4a0edca5839f8f` (commit: “docs: reconcile public Upstox contract note GST examples”).
- **Exact-head CI:** PASS — [GitHub Actions run #40304398632](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40304398632), commit `d287da70ce184c904c6f9ede9e4a0edca5839f8f`; **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention also passed. This is CI evidence, not proof of a real Oracle recovery or broker-origin authenticity.
- **GST/IPFT research:** Three public third-party historical Upstox note copies were reconciled: 11-Feb-2025 base ₹2.97 / IGST ₹0.53; 21-May-2024 base ₹77.56 / IGST ₹13.96 (IPFT ₹0.11 listed outside that note's printed base); 12-Mar-2025 base ₹2.75 / IGST ₹0.50. Printed-base compositions differ historically. The current official Upstox schedule supports the **estimate-only** base of brokerage + transaction charges + demat where applicable + IPFT, with IPFT represented exactly once because it is combined with transaction charges. Do not add SEBI to this current estimate base without current applicable billing evidence; never calculate GST on trade notional or infer zero from missing/null fields.
- **Tax/accounting approval:** all four GST component candidates remain `DRAFT`. Historical public copies do not prove current actual per-fill billing across products/accounts. Actual-charge promotion stays gated; estimate logic and actual invoice reconciliation are distinct. Follow effective dates and preserve raw API/source evidence.
- **Next action when resuming:** continue Phase 3 from this exact commit and checkpoint. Next gate is component-specific GST acceptance cases for equity delivery, intraday, futures and options, then implementation review and exact-head CI; do not restart from earlier saved checkpoints.
- **Safety / PR:** PAPER mode mandatory; live broker `place_order`/`modify_order`/`cancel_order` and automatic live-fill promotion remain disabled. PR #6 remains open, draft and unmerged. Original `tarunsharma2610-del/Tradepro` is not the work target and must remain untouched.
- This checkpoint supersedes older statements in this document about CI being in progress or requiring verification for the pre-`d287da7` head. Historical notes remain history; this is the canonical resume point.

## Canonical resume checkpoint — 26 October 2026 (latest branch head verified)

- **Target:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **PR #6:** open, draft, unmerged. Never modify original `tarunsharma2610-del/Tradepro`.
- **Latest branch head before this documentation synchronization:** `5c929ff933d627dd81d5c32ec863843c2ef0f19b`. Exact-head Backend CI **PASS**, run [#40315135121](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40315135121): **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore and evidence retention passed; synthetic restore is not proof of real Oracle recovery.
- **GST/IPFT finding:** current official Upstox guidance supports an 18% public-schedule estimate base of brokerage + combined transaction/IPFT charges + delivery demat where applicable. Count combined transaction/IPFT once. CBIC FAQ Q77 makes exclusion of STT/stamp duty/other recoveries conditional on Rule 33 pure-agent conditions. Three public historical third-party notes show differing bases (11-Feb-2025 ₹2.97/IGST ₹0.53; 21-May-2024 ₹77.56/IGST ₹13.96 with IPFT outside that printed base; 12-Mar-2025 ₹2.75/IGST ₹0.50); they are not authenticated current evidence.
- **Decision:** all four product GST component candidates remain `DRAFT`; actual per-fill GST promotion is blocked pending reviewed current source/invoice mapping. Never tax trade notional, infer zero from missing/null fields, or double-count IPFT. Aggregate charges API data is not per-fill evidence; the brokerage calculator is estimate-only.
- **Next gate:** continue Phase 3 product/segment-specific GST component acceptance and evidence reconciliation. Do not repeat canonical live-fill integration or restart from older checkpoints. Defer AI/open-source adaptations, including Algory.app, until Phase 3 acceptance.
- **Safety:** PAPER mode mandatory; live broker order writes and automatic live-fill promotion/scheduling remain disabled. Do not merge PR #6 without explicit user approval. This documentation-sync commit must pass exact-head CI.


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
