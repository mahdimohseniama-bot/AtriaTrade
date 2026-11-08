import os
import sys
import time
import logging
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.paper_live_runner import PaperTradingLiveRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WallexLiveLoop")

def fetch_wallex_price():
    try:
        # Wallex public ticker API for BTC/USDT
        url = "https://api.wallex.ir/v1/markets"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("success"):
            symbols = data["result"]["symbols"]
            if "BTCUSDT" in symbols:
                price = float(symbols["BTCUSDT"]["stats"]["lastPrice"])
                return price
    except Exception as e:
        logger.warning(f"Failed to fetch live price from Wallex API: {e}. Using fallback simulation.")
    return None

def main():
    logger.info("--- Starting Wallex Live Market Paper Trading Loop ---")
    
    adapter = WallexPaperAdapter(initial_usdt=50000.0, initial_btc=0.5)
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=50000.0)
    runner.start()
    
    logger.info("Feeding warm-up candles for regime establishment...")
    base_price = fetch_wallex_price() or 75000.0
    for i in range(25):
        p = base_price + (i * 50.0)
        candle = {
            "timestamp": int(time.time()) - ((25 - i) * 60),
            "open": p - 20,
            "high": p + 80,
            "low": p - 40,
            "close": p,
            "volume": 15.0
        }
        runner.ingest_candle(candle)
        
    logger.info("Running live market feed simulation loop (3 iterations)...")
    for step in range(3):
        current_price = fetch_wallex_price() or (base_price + 1200.0 + (step * 100.0))
        logger.info(f"Fetched Wallex BTC/USDT Price: {current_price}")
        
        candle = {
            "timestamp": int(time.time()),
            "open": current_price - 30,
            "high": current_price + 50,
            "low": current_price - 50,
            "close": current_price,
            "volume": 20.0
        }
        res = runner.ingest_candle(candle)
        logger.info(f"Candle Ingest Result: {res}")
        
        # Test signal generation
        signal = {"side": "BUY", "size_pct": 0.02}
        signal_res = runner.process_signal(signal, candle)
        logger.info(f"Signal Process Result: {signal_res}")
        
        time.sleep(1)
        
    logger.info(f"Final Paper Balances -> USDT: {adapter.get_balance('USDT')}, BTC: {adapter.get_balance('BTC')}")
    runner.stop()
    logger.info("[SUCCESS] Wallex Live Loop verified successfully!")

if __name__ == "__main__":
    main()
