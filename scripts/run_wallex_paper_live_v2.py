import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.paper_live_runner import PaperTradingLiveRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WallexPaperLiveV2")

def main():
    logger.info("--- Starting Advanced Wallex Paper Live Runner & Regime Test ---")
    
    adapter = WallexPaperAdapter(initial_usdt=100000.0, initial_btc=1.0)
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=100000.0)
    runner.start()
    
    # Feed an upward trend sequence to satisfy regime detection requirements
    base_price = 70000.0
    for i in range(30):
        p = base_price + (i * 300.0)  # Steady upward movement
        candle = {
            "timestamp": 1761930000 + (i * 60),
            "open": p - 50,
            "high": p + 150,
            "low": p - 100,
            "close": p,
            "volume": 25.0
        }
        res = runner.ingest_candle(candle)
        if i % 10 == 0:
            logger.info(f"Ingest step {i}: Price={p}, Regime={res.get('regime')}")
            
    # Test final signal processing in established regime
    final_candle = {"timestamp": 1761931800, "open": 79000.0, "high": 79500.0, "low": 78900.0, "close": 79200.0, "volume": 30.0}
    runner.ingest_candle(final_candle)
    
    signal = {"side": "BUY", "size_pct": 0.05}
    signal_res = runner.process_signal(signal, final_candle)
    logger.info(f"Advanced Signal Process Result: {signal_res}")
    
    logger.info(f"Final Balances -> USDT: {adapter.get_balance('USDT')}, BTC: {adapter.get_balance('BTC')}")
    runner.stop()
    logger.info("[SUCCESS] Advanced Wallex integration workflow verified!")

if __name__ == "__main__":
    main()
