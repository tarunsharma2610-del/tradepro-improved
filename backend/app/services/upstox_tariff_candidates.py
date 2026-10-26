"""DRAFT Upstox tariff candidates extracted from dated public-source snapshot.

These rows are intentionally not APPROVED and select_tariff_rule must reject them.
They are a review/test inventory, not executable tariffs. Source snapshot:
docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md
"""
from dataclasses import dataclass
from datetime import date

from app.services.broker_tariff_rules import TariffRule

SOURCE_SNAPSHOT_SHA256 = "c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420"
UPSTOX_CHARGES_URL = "https://upstox.com/brokerage-charges/"
NSE_STT_URL = "https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax"
RETRIEVED_ON = date(2026, 10, 24)



@dataclass(frozen=True)
class GSTComponentSetCandidate:
    """Non-executable, source-backed GST component-set candidate.

    These component sets are review inventory only. They do not determine legal
    tax treatment and must not be passed to the calculator as approved sets.
    """
    broker: str
    exchanges: tuple[str, ...]
    segment: str
    product: str
    taxable_components: tuple[str, ...]
    rate_percent: str
    source_url: str
    observed_on: date
    source_snapshot_sha256: str
    review_status: str = "DRAFT"


def upstox_gst_component_set_candidates() -> tuple[GSTComponentSetCandidate, ...]:
    """Return DRAFT GST-base candidates from Upstox's published charge schedule.

    IPFT is represented inside canonical exchange_charges because the published
    Upstox schedule says IPFT is combined with transaction charges. The
    delivery-only demat addition is explicit. No candidate is approved.
    """
    observed_on = date(2026, 10, 24)
    common = ("brokerage", "exchange_charges")
    return (
        GSTComponentSetCandidate(
            "Upstox", ("NSE", "BSE"), "EQ", "DELIVERY",
            common + ("demat_charges",), "18", UPSTOX_CHARGES_URL,
            observed_on, SOURCE_SNAPSHOT_SHA256,
        ),
        GSTComponentSetCandidate(
            "Upstox", ("NSE", "BSE"), "EQ", "INTRADAY",
            common, "18", UPSTOX_CHARGES_URL, observed_on, SOURCE_SNAPSHOT_SHA256,
        ),
        GSTComponentSetCandidate(
            "Upstox", ("NSE", "BSE"), "FO", "FUTURES",
            common, "18", UPSTOX_CHARGES_URL, observed_on, SOURCE_SNAPSHOT_SHA256,
        ),
        GSTComponentSetCandidate(
            "Upstox", ("NSE", "BSE"), "FO", "OPTIONS",
            common, "18", UPSTOX_CHARGES_URL, observed_on, SOURCE_SNAPSHOT_SHA256,
        ),
    )


def upstox_tariff_candidate_rules() -> tuple[TariffRule, ...]:
    """Return effective-dated research candidates, all DRAFT and non-selectable."""
    rules = [
        # STT rows corroborated by the NSE derivatives STT page and Upstox tariff page.
        TariffRule("stt", "Upstox", "NSE", "EQ", "DELIVERY", "BUY", "TURNOVER",
                   "0.1", "PERCENT", date(2023, 4, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("stt", "Upstox", "NSE", "EQ", "DELIVERY", "SELL", "TURNOVER",
                   "0.1", "PERCENT", date(2023, 4, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("stt", "Upstox", "NSE", "EQ", "INTRADAY", "SELL", "TURNOVER",
                   "0.025", "PERCENT", date(2023, 4, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("stt", "Upstox", "NSE", "FO", "FUTURES", "SELL", "TURNOVER",
                   "0.05", "PERCENT", date(2026, 4, 1), None, NSE_STT_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("stt", "Upstox", "NSE", "FO", "FUTURES", "SELL", "TURNOVER",
                   "0.02", "PERCENT", date(2024, 10, 1), date(2026, 3, 31), UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("stt", "Upstox", "NSE", "FO", "OPTIONS", "SELL", "PREMIUM",
                   "0.15", "PERCENT", date(2026, 4, 1), None, NSE_STT_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("stt", "Upstox", "NSE", "FO", "OPTIONS", "SELL", "PREMIUM",
                   "0.1", "PERCENT", date(2024, 10, 1), date(2026, 3, 31), UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("stt", "Upstox", "NSE", "FO", "OPTIONS_EXERCISED", "BUY", "INTRINSIC_VALUE",
                   "0.15", "PERCENT", date(2026, 4, 1), None, NSE_STT_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),

        # Rates below are the published combined NSE outflow from 2026-03-01
        # (transaction charge + NSE IPFT contribution), corroborated by NSE
        # Circular NSE/FA/73061. Do not add legacy ₹10/₹50 per-crore IPFT
        # values on top. Rows remain DRAFT until account/API/contract-note
        # reconciliation and independent scope review are complete.
        TariffRule("exchange_charges", "Upstox", "NSE", "EQ", "DELIVERY", "BUY", "TURNOVER",
                   "0.00307", "PERCENT", date(2026, 3, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("exchange_charges", "Upstox", "NSE", "EQ", "DELIVERY", "SELL", "TURNOVER",
                   "0.00307", "PERCENT", date(2026, 3, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("exchange_charges", "Upstox", "NSE", "EQ", "INTRADAY", "BUY", "TURNOVER",
                   "0.00307", "PERCENT", date(2026, 3, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("exchange_charges", "Upstox", "NSE", "EQ", "INTRADAY", "SELL", "TURNOVER",
                   "0.00307", "PERCENT", date(2026, 3, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("exchange_charges", "Upstox", "NSE", "FO", "FUTURES", "BUY", "TURNOVER",
                   "0.00183", "PERCENT", date(2026, 3, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("exchange_charges", "Upstox", "NSE", "FO", "FUTURES", "SELL", "TURNOVER",
                   "0.00183", "PERCENT", date(2026, 3, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("exchange_charges", "Upstox", "NSE", "FO", "OPTIONS", "BUY", "PREMIUM",
                   "0.03553", "PERCENT", date(2026, 3, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("exchange_charges", "Upstox", "NSE", "FO", "OPTIONS", "SELL", "PREMIUM",
                   "0.03553", "PERCENT", date(2026, 3, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("exchange_charges", "Upstox", "BSE", "FO", "OPTIONS", "BUY", "PREMIUM",
                   "0.0325", "PERCENT", date(2026, 3, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
        TariffRule("exchange_charges", "Upstox", "BSE", "FO", "OPTIONS", "SELL", "PREMIUM",
                   "0.0325", "PERCENT", date(2026, 3, 1), None, UPSTOX_CHARGES_URL,
                   RETRIEVED_ON, SOURCE_SNAPSHOT_SHA256, "DRAFT"),
    ]
    return tuple(rules)
