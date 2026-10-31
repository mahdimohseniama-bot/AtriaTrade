import pytest
from src.core.wallex_balance_allocator import WallexBalanceAllocator, AllocationResult

class MockBalanceProvider:
    def __init__(self, balances):
        self._balances = balances

    def get_balances(self):
        return self._balances

def test_stage38_allocation_sufficient_capital():
    # Free USDT: 250, locked: 50
    provider = MockBalanceProvider({
        "USDT": {"free": 250.0, "locked": 50.0},
        "BTC": {"free": 0.02, "locked": 0.0}
    })
    allocator = WallexBalanceAllocator(balance_provider=provider, max_allocation_pct=0.20)
    
    # Target buy order worth 40 USDT (within 20% of 250 = 50 max)
    res = allocator.allocate(symbol="BTCUSDT", quote_currency="USDT", requested_amount_quote=40.0)
    
    assert res.is_allowed is True
    assert res.allocated_amount == 40.0
    assert res.remaining_free == 210.0
    assert res.rejection_reason is None

def test_stage38_allocation_capped_by_risk_limit():
    # Free USDT: 100
    provider = MockBalanceProvider({"USDT": {"free": 100.0, "locked": 0.0}})
    # Max allocation 10% = 10 USDT
    allocator = WallexBalanceAllocator(balance_provider=provider, max_allocation_pct=0.10)
    
    # Requesting 25 USDT -> Must cap to 10 USDT
    res = allocator.allocate(symbol="BTCUSDT", quote_currency="USDT", requested_amount_quote=25.0)
    
    assert res.is_allowed is True
    assert res.allocated_amount == 10.0
    assert res.capped_by_risk is True

def test_stage38_allocation_insufficient_funds_rejected():
    # Only 5 USDT free, below minimum trading threshold (e.g. 10 USDT)
    provider = MockBalanceProvider({"USDT": {"free": 5.0, "locked": 100.0}})
    allocator = WallexBalanceAllocator(balance_provider=provider, min_order_quote=10.0)
    
    res = allocator.allocate(symbol="BTCUSDT", quote_currency="USDT", requested_amount_quote=15.0)
    
    assert res.is_allowed is False
    assert res.allocated_amount == 0.0
    assert res.rejection_reason == "INSUFFICIENT_FREE_BALANCE"
