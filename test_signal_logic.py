import json

# تنظیمات سخت‌گیرانه فعلی
MAX_SPREAD_RATIO = 0.0008  # 0.08%
MIN_IMBALANCE = 1.25       # نسبت خریدار به فروشنده

def evaluate_signal(spread, imbalance, bid_ask_ratio):
    print(f"\nEvaluating Signal:")
    print(f"  Spread: {spread*100:.4f}% | Limit: {MAX_SPREAD_RATIO*100:.4f}%")
    print(f"  Imbalance: {imbalance:.4f} | Limit: {MIN_IMBALANCE}")

    # چک کردن اسپرد
    if spread > MAX_SPREAD_RATIO:
        return False, "Rejected: Spread too high"

    # چک کردن ایمبالانس (اینجا چون مقدار ما منفی است، باید منطقش را درست کنیم)
    # اگر imbalace < 0 باشد یعنی فروشنده بیشتر است. ما برای خرید ایمبالانس مثبت می‌خواهیم.
    if imbalance < 0:
        return False, "Rejected: Heavy selling pressure (Negative Imbalance)"
        
    if imbalance < MIN_IMBALANCE:
        return False, f"Rejected: Imbalance {imbalance:.2f} < {MIN_IMBALANCE}"

    return True, "SIGNAL: OK to trade"

# دیتای تست (بر اساس خروجی Wallex که گرفتیم)
# BTC: spread 0.0006, imbalance -0.5
decision, reason = evaluate_signal(0.0006, -0.5, 0.32)
print(f"Result: {decision} | Reason: {reason}")
