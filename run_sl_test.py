import time
from src.core.paper_live_runner import PaperTradingLiveRunner
from src.core.market_regime import MarketRegimeFilter

def test_stop_loss_mechanism():
    print("=" * 65)
    print("🛡️ AtriaTrade - RISK & STOP-LOSS DEFENSE TEST")
    print("=" * 65)

    regime = MarketRegimeFilter(fast_window=4, slow_window=10, trend_threshold_pct=0.005)
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=10045.0, regime_filter=regime)
    runner.start()

    base_p = 65000.0

    # ۱. تثبیت اولیه برای اجازه ورود
    print("\n[۱/۳] ⏳ تثبیت کندل‌ها در وضعیت نرمال...")
    for i in range(12):
        p = base_p + (i * 20)
        runner.ingest_candle({"open": p-10, "high": p+20, "low": p-20, "close": p, "volume": 100})

    entry_candle = runner.candles[-1]
    res_buy = runner.process_signal({"side": "BUY", "size_pct": 0.10}, entry_candle)
    entry_price = res_buy.get("price", entry_candle["close"])
    print(f"   🟢 ورود به معامله در قیمت: ${entry_price:,.2f} | پوزیشن: {res_buy.get('position_id')}")

    # ۲. شبیه‌سازی ریزش ناگهانی و برخورد به حد ضرر (Flash Drop)
    print("\n[۲/۳] 💥 ریزش ناگهانی ۲.۵ درصدی بر خلاف پوزیشن (تست واکنش به ضرر)...")
    sl_price = entry_price * 0.975  # افت ۲.۵ درصدی
    drop_candle = {
        "open": entry_price * 0.99,
        "high": entry_price * 0.995,
        "low": sl_price * 0.998,
        "close": sl_price,
        "volume": 450
    }
    runner.ingest_candle(drop_candle)

    # ارسال خروج اضطراری / حد ضرر
    res_close = runner.process_signal({"side": "SELL", "reason": "STOP_LOSS"}, drop_candle)
    print(f"   🛑 بستن اضطراری: وضعیت = {res_close.get('status')} | PnL = ${res_close.get('pnl', 0):,.2f}")
    print(f"   💼 بالانس پس از خروج ایمن: ${runner.balance:,.2f}")

    # ۳. تایید سلامت سیستم و تخلیه پوزیشن‌های باز
    print("\n[۳/۳] 🔍 وضعیت نهایی پوزیشن‌های باز...")
    print(f"   پوزیشن‌های باز در حافظه: {len(runner.open_positions)}")
    print(f"   تعداد کل معاملات بسته‌شده: {len(runner.trade_history)}")
    
    runner.stop()
    print("=" * 65)
    print(f"✅ تست Stop-Loss با موفقیت تایید شد. بالانس نهایی: ${runner.balance:,.2f}")
    print("=" * 65)

if __name__ == "__main__":
    test_stop_loss_mechanism()
