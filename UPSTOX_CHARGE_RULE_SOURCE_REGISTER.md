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

## IPFT research resolution — NSE rates effective 1 March 2026

Official source: [NSE Circular NSE/FA/73061](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf), effective 1 March 2026; cross-check: [Upstox brokerage and charges](https://upstox.com/brokerage-charges/).

For the listed NSE cash-equity and equity-derivative scopes, the published **combined exchange outflow** is:

| Scope | Combined rate | Calculation base |
|---|---:|---|
| NSE equity delivery/intraday | 0.00307% | Traded turnover |
| NSE equity futures | 0.00183% | Traded turnover |
| NSE equity options | 0.03553% | Option premium |

These combined rates include the revised NSE IPFT contribution of ₹0.01 per crore. Do **not** add a second IPFT amount on top of these combined rates. The tariff candidate inventory in `backend/app/services/upstox_tariff_candidates.py` represents these scopes under `exchange_charges`, and regression tests assert the effective date/rates and absence of a separate `ipft` candidate.

**Scope limit:** this does not resolve BSE equity/scrip-group charges, MCX, currency derivatives, every broker API response shape, or the GST taxable-component mapping. An API's separate `ipft` field must be preserved as returned (including missing/null), not automatically added to a combined rate. Where the response semantics do not establish whether values are additive or explanatory, mark the estimate/reconciliation as unresolved rather than double-counting.

**Implementation state:** research and regression coverage for the combined NSE rate are present; the candidate rows remain DRAFT and non-selectable pending independent approval and the remaining tariff/GST scope review. This is not approval to activate automatic accounting or live trading.

## Public schedule cross-check — BSE and MCX boundaries (24 October 2026)

Cross-check source: [Zerodha support — exchange transaction charges](https://support.zerodha.com/category/account-opening/resident-individual/ri-charges/articles/exchange-transaction-charges), which publishes a current comparative schedule and explicitly notes NSE IPFT is included in NSE exchange transaction fees. This is a secondary broker reference, useful for cross-checking, not a substitute for the applicable exchange circular.

The published comparison lists (rates as shown by that source):
- BSE equity cash: 0.00375% for specified scrip groups; other scrip groups have separate rates.
- BSE equity index options are contract/index-specific (the source lists Sensex/Bankex and other index distinctions); do not treat the existing BSE FO candidate as a universal BSE options tariff.
- MCX commodity futures: 0.0021%; MCX commodity options: 0.0418%.
- NSE currency/commodity products and BSE currency products have separate rates and bases and must not inherit NSE cash/equity-derivative rules.

These values are recorded as **research leads, not approved selectable tariff rows**. Before implementation/activation, retrieve the governing exchange circular/master circular for the exact effective period and contract category, including any turnover slabs, expiry-specific rates, scrip groups, caps, or exemptions. The current candidate inventory does not establish complete BSE/MCX coverage.

## API representation rule reaffirmed

Official Upstox docs:
- [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/) is an instrument/quantity/product/side/price-specific estimate. Its schema lists numeric `other_charges.ipft`.
- [Get Trade Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/) returns segment/FY charge breakdown and its example shows `charges.ipft: null`.

Treat those as different response contexts. Preserve raw JSON and distinguish absent, null, zero, and numeric values. A null in an aggregate sample is **unknown/not supplied**, not proof of zero, and not proof that IPFT was bundled into another field. Do not use a summary API field as a per-fill actual. The NSE combined effective-dated tariff rule remains authoritative for the covered NSE scope; API fields are reconciled against that scope only when their semantics and calculation bases are explicit.

## Governing exchange source pointers for next tariff review — 24 October 2026

- **BSE cash equity:** [BSE Equity Segment Master Circular](https://www.bseindia.com/markets/MarketInfo/DownloadAttach.aspx?attachedId=8a7fec3a-95bc-4bd2-82de-76e2a84e2915&id=20250429-51). It explicitly differentiates scrip groups and points to the daily scrip master / applicable-scrip file; a single generic BSE equity rate is insufficient. Use the circular and date-specific scrip metadata before selecting a rate.
- **BSE equity derivatives:** [BSE Notice 20231020-46](https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20231020-46) describes tiered monthly billable premium turnover rates for SENSEX options, including expiry-specific rules. Treat as historical evidence and check for superseding notices before any effective-date activation.
- **MCX:** [Official MCX circular archive](https://www.mcxindia.com/circulars/all-circulars) is the primary discovery source. The [MCX compliance FAQ](https://www.mcxindia.com/faq/compliance) also references applicable CTT, stamp duty, GST and other statutory dues, and clarifies that statutory charges and contract/brokerage requirements must be handled by scope. Do not activate a generic MCX rate based only on a secondary broker schedule.

These pointers are research sources, not approved tariff rules. The existing candidate registry does not yet implement date-specific BSE scrip-group/monthly slabs or all MCX product/contract distinctions. Preserve the fail-closed behaviour until current governing circulars and calculation bases are encoded and tested.

## BSE / MCX circular review — latest public results checked 24 October 2026

### BSE cash equity
The [BSE Equity Segment Master Circular](https://www.bseindia.com/markets/MarketInfo/DownloadAttach.aspx?attachedId=8a7fec3a-95bc-4bd2-82de-76e2a84e2915&id=20250429-51) describes the existing transaction-charge framework by scrip group and exclusivity status, and refers to exchange-provided turnover/charge files. This supports implementing BSE equity as a date-specific lookup using exchange-provided scrip classification rather than one percentage hardcoded for every scrip. Before activation, confirm whether a newer BSE notice supersedes each applicable clause and capture the official daily scrip classification file for the trade date.

### BSE equity derivatives
The official [BSE Notice 20231020-46](https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20231020-46) applies a monthly incremental premium-turnover slab schedule to S&P BSE SENSEX options nearest/immediate expiry from 1 November 2023. It says other equity-derivative contracts were unchanged by that notice. Because this is an old, narrow notice, it is evidence for the calculation model (monthly cumulative slab + incremental turnover), not sufficient by itself to certify rates current for every contract in 2026. Do not apply this SENSEX schedule to Bankex, stock options, or all BSE derivatives without matching a current official notice.

### MCX
The [MCX official circular archive](https://www.mcxindia.com/circulars/all-circulars) was checked; the current archive includes dated contract specification, due-date-rate, and product-ID changes. Those are relevant to contract metadata and product scoping but do not alone establish a complete current transaction-charge schedule. The [MCX compliance FAQ](https://www.mcxindia.com/faq/compliance) points to Circular MCX/INSP/286/2024 for contract notes and statutory dues and requires applicable CTT, stamp duty, GST and other statutory charges. Treat this as support for the statutory component checklist, not as a tariff rate table.

### Implementation decision
- No new BSE or MCX rates are approved/selectable from this review alone.
- BSE cash equity needs dated scrip-group/exclusivity metadata and the applicable current charge file.
- BSE nearest-expiry SENSEX options needs monthly cumulative turnover state and a current rate schedule; per-fill linear allocation is not equivalent to the exchange's monthly slab charge.
- MCX needs exact effective-dated schedules for the product/contract/side and separate CTT/stamp-duty/GST bases.
- Keep current candidates DRAFT and fail closed where the exact date, scope, or required lookup data is absent.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a6b3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Resolver now verifies that the payload field matches the terminal field in the approved mapping path. Implementation `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression test `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI is pending for these and subsequent documentation commits.
- The field-identity guard is a code correctness safeguard, not approval of production Upstox field semantics or tariffs. Existing live-fill tests cover lock order, replay idempotency and rollback; genuine concurrent verification-versus-promotion coverage still needs confirmation.
- PR #6 remains draft/unmerged. Live order submission and automatic quantity/notional allocation remain disabled. Work only in `tradepro-improved`; original `Tradepro` remains untouched.
