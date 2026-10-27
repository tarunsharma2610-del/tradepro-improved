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


## Cross-broker GST taxable-base comparison — 27 October 2026

This is a policy-evidence comparison, not approval of a universal component set or actual per-fill billing rule.

| Broker/source | Published GST base/presentation | Acceptance implication |
|---|---|---|
| CBIC stock-broking FAQ, Q77 | STT, stamp duty and other central/state tax recoveries are outside GST value only if CGST Rule 33 pure-agent conditions are met; otherwise Section 15 and Rule 27 valuation applies. | Legal default and evidence gate; never exclude a levy solely by its label. [CBIC FAQ](https://cbic-gst.gov.in/sectoral-faq.html) |
| Zerodha | Brokerage + SEBI charges + transaction charges; IPFT is separately described by segment and at current NSE rates. | SEBI is included in this broker's published base; do not copy the Upstox estimate component set. [Zerodha charges](https://zerodha.com/charges/) |
| Dhan | Brokerage + transaction charges + SEBI turnover + IPFT/other tax. | Explicitly includes SEBI and IPFT/other tax in published base; effective-date and exact invoice mapping still required. [Dhan pricing](https://dhan.co/pricing/) |
| FYERS | Current charges page states brokerage + exchange transaction + clearing + SEBI turnover + NSE IPFT. Its support article also describes a narrower base, so source-page/version discrepancy must be tracked. | Do not silently choose between conflicting FYERS pages; retain URL, retrieval date/version and reviewed source precedence. [FYERS charges](https://fyers.in/charges-list) · [FYERS support article](https://support.fyers.in/portal/en/kb/articles/what-are-the-statutory-charges-on-trades-at-fyers-stt-gst-sebi-turnover-fee-ipft-etc) |
| Upstox | Public schedule describes brokerage + transaction charges + IPFT, with DP/demat additionally for equity delivery; API example arithmetic conflicts with that wording. | Broker-specific estimate only; actual taxable base remains unapproved without authoritative reconciliation/clarification. [Upstox pricing](https://upstox.com/brokerage-charges/) · [Brokerage API example](https://upstox.com/developer/api-documentation/get-brokerage/) |
| Angel One | Public table lists transaction, IPFT, GST 18%, SEBI and stamp duty rows, but the surfaced table does not itself fully specify the GST base composition. | Treat as incomplete evidence for tax-base membership; do not infer membership just from rows being adjacent. [Angel One charges](https://www.angelone.in/exchange-transaction-charges) |

### Decision and implementation gate

- There is no safe universal hard-coded GST component list supported by these broker pages. Keep a broker + exchange + segment/product + effective-date + source-version policy registry; estimates and actual invoice reconciliation must be distinct modes.
- Model component identity separately from GST membership: transaction charge and IPFT can be combined or separate depending on exchange schedule, broker display and effective date. Enforce exactly-once inclusion and reject double mapping.
- STT/stamp duty exclusion requires an evidence-backed Rule 33 pure-agent determination for the relevant recovery; otherwise apply the reviewed Section 15/Rule 27 treatment. Do not turn this general rule into a blanket “always include”/“always exclude” without facts about the supply and pure-agent conditions.
- SEBI turnover, clearing, DP/demat and other line items must be explicitly included/excluded by reviewed broker-specific policy with provenance. Missing source field, conflicting public sources, unknown tax jurisdiction, or unresolved source precedence => unresolved/incomplete, not zero and not auto-approved.
- No actual GST candidate is promoted by this comparison. Next code gate is policy resolver + tests for effective-date/source-version conflicts, broker-specific component membership, Rule 33 evidence flags, combined/separate IPFT exactly-once handling and fail-closed missing facts.


## GST policy resolver hardening — 27 October 2026

- Audited existing `backend/app/services/broker_gst_component_policy.py` before changing it. It already provides effective-dated broker/exchange/segment/product selection, source URL/retrieval date/SHA-256 provenance, explicit combined/separate/not-applicable IPFT representation, exact component-set checking and an estimate-only calculation path. Avoid creating a parallel resolver.
- New code commit `eef5eebc1e1abfc37c92b4e50d5c35e9afddcbb4`: policy state `CONFLICT` now exists and any effective conflict for the exact scope/date blocks selection even if an approved policy also matches. This prevents silently preferring one of contradictory public sources.
- New test commit `761637aab1d5f36ed5bfc02ffb66ce8b31ab7820`: regression tests for a conflicting source blocking an approved candidate and for rejecting sub-paise component inputs rather than silently rounding them.
- The policy remains estimate-only. This does not approve any broker component set, does not integrate the statutory Rule 33 engine into actual accounting, and does not reconcile invoice-level GST. No broker policies are promoted to APPROVED by this change.
- Validation status: exact-head CI for these commits is not yet verified. Do not mark this increment green until the branch/PR workflow runs on the exact resulting head and all jobs pass. Next: inspect any CI result, fix failures, then synchronize maintained documents/checkpoint to the latest green head.


## Verified GST resolver hardening CI — 27 October 2026

- Service hardening commit `eef5eebc1e1abfc37c92b4e50d5c35e9afddcbb4` passed Backend CI [#40463452758](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463452758).
- Regression-test commit `761637aab1d5f36ed5bfc02ffb66ce8b31ab7820` passed Backend CI [#40463464076](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463464076). New coverage confirms an effective `CONFLICT` policy blocks selection despite an approved candidate, and sub-paise input is rejected.
- Documentation head `d604be9982dc9c37d3a4985abd89c85635b59106` passed Backend CI [#40463512765](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463512765). A newer checkpoint-only commit is pending its own exact-head CI; do not mark the latest branch head green until that run passes.
- The resolver is still estimate-only. No GST candidate or broker tariff has been promoted to approved actual accounting. PR #6/#7 remain Draft/unmerged, PAPER mandatory, live broker order writes disabled, original Tradepro repository out of scope.


## Confirmed statutory GST precision CI and resume point — 27 October 2026

- The initial code-only run for `58c841cb00f7f0137aece7bcd7c83d5a63ae81f9` failed because an older test still expected silent rounding of `0.025`. This was a test expectation conflict with the new fail-closed behavior, not an unresolved runtime regression in the final increment.
- Regression-test commit `c6e9dfb3e4cae6f93fd51a7f1f1facc86e7b804d` passed Backend CI [#40463868838 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463868838). It replaces the obsolete sub-paise rounding expectation with explicit rejection and a valid paise-precision test.
- Checkpoint commit `74015a285cb844a3735052d88cce9c2a2385e1ce` passed Backend CI [#40463883785 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463883785). This verifies the resulting head including the GST precision change, updated regression test and checkpoint document.
- Intermediate failed run: [#40463856382](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463856382); it was superseded by the successful regression and checkpoint runs above. Do not erase the failure from history; document the correction.
- Current implementation boundaries: statutory GST primitive applies Section 15 default inclusion and conditional Rule 33 pure-agent exclusion only when all modeled evidence flags are true; broker GST policy resolver remains an estimate-only source-specific path. Neither is yet a unified actual per-fill invoice acceptance path. No broker GST policy is approved here for actual accounting.
- Next Phase 3 task: audit the accounting charge reconciliation/promotion boundary and define a single reviewed path that consumes source-backed invoice line identities, statutory valuation evidence and effective-dated broker policy without letting estimates become actual ledger charges. If source provenance, Rule 33 facts, component identity, or GST invoice lines are missing/conflicting, actual accounting must fail closed. Add tests before integration; do not promote estimates or change live-trading safeguards.
- Safety unchanged: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope; PR #6/#7 Draft/unmerged; PAPER mode mandatory; live broker order writes disabled.


## Real-source statement reconciliation — 27 October 2026

A user-provided two-page statement image for derivatives trades has been reviewed as real-source evidence. The visible summary reports brokerage ₹1,000.00; transaction charges ₹111.61; SEBI fees ₹0.22; GST on brokerage ₹180.00; GST on charges ₹20.15; stamp duty ₹3.00; STT lines ₹0.32 (RND buy), ₹1.21 (RND sell), and ₹51.89 (SQUP); and total net value ₹4,487.73. The statement footnote says GST applies to the listed charges and that GST on SEBI fees became applicable from 18 July 2022.

### Reconciliation result

- ₹180.00 equals 18% of the reported ₹1,000.00 brokerage.
- The visible transaction + SEBI base is ₹111.61 + ₹0.22 = ₹111.83; 18% = ₹20.1294, rounded to ₹20.13, whereas the source reports ₹20.15. Preserve this ₹0.02 difference as a source variance; do not silently alter the actual tax line or infer a missing component.
- This is an aggregate summary by security/statement, not proof of per-execution-fill GST allocation.
- The visible statement does not identify IPFT as a separate line. Do not infer that IPFT is absent or included in transaction charges solely from this layout.
- The source image appears to be an older 2023-period statement. It is useful as historical source evidence, not as proof of 2026 tariffs or current broker billing.

### Implementation acceptance requirements from this evidence

1. Preserve actual GST source lines and source labels independently from computed estimate GST.
2. Reconcile GST-on-brokerage and GST-on-other-charges separately where the source does so.
3. Report a ₹0.02 mismatch for the visible GST-on-charges calculation as a reviewable variance, not a rounding tolerance or silent correction.
4. Do not promote aggregate statement totals as per-fill actuals without a reviewed source-to-fill allocation basis.
5. Treat IPFT as UNKNOWN when not explicitly identifiable; a null/missing IPFT API field is not zero.
6. Keep the current public estimate rule separate: Upstox publicly describes GST at 18% on brokerage + transaction + IPFT, plus DP/demat for equity delivery. The Upstox brokerage API sample exposes transaction ₹5.68, IPFT ₹0.17 and GST ₹1.02 (arithmetically matching 18% of transaction alone, not transaction+IPFT); its trade-charges API shows ipft:null. These API examples are documentation/API evidence, not actual invoice proof. See https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://support.zerodha.com/category/account-opening/resident-individual/ri-charges/articles/ipft-charges ; https://cbic-gst.gov.in/sectoral-faq.html.

Disposition: real-source review is now started using this statement. GST/IPFT estimate policy can be implemented separately, but actual per-fill tax acceptance remains blocked on a verified component/tax-base mapping and fill-level source relationship. Do not describe this historical statement alone as resolving IPFT or every broker's invoice treatment.


## Cross-broker and exchange source review — 27 October 2026

### What is confirmed

- **GST rate / valuation framework:** CBIC's stock-broking FAQ says GST applies to brokerage services and third-party recoveries such as STT/stamp duty are excluded only where CGST Rule 33 pure-agent conditions are met; otherwise valuation follows CGST Act section 15 and Rule 27. Place of supply for domestic stock-broking follows recipient address on broker records under IGST Act section 12(12). Sources: https://cbic-gst.gov.in/sectoral-faq.html and https://taxinformation.cbic.gov.in/content-page/explore-act/1000284/1000001.
- **NSE equity cash/futures/options effective 1 March 2026:** official NSE circular NSE/FA/73061 sets combined member outflow transaction + IPFT at ₹307/crore cash, ₹183/crore equity futures, and ₹3,553/crore equity options premium, each side. The detailed split is transaction ₹306.99 + IPFT ₹0.01 cash, ₹182.99 + ₹0.01 futures, and ₹3,552 + ₹0.01 options. Do not add the separate IPFT component again when using the combined total. Source: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf.
- **Broker presentation differs:** Upstox public pricing says transaction and IPFT are combined and GST is 18% on brokerage + transaction + IPFT, with DP/demat included for delivery. Zerodha says NSE IPFT is included under exchange transaction charges and lists GST as 18% of brokerage + SEBI + transaction charges. Groww's public pricing also presents GST on the brokerage/transaction/SEBI fee basket. These are broker-specific calculator/presentation policies and not a replacement for the statutory valuation analysis or actual invoice lines. Sources: https://upstox.com/brokerage-charges/ ; https://zerodha.com/charges/ ; https://groww.in/pricing ; https://support.zerodha.com/category/account-opening/resident-individual/ri-charges/articles/ipft-charges.
- **BSE/MCX are not interchangeable with NSE:** Zerodha's current exchange-charge explainer lists distinct NSE/BSE/MCX rates by segment; BSE rates vary by product/scrip group and index contract, while MCX commodity futures/options have their own schedules. BSE's 2025 equity master circular retains group-dependent cash transaction charges. Do not use NSE rates or NSE IPFT assumptions for BSE/MCX. Sources: https://support.zerodha.com/category/account-opening/resident-individual/ri-charges/articles/exchange-transaction-charges ; https://www.bseindia.com/markets/MarketInfo/DownloadAttach.aspx?attachedId=8a7fec3a-95bc-4bd2-82de-76e2a84e2915&id=20250429-51.

### Limits and implementation rule

Public sources establish the statutory framework and effective-dated exchange schedules; they do not establish one universal actual taxable base for every broker, contract-note layout, segment and tax invoice. The Upstox API example (transaction ₹5.68, IPFT ₹0.17, GST ₹1.02) remains inconsistent with applying 18% to the combined ₹5.85; `ipft:null` from an aggregate charges API remains UNKNOWN, not zero. The user's real statement has GST on charges ₹20.15 against visible transaction ₹111.61 + SEBI ₹0.22 = ₹111.83; expected 18% is ₹20.13. Preserve the ₹0.02 difference for review; no source found explains it conclusively.

Decision: implement reviewed, effective-dated **estimates** by broker/exchange/segment/product/date; keep source-reported actual GST separate; flag actual source variances; no automatic actual per-fill acceptance without source-to-fill mapping and approved tax-base evidence. Do not state that GST/IPFT actual billing is universally resolved by these public sources.


## 27 October 2026 continuation — API-first integration

User direction: stop repeating GST/IPFT research; wire the existing Upstox APIs into a safe accounting/reconciliation path. The read-only client already exposes `get_brokerage_estimate` (`/v2/charges/brokerage`, estimate only) and `get_trade_charges` (`/v2/trade/profit-loss/charges`, aggregate only). These client methods do not, by themselves, complete API-to-accounting integration. The next implementation must trace and connect the orchestration layer, exact approved field mappings, source provenance, and reconciliation service. Aggregate endpoint output must never be represented as actual per-fill charges or distributed across fills as if broker-confirmed. Null IPFT remains unknown, not zero; combined transaction/IPFT must be counted once. The ₹20.15 historical GST amount remains source-reported with the ₹0.02 visible-base variance preserved; cause unproven and not a blocker to API integration. GST public schedule remains estimate-only. Exact-head CI is pending for the upcoming code increment; do not mark the docs head green without it.


## 27 October 2026 — orchestration code increment

Added a typed Upstox charge API orchestration service and focused tests. The brokerage calculator is labelled estimate-only; the post-trade charges API is labelled aggregate-reconciliation-only; both explicitly reject per-fill-actual interpretation. API failures do not produce usable evidence, and null IPFT remains null/unknown. This is the first orchestration boundary, not full UI/accounting integration. The next gate is wiring it to the read-only reconciliation endpoint/ledger, while retaining exact approved mappings and keeping aggregate evidence out of per-fill promotion. CI on the new code/test head remains unverified; no green status is claimed.


## 27 October 2026 — authenticated API routes added

Added authenticated, read-only routes for Upstox brokerage estimates and aggregate trade-charge responses. Routes require the signed-in user's own connected Upstox connection and decrypt the token server-side; no token is returned. Estimate endpoint stays estimate-only, aggregate endpoint stays reconciliation-only, and both explicitly report no per-fill-actual eligibility. CI passed on the previous documentation head but is still running on the route/router commits; exact latest-head green is not yet established. Route-level tests, evidence-ledger integration review and exact-head CI remain gates.


## Route-level test increment — 27 October 2026

Added `backend/tests/test_upstox_charge_api_routes.py` for authenticated estimate/aggregate route semantics, null IPFT preservation, and request validation. Previous backend CI passed on doc head `24b7b9ee728049f26b200cbee54571ae3c22b7bf` (run #40473895336); the new test commit `ffb87c9af7c87d921eadf0198b7ba8704be65e76` requires its own CI result. Aggregate response remains reconciliation-only; no per-fill accounting promotion.


## Annual GST statement reconciliation finding — 27 October 2026

- A user-provided Upstox/RKSV annual global transaction statement for FY 2022–23 was reviewed as annual aggregate evidence, not as an individual contract note. Its visible charge rows do not, by themselves, reconcile the reported aggregate “IGST on Charges” line to a unique taxable base at paise precision.
- Preserve original source-row labels exactly. Do not relabel an STT rounding row as SEBI fees. Establish the taxable base from underlying invoice/contract-note lines and the applicable historical policy; do not choose a charge merely because it makes the arithmetic match.
- The GST reconciliation helper correctly retains reported-vs-expected variance instead of inferring or rewriting the base. A small annual variance may reflect invoice-level tax rounding/aggregation or a charge not visible in summarized lines; this annual statement alone cannot distinguish these explanations.
- Do not use an annual AGS total to approve actual per-fill GST or promote canonical charge allocations. Next evidence gate: an itemized individual contract note or underlying invoice-level breakdown. Keep FY 2022–23 evidence separate from the 2026 public-schedule estimate policy.
- This is an evidence-scope clarification, not a change to GST/IPFT policy or a declaration that the broker billed incorrectly. No personal identifiers or account-specific figures are copied into this repository note.
- Latest code/test head remains `9eb278588b78d2a966cc196c15d7a4d9a6ae8868`; Backend CI [#40505176395 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40505176395). This documentation sync creates a new head and requires its own exact-head CI before it is marked green.
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` out of scope; PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes disabled.

## Historical Upstox invoice evidence — 27 October 2026

- User-provided text for five January 2023 daily contract notes explicitly gives taxable value as brokerage + transaction charges + SEBI fees. The disclosed brokerage GST and GST on charges reproduce at 18%, rounded to paise, for all five dates.
- Regression fixture: `backend/tests/test_historical_upstox_contract_note_gst.py`; commits `98f14aef1b3b541c2a6e07beb227b6f3f0471a42` and `547917868d28d3f46f1f549a8daa50d57fc4542d`.
- The transcribed daily notes do not separately label IPFT. This does not prove zero IPFT and does not establish whether it was bundled within the transaction/other-charge figure. Keep this unknown distinct from zero; don't force a per-fill allocation from a daily aggregate.
- The annual statement's displayed GST-on-charges differs by ₹0.02 from recomputing 18% solely from its rounded displayed transaction charges + SEBI fees. Treat this as an aggregate reconciliation variance, not evidence of broker error; don't insert an arbitrary two-paise adjustment. Daily invoice cases reconcile.
- Effective-dated IPFT tariff and GST policy must remain distinct from the current Upstox calculator estimate. Exact-head CI for the fixture and documentation refresh is pending verification.
