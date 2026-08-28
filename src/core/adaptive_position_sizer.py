from typing import Dict, Any


class AdaptivePositionSizer:
    """
    موتور محاسبه پویای حجم معامله بر اساس نوسانات بازار (ATR) و کسر ریسک حساب.
    """

    def __init__(
        self,
        default_risk_per_trade_pct: float = 1.0,
        max_position_size_pct: float = 100.0,
    ):
        self.default_risk_per_trade_pct = default_risk_per_trade_pct
        self.max_position_size_pct = max_position_size_pct

    def calculate_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss_price: float,
        atr_value: float = 0.0,
        win_rate: float = 0.5,
        risk_reward_ratio: float = 1.5,
        use_half_kelly: bool = False,
    ) -> Dict[str, Any]:
        """
        محاسبه حجم بهینه ورود و مقدار سرمایه درگیر.
        """
        if capital <= 0 or entry_price <= 0 or stop_loss_price <= 0 or entry_price == stop_loss_price:
            return {"valid": False, "size": 0.0, "reason": "INVALID_PRICE_OR_CAPITAL"}

        risk_pct = self.default_risk_per_trade_pct

        # در صورت فعال بودن نیمه-کلی (Half Kelly)
        if use_half_kelly and win_rate > 0 and risk_reward_ratio > 0:
            q = 1.0 - win_rate
            kelly_f = (win_rate * risk_reward_ratio - q) / risk_reward_ratio
            half_kelly_pct = max(0.0, (kelly_f / 2.0) * 100.0)
            risk_pct = min(risk_pct, half_kelly_pct) if half_kelly_pct > 0 else 0.5

        # تنظیم ریسک بر اساس نوسان (در صورت ارائه ATR معتبر)
        if atr_value > 0:
            atr_pct = (atr_value / entry_price) * 100.0
            if atr_pct > 3.0:  # نوسان خیلی بالا
                risk_pct *= 0.75  # کاهش ریسک
            elif atr_pct < 0.8:  # نوسان ملایم
                risk_pct *= 1.1   # افزایش جزئی ریسک

        risk_amount = capital * (risk_pct / 100.0)
        risk_per_unit = abs(entry_price - stop_loss_price)

        size = risk_amount / risk_per_unit
        total_position_val = size * entry_price
        max_allowed_val = capital * (self.max_position_size_pct / 100.0)

        # اعمال سقف حداکثر سرمایه مجاز در یک پوزیشن
        if total_position_val > max_allowed_val:
            size = max_allowed_val / entry_price
            total_position_val = max_allowed_val

        return {
            "valid": True,
            "size": round(size, 6),
            "position_value": round(total_position_val, 2),
            "effective_risk_pct": round(risk_pct, 4),
            "risk_amount": round(risk_amount, 2),
        }
