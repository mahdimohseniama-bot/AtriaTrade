import pytest
from src.core.strategy_aggregator import StrategyAggregator

@pytest.fixture
def aggregator():
    return StrategyAggregator(min_confidence_score=0.70)

def test_hold_decision_on_conflicting_signals(aggregator):
    # Trend BUY (+0.3), Order Flow SELL (-0.35), Liquidity Sweep NONE (0.0) -> Score = -0.05 (HOLD)
    res = aggregator.aggregate_signals(
        trend_signal="BUY",
        order_flow_imbalance=-0.3,
        liquidity_sweep={"sweep_type": "NONE"},
        volume_profile_poc=100.0,
        current_price=101.0
    )
    assert res["status"] == "AGGREGATED"
    assert res["action"] == "HOLD"
    assert res["is_actionable"] is False

def test_strong_buy_confluence(aggregator):
    # Trend BUY (+0.3), Order Flow BUY (+0.35), Bullish Sweep (+0.35) -> Score = 1.0 (BUY)
    res = aggregator.aggregate_signals(
        trend_signal="BUY",
        order_flow_imbalance=0.4,
        liquidity_sweep={"sweep_type": "BULLISH_SWEEP"},
        volume_profile_poc=100.0,
        current_price=100.5
    )
    assert res["status"] == "AGGREGATED"
    assert res["action"] == "BUY"
    assert res["confidence_score"] >= 0.70
    assert res["is_actionable"] is True
    assert "BULLISH_LIQUIDITY_SWEEP" in res["factors"]
    assert "BUY_ORDER_FLOW_IMBALANCE" in res["factors"]

def test_strong_sell_confluence(aggregator):
    # Trend SELL (-0.3), Order Flow SELL (-0.35), Bearish Sweep (-0.35) -> Score = -1.0 (SELL)
    res = aggregator.aggregate_signals(
        trend_signal="SELL",
        order_flow_imbalance=-0.5,
        liquidity_sweep={"sweep_type": "BEARISH_SWEEP"},
        volume_profile_poc=105.0,
        current_price=104.0
    )
    assert res["status"] == "AGGREGATED"
    assert res["action"] == "SELL"
    assert res["confidence_score"] >= 0.70
    assert res["is_actionable"] is True
    assert "SELL_ORDER_FLOW_IMBALANCE" in res["factors"]
