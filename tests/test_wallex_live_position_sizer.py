import pytest
from src.core.wallex_live_position_sizer import WallexLivePositionSizer

@pytest.fixture
def sizer():
    return WallexLivePositionSizer(
        max_capital_allocation=20.0,
        risk_per_trade_pct=0.02,
        min_order_notional=5.0,
        taker_fee_pct=0.0025
    )

def test_sizer_rejects_insufficient_balance(sizer):
    res = sizer.compute_size(account_balance=3.0, entry_price=100.0, stop_loss_price=95.0)
    assert res["allowed"] is False
    assert res["reason"] == "BALANCE_BELOW_MIN_NOTIONAL"
    assert res["size"] == 0.0

def test_sizer_rejects_invalid_zero_price(sizer):
    res = sizer.compute_size(account_balance=15.0, entry_price=0.0, stop_loss_price=95.0)
    assert res["allowed"] is False
    assert res["reason"] == "INVALID_PRICES"

def test_sizer_calculates_micro_allocation(sizer):
    # Total balance is 50 USDT, but allocation caps at 20 USDT
    res = sizer.compute_size(account_balance=50.0, entry_price=10.0, stop_loss_price=9.5)
    assert res["allowed"] is True
    assert res["reason"] == "SIZE_CALCULATED_SUCCESSFULLY"
    assert res["notional"] >= 5.0
    assert res["notional"] <= 20.0
    assert res["size"] > 0.0

def test_sizer_enforces_min_order_notional(sizer):
    # Tight stop loss would yield tiny size, but sizer ensures min notional threshold
    res = sizer.compute_size(account_balance=15.0, entry_price=100.0, stop_loss_price=99.9)
    assert res["allowed"] is True
    assert res["notional"] >= 5.0
