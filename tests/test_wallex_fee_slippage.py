import pytest
from src.core.paper_live_runner import PaperTradingLiveRunner

def test_wallex_fee_and_slippage_accounting():
    initial_balance = 10000.0
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=initial_balance)
    runner.start()

    base_price = 70000.0
    # Warm-up runner
    for i in range(20):
        runner.ingest_candle({
            "timestamp": 1700000000 - (20 - i) * 60,
            "open": base_price, "high": base_price + 10,
            "low": base_price - 10, "close": base_price,
            "volume": 5.0
        })

    # Ingest entry candle
    candle = {
        "timestamp": 1700000000,
        "open": base_price, "high": base_price + 20,
        "low": base_price - 20, "close": base_price,
        "volume": 10.0
    }
    runner.ingest_candle(candle)

    # Buy order with 20% size
    order = runner.process_signal({"side": "BUY", "size_pct": 0.20}, candle)
    assert order["status"] == "FILLED"

    pos_id = list(runner.open_positions.keys())[0]
    pos = runner.open_positions[pos_id]

    # Verify execution slippage within realistic boundary (< 0.1%)
    exec_price = pos["entry_price"]
    slippage_pct = abs(exec_price - base_price) / base_price
    assert slippage_pct <= 0.001

    # Verify runner remaining balance is properly deducted
    expected_max_balance = initial_balance - (initial_balance * 0.20 * 0.99)
    assert runner.balance <= expected_max_balance

    runner.stop()
