import pytest
from src.core.liquidity_exit_sizer import LiquidityExitSizer


def test_direct_exit_within_liquidity():
    sizer = LiquidityExitSizer(max_depth_impact_ratio=0.10)
    # خروج حجم 1.0 واحد زمانی که عمق اردربوک 100 واحد است (حداکثر مجاز: 10 واحد)
    res = sizer.calculate_exit_slices(total_quantity=1.0, orderbook_depth_qty=100.0, is_emergency=False)
    assert res["num_slices"] == 1
    assert res["execution_mode"] == "DIRECT_MARKET"
    assert res["slice_sizes"] == [1.0]


def test_sliced_exit_when_depth_is_thin():
    sizer = LiquidityExitSizer(max_depth_impact_ratio=0.05, min_slice_size=0.1)
    # حجم کل 10.0 واحد با عمق اردربوک 50.0 واحد -> حداکثر هر اسلایس = 2.5 واحد
    res = sizer.calculate_exit_slices(total_quantity=10.0, orderbook_depth_qty=50.0, is_emergency=False)
    assert res["num_slices"] == 4
    assert res["execution_mode"] == "SLICED_TWAP"
    assert sum(res["slice_sizes"]) == pytest.approx(10.0, 1e-5)
    assert res["slice_sizes"] == [2.5, 2.5, 2.5, 2.5]


def test_emergency_sweep_override():
    sizer = LiquidityExitSizer(max_depth_impact_ratio=0.05)
    # حتی اگر عمق بازار کم باشد، در وضعیت اضطراری باید یکجا خارج شود
    res = sizer.calculate_exit_slices(total_quantity=20.0, orderbook_depth_qty=10.0, is_emergency=True)
    assert res["num_slices"] == 1
    assert res["execution_mode"] == "EMERGENCY_SWEEP"
    assert res["slice_sizes"] == [20.0]
