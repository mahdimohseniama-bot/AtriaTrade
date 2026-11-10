import pytest
from src.core.strategy_orchestrator import StrategyOrchestrator
from src.adapters.wallex_paper import WallexPaperAdapter

def test_strategy_orchestrator_signal():
    adapter = WallexPaperAdapter()
    orchestrator = StrategyOrchestrator(adapter)
    signal = orchestrator.get_signal("BTCUSDT")
    assert signal in ["BUY", "SELL", "HOLD"]

def test_sma_calculation():
    adapter = WallexPaperAdapter()
    orchestrator = StrategyOrchestrator(adapter)
    mock_candles = [{"close": 100.0} for _ in range(20)]
    sma = orchestrator.calculate_sma(mock_candles, period=20)
    assert sma == 100.0
