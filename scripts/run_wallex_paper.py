#!/usr/bin/env python3
import sys
from pathlib import Path

# تنظیم داینامیک ریشه پروژه در sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.adapters.paper_factory import PaperExchangeFactory
from src.core.paper_live_runner import PaperTradingLiveRunner

def main():
    print("=" * 60)
    print("🚀 [AtriaTrade] Starting Wallex Paper Trading Runner...")
    print("=" * 60)

    # 1. ساخت آداپتور شبیه‌ساز والکس از طریق Factory با بالانس مشخص
    initial_wallex_balances = {
        "tm": 100_000_000.0,
        "usdt": 2000.0,
        "btc": 0.5,
        "eth": 2.0
    }
    wallex_adapter = PaperExchangeFactory.create_adapter("wallex", initial_balances=initial_wallex_balances)
    print(f"✅ Adapter initialized: {wallex_adapter.__class__.__name__}")
    print(f"💰 Initial Balances -> TM: {wallex_adapter.get_balance('tm'):,.0f} | USDT: {wallex_adapter.get_balance('usdt')} | BTC: {wallex_adapter.get_balance('btc')}")

    # 2. تست اولیه قیمت مارکت و اردربوک
    symbol = "BTCUSDT"
    ticker = wallex_adapter.get_ticker(symbol)
    print(f"📈 Market Ticker ({symbol}): Last Price = {ticker.get('lastPrice', 0):,.2f}")

    # 3. ساخت رانر زنده Paper Trading
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=100.0)
    runner.start()
    print("🎯 PaperTradingLiveRunner is ACTIVE and listening for signals!")
    print("=" * 60)

if __name__ == "__main__":
    main()
