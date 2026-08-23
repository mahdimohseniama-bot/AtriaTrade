"""
تست‌های موتور معاملات آزمایشی (Paper Trading Engine) — AtriaTrade
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.core.trading_engine import PaperTradingEngine

passed = 0


def check(condition, message):
    global passed
    if condition:
        passed += 1
        print(f"  [OK] {message}")
    else:
        raise AssertionError(f"خطا: {message}")


def test_01_engine_creation():
    print("تست ۱: ساخت موتور با تنظیمات اولیه")
    engine = PaperTradingEngine(initial_capital=10000.0, max_position_value=20000.0, risk_per_trade=0.02)
    check(engine.cash == 10000.0, "نقدینگی اولیه ۱۰۰۰۰ است")
    check(engine.get_open_trades() == [], "هیچ پوزیشن بازی در شروع وجود ندارد")
    check(engine.get_equity() == 10000.0, "سرمایه کل (Equity) برابر ۱۰۰۰۰ است")
    check(engine.generate_signal("BTCUSDT") == "HOLD", "بدون تاریخچه کافی، سیگنال HOLD است")


def test_02_open_buy_trade():
    print("تست ۲: باز کردن معامله BUY با محاسبه حجم از روی ریسک")
    engine = PaperTradingEngine(initial_capital=10000.0, max_position_value=20000.0, risk_per_trade=0.02)
    engine.update_price("BTCUSDT", 50000.0)
    trade = engine.open_trade("BTCUSDT", side="BUY", price=50000.0,
                              stop_loss=49000.0, take_profit=52000.0)
    check(abs(trade.quantity - 0.2) < 1e-9, f"حجم محاسبه‌شده 0.2 است ({trade.quantity})")
    check(trade.status == "OPEN", "وضعیت معامله OPEN است")
    check(len(engine.get_open_trades()) == 1, "یک پوزیشن باز وجود دارد")
    check(engine.cash == 0.0, "کل نقدینگی صرف پوزیشن شده است")


def test_03_stop_loss():
    print("تست ۳: فعال شدن خودکار حد ضرر (Stop Loss)")
    engine = PaperTradingEngine(initial_capital=10000.0, max_position_value=20000.0, risk_per_trade=0.02)
    engine.update_price("BTCUSDT", 50000.0)
    engine.open_trade("BTCUSDT", "BUY", price=50000.0, stop_loss=49000.0, take_profit=52000.0)
    events = engine.update_price("BTCUSDT", 49000.0)
    check(len(events) == 1, "یک رویداد بستن معامله رخ داد")
    check(events[0].reason == "STOP_LOSS", "دلیل بستن STOP_LOSS است")
    check(abs(events[0].pnl - (-200.0)) < 1e-6, f"ضرر دقیقاً ۲۰۰ دلار است ({events[0].pnl})")
    check(engine.get_open_trades() == [], "پوزیشن بسته شده است")
    check(abs(engine.cash - 9800.0) < 1e-6, f"نقدینگی پس از ضرر ۹۸۰۰ است ({engine.cash})")


def test_04_take_profit():
    print("تست ۴: فعال شدن خودکار حد سود (Take Profit)")
    engine = PaperTradingEngine(initial_capital=10000.0, max_position_value=20000.0, risk_per_trade=0.02)
    engine.update_price("BTCUSDT", 50000.0)
    engine.open_trade("BTCUSDT", "BUY", price=50000.0, stop_loss=49000.0, take_profit=52000.0)
    events = engine.update_price("BTCUSDT", 52000.0)
    check(len(events) == 1, "یک رویداد بستن معامله رخ داد")
    check(events[0].reason == "TAKE_PROFIT", "دلیل بستن TAKE_PROFIT است")
    check(abs(events[0].pnl - 400.0) < 1e-6, f"سود ۴۰۰ دلار است ({events[0].pnl})")
    check(abs(engine.cash - 10400.0) < 1e-6, f"نقدینگی پس از سود ۱۰۴۰۰ است ({engine.cash})")


def test_05_max_position_value():
    print("تست ۵: محدود شدن حجم توسط سقف ارزش پوزیشن")
    engine = PaperTradingEngine(initial_capital=10000.0, max_position_value=5000.0, risk_per_trade=0.02)
    engine.update_price("BTCUSDT", 50000.0)
    trade = engine.open_trade("BTCUSDT", "BUY", price=50000.0, stop_loss=49000.0)
    check(abs(trade.quantity - 0.1) < 1e-9, f"حجم به 0.1 محدود شده است ({trade.quantity})")
    check(abs(trade.quantity * trade.entry_price - 5000.0) < 1e-6, "ارزش پوزیشن دقیقاً ۵۰۰۰ است")


def test_06_sell_trade():
    print("تست ۶: معامله SELL (شورت) و حد سود آن")
    engine = PaperTradingEngine(initial_capital=10000.0, max_position_value=20000.0, risk_per_trade=0.02)
    engine.update_price("BTCUSDT", 50000.0)
    trade = engine.open_trade("BTCUSDT", "SELL", price=50000.0,
                              stop_loss=51000.0, take_profit=48000.0)
    check(abs(trade.quantity - 0.2) < 1e-9, "حجم معامله SELL برابر 0.2 است")
    events = engine.update_price("BTCUSDT", 48000.0)
    check(events[0].reason == "TAKE_PROFIT", "حد سود فروش فعال شد")
    check(abs(events[0].pnl - 400.0) < 1e-6, f"سود فروش ۴۰۰ دلار است ({events[0].pnl})")


def test_07_invalid_stop_loss():
    print("تست ۷: رد حد ضرر اشتباه")
    engine = PaperTradingEngine(initial_capital=10000.0, max_position_value=20000.0, risk_per_trade=0.02)
    engine.update_price("BTCUSDT", 50000.0)
    try:
        engine.open_trade("BTCUSDT", "BUY", price=50000.0, stop_loss=51000.0)
        check(False, "حد ضرر بالاتر از قیمت خرید باید رد شود")
    except ValueError:
        check(True, "حد ضرر اشتباه با ValueError رد شد")


def test_08_default_signal_bullish():
    print("تست ۸: سیگنال میانگین متحرک در روند صعودی")
    engine = PaperTradingEngine(initial_capital=10000.0, max_position_value=20000.0, risk_per_trade=0.02)
    for i in range(25):
        engine.update_price("BTCUSDT", 100.0 + i)
    check(engine.generate_signal("BTCUSDT") == "BUY", "در روند صعودی سیگنال BUY است")


def test_09_default_signal_bearish():
    print("تست ۹: سیگنال میانگین متحرک در روند نزولی")
    engine = PaperTradingEngine(initial_capital=10000.0, max_position_value=20000.0, risk_per_trade=0.02)
    for i in range(25):
        engine.update_price("ETHUSDT", 200.0 - i)
    check(engine.generate_signal("ETHUSDT") == "SELL", "در روند نزولی سیگنال SELL است")


def test_10_save_load_state():
    print("تست ۱۰: ذخیره و بازیابی وضعیت موتور")
    engine = PaperTradingEngine(initial_capital=10000.0, max_position_value=20000.0, risk_per_trade=0.02)
    engine.update_price("BTCUSDT", 50000.0)
    engine.open_trade("BTCUSDT", "BUY", price=50000.0, stop_loss=49000.0, take_profit=52000.0)
    engine.update_price("BTCUSDT", 49000.0)
    path = engine.save_state()
    check(os.path.exists(path), f"فایل وضعیت ساخته شد: {path}")

    engine2 = PaperTradingEngine(initial_capital=1.0)
    engine2.load_state(path)
    check(engine2.cash == engine.cash, "نقدینگی بازیابی شد")
    check(len(engine2.get_closed_trades()) == 1, "تاریخچه معاملات بسته بازیابی شد")
    check(abs(engine2.get_closed_trades()[0].pnl - (-200.0)) < 1e-6, "سود/زیان بازیابی شد")
    check(engine2.get_equity() == engine.get_equity(), "سرمایه کل بازیابی شد")


def show_demo_status():
    print("\nنمایش وضعیت موتور پس از یک معامله سودده:")
    engine = PaperTradingEngine(initial_capital=10000.0, max_position_value=20000.0, risk_per_trade=0.02)
    engine.update_price("BTCUSDT", 50000.0)
    engine.open_trade("BTCUSDT", "BUY", price=50000.0, stop_loss=49000.0, take_profit=52000.0)
    engine.update_price("BTCUSDT", 52000.0)
    status = engine.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")


def main():
    print("=" * 50)
    print("آزمون موتور معاملات آزمایشی AtriaTrade")
    print("=" * 50)
    test_01_engine_creation()
    test_02_open_buy_trade()
    test_03_stop_loss()
    test_04_take_profit()
    test_05_max_position_value()
    test_06_sell_trade()
    test_07_invalid_stop_loss()
    test_08_default_signal_bullish()
    test_09_default_signal_bearish()
    test_10_save_load_state()
    show_demo_status()
    print("-" * 50)
    print(f"همه {passed} تست با موفقیت پاس شدند")
    print("=== TRADING ENGINE TEST PASSED ===")


if __name__ == "__main__":
    main()
