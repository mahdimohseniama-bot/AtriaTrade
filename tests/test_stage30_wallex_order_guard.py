import pytest
from src.core.wallex_order_guard import WallexOrderGuard

def test_stage30_order_guard_validates_safe_order():
    guard = WallexOrderGuard(min_order_value_usdt=5.0, max_spread_pct=0.5)
    # Bid: 100, Ask: 100.2 -> Spread ~ 0.2%
    is_safe, msg = guard.is_order_safe(amount=1.0, price=100.0, best_bid=100.0, best_ask=100.2)
    assert is_safe is True
    assert msg == "Order verified safe"

def test_stage30_order_guard_rejects_wide_spread():
    guard = WallexOrderGuard(min_order_value_usdt=5.0, max_spread_pct=0.5)
    # Bid: 100, Ask: 102 -> Spread ~ 2.0%
    is_safe, msg = guard.is_order_safe(amount=1.0, price=100.0, best_bid=100.0, best_ask=102.0)
    assert is_safe is False
    assert "Spread too wide" in msg

def test_stage30_order_guard_rejects_sub_minimum_size():
    guard = WallexOrderGuard(min_order_value_usdt=10.0, max_spread_pct=1.0)
    # Notional: 0.05 * 100 = 5.0 USDT (< 10.0 min)
    is_safe, msg = guard.is_order_safe(amount=0.05, price=100.0, best_bid=100.0, best_ask=100.1)
    assert is_safe is False
    assert "below minimum" in msg
