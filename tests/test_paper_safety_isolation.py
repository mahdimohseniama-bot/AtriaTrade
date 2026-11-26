import pytest
from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.paper_live_runner import PaperTradingLiveRunner

def test_wallex_paper_adapter_offline_execution():
    # Verify WallexPaperAdapter initializes virtual balances safely using get_balances()
    adapter = WallexPaperAdapter(initial_balances={"USDT": 10000.0, "BTC": 0.5})
    balances = adapter.get_balances()
    assert balances["usdt"] == 10000.0
    assert balances["btc"] == 0.5

def test_paper_runner_instantiation():
    # Verify PaperTradingLiveRunner instantiates successfully in offline paper mode
    runner = PaperTradingLiveRunner(symbol="BTC/USDT")
    assert runner.symbol == "BTC/USDT"
