import pytest
from src.core.wallex_orderbook_liquidity_guard import WallexOrderBookLiquidityGuard

@pytest.fixture
def guard():
    return WallexOrderBookLiquidityGuard(max_slippage_pct=0.01, min_depth_coverage_ratio=1.2)

def test_empty_orderbook(guard):
    res = guard.evaluate_execution_slippage("BUY", 1.0, {"asks": [], "bids": []})
    assert res["allowed"] is False
    assert res["reason"] == "EMPTY_ORDERBOOK_OR_INVALID_QTY"

def test_insufficient_depth(guard):
    book = {"asks": [[100.0, 0.5]]}
    # Target 1.0 needs at least 1.2 depth
    res = guard.evaluate_execution_slippage("BUY", 1.0, book)
    assert res["allowed"] is False
    assert res["reason"] == "INSUFFICIENT_LIQUIDITY_DEPTH"

def test_acceptable_slippage_buy(guard):
    # Target 1.0; 0.5 @ 100, 0.5 @ 101 => VWAP = 100.5 (Slippage = 0.5% < 1.0%)
    book = {"asks": [[100.0, 0.5], [101.0, 1.0]]}
    res = guard.evaluate_execution_slippage("BUY", 1.0, book)
    assert res["allowed"] is True
    assert res["reason"] == "APPROVED"
    assert res["estimated_vwap"] == 100.5
    assert res["slippage_pct"] == pytest.approx(0.005, abs=1e-5)

def test_excessive_slippage_sell(guard):
    # Target 1.0; best = 100. 0.1 @ 100, 0.9 @ 90 => VWAP = 91. Slippage = (100 - 91)/100 = 9% > 1%
    book = {"bids": [[100.0, 0.1], [90.0, 2.0]]}
    res = guard.evaluate_execution_slippage("SELL", 1.0, book)
    assert res["allowed"] is False
    assert res["reason"] == "EXCESSIVE_SLIPPAGE"
    assert res["slippage_pct"] > 0.01
