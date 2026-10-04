import pytest
from src.core.spread_fee_filter import DynamicSpreadFeeFilter

def test_spread_fee_filter_approved():
    filter_engine = DynamicSpreadFeeFilter(
        max_spread_pct=0.01,
        default_taker_fee=0.001,
        min_reward_to_cost_ratio=1.5
    )
    # BUY scenario: ask=100.2, bid=100.0, exit=105.0 -> gross return ~4.79%
    approved, reason, metrics = filter_engine.evaluate_order(
        side="BUY",
        best_bid=100.0,
        best_ask=100.2,
        target_exit_price=105.0
    )
    assert approved is True
    assert "approved" in reason.lower()
    assert metrics["gross_return_pct"] > 0
    assert metrics["reward_to_cost_ratio"] >= 1.5

def test_spread_fee_filter_wide_spread_rejected():
    filter_engine = DynamicSpreadFeeFilter(max_spread_pct=0.002)
    # Spread is (105-100)/102.5 = ~4.8% which exceeds 0.2%
    approved, reason, metrics = filter_engine.evaluate_order(
        side="BUY",
        best_bid=100.0,
        best_ask=105.0,
        target_exit_price=110.0
    )
    assert approved is False
    assert "spread exceeds maximum" in reason.lower()

def test_spread_fee_filter_low_rr_rejected():
    filter_engine = DynamicSpreadFeeFilter(
        max_spread_pct=0.01,
        default_taker_fee=0.002,
        min_reward_to_cost_ratio=3.0
    )
    # Small target gain that cannot satisfy 3.0 ratio against friction
    approved, reason, metrics = filter_engine.evaluate_order(
        side="BUY",
        best_bid=100.0,
        best_ask=100.5,
        target_exit_price=100.8
    )
    assert approved is False
    assert "reward-to-cost ratio" in reason.lower()
