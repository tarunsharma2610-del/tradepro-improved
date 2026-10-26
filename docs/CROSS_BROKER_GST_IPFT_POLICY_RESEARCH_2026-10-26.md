# Cross-broker GST and IPFT policy research — 2026-10-26

Status: source-backed research checkpoint; not yet an approved live-accounting tariff registry. Rates and policies must remain estimates/DRAFT until reviewed and reconciled to broker-specific invoice evidence. This research does not require the user's personal contract note.

## Decision summary

1. GST is 18% on the taxable value of the stock-broking service. Do not infer one universal GST component set across all brokers solely from the statutory rate.
2. Represent GST inputs as explicit, named components selected by a broker + exchange + segment + product + effective-date policy. Preserve the policy's source URL, retrieval date, hash, status and reviewer.
3. Keep statutory pass-throughs (STT, stamp duty and other government levies) separate from broker service charges. CBIC says GST is not payable on STT/stamp duty/other tax recoveries when the CGST Rule 33 pure-agent conditions are met; otherwise valuation must be determined under section 15 and Rule 27. This is conditional, not an unconditional exemption for every charge.
4. Treat IPFT as a semantic component, not an extra amount to add blindly. The exchange schedule may publish transaction charges inclusive of the tiny IPFT component or list transaction and IPFT separately. Store one representation mode (COMBINED or SEPARATE) and never charge both representations for the same scope/date.
5. For actual invoice accounting, source-reported GST and source charge rows remain the authority. A public calculator or API estimate is not evidence of the actual per-fill charge. Aggregate-only API fields must not be silently split into per-fill values.
6. Do not activate any candidate tariff until independent review and exact-scope approval. Unknown/null is not zero.

## Source findings

### NSE transaction charges and IPFT from 2026-03-01

NSE circular NSE/FA/73061, dated 2026-02-27, effective 2026-03-01, sets the total trading-member outflow to:
- Cash market: ₹307 per crore per side = transaction charge ₹306.99 + IPFT ₹0.01.
- Equity futures: ₹183 per crore per side = transaction charge ₹182.99 + IPFT ₹0.01.
- Equity options: ₹3,553 per crore of premium per side = transaction charge ₹3,552 + IPFT ₹0.01.

This replaces the older split (₹297 + ₹10; ₹173 + ₹10; ₹3,503 + ₹50). Do not add the old IPFT rates on top of the new combined total.

Source: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf

### Published broker GST descriptions differ

- Upstox publishes GST as 18% on brokerage + transaction charges + demat charges for equity delivery + IPFT. Its exchange-charge page says IPFT is combined with transaction charges from 2026-03-01. For an estimate, the canonical exchange charge must therefore contain transaction/IPFT once; delivery DP/demat charge is a distinct component.
  Sources: https://upstox.com/brokerage-charges/ and https://upstox.com/developer/api-documentation/get-brokerage/
- Zerodha publishes GST as 18% of brokerage + SEBI charges + transaction charges. It separately describes IPFT contribution amounts, so do not assume the Upstox component set is interchangeable with Zerodha's published formula.
  Source: https://zerodha.com/charges/
- Angel One publishes NSE transaction charge rates of 0.0030699% for equity cash, 0.0018299% for futures and 0.0355299% for options, and lists IPFT separately as a row. This presentation must be reconciled with the NSE circular's effective-dated split before using it in a calculation; do not blindly add its separate IPFT row to a rate that already includes it.
  Source: https://www.angelone.in/exchange-transaction-charges
- Groww's calculator labels its charges tentative and directs users to the contract note for exact charges. This supports using public calculators as estimates only, not actual accounting evidence.
  Source: https://groww.in/calculators/brokerage-calculator
- Dhan's published pricing/calculator describes its own component base and calls calculator values estimates. Preserve its own sourced component set and effective date rather than borrowing Upstox/Zerodha policy.

## Legal GST boundary

CBIC's stock-broking sectoral FAQ says GST is not payable on recoveries of STT, stamp duty or other central/state taxes when the conditions for a pure agent under Rule 33 are met; otherwise valuation is under CGST Act section 15 and Rule 27. The implementation must not automatically treat every exchange-related line as a pure-agent reimbursement: the broker's legal treatment, invoice line and documented tariff policy matter.

Sources:
- https://cbic-gst.gov.in/sectoral-faq.html
- https://cbic-gst.gov.in/valuation-rules.html

## Required implementation contract

