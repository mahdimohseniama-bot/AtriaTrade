import pytest
from src.core.live_capital_guardrail import LiveCapitalGuardrail

def test_guardrail_rejects_below_min_notional():
    guard = LiveCapitalGuardrail(min_notional_irt=100000.0)
    res = guard.validate_capital_allocation(
        total_balance=10000000.0,
        available_balance=10000000.0,
        order_price=50000.0,
        order_quantity=1.0  # 50,000 < 100,000
    )
    assert res["permitted"] is False
    assert res["reason"] == "BELOW_MIN_NOTIONAL"

def test_guardrail_rejects_exceeding_max_order_cap():
    guard = LiveCapitalGuardrail(max_order_ratio=0.20)
    # Total: 10,000,000 -> Max order: 2,000,000
    res = guard.validate_capital_allocation(
        total_balance=10000000.0,
        available_balance=10000000.0,
        order_price=1000000.0,
        order_quantity=3.0  # 3,000,000 > 2,000,000
    )
    assert res["permitted"] is False
    assert res["reason"] == "EXCEEDS_MAX_ORDER_CAP"

def test_guardrail_rejects_reserve_floor_breach():
    guard = LiveCapitalGuardrail(max_order_ratio=0.50, min_reserve_ratio=0.20)
    # Total: 10,000,000 -> Min reserve: 2,000,000
    # Available: 2,500,000 -> Order: 1,000,000 -> Remaining: 1,500,000 (< 2,000,000)
    res = guard.validate_capital_allocation(
        total_balance=10000000.0,
        available_balance=2500000.0,
        order_price=1000000.0,
        order_quantity=1.0
    )
    assert res["permitted"] is False
    assert res["reason"] == "BREACHES_RESERVE_FLOOR"

def test_guardrail_permits_safe_order():
    guard = LiveCapitalGuardrail(
        max_order_ratio=0.25,
        min_reserve_ratio=0.10,
        min_notional_irt=100000.0
    )
    res = guard.validate_capital_allocation(
        total_balance=10000000.0,
        available_balance=8000000.0,
        order_price=500000.0,
        order_quantity=2.0  # 1,000,000 IRT
    )
    assert res["permitted"] is True
    assert res["order_notional"] == 1000000.0
    assert res["remaining_balance"] == 7000000.0
