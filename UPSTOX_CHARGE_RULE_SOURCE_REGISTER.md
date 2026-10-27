<!-- Phase 3 DP per-fill accounting checkpoint — 27 Oct 2026. Latest code/test head 855fcf68cb3202f09e3a2f98cecb99ce57240728 passed Backend CI #40456029280: 1,077 passed, 1 warning; broker-write boundary, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore and evidence retention all passed. DP is now included in LiveFillChargeBreakdown validation, Execution.total_charges, explicit KNOWN/NOT_APPLICABLE status, API completeness and replay identity. Equity-delivery SELL requires an independently reviewed/reconciled DP canonical snapshot and per-fill allocation; other fills reject an inapplicable DP allocation. Snapshot materialization allows per-component eligible-fill manifests, enabling DP to target only eligible delivery sells. Added successful synthetic delivery-sell promotion test and paise/manifest/missing-DP regressions. Latest documentation synchronization is in progress across 20 maintained documents; exact-head CI for the final documentation head remains pending verification. GST/IPFT is not restarted; invoice-level acceptance and independent tariff approval remain separate gates. PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original Tradepro out of scope. -->

<!-- Phase 3 continuation sync: 27 October 2026. Latest verified code/test head: 31ce2a10bcc789c223608c6566082b24aea7358c; Backend CI #40383076131 SUCCESS. Current maintained-doc synchronization head at the time of this update: fbcefc1ae44f863b5d16d5e32fd819d277b0ead8; documentation CI #40384521664 SUCCESS. DP/demat Execution persistence and central charge-total recomputation are implemented; next gate is focused audit of unknown-vs-zero semantics, delivery/non-delivery rules, migration round-trips, idempotency, rollback, and integration with per-fill allocation/reconciliation. GST/IPFT implementation is not being restarted. PR #6/#7 stay Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro repository out of scope. -->

## Latest authoritative checkpoint — 26 October 2026, 21:06 IST

This section supersedes earlier statements in this file that identify an older commit or CI run as the latest checkpoint. Historical entries below are retained for audit history.

