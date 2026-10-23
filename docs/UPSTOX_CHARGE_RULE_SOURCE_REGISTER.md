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
