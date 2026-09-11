import os
import sys
import time
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.adapters.wallex_paper import WallexPaperAdapter


def main():
    print("=" * 65)
    print("🤖 [AtriaTrade] Live Paper Runner - Wallex Terminal Engine")
    print("=" * 65)

    symbol = "BTCUSDT"
    timeframe = "1m"
    adapter = WallexPaperAdapter(initial_balance_usdt=100.0)

    print(f"💰 Starting Capital : ${adapter.balance_usdt:.2f} USDT")
    print(f"🎯 Target Pair      : {symbol}")
    print(f"⏳ Timeframe        : {timeframe}")
    print("-" * 65)
    print("📡 Polling market data (Press Ctrl+C to stop)...\n")

    try:
        iteration = 1
        while iteration <= 3:  # اجرای تستی ۳ چرخه
            candles = adapter.get_market_candles(symbol=symbol, timeframe=timeframe, limit=5)
            latest_price = adapter.get_latest_price(symbol)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"[{now_str}] Cycle #{iteration}")
            print(f"  📊 Validated Candles Cached: {len(candles)}")
            print(f"  💵 Latest Market Price     : {latest_price:,.2f} USDT")
            print(f"  💼 Active Positions        : {len(adapter.positions)}")
            print(f"  🏦 Total Balance           : ${adapter.balance_usdt:.2f} USDT")
            print("-" * 65)

            iteration += 1
            if iteration <= 3:
                time.sleep(3)

        print("✅ Live Paper Engine Loop executed successfully without errors!")
    except KeyboardInterrupt:
        print("\n🛑 Runner stopped by user.")
    except Exception as err:
        print(f"\n❌ Runner Error: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
