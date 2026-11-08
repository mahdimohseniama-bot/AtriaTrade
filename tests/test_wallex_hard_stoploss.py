import pytest
from src.core.paper_live_runner import PaperTradingLiveRunner

def test_wallex_hard_stoploss_on_market_dump():
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=15000.0)
    runner.start()

    entry_price = 72000.0
    # Warm-up runner
    for i in range(20):
        runner.ingest_candle({
            "timestamp": 1700000000 - (20 - i) * 60,
            "open": entry_price, "high": entry_price + 15,
            "low": entry_price - 15, "close": entry_price,
            "volume": 8.0
        })

    # 1. Open BUY position
    entry_candle = {
        "timestamp": 1700000000,
        "open": entry_price,
        "high": entry_price + 20,
        "low": entry_price - 20,
        "close": entry_price,
        "volume": 12.0
    }
    runner.ingest_candle(entry_candle)
    order = runner.process_signal({"side": "BUY", "size_pct": 0.15}, entry_candle)
    assert order["status"] == "FILLED"
    assert len(runner.open_positions) == 1

    # 2. Flash dump candle: drops 3% below entry (e.g. to 69840.0)
    dump_price = entry_price * 0.97
    dump_candle = {
        "timestamp": 1700000060,
        "open": entry_price - 50.0,
        "high": entry_price,
        "low": dump_price - 50.0,
        "close": dump_price,
        "volume": 80.0
    }
    res_dump = runner.ingest_candle(dump_candle)
    assert res_dump["status"] == "PROCESSED"

    # 3. Emergency Stop-Loss signal execution
    sl_signal = {"side": "SELL", "size_pct": 1.0}
    sl_exit = runner.process_signal(sl_signal, dump_candle)
    assert sl_exit["status"] in ["CLOSED", "FILLED", "PROCESSED"]
    assert len(runner.open_positions) == 0

    # Ensure drawdown did not exceed safe maximum allocation
    assert runner.balance > 14000.0

    runner.stop()
