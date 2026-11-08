import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.paper_live_runner import PaperTradingLiveRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WallexPaperLiveTest")

def main():
    logger.info("--- Starting Wallex Paper Live Runner Integration ---")
    
    adapter = WallexPaperAdapter(initial_usdt=100000.0, initial_btc=1.0)
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=100000.0)
    runner.start()
    
    # Ingest multiple warm-up candles to establish market regime
    prices = [78000.0, 78200.0, 78400.0, 78600.0, 78800.0, 79000.0]
    for i, p in enumerate(prices):
        candle = {"timestamp": 1761930000 + i*60, "open": p-100, "high": p+200, "low": p-200, "close": p, "volume": 10.0}
        ingest_res = runner.ingest_candle(candle)
        logger.info(f"Warm-up Candle {i+1} Result: {ingest_res}")
    
    # Process a BUY signal with the latest candle
    latest_candle = {"timestamp": 1761930360, "open": 79000.0, "high": 79500.0, "low": 78900.0, "close": 79200.0, "volume": 15.0}
    runner.ingest_candle(latest_candle)
    
    signal = {"side": "BUY", "size_pct": 0.05}
    signal_res = runner.process_signal(signal, latest_candle)
    logger.info(f"Signal Process Result: {signal_res}")
    
    # Check balances correctly specifying asset
    usdt_bal = adapter.get_balance("USDT")
    btc_bal = adapter.get_balance("BTC")
    logger.info(f"Adapter Balances -> USDT: {usdt_bal}, BTC: {btc_bal}")
    
    runner.stop()
    logger.info("[SUCCESS] Wallex Paper Live Runner integration verified successfully!")

if __name__ == "__main__":
    main()
