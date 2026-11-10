import pytest
from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.risk_manager import RiskManager
from src.core.strategy_orchestrator import StrategyOrchestrator

def test_full_strategy_pipeline_integration():
    adapter = WallexPaperAdapter()
    risk_manager = RiskManager()
    strategy = StrategyOrchestrator(adapter)
    
    assert risk_manager.can_trade_today() is True
    signal = strategy.get_signal("BTCUSDT")
    assert signal in ["BUY", "SELL", "HOLD"]
    
    if signal in ["BUY", "SELL"]:
        order = adapter.create_order("BTCUSDT", signal.lower(), "market", 0.001, 65000.0)
        assert order["status"] == "filled"
