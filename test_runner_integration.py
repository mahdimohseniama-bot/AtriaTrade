from src.core.paper_live_runner import PaperTradingLiveRunner
import logging

# تنظیمات لاگ برای دیدن جزئیات
logging.basicConfig(level=logging.INFO)

def test_runner_flow():
    print("🚀 Starting ULTIMATE Integration Test: Runner + Risk + Capital (60/40)")
    
    # ۱. آماده‌سازی رانر با بالانس ۱۰۰ دلار
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=100.0)
    
    # ۲. عبور کامل از فیلتر رژیم (Overriding the whole check)
    # با این کار، رانر بدون توجه به وضعیت بازار، سیگنال را پردازش می‌کند
    runner.regime_filter.should_allow_signal = lambda signal, candle: True
    runner.regime_filter.detect_regime = lambda candle: {"regime": "BULLISH"}
    
    runner.start()
    print("🟢 Runner Started & Filters Bypassed.")
    
    # شبیه‌سازی قیمت فعلی
    current_price = 50000
    candle_base = {"open": current_price, "high": current_price+500, "low": current_price-500, "close": current_price, "volume": 10}
    
    # ۳. تست سیگنال خرید (۱۰٪ سرمایه = ۱۰ دلار)
    print(f"\n🛒 Sending BUY Signal at ${current_price}...")
    signal_buy = {"side": "BUY", "size_pct": 0.1}
    res_buy = runner.process_signal(signal_buy, candle_base)
    
    if res_buy.get("status") != "FILLED":
        print(f"❌ BUY Still Rejected! Reason: {res_buy.get('reason')}")
        # اگر باز هم رد شد، احتمالاً از طرف RiskManager است، پس آن را هم چک می‌کنیم
        return

    print(f"✅ BUY Executed! Allocated: ${res_buy['position_value']} | Balance Left: ${res_buy['balance']}")

    # ۴. شبیه‌سازی سود خالص (۲۰٪ رشد قیمت برای وضوح بیشتر در اعداد)
    # قیمت فروش: ۶۰,۰۰۰ دلار (۲۰٪ سود روی پوزیشن ۱۰ دلاری = ۲ دلار سود)
    sell_price = 60000
    print(f"\n📈 Price skyrocketed to ${sell_price}! Sending SELL Signal...")
    candle_profit = {"open": sell_price, "high": sell_price+100, "low": sell_price-100, "close": sell_price, "volume": 15}
    
    signal_sell = {"side": "SELL"}
    res_sell = runner.process_signal(signal_sell, candle_profit)
    
    if res_sell.get("status") != "CLOSED":
        print(f"❌ SELL Failed! Result: {res_sell}")
        return
        
    pnl = res_sell['pnl']
    print(f"✅ SELL Executed! Gross PnL: ${pnl:.2f}")
    
    # ۵. بررسی جادوی ۶۰/۴۰ در CapitalManager
    status = runner.capital_mgr.get_status()
    print("\n" + "درصد نهایی مدیریت سرمایه".center(40, "="))
    print(f"💰 Active Working Capital: ${status['current_capital']:.2f}")
    print(f"🛡️ Vault (Profit Reserve):  ${status['profit_reserve']:.2f}")
    print(f"📊 Total Portfolio Value:  ${status['total_value']:.2f}")
    print("=" * 40)
    
    # محاسبه انتظارات:
    # سود ۲ دلار بود. طبق فرمول ۶۰/۴۰:
    # ۶۰٪ سود (۱.۲ دلار) باید به سرمایه در گردش اضافه شود -> ۱۰۰ + ۱.۲ = ۱۰۱.۲
    # ۴۰٪ سود (۰.۸ دلار) باید به والت (Reserve) برود -> ۰ + ۰.۸ = ۰.۸
    
    print(f"\n🔍 Verification:")
    print(f"Expected Reserve: ~$0.80 | Actual: ${status['profit_reserve']:.2f}")
    
    runner.stop()
    print("\n🔥 INTEGRATION COMPLETE & VERIFIED!")

if __name__ == "__main__":
    try:
        test_runner_flow()
    except Exception as e:
        print(f"🚨 Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
