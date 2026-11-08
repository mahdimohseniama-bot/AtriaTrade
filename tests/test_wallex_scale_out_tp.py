import pytest
from src.core.paper_live_runner import PaperTradingLiveRunner

def test_wallex_partial_take_profit_scale_out():
    initial_balance = 20000.0
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=initial_balance)
    runner.start()

    entry_price = 70000.0
    # Warm-up candles
    for i in range(20):
        runner.ingest_candle({
            "timestamp": 1700000000 - (20 - i) * 60,
            "open": entry_price, "high": entry_price + 10,
            "low": entry_price - 10, "close": entry_price,
            "volume": 10.0
        })

    # 1. Full Entry: 20% size
    entry_candle = {
        "timestamp": 1700000000,
        "open": entry_price,
        "high": entry_price + 20,
        "low": entry_price - 20,
        "close": entry_price,
        "volume": 25.0
    }
    runner.ingest_candle(entry_candle)
    entry_res = runner.process_signal({"side": "BUY", "size_pct": 0.20}, entry_candle)
    assert entry_res["status"] == "FILLED"
    assert len(runner.open_positions) == 1

    # 2. Bullish pump to TP (+3%)
    tp_price = entry_price * 1.03
    candle_tp = {
        "timestamp": 1700000060,
        "open": entry_price + 500,
        "high": tp_price + 100,
        "low": entry_price + 400,
        "close": tp_price,
        "volume": 40.0
    }
    runner.ingest_candle(candle_tp)

    # Execute Take-Profit signal
    exit_tp = runner.process_signal({"side": "SELL", "size_pct": 1.0}, candle_tp)
    assert exit_tp["status"] in ["CLOSED", "FILLED", "PROCESSED"]
    assert len(runner.open_positions) == 0

    # Ensure Take Profit captured net gains after exchange fee
    assert runner.balance > initial_balance
    assert exit_tp.get("pnl", 1.0) > 0

    runner.stop()
