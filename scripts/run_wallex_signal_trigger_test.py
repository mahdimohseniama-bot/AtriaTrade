import os
import sys
import logging

# Add project root to path
sys.path.append(os.getcwd())

from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.trading_engine import TradingEngine
from src.strategies.sma_cross_strategy import SMACrossStrategy

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("WallexSignalTrigger")

def main():
    symbol = "BTCUSDT"
    logger.info(f"--- Starting Dynamic Signal & Execution Test for {symbol} on Wallex ---")

    # Initialize Wallex paper adapter with solid initial balances
    adapter = WallexPaperAdapter(initial_balances={"usdt": 10000.0, "btc": 0.1})
    
    # Fast SMA = 2, Slow SMA = 5 for immediate crossover trigger with fewer ticks
    strategy = SMACrossStrategy(fast_period=2, slow_period=5)
    
    # Simulate a price series with a clear dip then a sharp breakout crossover
    price_series = [
        75000.0, 74900.0, 74800.0, 74700.0, 74600.0, # Warm-up period (5 ticks)
        74500.0, 74400.0,                           # Lower lows
        75500.0, 76500.0, 77500.0, 78500.0          # Sharp upward rally -> Cross!
    ]

    initial_usdt = adapter.get_balance("usdt")
    initial_btc = adapter.get_balance("btc")
    logger.info(f"Initial Balances -> USDT: {initial_usdt:,.2f} | BTC: {initial_btc:.4f}")

    executed_orders = 0

    for idx, price in enumerate(price_series, start=1):
        adapter.set_market_price(symbol, price)
        ticker = adapter.get_ticker(symbol)
        
        bid = float(ticker.get("bidPrice", price * 0.999))
        ask = float(ticker.get("askPrice", price * 1.001))
        
        # 1. Feed tick to strategy
        signal = strategy.on_tick({"price": price, "symbol": symbol})
        
        logger.info(f"Tick {idx:02d} | Price: {price:,.2f} | Strategy Signal: {signal}")

        # 2. If strategy triggers a BUY or SELL, execute via Wallex adapter
        if signal in ["BUY", "SELL"]:
            qty = 0.005 # 0.005 BTC order size
            order_res = adapter.place_order(
                symbol=symbol,
                side=signal.lower(),
                order_type="market",
                amount=qty,
                price=price
            )
            logger.info(f">>> ORDER TRIGGERED ({signal})! Response: {order_res}")
            if order_res.get("status") == "success":
                executed_orders += 1

    final_usdt = adapter.get_balance("usdt")
    final_btc = adapter.get_balance("btc")
    
    logger.info("--- Execution Summary ---")
    logger.info(f"Total Orders Executed: {executed_orders}")
    logger.info(f"Final Balances -> USDT: {final_usdt:,.2f} | BTC: {final_btc:.4f}")
    
    if executed_orders > 0:
        logger.info("[SUCCESS] Dynamic signal generated and orders successfully executed on Wallex Paper Adapter!")
    else:
        logger.warning("[NOTICE] No order triggered. Adjusting price sequence further.")

if __name__ == "__main__":
    main()
