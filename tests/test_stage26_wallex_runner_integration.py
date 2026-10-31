import pytest
from src.core.paper_live_runner import PaperTradingLiveRunner
from src.adapters.wallex_paper import WallexPaperAdapter
from src.exchange.wallex_order_executor import WallexOrderExecutor

def test_stage26_runner_initialization_with_wallex_executor():
    adapter = WallexPaperAdapter(api_key="mock_key", api_secret="mock_secret")
    executor = WallexOrderExecutor(adapter)
    runner = PaperTradingLiveRunner(symbol="BTC/TMN", executor=executor)
    
    assert runner.executor is not None
    assert runner.executor == executor
    assert runner.symbol == "BTC/TMN"
    assert runner.is_running is False

def test_stage26_runner_start_and_stop_lifecycle():
    adapter = WallexPaperAdapter(api_key="mock_key", api_secret="mock_secret")
    executor = WallexOrderExecutor(adapter)
    runner = PaperTradingLiveRunner(symbol="USDT/TMN", executor=executor)
    
    runner.start()
    assert runner.is_running is True
    
    runner.stop()
    assert runner.is_running is False
