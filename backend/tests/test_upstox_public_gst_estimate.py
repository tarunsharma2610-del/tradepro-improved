from datetime import date
from decimal import Decimal

import pytest

from app.services.upstox_public_gst_estimate import (
    PUBLIC_SCHEDULE_ESTIMATE_ONLY,
    calculate_upstox_public_gst_estimate,
)


def test_nse_option_estimate_includes_combined_transaction_ipft_once():
    estimate = calculate_upstox_public_gst_estimate(
        trade_date=date(2026, 3, 1),
        exchange="NSE",
        segment="FO",
        product="OPTIONS",
        taxable_components={
            "brokerage": Decimal("0.00"),
            "exchange_charges": Decimal("5.85"),
        },
    )
    assert estimate.source_kind == PUBLIC_SCHEDULE_ESTIMATE_ONLY
    assert estimate.taxable_base == Decimal("5.85")
    assert estimate.gst_amount == Decimal("1.05")
    assert estimate.taxable_components == ("brokerage", "exchange_charges")
    assert "ipft" not in estimate.taxable_components


def test_equity_delivery_estimate_requires_explicit_demat_component():
    estimate = calculate_upstox_public_gst_estimate(
        trade_date=date(2026, 10, 26),
        exchange="NSE",
        segment="EQ",
        product="DELIVERY",
        taxable_components={
            "brokerage": Decimal("20.00"),
            "exchange_charges": Decimal("0.31"),
            "demat_charges": Decimal("20.00"),
        },
    )
    assert estimate.taxable_base == Decimal("40.31")
    assert estimate.gst_amount == Decimal("7.26")


@pytest.mark.parametrize(
    "components",
    [
        {"brokerage": "0.00", "exchange_charges": "5.68", "ipft": "0.17"},
        {"brokerage": "0.00"},
        {"brokerage": "0.00", "exchange_charges": "5.68", "sebi_charges": "0.01"},
    ],
)
def test_estimate_rejects_separate_ipft_missing_or_unreviewed_components(components):
    with pytest.raises(ValueError, match="exactly match"):
        calculate_upstox_public_gst_estimate(
            trade_date=date(2026, 3, 1),
            exchange="NSE",
            segment="FO",
            product="OPTIONS",
            taxable_components=components,
        )


def test_estimate_rejects_pre_boundary_and_unsupported_exchange_scope():
    with pytest.raises(ValueError, match="from 2026-03-01"):
        calculate_upstox_public_gst_estimate(
            trade_date=date(2026, 2, 28),
            exchange="NSE",
            segment="FO",
            product="OPTIONS",
            taxable_components={"brokerage": "0.00", "exchange_charges": "5.85"},
        )
    with pytest.raises(ValueError, match="outside the reviewed"):
        calculate_upstox_public_gst_estimate(
            trade_date=date(2026, 3, 1),
            exchange="BSE",
            segment="EQ",
            product="DELIVERY",
            taxable_components={
                "brokerage": "20.00",
                "exchange_charges": "0.31",
                "demat_charges": "20.00",
            },
        )


def test_gst_estimate_does_not_claim_actual_billing_or_approve_actual_candidates():
    from app.services.upstox_tariff_candidates import upstox_gst_component_set_candidates

    estimate = calculate_upstox_public_gst_estimate(
        trade_date=date(2026, 3, 1),
        exchange="NSE",
        segment="EQ",
        product="INTRADAY",
        taxable_components={"brokerage": "20.00", "exchange_charges": "0.31"},
    )
    assert estimate.source_kind == "PUBLIC_SCHEDULE_ESTIMATE_ONLY"
    assert all(candidate.review_status == "DRAFT" for candidate in upstox_gst_component_set_candidates())
