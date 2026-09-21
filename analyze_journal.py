#!/usr/bin/env python3
import json
import os

JOURNAL_FILE = "trade_journal.json"

def analyze():
    print("=" * 60)
    print("📈 [AtriaTrade] Performance & Journal Analytics")
    print("=" * 60)

    if not os.path.exists(JOURNAL_FILE):
        print(f"⚠️ فایل {JOURNAL_FILE} پیدا نشد.")
        return

    with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
        try:
            records = json.load(f)
        except Exception as e:
            print(f"❌ خطا در خواندن JSON: {e}")
            return

    if not isinstance(records, list) or len(records) == 0:
        print("ℹ️ ژورنال خالی است.")
        return

    entries = [r for r in records if r.get("event") == "ENTRY"]
    exits = [r for r in records if r.get("event") == "EXIT"]
    stopped = [r for r in records if r.get("event") == "STOPPED_WITH_OPEN_POSITION"]

    print(f"🔹 کل ورودها (Entries): {len(entries)}")
    print(f"🔹 کل خروج‌های تکمیل‌شده (Closed Trades): {len(exits)}")
    print(f"🔹 پوزیشن‌های متوقف‌شده دستی (Interrupted): {len(stopped)}")
    print("-" * 60)

    if not exits:
        print("ℹ️ هنوز هیچ تریدِ بسته‌شده‌ای (TP/SL) ثبت نشده تا آمار سود/زیان محاسبه شود.")
        print("💡 نکته: اجازه بدهید ربات در اجرای بعدی تا خوردن حد سود/ضرر روشن بماند.")
        return

    pnls = [r.get("pnl_percentage", 0.0) for r in exits]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]

    win_rate = (len(wins) / len(pnls)) * 100 if pnls else 0.0
    total_gain = sum(wins)
    total_loss = abs(sum(losses))
    profit_factor = (total_gain / total_loss) if total_loss > 0 else (999.0 if total_gain > 0 else 0.0)
    net_pnl = sum(pnls)

    print(f"🏆 Win Rate: {win_rate:.1f}% ({len(wins)} برد / {len(losses)} باخت)")
    print(f"📊 Net PnL (مجموع بازدهی): {net_pnl:+.2f}%")
    print(f"⚡ Profit Factor: {profit_factor:.2f}")
    print(f"🟢 میانگین ترید مثبت: {('+' + str(round(sum(wins)/len(wins), 2)) + '%') if wins else 'N/A'}")
    print(f"🔴 میانگین ترید منفی: {('-' + str(round(total_loss/len(losses), 2)) + '%') if losses else 'N/A'}")
    print("=" * 60)

if __name__ == "__main__":
    analyze()
