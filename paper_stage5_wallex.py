import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

SYMBOL = "BTCUSDT"
POLL_SECONDS = 10
RUN_SECONDS = 300
OUTPUT_FILE = Path("logs/paper_stage5_wallex.csv")

ORDERBOOK_URL = f"https://api.wallex.ir/v1/depth?symbol={SYMBOL}"

def fetch_orderbook():
    request = Request(
        ORDERBOOK_URL,
        headers={"Accept": "application/json", "User-Agent": "AtriaTrade-v1"},
    )
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))

    data = payload.get("result", {})
    bids = data.get("bid", [])
    asks = data.get("ask", [])

    if not bids or not asks:
        raise ValueError("Empty bids/asks received from Wallex API")

    best_bid = float(bids[0]["price"])
    best_bid_qty = float(bids[0]["quantity"])
    best_ask = float(asks[0]["price"])
    best_ask_qty = float(asks[0]["quantity"])

    return best_bid, best_ask, best_bid_qty, best_ask_qty

def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_exists = OUTPUT_FILE.exists()

    with OUTPUT_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp_utc", "symbol", "best_bid", "best_ask",
                "bid_qty", "ask_qty", "spread", "spread_pct", "mid_price"
            ])

        start_time = time.time()
        end_time = start_time + RUN_SECONDS
        poll_count = 0

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Started 5-min Wallex paper forward test for {SYMBOL}...")

        while time.time() < end_time:
            now_iso = datetime.now(timezone.utc).isoformat()
            try:
                best_bid, best_ask, bid_qty, ask_qty = fetch_orderbook()
                spread = best_ask - best_bid
                mid_price = (best_ask + best_bid) / 2.0
                spread_pct = (spread / mid_price) * 100.0 if mid_price > 0 else 0.0

                writer.writerow([
                    now_iso, SYMBOL, best_bid, best_ask,
                    bid_qty, ask_qty, round(spread, 2),
                    round(spread_pct, 4), round(mid_price, 2)
                ])
                f.flush()

                poll_count += 1
                remaining = max(0, int(end_time - time.time()))
                print(
                    f"[{poll_count:02d}] Mid: {mid_price:.2f} | Spread: {spread:.2f} ({spread_pct:.3f}%) | Left: {remaining}s"
                )
            except Exception as e:
                print(f"Fetch warning: {e}")

            time.sleep(POLL_SECONDS)

        print(f"\n[DONE] Stage 5 Paper Session completed! Total records: {poll_count}")
        print(f"Logged to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
