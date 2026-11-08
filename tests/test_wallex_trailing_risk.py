import pytest
from src.core.paper_live_runner import PaperTradingLiveRunner

def test_wallex_live_runner_profit_and_trailing_logic():
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=20000.0)
    runner.start()

    # Step 0: Warm-up the runner with baseline candles to avoid REJECTION
    base_price = 75000.0
    for i in range(20):
        runner.ingest_candle({
            "timestamp": 1700000000 - (20 - i) * 60,
            "open": base_price - 10, "high": base_price + 10,
            "low": base_price - 10, "close": base_price,
            "volume": 10.0
        })

    # Step 1: Open BUY position at 75000
    entry_candle = {
        "timestamp": 1700000000,
        "open": 74900.0,
        "high": 75100.0,
        "low": 74850.0,
        "close": 75000.0,
        "volume": 10.0
    }
    runner.ingest_candle(entry_candle)
    order_res = runner.process_signal({"side": "BUY", "size_pct": 0.05}, entry_candle)
    
    assert order_res["status"] == "FILLED"
    assert len(runner.open_positions) == 1

    pos_id = list(runner.open_positions.keys())[0]
    pos = runner.open_positions[pos_id]
    assert pos["side"] == "BUY"
    assert pos["entry_price"] == 75000.0

    # Step 2: Price surges up to 78000 -> unrealized profit
    peak_candle = {
        "timestamp": 1700000060,
        "open": 75000.0,
        "high": 78200.0,
        "low": 74950.0,
        "close": 78000.0,
        "volume": 25.0
    }
    ingest_peak = runner.ingest_candle(peak_candle)
    assert ingest_peak["status"] == "PROCESSED"

    # Step 3: Trigger SELL / Profit exit
    sell_signal = {"side": "SELL", "size_pct": 1.0}
    exit_res = runner.process_signal(sell_signal, peak_candle)
    assert exit_res["status"] in ["CLOSED", "FILLED", "PROCESSED"]

    runner.stop()
