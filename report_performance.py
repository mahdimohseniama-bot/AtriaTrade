#!/usr/bin/env python3
"""
AtriaTrade Real-Time Journal Performance Reporter
Analyzes trade_journal.json and provides actionable metrics:
- Win Rate, PnL (USD & %), Profit Factor, Trade Count
"""

import json
import os
from datetime import datetime

JOURNAL_FILE = "trade_journal.json"

def generate_report():
    print("=" * 60)
    print("      ATRIATRADE PAPER TRADING PERFORMANCE REPORT      ")
    print(f"      Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}      ")
    print("=" * 60)

    if not os.path.exists(JOURNAL_FILE):
        print(f"No journal file found ({JOURNAL_FILE}). Run the scalper first!")
        return

    try:
        with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading journal: {e}")
        return

    exits = [event for event in data if event.get("event") == "EXIT"]
    entries = [event for event in data if event.get("event") == "ENTRY"]

    total_closed = len(exits)
    if total_closed == 0:
        print(f"Active Entries Recorded: {len(entries)}")
        print("No closed trades yet. The engine is either holding or awaiting triggers.")
        print("=" * 60)
        return

    wins = [t for t in exits if t.get("pnl_usd", 0) > 0]
    losses = [t for t in exits if t.get("pnl_usd", 0) <= 0]

    gross_profit = sum(t.get("pnl_usd", 0) for t in wins)
    gross_loss = abs(sum(t.get("pnl_usd", 0) for t in losses))
    net_pnl = sum(t.get("pnl_usd", 0) for t in exits)

    win_rate = (len(wins) / total_closed) * 100 if total_closed > 0 else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)

    last_balance = exits[-1].get("balance", 100.0)

    print(f"Total Closed Trades : {total_closed}")
    print(f"Win Trades          : {len(wins)} ({win_rate:.1f}%)")
    print(f"Loss Trades         : {len(losses)} ({100 - win_rate:.1f}%)")
    print("-" * 60)
    print(f"Gross Profit        : +${gross_profit:.2f}")
    print(f"Gross Loss          : -${gross_loss:.2f}")
    print(f"Net Realized PnL    : {net_pnl:+.2f} USD")
    print(f"Profit Factor       : {profit_factor:.2f}")
    print(f"Current Paper Bal   : ${last_balance:.2f} USDT")
    print("=" * 60)
    print("Recent Closed Trades:")
    for t in exits[-5:]:
        sym = t.get("symbol", "N/A")
        side = t.get("direction", "N/A")
        pnl = t.get("pnl_usd", 0.0)
        reason = t.get("reason", "N/A")
        time_str = t.get("timestamp", "").split("T")[-1][:8]
        print(f" - [{time_str}] {sym:<8} {side:<4} | PnL: {pnl:+.2f}$ ({t.get('pnl_pct', 0):+.2f}%) | {reason}")
    print("=" * 60)

if __name__ == "__main__":
    generate_report()
