import pytest
from src.core.execution_realism import (
    ExecutionRealismModel,
    FeeConfig,
    SlippageConfig,
    SlippageModelType,
    LatencyConfig,
    ExecutionResult
)

def test_default_execution():
    model = ExecutionRealismModel()
    res = model.apply_realism(price=100.0, quantity=1.0, side="BUY")
    
    assert isinstance(res, ExecutionResult)
    # Default 0.05% slippage on BUY -> 100.05
    assert pytest.approx(res.executed_price, 0.001) == 100.05
    assert pytest.approx(res.slippage_cost, 0.001) == 0.05
    # Default 0.1% taker fee on 100.05 -> 0.10005
    assert pytest.approx(res.fee_amount, 0.0001) == 0.10005
    assert res.latency_ms == 50
    assert pytest.approx(res.net_value, 0.001) == 100.05 + 0.10005

def test_sell_execution_slippage():
    model = ExecutionRealismModel()
    res = model.apply_realism(price=100.0, quantity=2.0, side="SELL")
    
    # 0.05% slippage on SELL -> 99.95
    assert pytest.approx(res.executed_price, 0.001) == 99.95
    assert pytest.approx(res.slippage_cost, 0.001) == 0.10
    # Net value for sell: trade_value - fee
    assert res.net_value < (99.95 * 2.0)

def test_maker_vs_taker_fee():
    fee_cfg = FeeConfig(maker_fee_rate=0.0002, taker_fee_rate=0.0005, fixed_fee_per_trade=1.0)
    model = ExecutionRealismModel(fee_config=fee_cfg)

    maker_res = model.apply_realism(price=1000.0, quantity=1.0, side="BUY", is_maker=True)
    taker_res = model.apply_realism(price=1000.0, quantity=1.0, side="BUY", is_maker=False)

    assert maker_res.fee_amount < taker_res.fee_amount
    assert maker_res.fee_amount == pytest.approx((maker_res.executed_price * 0.0002) + 1.0)

def test_fixed_points_slippage():
    slip_cfg = SlippageConfig(model=SlippageModelType.FIXED_POINTS, slippage_points=2.5)
    model = ExecutionRealismModel(slippage_config=slip_cfg)

    buy_res = model.apply_realism(price=500.0, quantity=1.0, side="BUY")
    sell_res = model.apply_realism(price=500.0, quantity=1.0, side="SELL")

    assert buy_res.executed_price == 502.5
    assert sell_res.executed_price == 497.5

def test_volume_impact_slippage():
    slip_cfg = SlippageConfig(
        model=SlippageModelType.VOLUME_IMPACT,
        impact_factor=0.1
    )
    model = ExecutionRealismModel(slippage_config=slip_cfg)

    # 10% of bar volume
    res = model.apply_realism(price=100.0, quantity=10.0, side="BUY", bar_volume=100.0)
    # impact = 0.1 * (10 / 100) = 0.01 -> shift = 100 * 0.01 = 1.0 -> price = 101.0
    assert pytest.approx(res.executed_price, 0.01) == 101.0

def test_no_slippage_model():
    slip_cfg = SlippageConfig(model=SlippageModelType.NONE)
    model = ExecutionRealismModel(slippage_config=slip_cfg)

    res = model.apply_realism(price=250.0, quantity=1.0, side="BUY")
    assert res.executed_price == 250.0
    assert res.slippage_cost == 0.0

def test_invalid_inputs_validation():
    model = ExecutionRealismModel()
    with pytest.raises(ValueError):
        model.apply_realism(price=-10.0, quantity=1.0, side="BUY")
    with pytest.raises(ValueError):
        model.apply_realism(price=100.0, quantity=-5.0, side="BUY")
    with pytest.raises(ValueError):
        model.apply_realism(price=100.0, quantity=1.0, side="INVALID_SIDE")

def test_result_to_dict():
    model = ExecutionRealismModel()
    res = model.apply_realism(price=50.0, quantity=2.0, side="BUY")
    d = res.to_dict()
    assert "executed_price" in d
    assert "fee_amount" in d
    assert "slippage_cost" in d
    assert "latency_ms" in d
    assert "net_value" in d
