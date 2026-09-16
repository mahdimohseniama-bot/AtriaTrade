#!/usr/bin/env python3
"""
AtriaTrade Simulation Benchmark Script
Executes paper trading simulation against synthetic ticks to evaluate speed,
PnL, win rate, and profit reservation metrics.
"""

import sys
from pathlib import Path

# Add project root to sys.path so 'src' can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import time
import random
from typing import List, Dict, Any

from src.core.portfolio_manager import PortfolioManager
from src.core.risk_manager import RiskManager
from src.core.order_executor import OrderExecutor
from src.core.profit_reserve import ProfitReserveManager
from src.core.trading_engine import TradingEngine
from src.strategies.sma_cross_strategy import SMACrossStrategy


def generate_synthetic_ticks(count: int = 1000, start_price: float = 50000.0) -> List[Dict[str, Any]]:
    """Generates synthetic price ticks with realistic random walk."""
    ticks = []
    price = start_price
    random.seed(42)  # Deterministic seed for reproducible benchmarks
    for i in range(count):
        delta = price * random.gauss(0.0001, 0.005)
        price = max(100.0, price + delta)
        ticks.append({
            "symbol": "BTCUSDT",
            "price": round(price, 2),
            "timestamp": time.time() + i
        })
    return ticks


def run_benchmark(num_ticks: int = 2000):
    print("==================================================")
    print("🚀 Starting AtriaTrade Simulation Benchmark")
    print(f"📊 Dataset Size: {num_ticks} market ticks")
    print("==================================================")

    # 1. Initialize Components with verified signature mappings
    portfolio = PortfolioManager(initial_cash=10000.0)
    risk = RiskManager(initial_capital=10000.0)
    # OrderExecutor expects 'portfolio', not 'portfolio_manager'
    executor = OrderExecutor(portfolio=portfolio, risk_manager=risk)
    reserve = ProfitReserveManager()

    engine = TradingEngine(
        portfolio_manager=portfolio,
        risk_manager=risk,
        order_executor=executor,
        profit_reserve_manager=reserve
    )
    engine.start()

    strategy = SMACrossStrategy(
        symbol="BTCUSDT",
        fast_period=5,
        slow_period=20,
        quantity=0.05
    )

    # 2. Generate Synthetic Market Feed
    ticks = generate_synthetic_ticks(count=num_ticks)

    # 3. Execution Loop & Performance Measurement
    filled_trades = []
    start_time = time.perf_counter()

    for tick in ticks:
        price = tick["price"]
        symbol = tick["symbol"]
        sig = strategy.generate_signal(price)

        if sig in ("BUY", "SELL"):
            tick_payload = {
                "symbol": symbol,
                "price": price,
                "signal": sig,
                "quantity": strategy.quantity
            }
            res = engine.process_tick(tick_payload)
            if res and res.get("status") == "FILLED":
                filled_trades.append(res)

    engine.stop()
    elapsed_time = time.perf_counter() - start_time

    # 4. Metric Calculations
    ticks_per_sec = num_ticks / elapsed_time if elapsed_time > 0 else 0
    sells = [t for t in filled_trades if t.get("side") == "SELL"]
    profitable_trades = [t for t in sells if t.get("realized_pnl", 0.0) > 0]
    total_realized_pnl = sum(t.get("realized_pnl", 0.0) for t in sells)
    win_rate = (len(profitable_trades) / len(sells) * 100) if sells else 0.0

    vault_balance = getattr(reserve, "vault_balance", 0.0)
    final_cash = getattr(portfolio, "cash", 0.0)

    # 5. Summary Presentation
    print("\n📈 Benchmark Execution Summary:")
    print(f"  • Total Ticks Processed : {num_ticks:,}")
    print(f"  • Elapsed Time          : {elapsed_time:.4f} seconds")
    print(f"  • Processing Speed      : {ticks_per_sec:,.2f} ticks/sec")
    print(f"  • Total Trades Executed : {len(filled_trades)} (Buys: {len(filled_trades) - len(sells)}, Sells: {len(sells)})")
    print(f"  • Win Rate              : {win_rate:.2f}%")
    print(f"  • Total Realized PnL    : {total_realized_pnl:+.2f} USDT")
    print(f"  • Vault Reserved Profit : {vault_balance:+.2f} USDT")
    print(f"  • Final Cash Balance    : {final_cash:,.2f} USDT")
    print("==================================================")
    print("✅ Benchmark Completed Successfully!\n")


if __name__ == "__main__":
    run_benchmark(num_ticks=2000)