- **Only target repository:** [tarunsharma2610-del/tradepro-improved](https://github.com/tarunsharma2610-del/tradepro-improved). Branch: `phase3/durable-per-fill-charge-allocation`. Latest documentation commit before this sync: `73c4a7cdcde4490bd520d5e75cc87fe1b4ffa310`. Exact-head documentation CI [#40346810442 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40346810442).
- GST estimate implementation commit `b75a97f6cd0043c185375cc253b84a1e6d6bfea1`; exact-head CI [#40345937942 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 tests passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence-retention checks passed.
- **GST estimate decision:** apply 18% to brokerage + combined exchange transaction/IPFT charge exactly once; include explicit demat/DP charges additionally for equity delivery. Do not add STT, stamp duty, SEBI or trade notional to this published GST estimate base. Upstox's Brokerage Details API sample arithmetic conflicts with the explicit public schedule; the sample does not override the schedule or prove live billing is wrong. Sources: [Upstox pricing](https://upstox.com/brokerage-charges/), [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/), [Trades Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/), [NSE transaction/IPFT circular](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).
- **New Phase 3 gap found:** `demat_transaction_charges` is intentionally blocked by source-to-canonical mapping; canonical live accounting and `Execution` currently support six components only. Equity-delivery actual-charge accounting with a DP/demat charge is therefore not accepted yet. The estimate helper can include a demat amount, but that does not mean actual accounting can persist/reconcile it. Keep this fail-closed; do not drop DP charges or fold them into another component. Next implementation gate: product-aware canonical demat/DP component and total-charge persistence, migration, idempotency, allocation, and delivery/non-delivery regression tests—or keep delivery actual accounting unsupported until complete.
- Actual per-fill GST/invoice acceptance remains evidence-gated. Public schedules and calculators support estimates, not account-specific actuals; aggregate API values and null fields are not per-fill invoice proof. User is not required to provide a personal contract note. Actual tariff candidates remain DRAFT.
- Phase 3 remains IN PROGRESS; PR #6 remains open/draft/unmerged. PAPER mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling remain disabled. Original `tarunsharma2610-del/Tradepro` must not be modified. AI/Algory integrations remain deferred until Phase 3 acceptance.

---

## Historical checkpoint (superseded) — 26 October 2026 (latest verified CI)

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


# Legacy Upstox Charge Rule Source Register (root-level duplicate)

**Canonical source register:** [`docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`](docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md). This root-level copy is retained for historical compatibility only. Maintain source records and status changes in the canonical `docs/` file; do not edit this duplicate independently.

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


## 2026-10-24 — Latest resolver CI and PostgreSQL concurrency suite verified

- Backend workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654) passed on head `ed346e823cbfae8448fae0134c4ff864bfcc60ac`: **872 passed, 1 warning**; broker-write boundary guard passed.
- Dedicated PostgreSQL concurrency tests cover competing fill sets, source verification vs allocation promotion, and live-fill promotion vs ledger verification. The successful test summary has no skipped tests, confirming the collected suite ran in CI's synthetic database environment.
- This is not approval of production Upstox tariff/field mappings. PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; original `Tradepro` remains out of scope.


## 2026-10-24 — Official tariff/API source audit

- Upstox Developer API `GET /v2/trade/profit-loss/charges` is scoped by segment, financial year and optional dates; it returns a `charges_breakdown` summary, not a documented per-fill record. Its published example has `charges.ipft: null`. Do not use this endpoint alone to ground actual per-fill charges; null remains distinct from zero. https://upstox.com/developer/api-documentation/get-trade-charges/
- NSE Finance & Accounts circular NSE/FA/73061 dated 27-Feb-2026 is effective 1-Mar-2026: combined member outflow ₹307/crore cash, ₹183/crore equity futures, ₹3,553/crore equity-options premium; IPFT contribution ₹0.01/crore each side. This is scoped exchange schedule evidence, not proof of Upstox's contract-note field mapping. https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- Upstox's public charges page lists newer effective-date summary tables alongside older historical tables. Apply effective-dated versioning; don't select stale rates based on page position. STT/CTT values also change from 1-Apr-2026 on the published page. https://upstox.com/brokerage-charges/
- No production mapping or tariff is approved. Keep mappings DRAFT; reject aggregate/estimate/null values for actual per-fill evidence; do not separately add IPFT where already included in combined exchange outflow.
- Latest code/test head before this note, `ee1b2a74d2a9f6141b9afbb6e06562b5cf263a9b`, passed Backend workflow #40110597753. This documentation change needs fresh CI verification.
- PR #6 remains draft/unmerged. Live order submission and automatic quantity/notional allocation remain disabled. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Aggregate endpoint hard guard added; CI pending

- Resolver now blocks Upstox `/v2/trade/profit-loss/charges` from `PER_FILL_ACTUAL` use even if a mapping row is incorrectly labelled per-fill. Official documentation defines the endpoint as aggregate `charges_breakdown`, not per-fill evidence.
- Regression test `test_official_upstox_aggregate_charges_endpoint_cannot_be_promoted_to_per_fill` covers the guard. Implementation `cdc07afdd8cc0c8d0b37d7e4aa8cdf1bf6eac651`; test `8ae749017a8ba0016f2c9adeb77eaff41fb5ae70`. CI is pending for this test commit.
- Production field mappings and tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live order submission remain disabled. PR #6 stays draft/unmerged; original `Tradepro` remains untouched.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` takes proposed instrument, quantity, product, transaction type and price, returning a charge calculation; this is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver now blocks `/v2/charges/brokerage` from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use even if a mapping is misleadingly labelled. Existing guard still blocks `/v2/trade/profit-loss/charges` from per-fill actual use. New regression tests cover both misuse cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. Prior head `6cc8b58f635fcb4f1b1cb3e5997099d074800a28` passed workflow #40111501429. CI for the new commits must be verified.
- Production mappings/tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live broker order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Expanded source-component vocabulary — 25 October 2026

- The API and persistence vocabulary now accepts separate `transaction_charges`, `clearing_charges`, `ipft`, `other_charges` and `demat_transaction_charges` source rows so those published API labels can be transcribed without collapsing or discarding them.
- Migration `202610250019` expands both source-component and allocation constraints. New rows remain pending review; this does not approve any API field mapping or calculation rule.
- Live-fill promotion intentionally still requires exactly the existing six reconciled components. A separate IPFT or extra charge row therefore blocks promotion until a versioned representation/allocation contract is implemented and reviewed.


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


## Phase 3 forward checkpoint — persisted representation-contract version (2026-10-25)

- Audited the actual branch and confirmed the previous source-label authenticity guard is already implemented and CI-verified at `b92d0185f588e24d54510b36659944e77f498a6e`; this task does not repeat that work.
- Added nullable `representation_contract_version` to `BrokerChargeSourceComponent` and migration `202610250021`. Null is retained for legacy/undeclared rows; the migration does not infer a version for historical records.
- The source-component intake API now accepts, stores, and returns the version. Review of transaction/IPFT components requires the supported persisted version and requires sibling transaction/IPFT rows to agree on both mode and version before the existing combined/split validator runs.
- Added API regression assertions for persistence and response round-trip. Implementation commit: `1d327b145fe25d871a763985b5f746e12e107b75`. Exact-head backend workflow [#40190287853](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190287853) was **in progress when this checkpoint was written**; do not mark the implementation CI-verified until its conclusion is successful. The documentation commit will require its own exact-head CI as well.
- This is an auditability step, not tariff approval, source authenticity proof, GST approval, or authorization to promote more components. Live accounting still requires its existing six-component set; extra components remain fail-closed. Paper mode and live-order safeguards are unchanged; PR #6 stays draft/unmerged; original `Tradepro` remains out of scope.
- Next single implementation gate: define and persist an explicit versioned component-set contract that distinguishes supported canonical accounting components from retained evidence-only components, then add tests proving missing, extra, duplicate, mixed-representation, and legacy-version rows cannot be silently omitted or promoted.


### CI correction history — persisted representation-contract version (2026-10-25)

- Workflow [#40190287853](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190287853) failed on `1d327b145fe25d871a763985b5f746e12e107b75` due to one existing API regression assertion expecting the previous validation error wording. The underlying fail-closed mode check was still rejecting the request; the test stopped on the message mismatch.
- Corrected the response wording without relaxing validation in commit `db1ee170629fcb853b5c6e46f0d9d8654056bc44`. The failure remains recorded as history and is not counted as a successful verification.
- Workflow [#40190403007](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190403007) was triggered for documentation HEAD `0abfa9a1ed5dcd553f1b92010ec86b41ccf77a2b`; that SHA predates the wording correction and must not be treated as verification of `db1ee170629fcb853b5c6e46f0d9d8654056bc44`. Exact-head CI for the corrected implementation and current documentation head remains pending.
- Next action: confirm the corrected exact-head workflow succeeds, then add explicit missing-version API regression coverage and continue the versioned component-set contract. No tariff candidates are promoted; live accounting still requires the existing six canonical components.


## Phase 3 forward checkpoint — versioned canonical component set (2026-10-25)

- Added `broker_charge_component_set_contract.py` with explicit `live-fill-accounting-component-set-v1` and the exact six canonical accounting components: brokerage, STT, exchange charges, SEBI charges, stamp duty, and GST.
- Added nullable `component_set_version` to source-component records via migration `202610250022`. No version is backfilled for legacy records. Canonical components receive the current set version only during independent review; evidence-only components remain unversioned and cannot be silently counted as canonical.
- Live-fill promotion now checks the full non-rejected source-component set before accounting: missing/extra/duplicate components, null/unsupported versions, and unreviewed rows fail closed. Additional evidence labels are preserved but block promotion until an explicit reviewed mapping exists. The prior six-allocation check remains in place.
- Added contract tests for exact set, missing/extra/duplicate components, legacy version and unreviewed rows. Updated the real PostgreSQL race fixture to declare the set version explicitly.
- Implementation/test checkpoint: `f61cedd25f5982846774db3028fb646d2e108e07`. Exact-head CI [#40191140007](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40191140007) passed: **917 passed, 1 warning, 0 failures**. Broker-write boundary guard, SQLite/PostgreSQL migration round-trips through migration `202610250022`, and synthetic restore drill passed. Synthetic restore does not prove actual Oracle Cloud recovery.
- Prior failed CI remains documented: run [#40190926423](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190926423) exposed a missing set-version value in the PostgreSQL concurrency fixture; the fixture was corrected in the verified commit above. It is not counted as a successful run.
- This does not yet map raw `transaction_charges` + `ipft` source rows to canonical `exchange_charges`, approve tariffs/GST, or enable promotion of evidence-only rows. Live broker writes remain disabled; PR #6 remains draft/unmerged; original `Tradepro` remains untouched.
- Next single implementation gate: define and test an explicit, versioned source-to-canonical mapping for combined versus split transaction/IPFT evidence, preserving both raw source rows while producing one canonical exchange-charge amount only when the representation is explicitly reviewed. Other unsupported source components must continue to block promotion.


## Phase 3 forward checkpoint — combined/split source canonicalization contract (2026-10-25)

- Added `broker_charge_source_canonicalization.py` and focused tests. The pure contract maps explicit COMBINED transaction/IPFT source representation to one canonical `exchange_charges` amount, or sums SPLIT transaction charges plus separately evidenced IPFT exactly once. It retains source-row associations in its result and rejects ambiguous/mixed versions, double mapping, duplicate/missing labels, invalid amounts, and unsupported clearing/demat/other components.
- Exact-head CI [#40191589060](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40191589060) passed on implementation/test commit `44c12acd133924711cd68c27f315d9298c6acfde`: **930 passed, 1 warning, 0 failures**. Broker-write boundary guard and synthetic restore drill passed. Synthetic restore is not actual Oracle recovery.
- Important boundary: this is a tested pure canonicalization contract, **not yet wired into the API review flow or durable allocation ledger**. It does not authenticate source notes, approve tariffs/GST, allocate canonical totals to fills, or enable live accounting. Do not count the end-to-end mapping gate as complete.
- Current branch/PR safety remains unchanged: work only in `tarunsharma2610-del/tradepro-improved`; PR #6 stays draft/unmerged; PAPER mode mandatory; live broker writes disabled; original `Tradepro` untouched.
- Next single implementation gate: wire this canonicalization contract into reviewed source-component validation and per-fill allocation persistence so raw source rows remain immutable, canonical exchange charges reconcile exactly, and promotion cannot omit or double-count source components.


## Authoritative checkpoint — 26 October 2026 (documentation CI verified)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- Latest implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`; exact-head Backend CI [#40287765745 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745).
- Documentation synchronization commit: `f90573d653c7103bf9cfdb1f867da97b176d3240`; its exact-head Backend CI [#40289107666 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40289107666). Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of actual Oracle Cloud recovery.
- Approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries do not supersede this checkpoint.


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

## Cross-repository GST/IPFT audit — 26 October 2026

- OpenAlgo's composable charge schedule is a useful architecture reference, but its inspected India delivery preset taxes brokerage + exchange transaction charges + SEBI and does not explicitly model IPFT/demat; this conflicts with the current Upstox public GST wording. Do not copy its formula.
- A Shoonya backtest example taxes brokerage + SEBI + transaction charges and adds IPFT separately; it is hard-coded sample logic, not tax authority.
- NautilusTrader's pluggable per-fill fee models are relevant for simulation mechanics only, not Indian GST interpretation.
- Upstox official tariff wording names brokerage + transaction + IPFT (and delivery demat). Its documented brokerage API example's GST ₹1.02 matches 18% of transaction ₹5.68 alone, while IPFT is ₹0.17 separately; this is a docs-example arithmetic mismatch, not proof of live endpoint behavior. Aggregate trade-charges API is not per-fill evidence.
- Historical publicly surfaced Upstox notes dated 21-May-2024 and 12-Mar-2025 concern rights-entitlement/special-case transactions. They are conflict signals, not representative current evidence for ordinary trades.
- Decision: all four GST component sets remain DRAFT. Next evidence gate is current ordinary-trade contract notes/tax invoices for delivery, intraday, futures and options, plus clarification of the public-tariff/API-example mismatch. Do not promote actual per-fill GST based only on a third-party formula or estimate API.

## Canonical checkpoint update — 26 October 2026, after cross-repository GST/IPFT audit

- Validated parent commit: `0e15bba3bfa425296f4104c96be6d10e3b42bf40`; Backend tests PASS on exact SHA, run [#40329710846](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40329710846). This documentation-only sync needs its own exact-head CI pass before it is the next validated checkpoint.
- Cross-repository finding: OpenAlgo's configurable charge schedule is useful architecture, but not an Upstox tax authority; the inspected Shoonya formula is hard-coded and unverified; NautilusTrader is relevant only for fee-model mechanics. No inspected repository proves the correct current Upstox GST taxable base.
- Upstox's documented brokerage API example has a GST arithmetic discrepancy versus current public tariff wording; this is not proof of live API miscalculation. Aggregate trades charges and estimate API responses cannot alone establish actual per-fill GST.
- Keep all four product candidates `DRAFT` until current ordinary-trade Upstox contract notes/tax invoices or written broker clarification resolves taxable components for delivery, intraday, futures and options.
- Invariants: combined transaction/IPFT counted once; no legacy IPFT double-counting; never tax trade notional; missing/null remains unknown; no promotion from estimates/aggregates to actual per-fill tax.
- Safety: PAPER mode mandatory; live broker writes and automatic live-fill promotion/scheduling disabled; PR #6 remains draft/unmerged unless user explicitly approves.

## Follow-up source reconciliation — 26 October 2026

### Current public tariff wording is explicit; the API example remains inconsistent

- Upstox's current public brokerage-charge page explicitly states GST is 18% on brokerage + transaction + IPFT for intraday, futures and options, and brokerage + transaction + demat + IPFT for equity delivery. It also says that from 1 March 2026 IPFT is combined with transaction charges. Source: https://upstox.com/brokerage-charges/ (reviewed 26 October 2026; see GST and transaction/IPFT sections).
- For a schedule effective 1 March 2026 onward, the intended public-schedule estimate should therefore represent the exchange charge once as the combined transaction/IPFT amount. Do not add a separate legacy IPFT component on top of that combined value. For delivery, the public schedule also lists demat/DP charges in the GST base; do not infer DP is absent just because an estimate API example does not include it.
- The Upstox Brokerage Details API documentation example remains internally inconsistent with that wording: GST ₹1.02 equals 18% of transaction ₹5.68 alone (rounded), while IPFT ₹0.17 is separately displayed and the example's DP plan minimum is described as extra/not included in brokerage calculation. Source: https://upstox.com/developer/api-documentation/get-brokerage/ . This is a documentation example discrepancy; it does not prove live API behaviour or actual contract-note treatment.
- A third-party Upstox calculator surfaced in research (https://dematopen.com/tools/brokerage-calculator/) calculates GST on brokerage + transaction charges and lists DP charge with its own GST. That differs from Upstox's public delivery GST wording and is not authoritative; do not use it to override Upstox or invoice evidence.
- Result: we can align the **public schedule estimate model** to the explicit tariff wording, with versioned effective dates and a single combined transaction/IPFT input. The actual per-fill GST rule still cannot be promoted until ordinary-trade contract-note/tax-invoice evidence or written Upstox clarification reconciles the API example and confirms delivery DP treatment. Keep all four actual component candidates `DRAFT`.

## Revised evidence checklist

- [ ] Written Upstox clarification or current ordinary-trade contract note/tax invoice showing taxable value and GST for delivery (including DP/demat), intraday, futures and options.
- [ ] Clarify whether Brokerage Details API's sample GST is stale and whether actual live responses use the current tariff's combined transaction/IPFT base.
- [ ] Verify BSE and NSE separately where rates/charge presentation differ; verify date-effective tariff selection around 1 March 2026.
- [ ] Keep estimate rules separate from actual per-fill accounting; reconcile actual invoice/ledger totals without inferring per-fill tax from aggregates.


## Latest exact-head CI checkpoint — 26 October 2026

- Latest source/documentation head verified: `0ff70ee399a1b8fd3d7d3998dcc1c93cd89da7a3` on `phase3/durable-per-fill-charge-allocation`; exact-head Backend pytest workflow [#40331381116](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40331381116) completed successfully.
- All observed job steps passed: dependency install, full test suite, broker write boundary, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, isolated synthetic PostgreSQL/document-volume restore drill, and evidence retention.
- This CI result verifies the existing code/tests at `0ff70ee399a1b8fd3d7d3998dcc1c93cd89da7a3`; it does not certify a new docs-only commit until CI runs against that exact new head. Keep this note historical after the follow-up docs commit; check that commit's CI before calling the documentation checkpoint green.
- GST/IPFT decision unchanged: public-schedule estimate may count combined transaction/IPFT once; no legacy IPFT double-counting; actual per-fill GST component candidates remain `DRAFT` pending source/invoice or written broker clarification. Never request personal contract notes from the user; continue using public sources and clearly label unresolved points.
- Safety and scope unchanged: target `tarunsharma2610-del/tradepro-improved` only; original `Tradepro` untouched; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; PR #6 remains draft/unmerged; AI/Algory work deferred until Phase 3 acceptance.


## GST/IPFT public evidence update — 26 October 2026

- See `GST_IPFT_PUBLIC_EVIDENCE_ADDENDUM.md` for the public-source findings, links and explicit decision gate.
- Current Upstox tariff wording supports estimates that count the combined transaction/IPFT amount once from 1 March 2026; do not double-count IPFT.
- The published Brokerage Details API sample (GST ₹1.02 vs transaction ₹5.68 and IPFT ₹0.17) remains inconsistent with that tariff wording. Public Upstox contract notes found for 21 May 2024 and 12 March 2025 are historical and do not resolve the post-March-2026 discrepancy.
- No actual GST component candidate promoted; delivery, intraday, futures and options remain DRAFT pending current public invoice evidence or written broker clarification. User's own contract note is not required.
- Branch: `phase3/durable-per-fill-charge-allocation`; repository: `tarunsharma2610-del/tradepro-improved` only. PAPER mandatory; live order writes and automatic live-fill promotion/scheduling disabled; PR #6 remains draft/unmerged. AI/Algory remains deferred until Phase 3 acceptance.


## GST/IPFT reconciliation checkpoint — 26 October 2026

- Official Upstox schedule https://upstox.com/brokerage-charges/ says GST is 18% on brokerage + transaction charges + IPFT, and includes DP/demat for equity delivery. From 1-Mar-2026, published NSE combined transaction/IPFT totals are cash ₹307/crore, equity futures ₹183/crore and equity options ₹3,553/crore on premium. Never add IPFT twice. NSE circular: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf (NSE/FA/73061, 27-Feb-2026).
- Open discrepancy: official Upstox Brokerage Details API example https://upstox.com/developer/api-documentation/get-brokerage/ shows transaction ₹5.68 + IPFT ₹0.17 but GST ₹1.02, matching 18% of ₹5.68 rather than ₹5.85 (approx ₹1.05). Treat as docs-example mismatch, not proven live production defect.
- Upstox Trades Charges API https://upstox.com/developer/api-documentation/get-trade-charges/ is aggregate by segment/date range and may return IPFT null; null is unknown, not zero, and aggregate output is not per-fill proof.
- Public third-party contract-note copies from 2024/2025 are historical, unauthenticated, pre-current-tariff and show differing taxable bases. They support historical layout/schema checks only.
- Estimate may follow current schedule with effective-date/product/exchange handling and combined transaction/IPFT counted once. Actual per-fill GST candidates for delivery, intraday, futures and options remain DRAFT pending current public invoice evidence or written Upstox clarification. No actual-charge logic promoted.
- Previous exact-head CI passed on 996b126ff678b97441f0214ea817451ee1592203: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40341429226 (tests, broker-write boundary, SQLite/PostgreSQL migration round-trips, synthetic restore and evidence retention). The next docs commit must pass its own exact-head CI.
- Scope: repository tarunsharma2610-del/tradepro-improved only; original Tradepro untouched. PAPER mandatory; live order writes and automatic live-fill promotion/scheduling disabled; PR #6 draft/unmerged; do not ask user for a personal contract note; defer AI/Algory until Phase 3 acceptance.


## GST estimate implementation update — 26 October 2026

- Added backend/app/services/upstox_public_gst_estimate.py and backend/tests/test_upstox_public_gst_estimate.py. This is public-schedule estimate logic only, not actual-charge evidence; it uses explicit components and an 18% GST rule and labels results PUBLIC_SCHEDULE_ESTIMATE_ONLY.
- Supported scopes from 1-Mar-2026: NSE EQ delivery/intraday, NSE FO futures/options, and BSE FO options. Delivery requires brokerage, exchange_charges and explicit demat_charges; other scopes require brokerage and exchange_charges. NSE exchange_charges includes combined transaction/IPFT once; separate ipft is rejected. For BSE options use applicable BSE charge source, do not assume an NSE IPFT component.
- Official Upstox API sample conflict remains: transaction ₹5.68 + IPFT ₹0.17 but GST ₹1.02; 18% of ₹5.85 is about ₹1.05. Estimate follows tariff wording, actual per-fill billing remains unresolved. Four actual GST component candidates remain DRAFT.
- See GST_IPFT_ACCEPTANCE_MATRIX.md. Code/test head 221493eb17729533cfaf855e2ce52532ef0903ac had CI run #40342805295 pending at note time; this documentation commit also needs exact-head CI.
- Scope/safety: only tarunsharma2610-del/tradepro-improved; original Tradepro untouched; PAPER mandatory; live writes and automatic live-fill promotion/scheduling disabled; PR #6 draft/unmerged; no personal contract note required; defer AI/Algory until Phase 3 acceptance.


## Authoritative GST decision — 26 October 2026

**Decision: implement the current official Upstox public-schedule GST base for estimates now; do not let the inconsistent API documentation sample block it.** Upstox's pricing page explicitly states GST at 18% on brokerage + transaction charges + IPFT, with demat charges additionally included for equity delivery. From 1-Mar-2026, NSE Circular NSE/FA/73061 defines combined transaction/IPFT outflows (cash ₹307/crore, futures ₹183/crore, options ₹3,553/crore premium); represent that as one exchange_charges component and never add IPFT twice. The supported estimate path sums brokerage + combined exchange_charges, and adds explicit demat_charges for delivery. STT, stamp duty and SEBI are not added to this published GST base.

The Brokerage Details API example showing transaction ₹5.68, IPFT ₹0.17 and GST ₹1.02 is internally inconsistent with that page: 18% × ₹5.68 = ₹1.0224 → ₹1.02; 18% × (₹5.68 + ₹0.17) = ₹1.053 → ₹1.05. Treat this as a documentation-example discrepancy, not evidence that current production billing is wrong. Public schedule takes precedence for estimates; the API example does not override it. Trades Charges API is aggregate and its ipft:null is unknown, not zero.

This resolves the public-schedule estimate rule. It does not certify account-specific invoice totals or per-fill actual GST. Keep actual accounting/promotion evidence-gated until invoice/source evidence or written broker clarification is available. A personal contract note from the user is not required. Official sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://nsearchives.nseindia.com/content/circulars/FA73061.pdf ; https://cbic-gst.gov.in/sectoral-faq.html


## Latest GST/IPFT implementation checkpoint — 26 October 2026

- Implementation + synchronized GST decision commit b75a97f6cd0043c185375cc253b84a1e6d6bfea1 passed exact-head Backend CI [#40345937942](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 passed, 1 warning in 62.33s. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed.
- Estimate decision: use 18% on brokerage + combined transaction/IPFT exchange charges; add explicit demat charges for equity delivery. Count IPFT once. Exclude STT, stamp duty and SEBI from the published estimate base. API example GST mismatch is a docs-example inconsistency and does not override the current Upstox schedule.
- Actual invoice/per-fill GST acceptance remains separate and evidence-gated; actual component-set candidates stay DRAFT. Do not request a personal contract note. Safety: PAPER mandatory, live order writes/promotion/scheduling disabled, PR #6 draft/unmerged, original Tradepro untouched.


## Session checkpoint sync — 26 October 2026

- Exact-head Backend CI [#40368554399 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40368554399) passed on code head `9d3f255480da9a71980a9d3819fbb69a34835753`. New documentation-sync commits require their own final exact-head CI check.
- Statutory GST research: CBIC stock-broking FAQ and CGST Act section 15 / CGST Rules Rule 33 and Rule 27 govern valuation; pure-agent exclusion is conditional on evidence, not automatic. IGST Act section 12(12) governs stock-broking place of supply; supplier/place-of-supply state comparison determines IGST vs CGST+SGST. Sources: https://cbic-gst.gov.in/sectoral-faq.html ; https://cbic-gst.gov.in/valuation-rules.html
- GST public-schedule helper/tests remain estimate-only. Statutory GST valuation service and tests are not implemented yet; GST/IPFT acceptance remains open. Next: implement Section 15 inclusion, Rule 33 evidence gates, tax-state split, Decimal/paise rounding and fail-closed handling. IPFT combined/separate and DP/demat persistence/reconciliation remain open.
- No personal contract note available or required. Safety: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER-only; live broker order writes disabled; original Tradepro repository out of scope.
