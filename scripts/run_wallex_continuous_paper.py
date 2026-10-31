import os
import sys
import time
import logging

# Add project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.trading_engine import TradingEngine
from src.strategies.sma_cross_strategy import SMACrossStrategy

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("WallexContinuousPaper")

load_dotenv()

def main():
    symbol = os.getenv("WALLEX_TRADING_SYMBOL", "BTCUSDT")
    logger.info(f"Initializing AtriaTrade Wallex Continuous Paper Runner for {symbol}...")

    # Initialize exchange adapter & set mock market price for BTCUSDT
    exchange = WallexPaperAdapter()
    exchange.set_market_price(symbol, 77500.0)

    strategy = SMACrossStrategy(fast_period=5, slow_period=20)
    engine = TradingEngine(strategy=strategy, order_executor=exchange)
    
    engine.is_running = True
    logger.info("Engine started successfully. Entering live tick polling loop (Ctrl+C to stop)...")

    tick_count = 0
    try:
        while tick_count < 10:
            tick_count += 1
            ticker = exchange.get_ticker(symbol)
            
            if ticker and "lastPrice" in ticker:
                price = float(ticker["lastPrice"])
                bid = float(ticker.get("bidPrice", price * 0.999))
                ask = float(ticker.get("askPrice", price * 1.001))
                
                tick_payload = {
                    "symbol": symbol,
                    "price": price,
                    "bid": bid,
                    "ask": ask,
                    "signal": "HOLD",
                    "quantity": 0.001
                }
                
                # Process tick through strategy & engine
                result = engine.process_tick(tick_payload)
                logger.info(f"Tick {tick_count:02d} | Symbol: {symbol} | Price: {price:,.2f} | Bid: {bid:,.2f} | Ask: {ask:,.2f} | Result: {result}")
            else:
                logger.warning(f"Failed to fetch valid ticker data for {symbol}: {ticker}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Continuous paper runner stopped by user.")
    
    logger.info("Wallex continuous paper session completed successfully.")

if __name__ == "__main__":
    main()
