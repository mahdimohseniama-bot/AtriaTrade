import time
from src.core.paper_live_runner import PaperTradingLiveRunner
from src.core.market_regime import MarketRegimeFilter

def test_full_lifecycle():
    print("=" * 65)
    print("⚡ AtriaTrade - MULTI-REGIME & EXECUTION LIFECYCLE")
    print("=" * 65)

    # تنظیم رژیم با ترش‌هولد دقیق برای تشخیص صعودی و نزولی
    regime = MarketRegimeFilter(fast_window=4, slow_window=10, trend_threshold_pct=0.008)
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=10000.0, regime_filter=regime)
    runner.start()

    base_price = 60000.0

    # مرحله ۱: ایجاد یک پامپ صعودی با شیب قوی برای قفل شدن در BULL_TREND
    print("\n[۱/۳] 📈 شبیه‌سازی موج صعودی (Bull Wave)...")
    for i in range(15):
        # رشد شارپ ۱ درصدی در هر کندل
        p = base_price * ((1.01) ** i)
        c = {"open": p * 0.995, "high": p * 1.005, "low": p * 0.99, "close": p, "volume": 150 + i * 10}
        runner.ingest_candle(c)

    reg_info = runner.regime_filter.detect_regime(runner.candles)
    print(f"   📊 وضعیت رژیم: [{reg_info['regime']}] | قدرت روند: {reg_info['trend_strength_pct']*100:.2f}%")

    # ورود سیگنال خرید
    last_c = runner.candles[-1]
    res_buy = runner.process_signal({"side": "BUY", "size_pct": 0.15}, last_c)
    print(f"   🟢 سیگنال خرید: {res_buy.get('status')} | پوزیشن: {res_buy.get('position_id')} | ورود: ${res_buy.get('price', 0):,.2f}")

    # مرحله ۲: کسب سود و فروش در اوج
    print("\n[۲/۳] 🎯 تارگت سود محقق شد - ارسال سیگنال تسویه (Take-Profit)...")
    tp_price = last_c["close"] * 1.03  # ۳٪ سود
    tp_candle = {"open": tp_price*0.998, "high": tp_price*1.002, "low": tp_price*0.995, "close": tp_price, "volume": 220}
    runner.ingest_candle(tp_candle)
    res_sell = runner.process_signal({"side": "SELL"}, tp_candle)
    print(f"   💰 تسویه معامله: {res_sell.get('status')} | سود خالص (PnL): ${res_sell.get('pnl', 0):,.2f} | بالانس فعلی: ${runner.balance:,.2f}")

    # مرحله ۳: شبیه‌سازی موج نزولی (Bear Wave) و مسدود شدن خرید اشتباه
    print("\n[۳/۳] 📉 شبیه‌سازی ریزش شارپ بازار (DUMP) و اعتبارسنجی محافظ رژیم...")
    current_p = tp_price
    for i in range(15):
        current_p = current_p * 0.985  # ریزش ۱.۵ درصدی هر کندل
        c_dump = {"open": current_p * 1.005, "high": current_p * 1.01, "low": current_p * 0.99, "close": current_p, "volume": 300}
        runner.ingest_candle(c_dump)

    dump_reg = runner.regime_filter.detect_regime(runner.candles)
    print(f"   📊 وضعیت رژیم پس از ریزش: [{dump_reg['regime']}] | شیب: {dump_reg['trend_strength_pct']*100:.2f}%")

    # تست سیستم ایمنی: آیا ربات جلوی ورود BUY در رژیم نزولی را می‌گیرد؟
    res_rejected = runner.process_signal({"side": "BUY", "size_pct": 0.1}, runner.candles[-1])
    print(f"   🛡️ نتیجه تلاش برای خرید در روند نزولی: وضعیت = {res_rejected.get('status')} | دلیل = {res_rejected.get('reason')}")

    runner.stop()
    print("\n" + "=" * 65)
    print(f"🏆 بالانس نهایی سرمایه: ${runner.balance:,.2f}")
    print(f"📑 کل معاملات خاتمه‌یافته: {len(runner.trade_history)}")
    print("=" * 65)

if __name__ == "__main__":
    test_full_lifecycle()
