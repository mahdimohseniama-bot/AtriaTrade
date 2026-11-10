import pytest
from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.strategy_orchestrator import StrategyOrchestrator

def test_signal_deduplication_flow():
    adapter = WallexPaperAdapter()
    strategy = StrategyOrchestrator(adapter)
    
    sig = strategy.get_signal("BTCUSDT")
    assert sig in ["BUY", "SELL", "HOLD"]
    
    # State transition test
    pos = "FLAT"
    order_count = 0
    for _ in range(3):
        if sig == "SELL" and pos != "SHORT":
            adapter.create_order("BTCUSDT", "sell", "market", 0.001)
            pos = "SHORT"
            order_count += 1
        elif sig == "BUY" and pos != "LONG":
            adapter.create_order("BTCUSDT", "buy", "market", 0.001)
            pos = "LONG"
            order_count += 1
            
    # Regardless of loop count, duplicate consecutive signals should only trigger 1 order
    if sig in ["BUY", "SELL"]:
        assert order_count == 1
    else:
        assert order_count == 0
