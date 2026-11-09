import sys
import time
import argparse
from pathlib import Path

# Auto-resolve project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.risk_manager import RiskManager
from src.core.monitoring import AtriaLogger

logger = AtriaLogger(name="WallexPaperRunner").get_logger()

def run_paper_session(duration_sec: int = 10, interval_sec: int = 2, symbol: str = "BTCUSDT"):
    logger.info("Initializing Wallex Paper Trading Session...")
    logger.info(f"Target Symbol: {symbol} | Duration: {duration_sec}s | Interval: {interval_sec}s")
    
    adapter = WallexPaperAdapter(initial_balance=1000.0)
    risk_manager = RiskManager(capital=1000.0, max_daily_loss_percent=3.0)
    
    start_time = time.time()
    cycle = 1
    order_executed = False

    logger.info("Wallex Paper Runner started successfully. Monitoring market feed...")
    
    while time.time() - start_time < duration_sec:
        ticker = adapter.get_ticker(symbol)
        price = ticker.get("last_price", 0.0)
        
        if price <= 0.0:
            logger.warning(f"Iteration {cycle}: Invalid market price received ({price}). Retrying...")
            time.sleep(interval_sec)
            cycle += 1
            continue
            
        can_trade = risk_manager.can_trade_today()
        logger.info(f"[Cycle {cycle:03d}] Symbol: {symbol} | Price: {price:,.2f} | Can Trade: {can_trade}")
        
        # Place a single simulated paper trade on cycle 2 if allowed
        if cycle == 2 and can_trade and not order_executed:
            order_qty = 0.001
            sl_price = price * 0.98
            logger.info(f"Simulating PAPER BUY: Qty={order_qty}, Price={price:,.2f}, SL={sl_price:,.2f}")
            order = adapter.create_order(
                symbol=symbol,
                side="BUY",
                order_type="LIMIT",
                quantity=order_qty,
                price=price
            )
            logger.info(f"Paper Order Executed: {order}")
            order_executed = True
            
        time.sleep(interval_sec)
        cycle += 1

    logger.info("=" * 50)
    logger.info("SESSION COMPLETED SUCCESSFULLY")
    logger.info(f"Cycles Executed: {cycle - 1}")
    logger.info(f"Daily Loss Recorded: {risk_manager.get_today_loss():.2f}")
    logger.info(f"Trading Allowed Status: {risk_manager.can_trade_today()}")
    logger.info("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Wallex Paper Live Session")
    parser.add_argument("--duration", type=int, default=6, help="Session duration in seconds")
    parser.add_argument("--interval", type=int, default=2, help="Poll interval in seconds")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol")
    args = parser.parse_args()
    
    run_paper_session(duration_sec=args.duration, interval_sec=args.interval, symbol=args.symbol)
