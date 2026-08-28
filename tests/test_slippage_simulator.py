import pytest
from src.core.slippage_simulator import MarketDepthSlippageSimulator


def test_slippage_simulator_init_and_defaults():
    sim = MarketDepthSlippageSimulator()
    assert sim.base_slippage_pct == 0.0005
    assert sim.depth_impact_factor == 0.05
    assert sim.max_slippage_pct == 0.03
    assert sim.base_latency_ms == 50.0


def test_slippage_calculation_buy_order():
    sim = MarketDepthSlippageSimulator(base_slippage_pct=0.001)
    result = sim.calculate_executed_price(
        side="BUY",
        target_price=50000.0,
        order_volume=1.0,
        available_depth_volume=100.0,
        volatility_factor=1.0
    )
    assert result["side"] == "BUY"
    assert result["executed_price"] > 50000.0  # Slippage increases buy price
    assert result["slippage_pct"] >= 0.001
    assert result["estimated_latency_ms"] == 50.0


def test_slippage_calculation_sell_order():
    sim = MarketDepthSlippageSimulator(base_slippage_pct=0.001)
    result = sim.calculate_executed_price(
        side="SELL",
        target_price=50000.0,
        order_volume=1.0,
        available_depth_volume=100.0,
        volatility_factor=1.0
    )
    assert result["side"] == "SELL"
    assert result["executed_price"] < 50000.0  # Slippage decreases sell price
    assert result["slippage_pct"] >= 0.001


def test_slippage_caps_at_maximum():
    sim = MarketDepthSlippageSimulator(max_slippage_pct=0.02)
    # Huge order volume relative to depth
    slippage = sim.calculate_effective_slippage(
        order_volume=1000.0,
        available_depth_volume=1.0,
        volatility_factor=5.0
    )
    assert slippage == 0.02


def test_slippage_simulator_invalid_inputs():
    sim = MarketDepthSlippageSimulator()
    with pytest.raises(ValueError, match="Invalid side"):
        sim.calculate_executed_price("HOLD", 50000.0, 1.0, 10.0)

    with pytest.raises(ValueError, match="Target price must be strictly positive"):
        sim.calculate_executed_price("BUY", -10.0, 1.0, 10.0)
