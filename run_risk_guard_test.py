from src.core.paper_live_runner import PaperTradingLiveRunner
from src.core.market_regime import MarketRegimeFilter

def test_portfolio_exposure_guard():
    print("=" * 65)
    print("🛡️ AtriaTrade - PORTFOLIO EXPOSURE & ANTI-OVERTRADING TEST")
    print("=" * 65)

    regime = MarketRegimeFilter(fast_window=4, slow_window=10, trend_threshold_pct=0.002)
    # تنظیم دقیق: ماکسیمم ریسک سبد 30 درصد تعریف می‌شود
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=10077.0, regime_filter=regime)
    runner.portfolio_risk.max_total_exposure_pct = 0.30  # سقف ۳۰٪ معادل حدود ۳۰۲۳ دلار
    runner.start()

    base_p = 66000.0

    # ۱. تثبیت کندل‌ها در فاز صعودی
    print("\n[۱/۳] ⏳ تزریق کندل‌های صعودی و آماده‌سازی بازار...")
    for i in range(12):
        p = base_p + (i * 20)
        runner.ingest_candle({"open": p-10, "high": p+20, "low": p-15, "close": p, "volume": 150})

    current_c = runner.candles[-1]

    # ۲. باز کردن پوزیشن اول (تخصیص ۲۰٪ سرمایه)
    print("\n[۲/۳] 🟢 تلاش برای ورود به پوزیشن اول (تخصیص ۲۰٪ سرمایه)...")
    res1 = runner.process_signal({"side": "BUY", "size_pct": 0.20}, current_c)
    print(f"   وضعیت سفارش ۱: {res1.get('status')} | حجم: ${res1.get('position', {}).get('size', 0):,.2f}")

    # ۳. تلاش برای ورود فراتر از سقف مجاز ریسک سبد (درخواست ۲۰٪ دیگر که جمعاً ۴۰٪ > ۳۰٪ می‌شود)
    print("\n[۳/۳] 🛑 تلاش برای ورود به پوزیشن دوم (تخطی از سقف ریسک ۳۰ درصدی)...")
    res2 = runner.process_signal({"side": "BUY", "size_pct": 0.20}, current_c)
    print(f"   وضعیت سفارش ۲: {res2.get('status')} | دلیل رد: {res2.get('reason')}")

    # بررسی تایید دفاع ریسک
    print("\n🔍 گزارش وضعیت امنیت سرمایه:")
    print(f"   پوزیشن‌های باز مجاز: {len(runner.open_positions)}")
    print(f"   بالانس در امان مانده: ${runner.balance:,.2f}")

    runner.stop()
    print("=" * 65)
    if res2.get("status") == "REJECTED":
        print("✅ تست فیلتر سقف ریسک سبد (Portfolio Risk Guard) با موفقیت کامل پاس شد!")
    else:
        print("❌ خطا: سیستم مانع از افزایش بی‌رویه ریسک نشد!")
    print("=" * 65)

if __name__ == "__main__":
    test_portfolio_exposure_guard()
