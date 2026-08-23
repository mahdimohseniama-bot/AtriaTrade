"""
تست‌های اعتبارسنجی Backtesting Engine
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.backtest_engine import BacktestEngine, BacktestTrade


class MockStrategy:
    """استراتژی ساختگی جهت تست منطق بک‌تست"""
    def __init__(self, actions):
        self.actions = actions
        self.call_count = 0

    def generate_signal(self, history):
        if self.call_count < len(self.actions):
            sig = self.actions[self.call_count]
            self.call_count += 1
            return sig
        return "HOLD"

    def get_tp_sl(self, signal, price):
        if signal == "BUY":
            return round(price * 1.05, 2), round(price * 0.95, 2)
        return round(price * 0.95, 2), round(price * 1.05, 2)


def test_backtest_full_flow():
    print("=" * 50)
    print("شروع تست‌های Backtesting Engine")
    print("=" * 50)

    engine = BacktestEngine(initial_capital=10000.0, fee_rate=0.001)

    candles = [
        {"timestamp": "2026-01-01", "open": 100, "high": 102, "low": 98, "close": 100, "volume": 1000},
        {"timestamp": "2026-01-02", "open": 100, "high": 108, "low": 99, "close": 106, "volume": 1200},  # Trigger TP
        {"timestamp": "2026-01-03", "open": 106, "high": 107, "low": 101, "close": 102, "volume": 900},
        {"timestamp": "2026-01-04", "open": 102, "high": 103, "low": 90, "close": 91, "volume": 1500},
    ]

    # کندل اول سیگنال BUY و مابقی HOLD
    strategy = MockStrategy(["BUY", "HOLD", "HOLD", "HOLD"])
    report = engine.run(symbol="BTCUSDT", candles=candles, strategy=strategy)

    assert report["total_trades"] == 1, f"Expected 1 trade, got {report['total_trades']}"
    assert report["winning_trades"] == 1, "Expected 1 winning trade"
    assert report["final_equity"] > 10000.0, "Expected profit in final equity"
    assert report["win_rate_pct"] == 100.0, "Expected 100% win rate"
    assert "max_drawdown_pct" in report
    assert "sharpe_ratio" in report

    print("[OK] تست اجرای کامل و محاسبه حد سود موفق بود")
    print("[OK] گزارش نهایی بک‌تست:", report)
    print("=" * 50)
    print("=== BACKTEST ENGINE TEST PASSED ===")


if __name__ == "__main__":
    test_backtest_full_flow()
