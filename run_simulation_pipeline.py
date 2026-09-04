import time
import logging
from src.core.trading_engine import TradingEngine
from src.core.strategy_manager import StrategyManager
from src.strategies.sma_cross_strategy import SMACrossStrategy

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SimulationPipeline")

def main():
    logger.info("=== Starting AtriaTrade Simulation Pipeline ===")
    
    # 1. راه‌اندازی موتور و منیجر
    engine = TradingEngine()
    strategy_mgr = StrategyManager(engine)
    engine.set_strategy_manager(strategy_mgr)

    # 2. بارگذاری استراتژی
    strategy_mgr.load_strategy(SMACrossStrategy)
    
    engine.start()
    strategy_mgr.start_all()

    # 3. تغذیه دیتای بازار (شبیه‌سازی قیمت)
    simulated_market_prices = [
        60000, 60050, 60100, 60200, 60300, 60500, 60800, 61200, 61500, 62000, 62500,
        62000, 61500, 60800, 60200, 59800, 59200, 58500
    ]

    for price in simulated_market_prices:
        tick = {
            "symbol": "BTCUSDT",
            "price": price,
            "timestamp": time.time()
        }
        engine.process_tick(tick)
        time.sleep(0.05)

    # 4. خروجی نهایی
    logger.info("=== Simulation Completed ===")
    logger.info(f"Final Balance: {engine.balance:.2f} USDT")
    logger.info(f"Open Positions: {engine.positions}")
    logger.info(f"Total Orders Executed: {len(engine.orders)}")

    strategy_mgr.stop_all()
    engine.stop()

if __name__ == "__main__":
    main()
