import sys
import os

# اطمینان از قابل‌ import بودن پکیج src در هر محیط اجرا (Termux / CI / Local)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from datetime import datetime
from src.data.market_fetcher import MarketFetcher


def main():
    print("=" * 65)
    print("🚀 [AtriaTrade] Fetching Live Market Data from Wallex API...")
    print("=" * 65)

    fetcher = MarketFetcher(use_paper_trading=False)
    symbol = "BTCUSDT"
    timeframe = "1m"
    limit = 5

    print(f"📡 Requesting {limit} candles for {symbol} ({timeframe})...\n")

    try:
        candles = fetcher.fetch_ohlcv(
            exchange_name="WALLEX",
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        if not candles:
            print("⚠️ No candles returned from API.")
            return

        print(f"✅ Success! Received {len(candles)} validated candles:\n")
        print(f"{'Time':<20} | {'Open':<10} | {'High':<10} | {'Low':<10} | {'Close':<10} | {'Volume':<10}")
        print("-" * 75)

        for c in candles:
            dt = datetime.fromtimestamp(c["timestamp"] / 1000).strftime("%Y-%m-%d %H:%M")
            print(
                f"{dt:<20} | {c['open']:<10.2f} | {c['high']:<10.2f} | "
                f"{c['low']:<10.2f} | {c['close']:<10.2f} | {c['volume']:<10.4f}"
            )

        print("\n" + "=" * 65)
        print("🎯 Wallex Live Feed is 100% Operational and Validated!")
        print("=" * 65)

    except Exception as e:
        print(f"❌ Error fetching live data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
