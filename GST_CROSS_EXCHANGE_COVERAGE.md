# GST Cross-Exchange Coverage Matrix

Updated: 27 October 2026

## Design decision

NSE, BSE and MCX use one statutory GST valuation/tax-split engine. The engine
does not own exchange tariff rates. An upstream, effective-dated tariff/source
layer must determine each actual fee, the component's applicability, its basis,
and whether that amount belongs in the GST taxable value. Never reuse one
exchange's transaction-charge or IPFT rate as another exchange's rate.

The statutory engine uses the Section 15 default valuation, allows a Rule 33
pure-agent exclusion only when all required evidence flags are satisfied, and
splits IGST versus CGST+SGST from explicit supplier and place-of-supply state
codes. The output is a calculation result, not evidence that the source inputs
or a broker invoice were correct.

## Automated shared-engine coverage

`backend/tests/test_cross_exchange_gst_engine.py` exercises the same GST
engine across these synthetic product scopes and both intra-state/inter-state
tax modes:

| Exchange | Segments/products in test matrix |
|---|---|
| NSE | Equity delivery, equity intraday, equity F&O futures, equity F&O options |
| BSE | Equity delivery, equity intraday, equity F&O futures, equity F&O options |
| MCX | Commodity futures, commodity options |

The amounts in this test are deliberately synthetic. They prove that the same
tax engine and tax split work across product contexts; they are not exchange
tariff fixtures and do not prove tariff completeness. Rule 33 evidence behavior
is also tested independently of exchange.

## Official source register to maintain

- CBIC Sectoral FAQs, stock-broking questions 77–78: Section 15 treatment of
  statutory recoveries and brokerage GST: https://cbic-gst.gov.in/sectoral-faq.html
- CBIC Valuation Rules, Rule 33 pure-agent conditions:
  https://cbic-gst.gov.in/valuation-rules.html
- NSE equity/cash and equity-derivatives transaction charges and IPFT from
  1 March 2026: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- NSE commodity-derivatives transaction charges effective 1 April 2024:
  https://nsearchives.nseindia.com/content/circulars/FA61380.pdf
- BSE equity-derivatives notice 20240927-37 (effective 1 October 2024):
  https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20240927-37
- BSE equity segment master circular (29 April 2025):
  https://www.bseindia.com/markets/MarketInfo/DownloadAttach.aspx?attachedId=8a7fec3a-95bc-4bd2-82de-76e2a84e2915&id=20250429-51

## Still separately required before tariff-level acceptance

1. Build/review effective-dated charge rules for every enabled exchange × segment
   × product × side × charge component; do not assume the synthetic matrix proves
   these rates are populated.
2. Capture source document hash, effective dates, scope and independent approval
   for each active tariff rule. A missing or overlapping rule must fail closed.
3. Keep broker estimate, aggregate post-trade API output, and invoice-backed
   booked charge evidence as separate evidence classes.
4. Add source-backed golden invoice fixtures per exchange/broker as genuine notes
   become available. Do not invent per-fill charges or infer IPFT zero from an
   absent line item.

## Safety

This change does not enable live orders or live broker writes. PAPER mode remains
mandatory; PR #7 remains Draft/unmerged; only
`tarunsharma2610-del/tradepro-improved` is in scope.
