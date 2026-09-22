# مرحله ۴ - گام پایانی: ادغام هزینه‌ها در تصمیم نهایی
MAX_SPREAD_RATIO = 0.0008
MIN_BUY_IMBALANCE = 0.20
MAX_SELL_IMBALANCE = -0.20

WALLEX_TAKER_FEE = 0.0035
ESTIMATED_SLIPPAGE = 0.0005
TOTAL_ROUNDTRIP_COST = (WALLEX_TAKER_FEE + ESTIMATED_SLIPPAGE) * 2  # ~0.80%

# حداقل لبه سودآوری: هزینه رفت‌وبرگشت + بافر 20%
MIN_REQUIRED_MOVE = TOTAL_ROUNDTRIP_COST * 1.2  # ~0.96%

def full_decision(best_bid, best_ask, bid_qty, ask_qty, expected_move_pct):
    spread_ratio = (best_ask - best_bid) / best_bid
    total_qty = bid_qty + ask_qty
    imbalance = (bid_qty - ask_qty) / total_qty if total_qty > 0 else 0.0

    print("=" * 60)
    print(f"Spread: {spread_ratio*100:.4f}% | Imbalance: {imbalance:.4f}")
    print(f"Expected Move: {expected_move_pct*100:.2f}% | Required: {MIN_REQUIRED_MOVE*100:.2f}%")

    # Gate 1: اسپرد
    if spread_ratio > MAX_SPREAD_RATIO:
        return "NONE", f"REJECTED: Spread {spread_ratio*100:.4f}% > {MAX_SPREAD_RATIO*100:.4f}%"

    # Gate 2: تعیین جهت
    if imbalance >= MIN_BUY_IMBALANCE:
        direction = "BUY"
    elif imbalance <= MAX_SELL_IMBALANCE:
        direction = "SELL"
    else:
        return "NONE", f"NEUTRAL: Imbalance {imbalance:.2f} in noise zone"

    # Gate 3: صرفه اقتصادی (Economic Gate) — قلب مرحله ۴
    if expected_move_pct < MIN_REQUIRED_MOVE:
        return "NONE", (f"REJECTED {direction}: Expected move {expected_move_pct*100:.2f}% "
                        f"< required {MIN_REQUIRED_MOVE*100:.2f}% (roundtrip cost {TOTAL_ROUNDTRIP_COST*100:.2f}% + 20% buffer)")

    return direction, f"VALID {direction}: Economics OK (edge {expected_move_pct*100:.2f}% vs cost {MIN_REQUIRED_MOVE*100:.2f}%)"

# سناریو A: سیگنال خرید با هدف سود ۱.۵٪ (اقتصادی)
print("\n--- Scenario A: BUY with 1.5% expected move ---")
a, ra = full_decision(85950.0, 85980.0, 0.025, 0.005, 0.015)
print(f"Action: {a} | Reason: {ra}")

# سناریو B: سیگنال خرید با هدف سود فقط ۰.۵٪ (زیر هزینه رفت‌وبرگشت!)
print("\n--- Scenario B: BUY with only 0.5% expected move ---")
b, rb = full_decision(85950.0, 85980.0, 0.025, 0.005, 0.005)
print(f"Action: {b} | Reason: {rb}")

# سناریو C: داده واقعی والکس (فشار فروش، حرکت مورد انتظار ۱٪)
print("\n--- Scenario C: Real Wallex data, SELL with 1.0% expected move ---")
c, rc = full_decision(85947.95, 85999.99, 0.00644208, 0.01960127, 0.010)
print(f"Action: {c} | Reason: {rc}")
