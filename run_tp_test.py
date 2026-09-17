from src.core.paper_live_runner import PaperTradingLiveRunner
from src.core.market_regime import MarketRegimeFilter

def test_take_profit_rally():
    print("=" * 65)
    print("🎯 AtriaTrade - MULTI-CANDLE PROFIT HARVEST TEST")
    print("=" * 65)

    regime = MarketRegimeFilter(fast_window=4, slow_window=10, trend_threshold_pct=0.003)
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=10019.89, regime_filter=regime)
    runner.start()

    base_p = 65000.0

    # ۱. استقرار کندل‌ها و ایجاد تقاضای خرید
    print("\n[۱/۳] 🟢 شناسایی مومنتوم صعودی و ورود به پوزیشن...")
    for i in range(12):
        p = base_p + (i * 35)
        runner.ingest_candle({"open": p-15, "high": p+25, "low": p-20, "close": p, "volume": 120})

    entry_candle = runner.candles[-1]
    res_buy = runner.process_signal({"side": "BUY", "size_pct": 0.15}, entry_candle)
    entry_price = res_buy.get("price", entry_candle["close"])
    print(f"   🚀 پوزیشن خرید باز شد: ورود در ${entry_price:,.2f} | پوزیشن: {res_buy.get('position_id')}")

    # ۲. شبیه‌سازی رالی صعودی قوی (Bull Rally +3.5%)
    print("\n[۲/۳] 📈 شبیه‌سازی پمپاژ قیمت و فتح اهداف بالاتر (Bull Rally)...")
    rally_prices = [entry_price * 1.012, entry_price * 1.025, entry_price * 1.038]
    for idx, target_p in enumerate(rally_prices, 1):
        c = {
            "open": target_p * 0.995,
            "high": target_p * 1.005,
            "low": target_p * 0.992,
            "close": target_p,
            "volume": 300 + (idx * 50)
        }
        res_ingest = runner.ingest_candle(c)
        print(f"   کندل {idx}: قیمت = ${target_p:,.2f} | رژیم بازار = {res_ingest.get('regime')}")

    # ۳. صدور سیگنال شناسایی سود در تارگت نهایی (TP Hit)
    print("\n[۳/۳] 💰 لمس تارگت نهایی و بستن پوزیشن با سود...")
    exit_candle = runner.candles[-1]
    res_close = runner.process_signal({"side": "SELL", "reason": "TAKE_PROFIT_TARGET_HIT"}, exit_candle)
    
    print(f"   ✨ خروج موفق: وضعیت = {res_close.get('status')} | سود شناسایی‌شده (PnL) = ${res_close.get('pnl', 0):,.2f}")
    print(f"   💼 بالانس جدید کیف‌پول: ${runner.balance:,.2f}")
    print(f"   پوزیشن‌های باز: {len(runner.open_positions)} | معاملات بسته‌شده: {len(runner.trade_history)}")

    runner.stop()
    print("=" * 65)
    print(f"✅ تست حد سود تکمیل شد. بالانس نهایی: ${runner.balance:,.2f}")
    print("=" * 65)

if __name__ == "__main__":
    test_take_profit_rally()
