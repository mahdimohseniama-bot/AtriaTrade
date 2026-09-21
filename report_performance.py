#!/usr/bin/env python3
"""
AtriaTrade Live Performance & Fee Analyzer v2.0
Analyzes trade_journal.json & active_positions.json with net realistic stats.
"""

import os
import json
from datetime import datetime

JOURNAL_FILE = "trade_journal.json"
STATE_FILE = "active_positions.json"

def fmt_usd(val):
    sign = "+" if val > 0 else ""
    return f"{sign}${val:.2f}"

def fmt_pct(val):
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.2f}%"

def analyze():
    print("=" * 68)
    print(f" AtriaTrade Performance & Fee Report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 68)

    # 1. Check Active Positions
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                active = json.load(f)
            if active:
                print(f"⚡ ACTIVE POSITIONS IN FLIGHT ({len(active)}):")
                for sym, pos in active.items():
                    be_str = " [BE Active]" if pos.get("is_be") else ""
                    print(f"  • {sym} {pos['direction']} @ {pos['entry']:.2f} | TP: {pos['tp']:.2f} | SL: {pos['sl']:.2f}{be_str}")
            else:
                print("⚡ ACTIVE POSITIONS: None (Searching for SMC sweeps)")
        except Exception:
            print("⚡ ACTIVE POSITIONS: Unable to parse state file")
    else:
        print("⚡ ACTIVE POSITIONS: 0")

    print("-" * 68)

    # 2. Check Journal Performance
    if not os.path.exists(JOURNAL_FILE):
        print("⚠️ No trade_journal.json found yet.")
        print("=" * 68)
        return

    try:
        with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
            events = json.load(f)
    except Exception as e:
        print(f"⚠️ Error reading journal: {e}")
        return

    exits = [e for e in events if e.get("event") == "EXIT"]
    entries = [e for e in events if e.get("event") == "ENTRY"]

    print(f"📊 SUMMARY STATISTICS:")
    print(f"  • Total Entries Triggered: {len(entries)}")
    print(f"  • Completed Trades:       {len(exits)}")

    if not exits:
        print("\n⏳ No closed trades recorded yet. Waiting for market exits...")
        print("=" * 68)
        return

    total_net_pnl = sum(e.get("pnl_usd", 0.0) for e in exits)
    total_gross_pnl = sum(e.get("gross_pnl_usd", e.get("pnl_usd", 0.0)) for e in exits)
    total_fees = sum(e.get("fees_usd", 0.0) for e in exits)

    wins = [e for e in exits if e.get("pnl_usd", 0.0) > 0]
    losses = [e for e in exits if e.get("pnl_usd", 0.0) <= 0]
    win_rate = (len(wins) / len(exits)) * 100.0 if exits else 0.0

    gross_profit = sum(e.get("pnl_usd", 0.0) for e in wins)
    gross_loss = abs(sum(e.get("pnl_usd", 0.0) for e in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

    tp_hits = len([e for e in exits if e.get("reason") == "TP_HIT"])
    trail_hits = len([e for e in exits if e.get("reason") == "TRAILING_SL_HIT"])
    sl_hits = len([e for e in exits if e.get("reason") == "SL_HIT"])

    print(f"  • Win Rate:               {win_rate:.1f}% ({len(wins)}W / {len(losses)}L)")
    print(f"  • Profit Factor:          {profit_factor:.2f}")
    print(f"  • Gross PnL:              {fmt_usd(total_gross_pnl)}")
    print(f"  • Total Exchange Fees:    -${total_fees:.2f} (Wallex 0.2% Taker)")
    print(f"  • Net Realized PnL:       {fmt_usd(total_net_pnl)}")
    print(f"  • Exit Breakdown:         TP: {tp_hits} | Trailing-SL: {trail_hits} | Hard-SL: {sl_hits}")

    latest_bal = exits[-1].get("balance", 100.0)
    print(f"  • Current Balance:        ${latest_bal:.2f}")

    print("\n📜 RECENT COMPLETED TRADES:")
    for e in exits[-5:]:
        direction = e.get("direction", "N/A")
        sym = e.get("symbol", "N/A")
        pnl_u = e.get("pnl_usd", 0.0)
        pnl_p = e.get("pnl_pct", 0.0)
        reason = e.get("reason", "EXIT")
        ts = e.get("timestamp", "")[:19].replace("T", " ")
        print(f"  [{ts}] {sym:<7} {direction:<4} | Reason: {reason:<15} | Net: {fmt_usd(pnl_u):<8} ({fmt_pct(pnl_p):<7})")

    print("=" * 68)

if __name__ == "__main__":
    analyze()
