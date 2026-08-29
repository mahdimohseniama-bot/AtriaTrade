import pytest
from src.core.spread_fee_filter import DynamicSpreadFeeFilter


def test_normal_buy_approved():
    flt = DynamicSpreadFeeFilter(max_spread_pct=0.005, default_taker_fee=0.001, min_reward_to_cost_ratio=2.0)
    # Buy at 100.05, target 102.0 (gross ~1.95%), spread is 0.1 (0.1%), friction ~0.3%
    approved, reason, metrics = flt.evaluate_order(
        best_bid=99.95,
        best_ask=100.05,
        target_exit_price=102.0,
        side="BUY"
    )
    assert approved is True
    assert "approved" in reason.lower()
    assert metrics["reward_to_cost_ratio"] >= 2.0


def test_excessive_spread_rejected():
    flt = DynamicSpreadFeeFilter(max_spread_pct=0.004)
    # Spread is 1.0 on 100 mid -> 1.0% (exceeds 0.4%)
    approved, reason, metrics = flt.evaluate_order(
        best_bid=99.5,
        best_ask=100.5,
        target_exit_price=105.0,
        side="BUY"
    )
    assert approved is False
    assert "Spread" in reason and "exceeds" in reason


def test_insufficient_profit_relative_to_cost():
    flt = DynamicSpreadFeeFilter(min_reward_to_cost_ratio=2.5, default_taker_fee=0.001)
    # Target profit is too small to justify friction
    approved, reason, metrics = flt.evaluate_order(
        best_bid=100.0,
        best_ask=100.1,
        target_exit_price=100.25,  # only 0.15% profit
        side="BUY"
    )
    assert approved is False
    assert "Reward-to-cost ratio" in reason


def test_normal_sell_approved():
    flt = DynamicSpreadFeeFilter()
    # Sell short at 100.0, target exit at 97.0 (gross ~3.0%)
    approved, reason, metrics = flt.evaluate_order(
        best_bid=100.0,
        best_ask=100.05,
        target_exit_price=97.0,
        side="SELL"
    )
    assert approved is True
    assert metrics["net_return_pct"] > 0


def test_inverted_orderbook_rejected():
    flt = DynamicSpreadFeeFilter()
    approved, reason, _ = flt.evaluate_order(
        best_bid=105.0,
        best_ask=100.0,
        target_exit_price=110.0,
        side="BUY"
    )
    assert approved is False
    assert "Inverted" in reason


def test_negative_gross_return_rejected():
    flt = DynamicSpreadFeeFilter()
    # Buy at 100, target 95 -> losing trade
    approved, reason, _ = flt.evaluate_order(
        best_bid=99.9,
        best_ask=100.0,
        target_exit_price=95.0,
        side="BUY"
    )
    assert approved is False
    assert "non-positive" in reason


def test_invalid_init_parameters():
    with pytest.raises(ValueError):
        DynamicSpreadFeeFilter(max_spread_pct=-0.01)
    with pytest.raises(ValueError):
        DynamicSpreadFeeFilter(min_reward_to_cost_ratio=0)
