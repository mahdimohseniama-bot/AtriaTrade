import sys
import os
import time
import random

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.adapters.nobitex_paper import NobitexPaperAdapter
from src.core.paper_live_runner import PaperTradingLiveRunner


def make_candle_from_price(price: float) -> dict:
    high = price * (1.0 + random.uniform(0.0002, 0.0012))
    low = price * (1.0 - random.uniform(0.0002, 0.0012))
    return {
        "timestamp": int(time.time()),
        "open": price,
        "high": high,
        "low": low,
        "close": price,
        "volume": random.uniform(0.1, 1.5),
    }


def main():
    print("🚀 در حال راه‌اندازی موتور Paper Trading نوبیتکس (AtriaTrade)...")

    # 1) آداپتر پیپر نوبیتکس
    adapter = NobitexPaperAdapter(initial_balances={"rls": 500_000_000.0, "btc": 0.0})

    # 2) رانر پیپر موتور اصلی
    runner = PaperTradingLiveRunner(symbol="BTCIRT", initial_balance=500_000_000.0)
    runner.start()

    print("✅ موتور فعال شد")
    print("💼 Balances (Adapter):", adapter.get_all_balances())

    symbol = "BTCIRT"
    price = 6_500_000_000.0  # قیمت پایه اولیه (تومان)

    print("\n--- شروع حلقه شبیه‌سازی بازار (۱۰ سیکل) ---")
    for cycle in range(1, 11):
        # تغییر جزئی قیمت
        price *= (1.0 + random.uniform(-0.002, 0.002))

        # تزریق قیمت به آداپتر
        adapter.set_market_price(symbol, price)
        ticker = adapter.get_ticker(symbol)
        last_price = ticker.get("last", price)

        # ساخت کندل و تزریق به موتور رانر
        candle = make_candle_from_price(last_price)
        status = runner.ingest_candle(candle)

        regime = status.get("regime", "N/A")
        open_pos = status.get("open_positions_count", 0)
        bal = status.get("balance", 0.0)

        print(
            f"[{cycle:02d}/10] Price: {last_price:,.0f} RLS | Regime: {regime} | "
            f"Open Positions: {open_pos} | Runner Bal: {bal:,.0f}"
        )

        time.sleep(0.5)

    runner.stop()
    print("\n🛑 Runner stopped")
    print("🎉 تست پیپر با موفقیت اجرا شد.")


if __name__ == "__main__":
    main()
