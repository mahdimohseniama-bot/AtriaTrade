import os, time, json, requests
from datetime import datetime

BASE_URL = "https://api.wallex.ir"
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
POLL_INTERVAL = 5 # کمی بیشترش کردیم که فشار کمتر بشه
TAKER_FEE_RATE = 0.002
MAX_SPREAD_RATIO = 0.0008
COOLDOWN_SECONDS = 180
DEPTH_IMBALANCE_MIN = 1.25
TAKE_PROFIT_PCT = 0.012
STOP_LOSS_PCT = 0.006
POSITION_SIZE_USD = 50.0

POSITIONS_FILE = "active_positions.json"
JOURNAL_FILE = "trade_journal.json"
last_exit_times = {}

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f: return json.load(f)
        except: return default
    return default

def save_json(filepath, data):
    with open(filepath, 'w') as f: json.dump(data, f, indent=2)

def fetch_orderbook(symbol):
    try:
        url = f"{BASE_URL}/v1/depth?symbol={symbol}"
        res = requests.get(url, timeout=5)

        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"📡 {symbol} | HTTP {res.status_code}"
        )

        if res.status_code != 200:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"⚠️ API response for {symbol}: {res.text[:300]}"
            )
            return None, None, 1.0

        try:
            payload = res.json()
        except ValueError as e:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"⚠️ Invalid JSON for {symbol}: {e}"
            )
            print(f"Raw response: {res.text[:300]}")
            return None, None, 1.0

        result = payload.get("result", payload)

        bids = result.get("bid", result.get("bids", []))
        asks = result.get("ask", result.get("asks", []))

        if not bids or not asks:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"⚠️ Empty orderbook for {symbol} | "
                f"keys={list(result.keys()) if isinstance(result, dict) else type(result)}"
            )
            return None, None, 1.0

        def price_of(level):
            if isinstance(level, dict):
                return float(level.get("price", level.get("rate")))
            return float(level[0])

        def quantity_of(level):
            if isinstance(level, dict):
                return float(
                    level.get(
                        "quantity",
                        level.get("amount", level.get("volume", 0))
                    )
                )
            return float(level[1])

        best_bid = price_of(bids[0])
        best_ask = price_of(asks[0])

        bid_vol = sum(quantity_of(level) for level in bids[:5])
        ask_vol = sum(quantity_of(level) for level in asks[:5])

        imbalance = bid_vol / ask_vol if ask_vol > 0 else 1.0

        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"✅ {symbol} | bid={best_bid} | ask={best_ask} | "
            f"imb={imbalance:.3f}"
        )

        return best_bid, best_ask, imbalance

    except requests.RequestException as e:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"🌐 Network Error for {symbol}: {type(e).__name__}: {e}"
        )
    except (KeyError, TypeError, ValueError, IndexError) as e:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"🧩 Data Format Error for {symbol}: {type(e).__name__}: {e}"
        )
    except Exception as e:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"❌ Unexpected Error for {symbol}: {type(e).__name__}: {e}"
        )

    return None, None, 1.0

def main():
    print("🚀 AtriaTrade v4.4 [Debugger Enabled]")
    positions, journal = load_json(POSITIONS_FILE, {}), load_json(JOURNAL_FILE, [])
    while True:
        now, now_str = time.time(), datetime.now().strftime("%H:%M:%S")
        print(f"[{now_str}] 🔎 Scanning markets...")
        for sym in SYMBOLS:
            best_bid, best_ask, imb = fetch_orderbook(sym)
            if not best_bid: continue
            
            mid = (best_bid + best_ask) / 2.0
            spread = (best_ask - best_bid) / mid
            
            if sym in positions:
                pos = positions[sym]
                pnl = ((best_bid - pos["entry_price"]) / pos["entry_price"]) - (2 * TAKER_FEE_RATE)
                if pnl >= TAKE_PROFIT_PCT or pnl <= -STOP_LOSS_PCT:
                    print(f"[{now_str}] ✅ Exit {sym} | PnL: {pnl*100:.2f}%")
                    journal.append({"symbol": sym, "pnl": round(pnl*100, 3)})
                    save_json(JOURNAL_FILE, journal)
                    del positions[sym]; save_json(POSITIONS_FILE, positions)
            elif (now - last_exit_times.get(sym, 0)) > COOLDOWN_SECONDS:
                if spread <= MAX_SPREAD_RATIO and imb >= DEPTH_IMBALANCE_MIN:
                    positions[sym] = {"entry_price": best_ask, "entry_time": now_str, "size_usd": POSITION_SIZE_USD}
                    save_json(POSITIONS_FILE, positions)
                    print(f"[{now_str}] 🔥 [ENTRY] {sym} @ {best_ask:.2f} | Imb: {imb:.2f}x")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__": main()
