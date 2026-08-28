from typing import Dict, Any, List, Optional


class ScaleOutEngine:
    """
    موتور مدیریت خروج پله‌ای (Scale-Out) و سیو سود هوشمند.
    """

    def __init__(self, targets: Optional[List[Dict[str, float]]] = None):
        """
        targets: لیستی از دیکشنری‌های تارگت سود
        مثال:
        [
            {"profit_pct": 2.0, "close_ratio": 0.33},  # سود ۲٪، بستن یک‌سوم
            {"profit_pct": 5.0, "close_ratio": 0.33},  # سود ۵٪، بستن یک‌سوم دیگر
            {"profit_pct": 10.0, "close_ratio": 0.34}  # سود ۱۰٪، بستن باقی‌مانده
        ]
        """
        self.targets = targets or [
            {"profit_pct": 2.0, "close_ratio": 0.33},
            {"profit_pct": 5.0, "close_ratio": 0.33},
            {"profit_pct": 10.0, "close_ratio": 0.34},
        ]
        # مرتب‌سازی تارگت‌ها بر اساس درصد سود
        self.targets.sort(key=lambda x: x["profit_pct"])

    def evaluate_scale_out(
        self,
        entry_price: float,
        current_price: float,
        current_qty: float,
        side: str = "BUY",
        executed_target_indices: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        ارزیابی قیمت لحظه‌ای نسبت به تارگت‌ها و تولید دستور خروج پله‌ای.
        """
        if entry_price <= 0 or current_price <= 0 or current_qty <= 0:
            return {"should_scale_out": False, "reason": "INVALID_INPUTS"}

        executed_indices = set(executed_target_indices or [])

        # محاسبه درصد سود/زیان پوزیشن
        if side.upper() in ["BUY", "LONG"]:
            pnl_pct = ((current_price - entry_price) / entry_price) * 100.0
        else:  # SELL / SHORT
            pnl_pct = ((entry_price - current_price) / entry_price) * 100.0

        for idx, target in enumerate(self.targets):
            if idx not in executed_indices:
                if pnl_pct >= target["profit_pct"]:
                    close_qty = round(current_qty * target["close_ratio"], 8)
                    return {
                        "should_scale_out": True,
                        "target_index": idx,
                        "target_profit_pct": target["profit_pct"],
                        "current_pnl_pct": round(pnl_pct, 4),
                        "close_ratio": target["close_ratio"],
                        "close_qty": close_qty,
                        "reason": f"TARGET_HIT_{idx+1}",
                    }

        return {
            "should_scale_out": False,
            "current_pnl_pct": round(pnl_pct, 4),
            "reason": "NO_NEW_TARGET_HIT",
        }
