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
Added `docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md`. Its canonical extracted-payload SHA-256 is `c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420`. This is a normalized excerpt, not a byte-for-byte copy of live source HTML. NSE's official derivatives STT page corroborates the 1 April 2026 futures/options/exercised-option rates. `backend/app/services/upstox_tariff_candidates.py` now lists 18 effective-dated STT and exchange-charge candidates; all remain DRAFT and are not selectable. Exchange/IPFT composition is unresolved and the NSE stamp-duty page is dated 3 October 2023, so no rates are activated. Exact-head CI run `40065979244` passed on `f76ecde4ac785123de2980539138ce89ff660294` (**760 passed, 1 warning**).


## Official-source recheck — 2026-10-24 (no tariff activation)

- Rechecked the live official Upstox charges page on 2026-10-24. It explicitly lists STT/CTT changes effective 1 April 2026 (NSE futures 0.05% sell-side; options 0.15% sell-side on premium; exercised-option sales 0.15%) and NSE transaction-charge changes effective 1 March 2026 (equity 0.00307%, futures 0.00183%, options 0.03553% on premium; BSE options 0.0325% and BSE futures nil). Source: https://upstox.com/brokerage-charges/.
- The same page says IPFT is combined with transaction charges and lists ₹0.01 per crore of traded value (options on premium) plus GST. The candidate registry currently represents the published transaction-charge rates only; do not silently treat those rates as the combined transaction + IPFT total. Resolve the component representation and exact effective date for IPFT before approval.
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
