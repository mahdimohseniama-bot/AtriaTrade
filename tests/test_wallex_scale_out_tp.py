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

    pos_id = list(runner.open_positions.keys())[0]
    initial_qty = runner.open_positions[pos_id]["size"]
    assert initial_qty > 0

    # 2. Bullish leg 1 to TP1 (+2%)
    tp1_price = entry_price * 1.02
    candle_tp1 = {
        "timestamp": 1700000060,
        "open": entry_price + 500,
        "high": tp1_price + 100,
        "low": entry_price + 400,
        "close": tp1_price,
        "volume": 40.0
    }
    runner.ingest_candle(candle_tp1)

    # Partial exit: 50% scale-out at TP1
    exit_tp1 = runner.process_signal({"side": "SELL", "size_pct": 0.50}, candle_tp1)
    assert exit_tp1["status"] in ["CLOSED", "FILLED", "PROCESSED"]

    # If position remains partially open, size is reduced; otherwise verify realized profit
    if len(runner.open_positions) > 0:
        remaining_qty = runner.open_positions[pos_id]["size"]
        assert remaining_qty < initial_qty
    
    # 3. Bullish leg 2 to TP2 (+4%) -> full close remainder
    tp2_price = entry_price * 1.04
    candle_tp2 = {
        "timestamp": 1700000120,
        "open": tp1_price,
        "high": tp2_price + 50,
        "low": tp1_price - 50,
        "close": tp2_price,
        "volume": 35.0
    }
    runner.ingest_candle(candle_tp2)

    exit_tp2 = runner.process_signal({"side": "SELL", "size_pct": 1.0}, candle_tp2)
    assert exit_tp2["status"] in ["CLOSED", "FILLED", "PROCESSED"]
    assert len(runner.open_positions) == 0

    # Profit check
    assert runner.balance > initial_balance

    runner.stop()
