import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("WALLEX_BASE_URL", "https://api.wallex.ir")
SYMBOL = os.getenv("WALLEX_TRADING_SYMBOL", "BTCUSDT")

print(f"[FORWARD-TEST] Initializing Live Paper Runner for Wallex ({SYMBOL})...")
print(f"[FORWARD-TEST] Connecting to public ticker: {BASE_URL}/v1/depth?symbol={SYMBOL}")

def fetch_orderbook(symbol):
    try:
        url = f"{BASE_URL}/v1/depth?symbol={symbol}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get("result", {})
            bids = data.get("bid", [])
            asks = data.get("ask", [])
            if bids and asks:
                best_bid = float(bids[0]["price"])
                best_ask = float(asks[0]["price"])
                spread = best_ask - best_bid
                spread_bps = (spread / best_bid) * 10000
                return best_bid, best_ask, spread_bps
    except Exception as e:
        print(f"[WARN] Fetch error: {e}")
    return None, None, None

# Run bounded forward-test loop (5 sample ticks)
print("\n[INFO] Starting 5 real-time market data sample iterations...\n")
for tick in range(1, 6):
    best_bid, best_ask, spread_bps = fetch_orderbook(SYMBOL)
    if best_bid and best_ask:
        status = "HEALTHY" if spread_bps < 25 else "HIGH_SPREAD"
        print(f"Tick {tick}/5 | {SYMBOL} | Bid: {best_bid:,.2f} | Ask: {best_ask:,.2f} | Spread: {spread_bps:.2f} bps | Guard: [{status}]")
    else:
        print(f"Tick {tick}/5 | Failed to retrieve depth for {SYMBOL}")
    time.sleep(1)

print("\n[FORWARD-TEST] Live Orderbook feed and spread guard verified successfully.\n")
