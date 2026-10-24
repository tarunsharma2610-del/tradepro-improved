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
