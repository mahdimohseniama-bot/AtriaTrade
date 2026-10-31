import pytest
import time
from src.core.wallex_slippage_guard import WallexSlippageGuard, SlippageCheckResult

def test_stage40_slippage_within_acceptable_threshold():
    guard = WallexSlippageGuard(max_slippage_pct=0.5, max_latency_sec=3.0)
    
    # Asks: [(price, quantity)]
    asks = [
        (60000.0, 0.5),
        (60100.0, 0.5),
        (60300.0, 1.0)
    ]
    
    current_time = time.time()
    result = guard.evaluate_order_execution(
        symbol="BTCUSDT",
        side="BUY",
        target_qty=0.8,
        expected_price=60000.0,
        orderbook_side=asks,
        quote_timestamp=current_time
    )
    
    # Fill calculation:
    # 0.5 BTC @ 60000 = 30000
    # 0.3 BTC @ 60100 = 18030
    # Total cost = 48030 / 0.8 = 60037.5
    # Slippage = (60037.5 - 60000) / 60000 = 0.0625% < 0.5%
    assert result.is_allowed is True
    assert result.estimated_average_price == pytest.approx(60037.5, rel=1e-4)
    assert result.slippage_pct == pytest.approx(0.0625, rel=1e-3)
    assert result.rejection_reason is None

def test_stage40_slippage_exceeds_threshold_rejected():
    guard = WallexSlippageGuard(max_slippage_pct=0.2, max_latency_sec=3.0)
    
    asks = [
        (60000.0, 0.1),
        (60500.0, 1.0)
    ]
    
    result = guard.evaluate_order_execution(
        symbol="BTCUSDT",
        side="BUY",
        target_qty=0.5,
        expected_price=60000.0,
        orderbook_side=asks,
        quote_timestamp=time.time()
    )
    
    # 0.1 @ 60000 = 6000
    # 0.4 @ 60500 = 24200
    # Total cost = 30200 / 0.5 = 60400.0
    # Slippage = (60400 - 60000) / 60000 = 0.6667% > 0.2%
    assert result.is_allowed is False
    assert result.slippage_pct > 0.2
    assert result.rejection_reason == "SLIPPAGE_EXCEEDED"

def test_stage40_stale_orderbook_latency_rejected():
    guard = WallexSlippageGuard(max_slippage_pct=1.0, max_latency_sec=2.0)
    
    asks = [(60000.0, 1.0)]
    stale_timestamp = time.time() - 5.0  # 5 seconds old
    
    result = guard.evaluate_order_execution(
        symbol="BTCUSDT",
        side="BUY",
        target_qty=0.5,
        expected_price=60000.0,
        orderbook_side=asks,
        quote_timestamp=stale_timestamp
    )
    
    assert result.is_allowed is False
    assert result.rejection_reason == "ORDERBOOK_STALE"
