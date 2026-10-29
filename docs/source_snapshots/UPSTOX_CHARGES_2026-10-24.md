<!-- Phase 3 continuation sync: 27 October 2026. Latest verified code/test head: 31ce2a10bcc789c223608c6566082b24aea7358c; Backend CI #40383076131 SUCCESS. Previous maintained-doc synchronization head fbcefc1ae44f863b5d16d5e32fd819d277b0ead8 has documentation CI #40384521664 SUCCESS. DP/demat Execution persistence and central charge-total recomputation are implemented; next gate is focused audit of unknown-vs-zero semantics, delivery/non-delivery rules, migration round-trips, idempotency, rollback, and integration with per-fill allocation/reconciliation. GST/IPFT implementation is not being restarted. PR #6/#7 stay Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro repository out of scope. -->

# Official charge-source excerpt snapshot — 2026-10-24

**Purpose:** source research record only. This is a normalized excerpt of the pages below, not a byte-for-byte archive of their HTML. Rates are not active in the application.

**SHA-256 of canonical JSON payload:** `c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420`  
Canonicalization: UTF-8 JSON, sorted object keys, compact separators, no ASCII escaping.

## Sources and extracted observations

### Upstox brokerage and charges
Source: https://upstox.com/brokerage-charges/  
Retrieved: 2026-10-24

- Brokerage: equity delivery ₹20 per executed order.
- Equity intraday: ₹20 per executed order or 0.1% of the applicable base, whichever is lower.
- Equity futures: ₹20 per executed order or 0.05% of the applicable base, whichever is lower.
- Equity options: flat ₹20 per executed order.
- STT/CTT from 1 April 2026: equity delivery 0.1% buy and sell; intraday 0.025% sell-side; equity futures 0.05% sell-side; equity options 0.15% sell-side on premium; exercised-option sales 0.15%.
- GST is 18%. Upstox lists the delivery base as brokerage + transaction + demat + IPFT, and intraday/futures/options as brokerage + transaction + IPFT.
- Stamp duty listed: delivery 0.015% buyer-side; intraday 0.003% buyer-side; futures 0.002% buyer-side; options 0.003% buyer-side.
- Transaction charges from 1 March 2026: NSE delivery/intraday 0.00307%; NSE futures 0.00183%; NSE options 0.03553% on premium; BSE options 0.0325%; BSE delivery/intraday varies by scrip group; BSE futures nil.
- IPFT listed as ₹0.01 per crore of traded value plus GST; options use premium value.
- DP charges listed as ₹20 per scrip per day for sell-side equity delivery only.
- SEBI turnover charges listed as ₹10 per crore.

### NSE STT reference
Source: https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax  
Retrieved: 2026-10-24

- Effective 1 April 2026: option sale 0.15% seller on premium; exercised option 0.15% purchaser on intrinsic value; futures sale 0.05% seller.
- The source explicitly distinguishes the new effective date from rates up to 31 March 2026.

### NSE stamp duty reference
Source: https://www.nseindia.com/static/invest/first-time-investor-stamp-duty-charges-taxes  
Retrieved: 2026-10-24

- Listed rates: delivery securities 0.015% buyer; non-delivery 0.003% buyer; equity futures 0.002% buyer; equity options 0.003% buyer.
- The page shows an update date of 3 October 2023. Treat it as corroborative background only; obtain a more current statutory confirmation before activating rules.

## Canonical JSON payload whose UTF-8 bytes are hashed

```json
{
  "retrieved_on": "2026-10-24",
  "sources": [
    {
      "url": "https://upstox.com/brokerage-charges/",
      "observations": [
        "Brokerage: equity delivery INR 20 per executed order.",
        "Brokerage: equity intraday INR 20 per executed order or 0.1 percent, whichever is lower.",
        "Brokerage: equity futures INR 20 per executed order or 0.05 percent, whichever is lower.",
        "Brokerage: equity options flat INR 20 per executed order.",
        "STT/CTT effective 2026-04-01: equity delivery 0.1 percent buy and sell; intraday 0.025 percent sell; equity futures 0.05 percent sell; equity options 0.15 percent sell on premium; exercised-option sales 0.15 percent.",
        "GST 18 percent: delivery base brokerage + transaction + demat + IPFT; intraday/futures/options base brokerage + transaction + IPFT.",
        "Stamp duty: delivery 0.015 percent buyer; intraday 0.003 percent buyer; futures 0.002 percent buyer; options 0.003 percent buyer.",
        "Transaction charges effective 2026-03-01: NSE delivery/intraday 0.00307 percent; NSE futures 0.00183 percent; NSE options 0.03553 percent on premium; BSE options 0.0325 percent; BSE delivery/intraday scrip-group specific; BSE futures nil.",
        "IPFT: INR 0.01 per crore traded value + GST; options use premium value.",
        "DP charge: INR 20 per scrip per day on sell-side equity delivery only.",
        "SEBI turnover charges: INR 10 per crore."
      ]
    },
    {
      "url": "https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax",
      "observations": [
        "STT effective 2026-04-01: sale of option 0.15 percent seller on option premium; exercised option 0.15 percent purchaser on intrinsic value; sale of futures 0.05 percent seller.",
        "The NSE page distinguishes rates effective 2026-04-01 from rates up to 2026-03-31."
      ]
    },
    {
      "url": "https://www.nseindia.com/static/invest/first-time-investor-stamp-duty-charges-taxes",
      "observations": [
        "Stamp duty table: delivery securities 0.015 percent buyer; non-delivery 0.003 percent buyer; equity futures 0.002 percent buyer; equity options 0.003 percent buyer.",
        "NSE page says stamp duty is collected through clearing corporations and shows update date 2023-10-03; corroboration with a more current statutory source is required before activation."
      ]
    }
  ]
}
```

## Activation gate

- [x] Current official Upstox page captured as a dated normalized excerpt.
- [x] STT rows cross-checked against NSE's official derivatives STT page.
- [ ] Archive original HTML/PDF bytes where possible and hash those original bytes separately.
- [ ] Independently corroborate stamp duty and all applicable statutory rates.
- [ ] Define exact segment/product/side/calculation base and effective-date boundaries for each component.
- [ ] Add boundary tests and obtain reviewer approval.
- [ ] Keep candidate rules DRAFT and tariff-driven automatic allocation disabled until all gates pass.
