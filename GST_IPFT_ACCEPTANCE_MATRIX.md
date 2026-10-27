<!-- Phase 3 checkpoint update — 27 Oct 2026. Latest code/test head 8feeb0cbb0c35e1e37012302c9075d43f1f33eb1 passed Backend CI #40458822529: 1,097 passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed. DP completeness checks require a consistent KNOWN + explicit valid finite nonnegative paise-exact amount, or NOT_APPLICABLE + no amount; invalid status, UNKNOWN-with-amount, KNOWN-without-amount, NOT_APPLICABLE-with-amount, NaN, negative and fractional-paise amounts fail closed. DP canonical manifests are checked against persisted broker trade → child order → local order mappings; only mapped equity-delivery SELL fills are accepted. Delivery SELL still requires reviewed/reconciled DP evidence and durable per-fill allocation; DP is included once in total and replay identity. Maintained docs are being synchronized after the green code run; exact-head CI on the final docs/checkpoint commit must pass before it is called green. PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original Tradepro repository out of scope. -->

## GST/IPFT statutory-engine implementation update — 26 October 2026 (code/test CI passed; docs head must be checked)

- Added `backend/app/services/statutory_stock_broking_gst.py` and `backend/tests/test_statutory_stock_broking_gst.py` on the current Phase 3 branch. The service implements CGST Act section 15's default taxable valuation, conditional CGST Rule 33 pure-agent exclusion requiring every evidence flag, and IGST Act section 12(12) recipient-location/fallback state selection for IGST versus CGST+SGST.
- Service/test changes are in commits `dcad71e148b89a2c384631b36090008c8fad193e` and `037ad2da02dca34c399e0ec454674c50ae65b5a7`, included in the verified checkpoint head above. Exact-head Backend CI [#40375335160 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40375335160) passed on checkpoint head `cc2d591cf74daea5d68b6ba704ae87a342cc96fd`: **1,051 passed, 1 warning**. Broker-write guard, SQLite/PostgreSQL 16 migration round-trips and synthetic restore drill passed. Later documentation commits are newer and still require exact-head CI verification.
- The statutory engine is a separate primitive and is not yet wired into actual per-fill accounting. It does not infer Rule 33 pure-agent status from a charge label; absent complete evidence, third-party recovery lines remain in the section 15 base. It keeps the Upstox published-schedule estimate separate from statutory valuation and does not override the unresolved API sample discrepancy.
- Regression coverage added for combined/separate exchange/IPFT values in the taxable base, Rule 33 all-conditions gate, same-state versus cross-state tax type, recipient-state fallback, invalid/missing money, duplicate line names, and paise rounding. Intra-state CGST/SGST tax heads are rounded independently to paise and the returned total equals the two heads.
- Remaining gates: run exact-head backend CI and fix failures; independently review tax-head rounding and legal policy; implement product/broker effective-dated mapping and IPFT resolver; complete DP/demat persistence + total reconciliation; integrate only reviewed policy paths; synchronize this checkpoint again to the final CI-verified head. Actual per-fill invoice evidence remains deferred until source records/deployment exist; no personal contract note is required.
- Official source basis: [CBIC stock-broking FAQ](https://cbic-gst.gov.in/sectoral-faq.html), [CGST Act section 15](https://cbic-gst.gov.in/hindi/CGST-bill-e.html), [Upstox Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/), and [Upstox public charges](https://upstox.com/brokerage-charges/).
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft and unmerged; PAPER-only; live broker writes disabled; original `Tradepro` untouched.
## Latest authoritative checkpoint — 26 October 2026, 21:06 IST

This section supersedes earlier statements in this file that identify an older commit or CI run as the latest checkpoint. Historical entries below are retained for audit history.

- **Only target repository:** [tarunsharma2610-del/tradepro-improved](https://github.com/tarunsharma2610-del/tradepro-improved). Branch: `phase3/durable-per-fill-charge-allocation`. Latest documentation commit before this sync: `73c4a7cdcde4490bd520d5e75cc87fe1b4ffa310`. Exact-head documentation CI [#40346810442 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40346810442).
- GST estimate implementation commit `b75a97f6cd0043c185375cc253b84a1e6d6bfea1`; exact-head CI [#40345937942 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 tests passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence-retention checks passed.
- **GST estimate decision:** apply 18% to brokerage + combined exchange transaction/IPFT charge exactly once; include explicit demat/DP charges additionally for equity delivery. Do not add STT, stamp duty, SEBI or trade notional to this published GST estimate base. Upstox's Brokerage Details API sample arithmetic conflicts with the explicit public schedule; the sample does not override the schedule or prove live billing is wrong. Sources: [Upstox pricing](https://upstox.com/brokerage-charges/), [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/), [Trades Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/), [NSE transaction/IPFT circular](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).
- **New Phase 3 gap found:** `demat_transaction_charges` is intentionally blocked by source-to-canonical mapping; canonical live accounting and `Execution` currently support six components only. Equity-delivery actual-charge accounting with a DP/demat charge is therefore not accepted yet. The estimate helper can include a demat amount, but that does not mean actual accounting can persist/reconcile it. Keep this fail-closed; do not drop DP charges or fold them into another component. Next implementation gate: product-aware canonical demat/DP component and total-charge persistence, migration, idempotency, allocation, and delivery/non-delivery regression tests—or keep delivery actual accounting unsupported until complete.
- Actual per-fill GST/invoice acceptance remains evidence-gated. Public schedules and calculators support estimates, not account-specific actuals; aggregate API values and null fields are not per-fill invoice proof. User is not required to provide a personal contract note. Actual tariff candidates remain DRAFT.
- Phase 3 remains IN PROGRESS; PR #6 remains open/draft/unmerged. PAPER mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling remain disabled. Original `tarunsharma2610-del/Tradepro` must not be modified. AI/Algory integrations remain deferred until Phase 3 acceptance.

---

# GST/IPFT acceptance matrix — estimate vs actual evidence

Updated 26 October 2026. This matrix separates estimate calculations from actual per-fill invoice reconciliation.

## Scenarios and acceptance criteria

| Scenario | Estimate acceptance | Actual-charge acceptance |
|---|---|---|
| NSE equity delivery, tariff boundary 1-Mar-2026 | Effective-dated cash rate; combined transaction/IPFT once; GST estimate base per Upstox schedule includes brokerage, transaction/IPFT and DP/demat where applicable. Do not apply DP per fill indiscriminately. | DRAFT pending current invoice or written broker clarification; DP is typically sell-side per scrip/day. |
| NSE equity intraday, boundary 1-Mar-2026 | Effective-dated cash rate; combined transaction/IPFT once. | DRAFT; resolve API sample mismatch first. |
| NSE equity futures, boundary 1-Mar-2026 | Current total ₹183/crore; don't add IPFT separately. | DRAFT; current invoice/base evidence needed. |
| NSE equity options, boundary 1-Mar-2026 | Current total ₹3,553/crore on premium; don't add IPFT separately. | DRAFT; current invoice/base evidence needed. |
| BSE products | Use current BSE/scrip-group/product-specific schedule, never substitute NSE rate. | DRAFT until applicable schedule and tax base sourced. |
| API example: transaction ₹5.68, IPFT ₹0.17, GST ₹1.02 | Flag discrepancy: 18% × ₹5.68 = ₹1.0224 (₹1.02); 18% × ₹5.85 = ₹1.053 (about ₹1.05). No silent choice for actuals. | Block promotion until Upstox clarifies current billing/API semantics. |
| Aggregate API IPFT null | Treat null as unknown, not zero. | Cannot satisfy per-fill evidence gate. |
| Historical public contract-note copy | Layout/historical comparison only. | Cannot prove current per-fill tax composition. |
| Rounding/allocation | Deterministic paise rounding and tariff/source fingerprint. | Reviewed component provenance, exact eligible-fill set, approved method/basis, and paise-exact source-total reconciliation required; fail closed on mismatch. |

## Gate to promote DRAFT GST candidates

1. Current public evidence after 1-Mar-2026 or written Upstox clarification resolves GST/IPFT base when API fields are separate.
2. Confirm delivery (including DP/demat), intraday, futures, options and relevant NSE/BSE/MCX product-specific treatment.
3. Add cited expected-value fixtures for tariff boundaries and verified invoice component breakdown only after source evidence is sufficient.
4. Tests prove null is not zero, combined transaction/IPFT is not double-counted, GST is not applied to trade notional, and STT/stamp duty/SEBI are not included without explicit source support.
5. Actual allocations must reconcile exactly to reviewed source totals; synthetic examples must be labelled test-only and never represented as genuine broker documents.

Current disposition: no actual-charge GST logic is approved by this matrix. PAPER mandatory; live order writes and automatic live-fill promotion/scheduling disabled; PR #6 remains draft/unmerged.


## Public-schedule GST estimate implementation — 26 October 2026

The estimate-only path is implemented in backend/app/services/upstox_public_gst_estimate.py with regression tests in backend/tests/test_upstox_public_gst_estimate.py. It requires explicit source components, uses 18%, labels results PUBLIC_SCHEDULE_ESTIMATE_ONLY, and is scoped to reviewed NSE/BSE product combinations from 1-Mar-2026. Delivery includes explicit demat_charges; all supported products include brokerage + exchange_charges; NSE exchange_charges already includes transaction/IPFT once. A separate ipft input is rejected to prevent double counting. BSE options must use the applicable BSE schedule and must not inherit NSE IPFT assumptions.

This does not resolve actual billing: the Upstox Brokerage Details API example (transaction ₹5.68, IPFT ₹0.17, GST ₹1.02) conflicts with the tariff base wording because 18% of ₹5.85 rounds to about ₹1.05. Public estimate calculation follows published tariff wording only; actual per-fill GST candidates remain DRAFT. CI for code/test head 221493eb17729533cfaf855e2ce52532ef0903ac was pending at note time. Final exact-head CI is required before accepting this update.


## Authoritative GST decision — 26 October 2026

**Decision: implement the current official Upstox public-schedule GST base for estimates now; do not let the inconsistent API documentation sample block it.** Upstox's pricing page explicitly states GST at 18% on brokerage + transaction charges + IPFT, with demat charges additionally included for equity delivery. From 1-Mar-2026, NSE Circular NSE/FA/73061 defines combined transaction/IPFT outflows (cash ₹307/crore, futures ₹183/crore, options ₹3,553/crore premium); represent that as one exchange_charges component and never add IPFT twice. The supported estimate path therefore sums brokerage + combined exchange_charges, and adds explicit demat_charges for delivery. STT, stamp duty and SEBI are not added to this published GST base.

The Brokerage Details API example showing transaction ₹5.68, IPFT ₹0.17 and GST ₹1.02 is internally inconsistent with that page: 18% × ₹5.68 = ₹1.0224 → ₹1.02; 18% × (₹5.68 + ₹0.17) = ₹1.053 → ₹1.05. Treat this as a documentation-example discrepancy, not evidence that current production billing is wrong. Public schedule takes precedence for the estimate path; the API example does not override it. Trades Charges API is aggregate and its ipft:null is unknown, not zero.

This resolves the public-schedule estimate rule. It does not certify account-specific invoice totals or per-fill actual GST. Keep actual accounting/promotion evidence-gated until invoice/source evidence or written broker clarification is available. A personal contract note from the user is not required. Official sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://nsearchives.nseindia.com/content/circulars/FA73061.pdf ; https://cbic-gst.gov.in/sectoral-faq.html


## Latest GST/IPFT implementation checkpoint — 26 October 2026

- Implementation + synchronized GST decision commit b75a97f6cd0043c185375cc253b84a1e6d6bfea1 passed exact-head Backend CI [#40345937942](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 passed, 1 warning in 62.33s. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed.
- Estimate decision: use 18% on brokerage + combined transaction/IPFT exchange charges; add explicit demat charges for equity delivery. Count IPFT once. Exclude STT, stamp duty and SEBI from the published estimate base. API example GST mismatch is a docs-example inconsistency and does not override the current Upstox schedule.
- Actual invoice/per-fill GST acceptance remains separate and evidence-gated; actual component-set candidates stay DRAFT. Do not request a personal contract note. Safety: PAPER mandatory, live order writes/promotion/scheduling disabled, PR #6 draft/unmerged, original Tradepro untouched.


## Session checkpoint sync — 26 October 2026

- Exact-head Backend CI [#40368554399 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40368554399) passed on code head `9d3f255480da9a71980a9d3819fbb69a34835753`. Documentation-only synchronization is now creating newer commits; do not treat the new documentation head as green until its own CI completes.
- Statutory GST research: CBIC stock-broking FAQ and CGST Act section 15 / CGST Rules Rule 33 and Rule 27 are the legal framework. Rule 33 pure-agent exclusion is conditional on evidence, not an automatic classification for every charge. IGST Act section 12(12) provides stock-broking place of supply; compare supplier and place-of-supply states for IGST versus CGST+SGST. Sources: https://cbic-gst.gov.in/sectoral-faq.html ; https://cbic-gst.gov.in/valuation-rules.html
- Public GST schedule helper/tests are estimate-only. A statutory valuation engine and its tests are **not yet implemented**; GST/IPFT acceptance remains open. Next: implement Section 15 inclusion, Rule 33 evidence gates, state-based tax split, Decimal/paise rounding and fail-closed handling. IPFT combined/separate representation and DP/demat persistence/reconciliation remain open.
- No personal contract note is available or required. Safety: target only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER-only; live order writes disabled; original Tradepro out of scope.


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

## Verified checkpoint — 27 October 2026 (DP/demat completeness)

- Exact-head Backend CI #40459846143 passed on code/test commit `9400bc9aa221e2cf3b735e49a8e9a6d351237f02`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40459846143. Backend pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic PostgreSQL/document-volume restore checks passed.
- DP completeness regression is verified: invalid status cannot yield a complete total; `KNOWN` needs valid paise-exact amount; `NOT_APPLICABLE` needs no amount; unknown/inconsistent states fail closed. This checkpoint does not approve statutory tariff or invoice-level GST/IPFT composition.
- Next gate: per-fill source mapping, replay/idempotency conflicts, atomic rollback and component applicability. Actual contract-note and production Oracle backup/restore acceptance remain evidence-gated.
- Safety: PAPER mandatory, live broker writes disabled, PR #6/#7 Draft/unmerged; original `Tradepro` repo out of scope.

## Public-source review — 27 October 2026 (GST valuation and NSE IPFT)

- CBIC's stock-broking FAQ says CGST Act section 15 generally includes statutory taxes/levies, SEBI fees and stamp duty in the GST value, except where pure-agent treatment under Rule 33 is valid: https://cbic-gst.gov.in/sectoral-faq.html
- Section 15 statutory text: https://cbic-gst.gov.in/hindi/CGST-bill-e.html ; Rule 33 conditions: https://cbic-gst.gov.in/valuation-rules.html . Rule 33 must be evidence-driven and cannot be assumed merely because a charge is described as a reimbursement.
- NSE Finance & Accounts circular NSE/FA/73061 dated 27 February 2026 states revised member outflow effective 1 March 2026 for cash, equity futures and equity options, with a separately stated tiny IPFT contribution (₹0.01 per crore) and corresponding transaction-charge change: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf . This is an exchange/member schedule, not sufficient by itself to prove every broker's client invoice representation or every exchange/segment tariff.
- Zerodha's public IPFT explanation says NSE IPFT is included under exchange transaction charges in its contract note and lists separate segment rates, including currency segments: https://support.zerodha.com/category/account-opening/resident-individual/ri-charges/articles/ipft-charges . Treat this as corroboration for one broker's representation, not a universal broker rule. The code must map exchange + segment + trade date + source-field identity and reject duplicate transaction/IPFT mapping.
- GST line normalizer commit `57730a21da77fa583fe19c12740bd03eb779fed6` passed Backend CI [#40462246316](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40462246316); regression tests commit `4290b46e55275e4a005b3661da327adc1b216028` passed [#40462263615](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40462263615). Normalization accepts IGST or paired CGST+SGST and rejects mixed/incomplete/invalid lines; it does not decide rate, jurisdiction, taxable base, or source authenticity.
- Remaining acceptance: effective-dated, independently reviewed statutory rates and state/jurisdiction inputs; authoritative broker/exchange/segment IPFT mapping; prove no double-counting across transaction charge/IPFT source rows; maintain estimate versus actual invoice reconciliation as separate modes. Until reviewed rule rows are approved, estimate paths must remain labelled estimates and actual accounting fail closed.

## Newly identified GST-base conflict requiring policy resolution — 27 October 2026

- Cross-source comparison found a material discrepancy: the CBIC stock-broking FAQ says Section 15 value includes all taxes except GST unless Rule 33 pure-agent treatment applies, and explicitly discusses SEBI fees and stamp duty. Zerodha's public schedule states GST on brokerage + SEBI charges + transaction charges, while Upstox's published schedule describes GST on brokerage + transaction charges + demat (delivery only) + IPFT and does not list SEBI charges in that base.
- Sources: CBIC FAQ https://cbic-gst.gov.in/sectoral-faq.html (Levy Q7); Zerodha https://zerodha.com/charges/; Upstox https://upstox.com/brokerage-charges/ . The Upstox public schedule also lists GST/IPFT composition, while its charge API schema exposes separate GST, STT, stamp duty, transaction, IPFT, SEBI turnover and demat fields: https://upstox.com/developer/api-documentation/get-trade-charges/ . The API schema describes fields but is not proof that a particular endpoint supplies final per-fill actual values.
- Existing `upstox_gst_component_set_candidates()` remains DRAFT and currently lists brokerage + exchange charges (plus demat for equity delivery), not SEBI turnover charges. Do NOT approve or silently broaden this candidate based on inference. Legal interpretation of Section 15/Rule 33, actual broker invoice treatment and the source schedule discrepancy require independent review and a documented effective-dated decision.
- Safe implementation rule: retain source-backed estimates as broker-specific; do not assume the Upstox public schedule or Zerodha's GST base is universal. Until the discrepancy is resolved by reviewed policy, actual accounting must use reviewed source invoice/tax totals and fail closed for automated tax-base reconstruction when the needed evidence is absent.
