## Canonical checkpoint reconciliation — 25 October 2026 (latest exact-head CI verified)

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **PR #6:** open, draft, unmerged.
- **Latest verified branch head before this documentation sync:** `e9440e2f31f9d4d108b9160608e653efffd2d9fc`. Exact-head Backend CI [run #40210391188](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40210391188) completed successfully on this exact SHA (25 October 2026).
- **Latest verified code/test checkpoint:** `50802e96e06756b57a9f930e0c54c680777922d4`; Backend CI [run #40209741299](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40209741299) passed on that exact SHA.
- **Verified gates:** backend pytest; broker-write safety boundary; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade; synthetic PostgreSQL/document-volume restore drill. The synthetic restore does not prove actual Oracle Cloud recovery.
- **Concurrency acceptance gap closed:** PostgreSQL coverage races two promotion calls for the same reviewed component alongside verification; both promotions must return the complete allocation set and final reconciled rows must share one durable reference.
- **Next single implementation step:** integrate canonical snapshot allocation/reconciliation end-to-end with live-fill accounting (Phase 3 Gates 1C/5). Current live-fill accounting still validates raw source-component rows through the legacy six-row ledger. Add focused integration coverage for combined/split transaction/IPFT, exact replay, complete totals, and fail-closed rejection of extra/unmapped components. Do not silently drop or double-count charges; do not introduce generic quantity/notional allocation.
- **Remaining gates:** evidence-backed effective-dated tariff selection (Gate 2); approved per-fill rule wiring (Gate 3); invoice/source-backed GST/component acceptance (Gate 4); final adversarial/migration/restore review (Gate 6); final exact-head documentation/sign-off (Gate 7).
- **Upstox controls:** no unused SDK runtime dependency; Agent Skill is static-review-only and must not be executed or supplied live credentials. Brokerage calculator output is estimate-only; aggregate charge endpoints are not per-fill actual evidence. GST/IPFT/tariff candidates remain DRAFT until authentic applicable evidence and independent review support approval.
- **Safety invariants:** original `tarunsharma2610-del/Tradepro` remains out of scope and must stay untouched; PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. Do not merge PR #6 without explicit user approval.
- **Checkpoint protocol:** this 25-file documentation sync must pass CI on its own resulting commit before the next implementation change. Parent-commit CI does not verify a newer SHA.

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
