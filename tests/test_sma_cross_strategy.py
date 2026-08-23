"""
Tests for SMA Cross Strategy
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategies.sma_cross_strategy import SMACrossStrategy


def test_sma_strategy():
    print("=" * 55)
    print("START: SMA Cross Strategy Tests")
    print("=" * 55)

    strategy = SMACrossStrategy(
        short_window=3,
        long_window=5,
        take_profit_pct=0.05,
        stop_loss_pct=0.02,
    )

    # 1. Insufficient data -> HOLD
    assert strategy.generate_signal([100, 101, 102, 103]) == "HOLD"
    print("[OK] Insufficient data -> HOLD")

    # 2. Bullish trend -> BUY
    bullish_prices = [100, 100, 100, 110, 120]
    assert strategy.generate_signal(bullish_prices) == "BUY"
    print("[OK] Bullish trend -> BUY")

    # 3. Bearish trend -> SELL
    bearish_prices = [120, 110, 100, 100, 100]
    assert strategy.generate_signal(bearish_prices) == "SELL"
    print("[OK] Bearish trend -> SELL")

    # 4. BUY TP / SL
    buy_tp, buy_sl = strategy.get_tp_sl("BUY", 100.0)
    assert buy_tp == 105.0
    assert buy_sl == 98.0
    print("[OK] BUY TP / SL calculation")

    # 5. SELL TP / SL
    sell_tp, sell_sl = strategy.get_tp_sl("SELL", 100.0)
    assert sell_tp == 95.0
    assert sell_sl == 102.0
    print("[OK] SELL TP / SL calculation")

    # 6. HOLD TP / SL
    hold_tp, hold_sl = strategy.get_tp_sl("HOLD", 100.0)
    assert hold_tp == 0.0
    assert hold_sl == 0.0
    print("[OK] HOLD TP / SL returns (0, 0)")

    # 7. Validation
    try:
        SMACrossStrategy(short_window=20, long_window=5)
        raise AssertionError("Expected ValueError on invalid windows")
    except ValueError:
        print("[OK] Window validation passed")

    print("=" * 55)
    print("=== SMA CROSS STRATEGY TEST PASSED ===")


if __name__ == "__main__":
    test_sma_strategy()
