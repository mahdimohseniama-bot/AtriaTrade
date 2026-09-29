import sys
import os
import logging

logging.basicConfig(level=logging.INFO)

from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.capital_manager import CapitalManager
from src.core.wallex_live_orchestrator import WallexLiveOrchestrator

def test_stage10():
    print("[STAGE 10] POSITION LIFECYCLE TEST STARTING...")
    adapter = WallexPaperAdapter()
    capital_mgr = CapitalManager(initial_capital=10_000_000.0)
    orchestrator = WallexLiveOrchestrator(adapter=adapter, capital_manager=capital_mgr)

    adapter.set_market_price("BTC_TMN", 2500000.0)
    
    orchestrator.open_paper_position(
        symbol="BTC_TMN",
        side="BUY",
        entry_price=2500000.0,
        quantity=1.0,
        stop_loss=2400000.0,
        take_profit=2600000.0
    )

    res1 = orchestrator.process_tick("BTC_TMN")
    assert res1["status"] == "OPEN"
    print(f"[TEST] Tick 1 processed successfully: {res1}")

    adapter.set_market_price("BTC_TMN", 2650000.0)
    res2 = orchestrator.process_tick("BTC_TMN")
    assert res2["status"] == "CLOSED"
    assert res2["exit_reason"] == "TAKE_PROFIT"
    print(f"[SUCCESS] Stage 10 Position Lifecycle Test Passed! PnL: {res2['pnl']}")

if __name__ == "__main__":
    test_stage10()
