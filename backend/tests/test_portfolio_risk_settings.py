from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.portfolio import PortfolioRiskSettings


def test_enabled_portfolio_risk_controls_require_at_least_one_limit():
    with pytest.raises(ValidationError, match="Enable at least one risk limit"):
        PortfolioRiskSettings(risk_controls_enabled=True)


def test_manual_portfolio_settings_accept_valid_limits_and_name():
    payload = PortfolioRiskSettings(
        name="Intraday portfolio",
        risk_controls_enabled=True,
        max_daily_loss=Decimal("1500"),
        max_open_exposure=Decimal("25000"),
        max_order_value=Decimal("5000"),
        max_open_positions=4,
        max_orders_per_day=12,
    )
    assert payload.name == "Intraday portfolio"
    assert payload.risk_controls_enabled is True
    assert payload.max_daily_loss == Decimal("1500")
    assert payload.max_open_positions == 4


def test_partial_settings_update_does_not_force_unspecified_defaults():
    payload = PortfolioRiskSettings(name="Renamed portfolio")
    assert payload.model_dump(exclude_unset=True) == {"name": "Renamed portfolio"}


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_daily_loss", 0),
        ("max_open_exposure", -1),
        ("max_order_value", 0),
        ("max_open_positions", 0),
        ("max_orders_per_day", 0),
    ],
)
def test_portfolio_risk_limits_must_be_positive(field, value):
    with pytest.raises(ValidationError):
        PortfolioRiskSettings(**{field: value})
