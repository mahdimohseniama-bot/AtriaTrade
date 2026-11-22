import sys
import os
import time
import logging
from pathlib import Path

# Auto-inject project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.capital_manager import CapitalManager
from src.core.risk_manager import RiskManager
from src.core.position_tracker import PositionTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "wallex_paper_live.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("WallexPaperRunner")

def main():
    symbol = "USDTTMN"
    logger.info("Initializing AtriaTrade Forward Paper Engine with Execution...")

    initial_balances = {
        "TMN": 50_000_000.0,
        "TM": 50_000_000.0,
        "USDT": 500.0,
        "BTC": 0.01
    }

    adapter = WallexPaperAdapter(symbol=symbol, initial_balances=initial_balances)
    capital_mgr = CapitalManager(initial_capital=50_000_000.0)
    risk_mgr = RiskManager()
    position_tracker = PositionTracker()

    logger.info(f"Target Symbol: {symbol} | Adapter Ready")
    balances = adapter.get_balances()
    logger.info(f"Initial Balances: {balances}")

    iteration = 0
    price_history = []

    try:
        while True:
            iteration += 1
            ticker = adapter.get_ticker(symbol)
            last_price = float(ticker.get("last_price") or ticker.get("last", 0.0))
            bid = float(ticker.get("bidPrice") or ticker.get("bid", 0.0))
            ask = float(ticker.get("askPrice") or ticker.get("ask", 0.0))

            price_history.append(last_price)
            if len(price_history) > 30:
                price_history.pop(0)

            logger.info(
                f"[Tick {iteration:03d}] {symbol} | "
                f"Price: {last_price:,.0f} | Bid: {bid:,.0f} | Ask: {ask:,.0f} | "
                f"Active Positions: {len(position_tracker.get_open_positions())}"
            )

            # Circuit breaker check
            if hasattr(risk_mgr, "is_circuit_broken") and risk_mgr.is_circuit_broken():
                logger.warning("Circuit breaker active. Halting execution.")
                time.sleep(10)
                continue

            # Forward testing simulated micro-cycle: trigger order test on iteration 5 if no open positions
            if iteration == 5 and len(position_tracker.get_open_positions()) == 0:
                logger.info("Triggering simulated Paper Buy Order to verify execution flow...")
                order_result = adapter.place_order(
                    symbol=symbol,
                    side="BUY",
                    order_type="MARKET",
                    quantity=10.0,
                    price=ask
                )
                logger.info(f"Simulated Buy Order Result: {order_result}")
                position_tracker.open_position(
                    symbol=symbol,
                    side="BUY",
                    entry_price=ask,
                    quantity=10.0
                )
                logger.info(f"Updated Balances: {adapter.get_balances()}")

            # Simulated exit test on iteration 10
            if iteration == 10 and len(position_tracker.get_open_positions()) > 0:
                logger.info("Triggering simulated Paper Sell Order to close cycle...")
                order_result = adapter.place_order(
                    symbol=symbol,
                    side="SELL",
                    order_type="MARKET",
                    quantity=10.0,
                    price=bid
                )
                logger.info(f"Simulated Sell Order Result: {order_result}")
                position_tracker.close_position(symbol=symbol, exit_price=bid)
                logger.info(f"Final Closed Balances: {adapter.get_balances()}")

            time.sleep(10)

    except KeyboardInterrupt:
        logger.info("Runner stopped gracefully by user.")
        logger.info(f"Session End Balances: {adapter.get_balances()}")

if __name__ == "__main__":
    main()
