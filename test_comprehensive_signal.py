import json

# تنظیمات استراتژی و مدیریت ریسک
MAX_SPREAD_RATIO = 0.0008     # سقف اسپرد: 0.08%
MIN_BUY_IMBALANCE = 0.20       # حداقل ایمبالانس مثبت برای خرید (۲۰٪ غلبه خریداران)
MAX_SELL_IMBALANCE = -0.20     # حداکثر ایمبالانس منفی برای فروش (۲۰٪ غلبه فروشندگان)

# هزینه‌ها (کارمزد والکس + اسلیپیج تخمینی)
WALLEX_TAKER_FEE = 0.0035     # 0.35% کارمزد تیکر
ESTIMATED_SLIPPAGE = 0.0005   # 0.05% اسلیپیج
TOTAL_ROUNDTRIP_COST = (WALLEX_TAKER_FEE + ESTIMATED_SLIPPAGE) * 2 # حدود 0.8% رفت و برگشت

def evaluate_market_signal(best_bid, best_ask, bid_qty, ask_qty):
    spread_ratio = (best_ask - best_bid) / best_bid
    total_qty = bid_qty + ask_qty
    imbalance = (bid_qty - ask_qty) / total_qty if total_qty > 0 else 0.0

    print("=" * 60)
    print(f"Best Bid: {best_bid} | Best Ask: {best_ask}")
    print(f"Spread: {spread_ratio * 100:.4f}% (Max Allowed: {MAX_SPREAD_RATIO * 100:.4f}%)")
    print(f"Imbalance: {imbalance:.4f}")
    print(f"Total Roundtrip Friction Fee+Slippage: {TOTAL_ROUNDTRIP_COST * 100:.2f}%")

    # 1. چک کردن اسپرد
    if spread_ratio > MAX_SPREAD_RATIO:
        return "NONE", f"REJECTED: Spread ({spread_ratio*100:.4f}%) > Max ({MAX_SPREAD_RATIO*100:.4f}%)"

    # 2. بررسی سیگنال خرید
    if imbalance >= MIN_BUY_IMBALANCE:
        return "BUY", f"VALID BUY SIGNAL: Imbalance ({imbalance:.2f}) >= {MIN_BUY_IMBALANCE}"

    # 3. بررسی سیگنال فروش
    if imbalance <= MAX_SELL_IMBALANCE:
        return "SELL", f"VALID SELL SIGNAL: Imbalance ({imbalance:.2f}) <= {MAX_SELL_IMBALANCE}"

    return "NONE", f"NEUTRAL: Imbalance ({imbalance:.2f}) within noise zone ({MAX_SELL_IMBALANCE} to {MIN_BUY_IMBALANCE})"

# تست با داده‌های نمونه واقعی والکس
print("\n--- Test Case 1: Real BTC Market Data (From Step 2) ---")
action1, reason1 = evaluate_market_signal(85947.95, 85999.99, 0.00644208, 0.01960127)
print(f"Action: {action1} | Reason: {reason1}")

print("\n--- Test Case 2: Simulated High Buying Pressure ---")
action2, reason2 = evaluate_market_signal(85950.00, 85980.00, 0.02500000, 0.00500000)
print(f"Action: {action2} | Reason: {reason2}")
