import sys
import os
import json
from datetime import datetime, timezone

sys.path.append(os.path.abspath("."))

from src.core.paper_live_runner import PaperTradingLiveRunner

def main():
    print("\033[96m" + "="*60)
    print(" 🎯 AtriaTrade - تست سناریوی خروج پوزیشن (TP/PnL Exit)")
    print("="*60 + "\033[0m")

    symbol = "BTC/USDT"
    runner = PaperTradingLiveRunner(symbol=symbol, initial_balance=1000.0)
    runner.start()

    # ۱. آماده‌سازی تاریخچه برای رژیم بازار
    base_price = 60500.0
    for i in range(16):
        c_price = base_price + (i * 50)
        runner.ingest_candle({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "open": c_price - 20,
            "high": c_price + 30,
            "low": c_price - 30,
            "close": c_price,
            "volume": 20.0
        })

    # ۲. ورود به پوزیشن در قیمت 61,250
    entry_price = 61250.0
    entry_candle = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "open": 61200.0,
        "high": 61300.0,
        "low": 61180.0,
        "close": entry_price,
        "volume": 50.0
    }
    runner.ingest_candle(entry_candle)
    entry_res = runner.process_signal({"side": "BUY", "size_pct": 0.15}, entry_candle)
    print(f"\033[92m✔ ورود انجام شد:\033[0m {entry_res}")
    print(f"   موجودی نقد پس از ورود: ${runner.balance:.2f}")

    # ۳. سناریوی رشد قیمت و رسیدن به تارگت SMC (قیمت 65,000)
    tp_price = 65000.0
    tp_candle = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "open": 64800.0,
        "high": 65100.0,
        "low": 64750.0,
        "close": tp_price,
        "volume": 75.0
    }
    runner.ingest_candle(tp_candle)

    print(f"\n\033[93m[3] ارسال سیگنال خروج (SELL) در قیمت تارگت ${tp_price}...\033[0m")
    exit_res = runner.process_signal({"side": "SELL"}, tp_candle)
    print(f"    نتیجه پردازش خروج: {json.dumps(exit_res, indent=2, ensure_ascii=False)}")

    # ۴. بررسی نتیجه مالی
    print(f"\n\033[96m" + "-"*60)
    print(" 📊 بیلان مالی پس از بسته شدن معامله:")
    print(f"    موجودی اولیه: $1000.00")
    print(f"    موجودی نهایی حساب: ${runner.balance:.2f}")
    net_pnl = runner.balance - 1000.0
    print(f"    سود/زیان کل (Net PnL): {'+' if net_pnl >= 0 else ''}${net_pnl:.2f}")
    print(f"    تعداد پوزیشن‌های باز باقی‌مانده: {len(runner.open_positions)}")
    print(f"    تعداد معاملات ثبت‌شده در تاریخچه: {len(runner.trade_history)}")
    print("="*60 + "\033[0m")

    if exit_res.get("status") == "CLOSED" and net_pnl > 0:
        print("\033[92m✔ عالی! چرخه کامل معامله (ورود -> تارگت -> خروج -> تسویه بالانس) بدون باگ انجام شد.\033[0m\n")
    else:
        print("\033[91m✖ خطا در بستن پوزیشن رخ داد.\033[0m\n")

if __name__ == "__main__":
    main()
