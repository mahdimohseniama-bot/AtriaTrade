import os
import sys
import time
import logging
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.paper_live_runner import PaperTradingLiveRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("WallexTrailingMonitor")

def fetch_wallex_live_price(symbol="BTCUSDT"):
    url = "https://api.wallex.ir/v1/markets"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "result" in data and "symbols" in data["result"]:
                market_info = data["result"]["symbols"].get(symbol)
                if market_info:
                    return float(market_info["stats"]["lastPrice"])
    except Exception as e:
        logger.warning(f"Error fetching live price: {e}")
    return None

def main():
    logger.info("Initializing Wallex Trailing Stop Live Monitor...")
    runner = PaperTradingLiveRunner(symbol="BTC/USDT", initial_balance=25000.0)
    runner.start()

    logger.info("Fetching initial price to calibrate entry...")
    entry_price = None
    for _ in range(5):
        entry_price = fetch_wallex_live_price("BTCUSDT")
        if entry_price:
            break
        time.sleep(1)

    if not entry_price:
        logger.error("Failed to connect to Wallex API.")
        return

    logger.info(f"Base Entry Price calibrated at: {entry_price:.2f} USDT")

    # Warm up runner
    for i in range(20):
        t = int(time.time()) - (20 - i) * 60
        runner.ingest_candle({
            "timestamp": t,
            "open": entry_price - 5.0,
            "high": entry_price + 5.0,
            "low": entry_price - 5.0,
            "close": entry_price,
            "volume": 10.0
        })

    # Simulate position entry
    now = int(time.time())
    entry_candle = {
        "timestamp": now,
        "open": entry_price - 2.0,
        "high": entry_price + 2.0,
        "low": entry_price - 2.0,
        "close": entry_price,
        "volume": 12.0
    }
    runner.ingest_candle(entry_candle)
    order = runner.process_signal({"side": "BUY", "size_pct": 0.10}, entry_candle)
    logger.info(f"Position opened: {order['status']} | Size: {runner.balance * 0.10:.2f} USDT")

    # Monitor 3 live ticks
    logger.info("Monitoring trailing conditions on live market ticks...")
    peak_price = entry_price
    trailing_pct = 0.005  # 0.5% trailing stop

    for tick in range(1, 4):
        time.sleep(2)
        current_price = fetch_wallex_live_price("BTCUSDT")
        if not current_price:
            current_price = entry_price

        if current_price > peak_price:
            peak_price = current_price

        stop_loss_price = peak_price * (1.0 - trailing_pct)
        pnl_pct = ((current_price - entry_price) / entry_price) * 100.0

        candle = {
            "timestamp": int(time.time()),
            "open": current_price,
            "high": max(current_price, peak_price),
            "low": min(current_price, stop_loss_price),
            "close": current_price,
            "volume": 5.0
        }
        runner.ingest_candle(candle)

        logger.info(
            f"Tick #{tick} | Live: {current_price:.2f} USDT | Peak: {peak_price:.2f} | "
            f"Trail SL: {stop_loss_price:.2f} | Unrealized PnL: {pnl_pct:+.2f}%"
        )

    runner.stop()
    logger.info("Trailing stop monitor iteration successfully concluded.")

if __name__ == "__main__":
    main()
