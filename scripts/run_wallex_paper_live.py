import sys
import time
import argparse
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.risk_manager import RiskManager
from src.core.strategy_orchestrator import StrategyOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/atria_trade.log")
    ]
)
logger = logging.getLogger("wallex_paper_live")

def run_live(symbol: str = "BTCUSDT", interval: int = 2, duration: int = 6):
    logger.info(f"Starting Wallex Paper Live Session for symbol: {symbol}")
    adapter = WallexPaperAdapter()
    risk_manager = RiskManager()
    strategy = StrategyOrchestrator(adapter)
    
    start_time = time.time()
    cycle = 0
    current_position = "FLAT"  # FLAT, LONG, SHORT

    while time.time() - start_time < duration:
        cycle += 1
        logger.info(f"--- Cycle {cycle} ---")
        
        # 1. Market Ticker
        ticker = adapter.get_ticker(symbol)
        price = ticker.get("last", 0.0)
        logger.info(f"Market Price: {price}")
        
        # 2. Risk Check
        can_trade = risk_manager.can_trade_today()
        logger.info(f"Risk Check - Can Trade: {can_trade}")
        if not can_trade:
            logger.warning("Trading blocked by RiskManager daily limit.")
            time.sleep(interval)
            continue
            
        # 3. Strategy Signal Generation
        signal = strategy.get_signal(symbol)
        logger.info(f"Strategy Signal: {signal} | Current Position: {current_position}")
        
        # 4. Position Deduplication Logic
        if signal == "BUY":
            if current_position != "LONG":
                order = adapter.create_order(symbol, "buy", "market", 0.001, price)
                current_position = "LONG"
                logger.info(f"Order Executed: ID={order.get('id')} Status={order.get('status')} Side=buy -> New Position: LONG")
            else:
                logger.info("Signal is BUY, but already LONG. Skipping execution (Dedup).")
        elif signal == "SELL":
            if current_position != "SHORT":
                order = adapter.create_order(symbol, "sell", "market", 0.001, price)
                current_position = "SHORT"
                logger.info(f"Order Executed: ID={order.get('id')} Status={order.get('status')} Side=sell -> New Position: SHORT")
            else:
                logger.info("Signal is SELL, but already SHORT. Skipping execution (Dedup).")
        else:
            logger.info("Signal is HOLD. No order placed.")
            
        time.sleep(interval)

    logger.info("Wallex Paper Live Session completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Wallex Paper Live Trading")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading pair symbol")
    parser.add_argument("--interval", type=int, default=2, help="Seconds between cycles")
    parser.add_argument("--duration", type=int, default=6, help="Total run duration in seconds")
    args = parser.parse_args()

    run_live(symbol=args.symbol, interval=args.interval, duration=args.duration)
