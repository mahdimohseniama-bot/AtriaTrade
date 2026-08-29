import pytest
from src.core.dynamic_leverage_engine import DynamicLeverageEngine

@pytest.fixture
def engine():
    return DynamicLeverageEngine(max_risk_per_trade_pct=0.02, max_leverage=10.0)

def test_invalid_input(engine):
    res = engine.calculate_sizing(0, 100, 95, 50)
    assert res["status"] == "INVALID_INPUT"

def test_normal_sizing_calculation(engine):
    # Account: 1000 USDT, Risk 2% = 20 USDT max loss
    # Entry: 100, SL: 98 (2% move)
    # Margin: 100 USDT -> Desired nominal = 20 / 0.02 = 1000 USDT -> Leverage = 10x
    res = engine.calculate_sizing(
        account_equity=1000.0,
        entry_price=100.0,
        stop_loss_price=98.0,
        allocated_margin=100.0
    )
    assert res["status"] == "CALCULATED"
    assert res["effective_leverage"] == 10.0
    assert res["nominal_position_value"] == 1000.0
    assert res["potential_loss"] == 20.0
    assert res["risk_pct_of_equity"] == 2.0

def test_leverage_clamping_on_tight_sl(engine):
    # Very tight SL (0.5% move). Theoretical leverage would be 40x, but capped at 10x.
    res = engine.calculate_sizing(
        account_equity=1000.0,
        entry_price=100.0,
        stop_loss_price=99.5,
        allocated_margin=100.0
    )
    assert res["status"] == "CALCULATED"
    assert res["effective_leverage"] == 10.0
    assert res["potential_loss"] <= 20.0
