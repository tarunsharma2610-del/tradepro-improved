# SYNTHETIC UPSTOX-STYLE CONTRACT-NOTE FIXTURE — TEST DATA ONLY

**NOT ISSUED BY UPSTOX. NOT A REAL CONTRACT NOTE. NOT EVIDENCE OF A REAL TRADE.**

This generated fixture is for Tradepro Improved's parser, charge-ledger, and reconciliation tests. It uses invented identifiers and transactions and must never be presented as a genuine broker document.

## Example transaction

| Field | Synthetic value |
|---|---|
| Broker | Upstox-style example only |
| Trade date | 2026-10-22 (fictional test date) |
| Exchange / segment | NSE / Equity intraday |
| Instrument | TESTCO-EQ (fictional) |
| Buy | 100 shares at ₹100.00 |
| Sell | 100 shares at ₹101.00 |
| Buy turnover | ₹10,000.00 |
| Sell turnover | ₹10,100.00 |
| Total turnover | ₹20,100.00 |
| Gross P&L before charges | ₹100.00 |

## Illustrative charge calculation

The rates below are illustrative assumptions based on the publicly published Upstox brokerage/charges page checked while creating this fixture. This is **not** a guarantee of the broker's actual assessment for a specific date, exchange, scrip, or order. In particular, statutory rates and exchange charges can change; use date-effective rules in production.

| Component | Illustrative basis | Unrounded amount | Fixture amount |
|---|---|---:|---:|
| Brokerage | 0.1% of buy turnover + 0.1% of sell turnover, each below ₹20 cap | ₹20.100000 | ₹20.10 |
| STT | 0.025% of sell turnover | ₹2.525000 | ₹2.53 |
| Exchange transaction charges | 0.00307% of total turnover | ₹0.617070 | ₹0.62 |
| SEBI turnover fee | ₹10 per crore of total turnover | ₹0.020100 | ₹0.02 |
| Stamp duty | 0.003% of buy turnover | ₹0.300000 | ₹0.30 |
| GST | 18% of brokerage + transaction charges; rounded inputs shown above | ₹3.729073 | ₹3.73 |
| IPFT | Not separately charged in this fixture because current published tariff notes its combination with transaction charges | ₹0.00 | ₹0.00 |
| **Illustrative total** | Sum of displayed component amounts | — | **₹27.30** |
| **Illustrative net P&L** | ₹100.00 gross P&L − ₹27.30 charges | — | **₹72.70** |

**Rounding note:** this fixture intentionally records the displayed, per-component rounded values as its source-summary amounts. A broker may apply rounding at different stages, so the total is a test expectation for this fixture—not a claim about a real Upstox calculation. For production, prefer the authenticated broker charge response/actual note and versioned effective-date rules over this example.

## Suggested test fills and reviewed allocation

For deterministic allocation tests, model three synthetic eligible fills with source-notional weights 20%, 30%, and 50%. The reviewer-approved total component amount must be distributed using the application's configured paise-exact deterministic rounding algorithm. Do not assume the broker note itself proves those fill-level weights; they are an explicit synthetic test choice.

| Synthetic fill ID | Synthetic notional | Weight |
|---|---:|---:|
| TEST-FILL-001 | ₹4,020.00 | 20% |
| TEST-FILL-002 | ₹6,030.00 | 30% |
| TEST-FILL-003 | ₹10,050.00 | 50% |
| **Total** | **₹20,100.00** | **100%** |

The fixture is suitable for testing:
- import/parsing of a source-summary document;
- currency and component-total checks;
- deterministic paise rounding and allocation replay;
- tampering detection when an individual fill changes but the aggregate total does not;
- fail-closed behavior when evidence is missing, stale, or inconsistent.

It is **not** suitable for claiming real-document acceptance, verifying actual account-specific charges, or proving that a particular Upstox account made these trades.

## Public references

- Upstox brokerage and statutory charges: https://upstox.com/brokerage-charges/
- Upstox brokerage calculator: https://upstox.com/calculator/brokerage-calculator/
- Authenticated trade-charge summary API: https://upstox.com/developer/api-documentation/get-trade-charges/
- Authenticated brokerage calculation API: https://upstox.com/developer/api-documentation/get-brokerage/
