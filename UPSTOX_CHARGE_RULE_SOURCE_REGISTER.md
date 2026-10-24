# Upstox Charge Rule and Evidence Source Register

**Audit date:** 2026-10-24  
**Status:** Research register only. No tariff rule in this document is approved for automatic accounting or live trading.

## Purpose and safety boundary

Separate (1) broker API estimates, (2) realized broker-reported charges, and (3) legally applicable/effective-dated tariff rules. An API estimate is useful for planning and comparison but is not, by itself, proof of realized charges or authority to allocate an order-level amount to individual fills. A contract note or broker trade-charge record must be reviewed before actuals can be reconciled.

## Verified official Upstox API sources

| Source | What it provides | Permitted use | Not sufficient for |
|---|---|---|---|
| [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/) — `GET /v2/charges/brokerage` | Estimate for instrument token, quantity, product, BUY/SELL and price; response breakdown includes total, brokerage, GST, STT, stamp duty, transaction/clearing/IPFT/SEBI turnover and DP-plan metadata | Store canonical request/response, endpoint/version, timestamp, input fill manifest, response digest and result as **estimate-only** evidence | Treating the result as realized charge evidence; assuming a breakdown is fill-level; using undocumented tariff assumptions |
| [Profit and Loss on Trades API](https://upstox.com/developer/api-documentation/get-trade-charges/) | Trade P&L/charge data, including charge breakdown fields such as brokerage, GST, STT, stamp duty, transaction, clearing, IPFT, SEBI turnover and demat transaction | Reconcile broker-reported realized charges for the API's supported segment and financial-year/date scope after validating identity and completeness | Replacing the source contract note or assuming a trade-level response is necessarily a unique exchange-fill allocation |
| [Upstox API overview](https://upstox.com/developer/api-documentation/) and [live Swagger](https://api.upstox.com/v2/swagger-ui/index.html) | Official endpoint catalogue, request/response schema and API operation definitions | Recheck endpoint schema/version, SDK parity and available evidence APIs during implementation | A static source of effective-dated exchange/regulatory tariff rates |

## Rule status by charge category

Every entry remains **DRAFT / NOT SELECTABLE** until the specific product, exchange/segment, transaction side, calculation base, applicable date interval, rounding, cap/minimum, source document and independent reviewer are recorded.

| Component | Rule inputs that must be proven before activation |
|---|---|
| Brokerage | Active Upstox plan/contract, product and segment, per-order or per-unit formula, cap/minimum, order grouping and effective dates |
| GST | Legally applicable rate and taxable-service base, inclusions/exclusions, rounding, effective dates and authoritative tax source |
| STT/CTT | Security/product/segment, buy/sell side, turnover basis, rate and effective dates from the relevant official tax/regulatory source |
| Stamp duty | Applicable segment/product, buyer-side rule, transaction value basis, rate and effective dates from authoritative source |
| Exchange/transaction charges | Exchange and segment, rate schedule, turnover basis, product/date, rounding and effective dates from the relevant exchange circular |
| SEBI turnover/IPFT/clearing/other charges | Applicable authority/exchange schedule, covered segment, basis, exemptions, effective dates and rounding |
| DP/demat charges | User-specific DP plan, applicable sale/scrip/day conditions, rate/minimum and the source confirming the user's plan |

## Activation and allocation gates

1. Preserve source URL/document, publication/effective dates, retrieval timestamp, content digest and a human-readable excerpt/reference.
2. Require independent review by an authorized reviewer; extraction alone is not approval.
3. Never infer a missing rate from a sample response, UI display, third-party calculator or previous tariff period.
4. Keep API estimates separate from reviewed actuals. Variance rows are analysis-only and must not mutate source evidence or charge allocations.
5. Do not distribute order-level charges across fills unless the component's economically and legally appropriate allocation basis is documented and reviewed. Brokerage caps, GST taxable bases and transaction levies may not be linearly attributable to each fill.
6. Until effective-dated component-specific rules are approved, only the existing explicitly reviewed per-fill allocation path may be eligible for reconciliation; quantity/notional defaults remain blocked.
7. Recheck official docs and source circulars before enabling any new tariff period. Fail closed on missing, stale, conflicting or unverifiable sources.

## Audit findings

- The official brokerage API is confirmed as an estimate endpoint with the documented inputs and charge-breakdown response above.
- Upstox documents a separate trade P&L/charges API, which should be evaluated for realized-charge reconciliation where its scope matches the trade and date.
- These API docs do **not** alone establish the current effective-dated legal rates, the user's active brokerage plan, or the correct fill-level allocation for each component.
- Therefore this register approves **no automatic tariff rule** and changes no live-order or accounting safety guard.

