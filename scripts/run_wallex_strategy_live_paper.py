import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
from src.strategies.sma_cross_strategy import SMACrossStrategy
from src.core.trading_engine import TradingEngine

load_dotenv()

# Setup
symbol = os.getenv("WALLEX_TRADING_SYMBOL", "BTCUSDT")
print(f"[STRATEGY-TEST] Initializing Strategy Runner for {symbol}...")

# Initialize engine and strategy
strategy = SMACrossStrategy(fast_period=5, slow_period=20)
engine = TradingEngine(strategy=strategy)

# Start engine
engine.is_running = True

# Simulated live tick loop with dict structure
print("[STRATEGY-TEST] Running signal evaluation on live ticks...")
for i in range(1, 6):
    price = 77485.61 + (i * 10) 
    # Construct proper tick dictionary accepted by TradingEngine.process_tick()
    tick = {
        "symbol": symbol,
        "price": price,
        "signal": "HOLD",  # Can be BUY, SELL, or HOLD
        "quantity": 0.01
    }
    signal = engine.process_tick(tick)
    print(f"Tick {i:02d} | Price: {price:,.2f} | Engine Result: {signal}")

print("[STRATEGY-TEST] Strategy signal pipeline validation complete.")