A GST estimate policy must be selected by:
- broker;
- exchange;
- segment and product;
- trade date / effective window;
- named component set (not free-form string parsing);
- IPFT representation mode and its effective window;
- source URL, retrieval date and source hash;
- review state.

Validation rules:
- Exactly one approved policy may match. Zero or multiple matches fail closed.
- COMBINED exchange charges prohibit an additional IPFT amount for the same scope.
- SEPARATE mode requires separately sourced transaction and IPFT values; combined totals are not accepted as a second input.
- STT and stamp duty remain outside the GST base when documented as qualifying pure-agent recoveries; no blanket assumption is allowed where the broker's invoice treatment differs.
- DP/demat charges are stored separately and included only when the broker/product's published rule explicitly includes them.
- Round GST to paise using the documented rounding convention and test boundary cases.
- For actual accounting, preserve the actual GST line and source provenance; never recompute an actual invoice amount from a public estimate and call it verified.
- Tariff candidates remain DRAFT until independently reviewed. This document does not approve live rates.

## Open gates (do not hide these)

1. Implement a cross-broker, effective-dated GST policy registry and component calculator, backed by tests.
2. Add canonical demat/DP component support to persistence, total-charge calculations and migrations, or explicitly keep actual delivery accounting blocked until that support exists.
3. Add a broker-specific IPFT representation resolver so combined vs separate schedules cannot double count.
4. Verify exact-head CI on implementation and documentation commits.
5. Keep PR #6 Draft/unmerged, PAPER mandatory and all live broker writes disabled. Do not modify the original tarunsharma2610-del/Tradepro repository.


## Review of user-supplied Upstox parsing/GST notes — 2026-10-26

The supplied notes are useful as **parser test scenarios and schema-design prompts**, but are not authoritative tax evidence. Some statements conflict with Upstox's currently published charge page and must not be imported as approved rules.

Verified against Upstox's public pricing page (retrieved 2026-10-26):
- The published GST description is 18% on brokerage + transaction charges + IPFT, with demat charges additionally included for equity delivery. The page does **not** list SEBI turnover fees in that stated GST base. Therefore, the supplied claim that Upstox retail GST must include SEBI turnover fees is not accepted by this implementation; actual invoice evidence or authoritative clarification would be needed to override the published wording.
- From 2026-03-01, Upstox says IPFT is combined with transaction charges. The parser must preserve an explicit IPFT row if it appears in an actual source, but policy resolution must prevent double counting when the transaction line is already combined. Do not assume that every PDF layout is the same.
- Upstox currently publishes DP charges of ₹20 per scrip per day on delivery sells, and its GST formula says demat charges are included for delivery. The supplied ₹18.50 base/₹21.83 total is not adopted as the current public estimate rule. DP charges must remain a distinct canonical component for actual accounting.
- The supplied examples for Zerodha, Groww, Angel One, MCX, NSE-CD and Orbis are not sufficient to approve their component/tax rules. They remain unverified examples until checked against each broker's current dated public tariff and applicable exchange/regulatory sources. No institutional clearing profile should be inferred for a retail Upstox account.

A conservative text extractor was added at `backend/app/services/upstox_contract_note_text_extractor.py` with regression tests. It recognizes common labels and segment tags, retains original lines and line numbers, flags duplicate components, and surfaces charge-like unmapped lines. It deliberately does **not** infer a GST base, sum duplicate rows, map unknown labels silently, or approve accounting. Regexes are extraction aids only; PDF layout, page/source locator, original bytes and SHA-256 must be retained by the caller for evidence review.

Open implementation gate: the existing canonical accounting model still supports only six components and explicitly blocks `demat_transaction_charges`. Do not accept actual delivery accounting until canonical DP/demat persistence, total-charge recomputation, migration, idempotency, and delivery/non-delivery regression tests are implemented and pass. The Upstox public estimate helper was also changed so it no longer creates an `APPROVED` accounting policy internally; estimate source status remains separate from accounting approval.

Sources: [Upstox brokerage charges](https://upstox.com/brokerage-charges/) (public component formula, post-2026-03-01 combined IPFT wording and ₹20 DP charge); [Upstox trades charges API](https://upstox.com/developer/api-documentation/get-trade-charges/) (returns transaction, clearing, IPFT, SEBI turnover and demat transaction fields but is not by itself per-fill invoice proof); [NSE circular effective 2026-03-01](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf); [CBIC sectoral FAQ](https://cbic-gst.gov.in/sectoral-faq.html).

CI status for these new extractor/approval-boundary changes: pending exact-head verification until the relevant workflow run completes.
