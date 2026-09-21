#!/usr/bin/env python3
"""
AtriaTrade Multi-Asset Live Paper Scalper v4.2 (Anti-Overtrading Cooldown)
- Dual Markets: BTCUSDT & ETHUSDT (1m Wallex UDF)
- Smart SMC Sweep Strategy + Order Book Spread Filter
- Realistic Fee Deduction (0.2% Taker per leg) & Dynamic Slippage
- Auto-Breakeven & Trailing Stop Engine
- Anti-Overtrading Cooldown (180s per symbol after exit)
- Crash Recovery with active_positions.json
- Real-time Telemetry & Persistent JSON Journaling
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

JOURNAL_FILE = "trade_journal.json"
STATE_FILE = "active_positions.json"
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
RESOLUTION = "1"
LIMIT_CANDLES = 50
CHECK_INTERVAL = 8
MAX_ALLOWED_SPREAD_PCT = 0.08  # Max 0.08% spread allowed for scalping entries
FEE_RATE = 0.002               # 0.20% Taker fee per side
COOLDOWN_SECONDS = 180         # 3 minutes cooldown per symbol after trade exit

INITIAL_BALANCE = 100.0
paper_balance = INITIAL_BALANCE
open_positions = {}
symbol_cooldowns = {}

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

class StateManager:
    @staticmethod
    def load_positions():
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log(f"[WARN] Failed to load saved state: {e}")
        return {}

    @staticmethod
    def save_positions(positions):
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(positions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(f"[ERROR] Failed to persist active positions: {e}")

class FastJournal:
    @staticmethod
    def record_event(data):
        journal = []
        if os.path.exists(JOURNAL_FILE):
            try:
                with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
                    journal = json.load(f)
            except Exception:
                journal = []
        journal.append(data)
        with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
            json.dump(journal, f, indent=2, ensure_ascii=False)

def fetch_candles(symbol: str):
    to_time = int(time.time())
    resolution_seconds = int(RESOLUTION) * 60
    from_time = to_time - (LIMIT_CANDLES * resolution_seconds)
    
    url = f"https://api.wallex.ir/v1/udf/history?symbol={symbol}&resolution={RESOLUTION}&from={from_time}&to={to_time}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile)",
        "Accept": "application/json"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("s") == "ok" and "t" in data and len(data["t"]) > 0:
                candles = []
                for i in range(len(data["t"])):
                    candles.append({
                        "time": data["t"][i],
                        "open": float(data["o"][i]),
                        "high": float(data["h"][i]),
                        "low": float(data["l"][i]),
                        "close": float(data["c"][i]),
                        "volume": float(data["v"][i]),
                    })
                return candles
    except Exception:
        pass
    return None

def fetch_orderbook_spread(symbol: str):
    url = f"https://api.wallex.ir/v1/depth?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile)",
        "Accept": "application/json"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=4)
        if resp.status_code == 200:
            data = resp.json().get("result", {})
            bids = data.get("bid", [])
            asks = data.get("ask", [])
            if bids and asks:
                best_bid = float(bids[0]["price"])
                best_ask = float(asks[0]["price"])
                spread_pct = ((best_ask - best_bid) / best_bid) * 100.0
                return spread_pct, best_bid, best_ask
    except Exception:
        pass
    return None, None, None

def analyze_smc_scalp(candles):
    if len(candles) < 12:
        return "HOLD", 0.0, 0.0

    c = candles[-1]
    prev = candles[-2]
    prev2 = candles[-3]

    volatility = max(c["high"] - c["low"], abs(c["high"] - prev["close"]))
    min_buffer = max(volatility * 1.2, c["close"] * 0.0025)

    if prev["low"] < prev2["low"] and c["close"] > prev["high"]:
        entry = c["close"]
        sl = entry - min_buffer
        tp = entry + (min_buffer * 2.2)
        return "BUY", sl, tp

    elif prev["high"] > prev2["high"] and c["close"] < prev["low"]:
        entry = c["close"]
        sl = entry + min_buffer
        tp = entry - (min_buffer * 2.2)
        return "SELL", sl, tp

    return "HOLD", 0.0, 0.0

def update_risk_management(pos, current_price):
    direction = pos["direction"]
    entry = pos["entry"]
    tp = pos["tp"]
    sl = pos["sl"]
    is_be = pos.get("is_be", False)
    target_dist = abs(tp - entry)
    updated = False

    if direction == "BUY":
        current_gain = current_price - entry
        if not is_be and current_gain >= (target_dist * 0.5):
            pos["sl"] = entry + (target_dist * 0.05)
            pos["is_be"] = True
            updated = True
            log(f"[RISK] {pos['symbol']} BE Activated! SL moved to {pos['sl']:.2f}")
        elif is_be and current_gain >= (target_dist * 0.7):
            new_sl = entry + (target_dist * 0.4)
            if new_sl > pos["sl"]:
                pos["sl"] = new_sl
                updated = True
                log(f"[RISK] {pos['symbol']} Trailing Stop adjusted to {pos['sl']:.2f}")

    elif direction == "SELL":
        current_gain = entry - current_price
        if not is_be and current_gain >= (target_dist * 0.5):
            pos["sl"] = entry - (target_dist * 0.05)
            pos["is_be"] = True
            updated = True
            log(f"[RISK] {pos['symbol']} BE Activated! SL moved to {pos['sl']:.2f}")
        elif is_be and current_gain >= (target_dist * 0.7):
            new_sl = entry - (target_dist * 0.4)
            if new_sl < pos["sl"]:
                pos["sl"] = new_sl
                updated = True
                log(f"[RISK] {pos['symbol']} Trailing Stop adjusted to {pos['sl']:.2f}")

    return updated

def main():
    global paper_balance, open_positions, symbol_cooldowns
    print("=" * 72, flush=True)
    print("AtriaTrade Scalper v4.2 (Anti-Overtrading Cooldown Engine)", flush=True)
    print(f"Markets: {', '.join(SYMBOLS)} | TF: {RESOLUTION}m | Cooldown: {COOLDOWN_SECONDS}s", flush=True)

    open_positions = StateManager.load_positions()
    if open_positions:
        log(f"[RECOVERY] Restored {len(open_positions)} active positions from disk.")
        for sym, p in open_positions.items():
            log(f" -> Restored {sym} {p['direction']} @ {p['entry']:.2f} | TP: {p['tp']:.2f} | SL: {p['sl']:.2f}")
    else:
        log("[STATE] No persisted positions found. Ready for fresh setups.")

    print("=" * 72, flush=True)

    trade_counter = int(time.time())

    while True:
        try:
            status_summary = []
            state_changed = False
            now_ts = time.time()

            for symbol in SYMBOLS:
                candles = fetch_candles(symbol)
                if not candles:
                    continue

                current_price = candles[-1]["close"]

                if symbol in open_positions:
                    pos = open_positions[symbol]
                    if update_risk_management(pos, current_price):
                        state_changed = True

                    direction = pos["direction"]
                    entry = pos["entry"]
                    tp = pos["tp"]
                    sl = pos["sl"]

                    hit_tp = (current_price >= tp) if direction == "BUY" else (current_price <= tp)
                    hit_sl = (current_price <= sl) if direction == "BUY" else (current_price >= sl)

                    gross_pnl_pct = ((current_price - entry) / entry * 100) if direction == "BUY" else ((entry - current_price) / entry * 100)

                    if hit_tp or hit_sl:
                        reason = "TP_HIT" if hit_tp else ("TRAILING_SL_HIT" if pos.get("is_be") else "SL_HIT")
                        gross_pnl_usd = pos["size"] * (gross_pnl_pct / 100.0)
                        
                        entry_fee = pos["size"] * FEE_RATE
                        exit_fee = (pos["size"] + gross_pnl_usd) * FEE_RATE
                        total_fee = entry_fee + exit_fee
                        net_pnl_usd = gross_pnl_usd - total_fee
                        net_pnl_pct = (net_pnl_usd / pos["size"]) * 100.0

                        paper_balance += net_pnl_usd

                        log(f"[EXIT] {symbol} {direction} | {reason} @ {current_price:.2f} | Net: {net_pnl_pct:+.2f}% (${net_pnl_usd:+.2f}) [Fee: -${total_fee:.2f}] | Bal: ${paper_balance:.2f}")

                        FastJournal.record_event({
                            "event": "EXIT",
                            "trade_id": pos["trade_id"],
                            "symbol": symbol,
                            "direction": direction,
                            "exit_price": current_price,
                            "gross_pnl_usd": round(gross_pnl_usd, 2),
                            "fees_usd": round(total_fee, 2),
                            "pnl_usd": round(net_pnl_usd, 2),
                            "pnl_pct": round(net_pnl_pct, 2),
                            "reason": reason,
                            "balance": round(paper_balance, 2),
                            "timestamp": datetime.now().isoformat()
                        })
                        del open_positions[symbol]
                        symbol_cooldowns[symbol] = now_ts + COOLDOWN_SECONDS
                        log(f"[COOLDOWN] {symbol} locked for {COOLDOWN_SECONDS}s to avoid overtrading.")
                        state_changed = True
                    else:
                        be_tag = "[BE]" if pos.get("is_be") else ""
                        status_summary.append(f"{symbol}: {direction}{be_tag} ({gross_pnl_pct:+.2f}%)")

                else:
                    # Check Cooldown
                    if symbol in symbol_cooldowns:
                        remaining = int(symbol_cooldowns[symbol] - now_ts)
                        if remaining > 0:
                            status_summary.append(f"{symbol}: COOLDOWN({remaining}s)")
                            continue
                        else:
                            del symbol_cooldowns[symbol]

                    signal, sl, tp = analyze_smc_scalp(candles)
                    if signal in ["BUY", "SELL"]:
                        spread_pct, best_bid, best_ask = fetch_orderbook_spread(symbol)
                        if spread_pct is not None and spread_pct > MAX_ALLOWED_SPREAD_PCT:
                            log(f"[SPREAD VETO] {symbol} {signal} rejected! Spread: {spread_pct:.3f}% > {MAX_ALLOWED_SPREAD_PCT}%")
                            status_summary.append(f"{symbol}: SPREAD_BLOCK({spread_pct:.2f}%)")
                            continue

                        trade_counter += 1
                        trade_size = 20.0
                        actual_entry = best_ask if (signal == "BUY" and best_ask) else (best_bid if (signal == "SELL" and best_bid) else current_price)

                        open_positions[symbol] = {
                            "trade_id": f"SMC-{trade_counter}",
                            "symbol": symbol,
                            "direction": signal,
                            "entry": actual_entry,
                            "sl": sl,
                            "tp": tp,
                            "size": trade_size,
                            "spread_pct": spread_pct,
                            "is_be": False,
                            "timestamp": datetime.now().isoformat()
                        }
                        state_changed = True
                        log(f"[ENTRY] {symbol} {signal} @ {actual_entry:.2f} (Spread: {spread_pct if spread_pct else 0:.3f}%) | TP: {tp:.2f} | SL: {sl:.2f} | Size: ${trade_size}")
                        FastJournal.record_event({
                            "event": "ENTRY",
                            "trade_id": f"SMC-{trade_counter}",
                            "symbol": symbol,
                            "direction": signal,
                            "entry_price": actual_entry,
                            "spread_pct": spread_pct,
                            "sl": sl,
                            "tp": tp,
                            "size": trade_size,
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        status_summary.append(f"{symbol}: {current_price:.1f}")

            if state_changed:
                StateManager.save_positions(open_positions)

            active_info = " | ".join(status_summary)
            log(f"[STATUS] Active Pos: {len(open_positions)} | {active_info}")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            log("[HALT] Scalper safely stopped by user. State is saved.")
            StateManager.save_positions(open_positions)
            break
        except Exception as e:
            log(f"[EXC] Loop error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
