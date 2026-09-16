"""
Tests for ExchangeSimulator.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.exchange.exchange_simulator import Candle, ExchangeSimulator


def test_exchange_simulator():
    print("=" * 60)
    print("START: ExchangeSimulator Tests")
    print("=" * 60)

    exchange = ExchangeSimulator(
        initial_prices={"BTCUSDT": 100.0},
        seed=42,
    )

    # Latest price
    assert exchange.get_price("BTCUSDT") == 100.0
    print("[OK] Initial price")

    # Set price
    exchange.set_price("BTCUSDT", 105.0)
    assert exchange.get_price("BTCUSDT") == 105.0
    print("[OK] Set and read price")

    # Create candle
    candle = exchange.create_candle(
        symbol="BTCUSDT",
        close_price=110.0,
        timestamp=1000,
        volume=25.0,
    )

    assert isinstance(candle, Candle)
    assert candle.symbol == "BTCUSDT"
    assert candle.open == 105.0
    assert candle.close == 110.0
    assert candle.high >= candle.close
    assert candle.low <= candle.open
    assert candle.volume == 25.0
    print("[OK] OHLCV candle creation")

    # Fixed candle stream
    fixed_prices = [111.0, 112.0, 113.0]
    candles = list(
        exchange.stream_candles(
            symbol="BTCUSDT",
            prices=fixed_prices,
        )
    )

    assert len(candles) == 3
    assert [item.close for item in candles] == fixed_prices
    print("[OK] Fixed price stream")

    # Callback
    received = []

    def on_candle(item):
        received.append(item)

    count = exchange.run_callback(
        symbol="BTCUSDT",
        callback=on_candle,
        prices=[114.0, 115.0],
    )

    assert count == 2
    assert len(received) == 2
    assert received[-1].close == 115.0
    print("[OK] Callback stream")

    # Invalid values
    try:
        exchange.set_price("BTCUSDT", 0)
        raise AssertionError("Expected ValueError for zero price")
    except ValueError:
        print("[OK] Invalid price validation")

    try:
        exchange.get_price("UNKNOWN")
        raise AssertionError("Expected KeyError for unknown symbol")
    except KeyError:
        print("[OK] Unknown symbol validation")

    # Safety status
    status = exchange.get_status()
    assert status["mode"] == "SIMULATION_ONLY"
    assert status["real_trading_enabled"] is False
    print("[OK] Simulation safety status")

    print("=" * 60)
    print("=== EXCHANGE SIMULATOR TEST PASSED ===")


if __name__ == "__main__":
    test_exchange_simulator()
