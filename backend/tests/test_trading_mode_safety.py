import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_trading_mode_is_normalized_to_paper():
    assert Settings(TRADING_MODE="paper").TRADING_MODE == "PAPER"
    assert Settings(TRADING_MODE=" PAPER ").TRADING_MODE == "PAPER"


@pytest.mark.parametrize("mode", ["LIVE", "live", "SIMULATION", "", "PAPER_LIVE", "true"])
def test_non_paper_trading_modes_fail_closed(mode):
    with pytest.raises(ValidationError, match="PAPER-only"):
        Settings(TRADING_MODE=mode)


def test_default_trading_mode_is_paper():
    assert Settings().TRADING_MODE == "PAPER"
