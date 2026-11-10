from typing import Dict, Any, Optional

class DynamicPositionProtector:
    def __init__(self, sl_pct: float = 0.015, tp_pct: float = 0.03):
        self.sl_pct = sl_pct
        self.tp_pct = tp_pct

    def calculate_levels(self, entry_price: float, side: str) -> Dict[str, float]:
        if side.upper() == "LONG":
            sl_price = entry_price * (1.0 - self.sl_pct)
            tp_price = entry_price * (1.0 + self.tp_pct)
        elif side.upper() == "SHORT":
            sl_price = entry_price * (1.0 + self.sl_pct)
            tp_price = entry_price * (1.0 - self.tp_pct)
        else:
            sl_price = entry_price
            tp_price = entry_price

        return {
            "entry_price": entry_price,
            "sl_price": round(sl_price, 2),
            "tp_price": round(tp_price, 2)
        }

    def check_exit(self, side: str, current_price: float, levels: Dict[str, float]) -> Optional[str]:
        if not levels or side.upper() not in ["LONG", "SHORT"]:
            return None

        sl = levels.get("sl_price", 0.0)
        tp = levels.get("tp_price", 0.0)

        if side.upper() == "LONG":
            if current_price <= sl:
                return "SL_TRIGGERED"
            if current_price >= tp:
                return "TP_TRIGGERED"
        elif side.upper() == "SHORT":
            if current_price >= sl:
                return "SL_TRIGGERED"
            if current_price <= tp:
                return "TP_TRIGGERED"

        return None
