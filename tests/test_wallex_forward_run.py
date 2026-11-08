import pytest
from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.paper_live_runner import PaperTradingLiveRunner

def test_wallex_live_forward_runner_simulation():
    adapter = WallexPaperAdapter(initial_balances={"USDT": 10000.0, "BTC": 0.0})
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=10000.0)
    runner.start()
    
    base_price = 68000.0
    for i in range(15):
        candle = {
            "timestamp": 1700001000 + (i * 60),
            "open": base_price + (i * 10),
            "high": base_price + (i * 10) + 50,
            "low": base_price + (i * 10) - 50,
            "close": base_price + (i * 10) + 20,
            "volume": 15.0
        }
        runner.ingest_candle(candle)
        
    # Send a buy order signal
    signal_candle = {
        "timestamp": 1700001900,
        "open": base_price + 200,
        "high": base_price + 350,
        "low": base_price + 150,
        "close": base_price + 300,
        "volume": 30.0
    }
    runner.ingest_candle(signal_candle)
    fill_res = runner.process_signal({"side": "BUY", "size_pct": 0.25}, signal_candle)
    
    assert fill_res["status"] == "FILLED"
    assert len(runner.open_positions) == 1
    
    runner.stop()
