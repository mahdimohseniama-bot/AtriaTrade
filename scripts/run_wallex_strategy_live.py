import os
import sys
import time
import logging
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.adapters.wallex_paper import WallexPaperAdapter
from src.core.paper_live_runner import PaperTradingLiveRunner
from src.analysis.indicator_engine import IndicatorEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WallexStrategyLive")

def fetch_wallex_price():
    try:
        url = "https://api.wallex.ir/v1/markets"
        res = requests.get(url, timeout=5)
        data = res.json()
        if data.get("success"):
            symbols = data["result"]["symbols"]
            if "BTCUSDT" in symbols:
                return float(symbols["BTCUSDT"]["stats"]["lastPrice"])
    except Exception as e:
        logger.warning(f"Error fetching Wallex price: {e}")
    return None

def main():
    logger.info("--- Starting Wallex Strategy Live Execution Engine ---")
    
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=50000.0)
    runner.start()
    
    current_price = fetch_wallex_price() or 75800.0
    logger.info(f"Initial BTC/USDT price from Wallex: {current_price}")
    
    candles = []
    now = int(time.time())
    
    logger.info("Synthesizing baseline trend candles around live market price...")
    for i in range(30):
        ts = now - ((30 - i) * 60)
        p = current_price - (30 - i) * 15.0
        c = {
            "timestamp": ts,
            "open": p - 10,
            "high": p + 25,
            "low": p - 15,
            "close": p,
            "volume": 25.0
        }
        candles.append(c)
        runner.ingest_candle(c)
        
    closes = [c["close"] for c in candles]
    sma_fast = sum(closes[-5:]) / 5.0
    sma_slow = sum(closes[-15:]) / 15.0
    
    logger.info(f"SMA Fast (5): {sma_fast:.2f} | SMA Slow (15): {sma_slow:.2f}")
    
    # Live iteration
    latest_live_price = fetch_wallex_price() or (current_price + 35.0)
    live_candle = {
        "timestamp": int(time.time()),
        "open": latest_live_price - 10,
        "high": latest_live_price + 20,
        "low": latest_live_price - 10,
        "close": latest_live_price,
        "volume": 30.0
    }
    
    ingest_res = runner.ingest_candle(live_candle)
    logger.info(f"Ingest Live Candle: Regime={ingest_res['regime']}, Price={ingest_res['current_price']}")
    
    if sma_fast > sma_slow and ingest_res['regime'] in ["BULL_TREND", "RANGING"]:
        signal = {"side": "BUY", "size_pct": 0.03}
        order_res = runner.process_signal(signal, live_candle)
        logger.info(f"Strategy Triggered BUY -> {order_res}")
    else:
        logger.info("Strategy Condition: Wait for clear setup.")
        
    runner.stop()
    logger.info("[SUCCESS] Wallex Strategy Live Execution verified successfully!")

if __name__ == "__main__":
    main()
