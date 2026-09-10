import sys
import os
from unittest.mock import MagicMock

# افزودن مسیر ریشه پروژه
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.paper_live_runner import PaperTradingLiveRunner

def test_paper_trading_integration_lifecycle():
    print("\n" + "="*50)
    print("🚀 [AtriaTrade] شروع تست یکپارچگی چرخه معاملاتی...")
    print("="*50)

    initial_balance = 100.0
    symbol = "BTC/USDT"

    # ساخت رانر
    runner = PaperTradingLiveRunner(symbol=symbol, initial_balance=initial_balance)
    
    # موک کردن متد واقعی رژیم بازار
    runner.regime_filter.detect_regime = MagicMock(return_value={"regime": "BULL_TREND", "reason": "Test Bull"})
    runner.regime_filter.should_allow_signal = MagicMock(return_value=True)

    # 1. فعال‌سازی رانر
    runner.start()
    assert runner.is_running is True, "❌ رانر باید فعال باشد."
    print("✅ مرحله ۱: رانر با موجودی ۱۰۰ دلار فعال شد.")

    # 2. سیگنال خرید
    buy_candle = {"close": 50000.0, "volume": 100.0}
    buy_signal = {"side": "BUY", "size_pct": 0.10}

    buy_res = runner.process_signal(buy_signal, buy_candle)
    print(f"📥 خروجی خرید: {buy_res}")

    assert buy_res.get("status") == "FILLED", f"❌ خرید انجام نشد: {buy_res}"
    assert buy_res.get("price") == 50000.0
    assert buy_res.get("size") == 10.0
    assert len(runner.open_positions) >= 1
    print("✅ مرحله ۲: پوزیشن خرید با موفقیت در سیستم ثبت شد.")

    # 3. سیگنال فروش با سود
    sell_candle = {"close": 55000.0, "volume": 100.0}
    sell_signal = {"side": "SELL"}

    sell_res = runner.process_signal(sell_signal, sell_candle)
    print(f"📤 خروجی فروش: {sell_res}")

    assert sell_res.get("status") == "CLOSED", f"❌ سفارش فروش بسته نشد: {sell_res}"
    assert len(runner.open_positions) == 0
    print("✅ مرحله ۳: پوزیشن با سود بسته شد و موجودی به‌روزرسانی گردید.")

    # 4. متوقف‌سازی
    runner.stop()
    assert runner.is_running is False
    print("✅ مرحله ۴: رانر متوقف شد.")

    print("\n" + "="*50)
    print("🎯 تمامی مراحل تست یکپارچگی با موفقیت ۱۰۰٪ پاس شدند!")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_paper_trading_integration_lifecycle()
