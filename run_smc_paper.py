import sys
import os
import json
from datetime import datetime, timezone

# افزودن مسیر ریشه پروژه به پایتون
sys.path.append(os.path.abspath("."))

from src.core.paper_live_runner import PaperTradingLiveRunner
from src.core.smc_composite_engine import SMCCompositeEngine

def print_banner():
    print("\033[96m" + "="*60)
    print(" 🚀 AtriaTrade - SMC Paper Live Execution Engine Test")
    print("="*60 + "\033[0m")

def main():
    print_banner()

    symbol = "BTC/USDT"
    initial_capital = 1000.0

    print(f"\033[93m[1] مقداردهی اولیه PaperTradingLiveRunner برای {symbol} با سرمایه ${initial_capital}...\033[0m")
    runner = PaperTradingLiveRunner(symbol=symbol, initial_balance=initial_capital)
    runner.start()
    print(f"     وضعیت رانر: {'فعال (Running)' if runner.is_running else 'غیرفعال'}")

    # برای عبور از فیلتر رژیم (slow_window=15)، حداقل 15 کندل گرم‌کردن (Warm-up) تزریق می‌کنیم
    print(f"\033[93m[2] تغذیه تاریخچه کندل‌ها جهت تشخیص رژیم بازار (Warm-up 15 کندل)...\033[0m")
    base_price = 60500.0
    for i in range(16):
        c_price = base_price + (i * 50)  # روند صعودی ملایم و باثبات
        candle = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "open": c_price - 30,
            "high": c_price + 40,
            "low": c_price - 40,
            "close": c_price,
            "volume": 20.0 + i
        }
        runner.ingest_candle(candle)
    
    current_regime = runner.regime_filter.detect_regime(runner.candles).get("regime")
    print(f"     رژیم تشخیص داده شده توسط سیستم: \033[92m{current_regime}\033[0m")

    print(f"\033[93m[3] تحلیل وضعیت با موتور اسمارت مانی (SMCCompositeEngine)...\033[0m")
    smc_engine = SMCCompositeEngine(min_confidence_score=60.0)

    range_high = 65000.0
    range_low = 60000.0
    current_price = 61250.0

    signal = smc_engine.generate_signal(
        symbol=symbol,
        current_price=current_price,
        range_high=range_high,
        range_low=range_low,
        fvg_detected=True,
        fvg_direction="BUY",
        ob_detected=True,
        ob_direction="BUY",
        liquidity_swept=True,
        ote_aligned=True
    )

    print(f"     جهت سیگنال: \033[92m{signal.direction}\033[0m")
    print(f"     سطح اطمینان: {signal.confidence} (امتیاز: {signal.score}/100)")
    print(f"     حد ضرر (SL): {signal.stop_loss} | حد سود (TP): {signal.take_profit}")
    print(f"     همگرایی‌ها: {', '.join(signal.confluences)}")

    # کندل تریگر نهایی
    trigger_candle = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "open": 61200.0,
        "high": 61300.0,
        "low": 61180.0,
        "close": current_price,
        "volume": 55.0
    }
    runner.ingest_candle(trigger_candle)

    print(f"\n\033[93m[4] ارسال سیگنال به ماژول مدیریت پوزیشن Paper Runner...\033[0m")
    execution_result = runner.process_signal(
        signal={"side": signal.direction, "size_pct": 0.15},
        candle=trigger_candle
    )

    print(f"    نتیجه پردازش: {json.dumps(execution_result, indent=2, ensure_ascii=False)}")

    # بررسی وضعیت پوزیشن و موجودی
    print(f"\n\033[96m" + "-"*60)
    print(" 📊 خلاصه وضعیت حساب و پوزیشن‌ها:")
    print(f"    موجودی نقد آزاد: ${runner.balance:.2f}")
    print(f"    تعداد پوزیشن‌های باز: {len(runner.open_positions)}")
    for pos_id, pos in runner.open_positions.items():
        print(f"    📌 شناسه پوزیشن: {pos_id}")
        print(f"       جهت: {pos.get('side')} | قیمت ورود: ${pos.get('entry_price')} | مارجین درگیر: ${pos.get('size'):.2f}")
        print(f"       حجم: {pos.get('units'):.6f} BTC")
    print("="*60 + "\033[0m")

    if execution_result.get("status") == "FILLED":
        print("\033[92m✔ فوق‌العاده است! پوزیشن با موفقیت در پیپر تریدینگ لایو FILLED شد.\033[0m\n")
    else:
        print(f"\033[91m✖ پوزیشن ثبت نشد. دلیل: {execution_result.get('reason')}\033[0m\n")

if __name__ == "__main__":
    main()
