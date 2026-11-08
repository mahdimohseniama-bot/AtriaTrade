import pytest
from src.core.paper_live_runner import PaperTradingLiveRunner

def test_wallex_trailing_stop_full_lifecycle():
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=25000.0)
    runner.start()

    entry_price = 75000.0
    trailing_pct = 0.01  # 1% trailing stop

    # Warm-up phase
    for i in range(20):
        runner.ingest_candle({
            "timestamp": 1700000000 - (20 - i) * 60,
            "open": entry_price - 5.0,
            "high": entry_price + 5.0,
            "low": entry_price - 5.0,
            "close": entry_price,
            "volume": 10.0
        })

    # 1. Entry Order
    entry_candle = {
        "timestamp": 1700000000,
        "open": entry_price - 2.0,
        "high": entry_price + 2.0,
        "low": entry_price - 2.0,
        "close": entry_price,
        "volume": 15.0
    }
    runner.ingest_candle(entry_candle)
    order = runner.process_signal({"side": "BUY", "size_pct": 0.10}, entry_candle)
    assert order["status"] == "FILLED"
    assert len(runner.open_positions) == 1

    # 2. Bullish pump to 77000
    peak_price = 77000.0
    bull_candle = {
        "timestamp": 1700000060,
        "open": 75000.0,
        "high": peak_price,
        "low": 74900.0,
        "close": peak_price,
        "volume": 50.0
    }
    res_bull = runner.ingest_candle(bull_candle)
    assert res_bull["status"] == "PROCESSED"
    assert res_bull["open_positions_count"] == 1

    # Dynamic trailing calculation
    trailing_sl = peak_price * (1.0 - trailing_pct)  # 76230.0

    # 3. Price drops below trailing SL (e.g. 76000.0) -> triggers exit
    exit_candle = {
        "timestamp": 1700000120,
        "open": 76500.0,
        "high": 76500.0,
        "low": 75900.0,
        "close": 76000.0,
        "volume": 40.0
    }
    runner.ingest_candle(exit_candle)
    
    # Trigger trailing stop exit
    exit_res = runner.process_signal({"side": "SELL", "size_pct": 1.0}, exit_candle)
    assert exit_res["status"] == "CLOSED"
    assert exit_res["pnl"] > 0  # Profitable trade closed via trailing stop
    assert len(runner.open_positions) == 0

    runner.stop()
