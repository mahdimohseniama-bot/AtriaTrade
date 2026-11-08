import pytest
from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.spread_fee_filter import DynamicSpreadFeeFilter

def test_wallex_spread_fee_filter_blocks_wide_spread():
    adapter = WallexPaperAdapter()
    spread_filter = DynamicSpreadFeeFilter(max_spread_pct=0.5) # Max allowed spread: 0.5%
    
    # 1. Normal tight spread: bid=70000, ask=70100 (diff=100 -> ~0.14%) -> ALLOW
    normal_ticker = {"symbol": "BTC/USDT", "bid": 70000.0, "ask": 70100.0, "last": 70050.0}
    res_normal = spread_filter.evaluate_spread(normal_ticker["bid"], normal_ticker["ask"])
    assert res_normal["allowed"] is True
    
    # 2. Abnormal wide spread: bid=69000, ask=70500 (diff=1500 -> ~2.17%) -> REJECT
    wide_ticker = {"symbol": "BTC/USDT", "bid": 69000.0, "ask": 70500.0, "last": 69500.0}
    res_wide = spread_filter.evaluate_spread(wide_ticker["bid"], wide_ticker["ask"])
    assert res_wide["allowed"] is False

def test_wallex_fee_threshold_calculation():
    adapter = WallexPaperAdapter()
    fees = adapter.DEFAULT_FEES
    taker_fee = fees["taker"]
    maker_fee = fees["maker"]
    
    # Ensure Wallex fee structure matches realistic domestic tiers
    assert taker_fee <= 0.003
    assert maker_fee <= taker_fee
