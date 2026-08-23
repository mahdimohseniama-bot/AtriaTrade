"""
Tests for BacktestEngine
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.backtest_engine import BacktestEngine
from src.strategies.sma_cross_strategy import SMACrossStrategy

def test_backtest_engine():
    print("=" * 60)
    print("START: Backtest Engine Comprehensive Test")
    print("=" * 60)

    # Instantiate strategy using matching argument names (short_window & long_window)
    strategy = SMACrossStrategy(short_window=2, long_window=4)
    engine = BacktestEngine(strategy=strategy, initial_capital=1000.0, fee_rate=0.001)

    historical_data = [
        {"timestamp": 1600000000, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 10},
        {"timestamp": 1600000060, "open": 100.0, "high": 102.0, "low": 100.0, "close": 101.0, "volume": 12},
        {"timestamp": 1600000120, "open": 101.0, "high": 103.0, "low": 101.0, "close": 102.0, "volume": 15},
        {"timestamp": 1600000180, "open": 102.0, "high": 104.0, "low": 102.0, "close": 103.0, "volume": 18},
        {"timestamp": 1600000240, "open": 103.0, "high": 106.0, "low": 103.0, "close": 105.0, "volume": 25},
        {"timestamp": 1600000300, "open": 105.0, "high": 105.5, "low": 102.0, "close": 102.5, "volume": 20},
        {"timestamp": 1600000360, "open": 102.5, "high": 103.0, "low": 99.0, "close": 99.5, "volume": 22},
        {"timestamp": 1600000420, "open": 99.5, "high": 100.0, "low": 98.0, "close": 98.5, "volume": 14}
    ]

    summary = engine.run(historical_data, symbol="BTCUSDT")

    print("\nBacktest Summary Metrics:")
    for k, v in summary.items():
        if k != "closed_trades":
            print(f"  - {k}: {v}")

    # Assertions
    assert "total_trades" in summary
    assert "win_rate_percent" in summary
    assert "max_drawdown_percent" in summary
    assert "closed_trades" in summary
    assert summary["initial_capital"] == 1000.0
    assert isinstance(summary["final_capital"], float)
    assert isinstance(summary["net_profit"], float)

    print("\n" + "=" * 60)
    print("=== BACKTEST ENGINE TEST PASSED ===")
    print("=" * 60)

if __name__ == "__main__":
    test_backtest_engine()
