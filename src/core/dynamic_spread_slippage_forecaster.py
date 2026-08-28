from dataclasses import dataclass
from typing import Dict, Any, Optional
import math


@dataclass
class MarketMicrostructureState:
    bid_price: float
    ask_price: float
    order_size: float
    depth_volume_top: float  # حجم در بهترین قیمت‌های خرید/فروش
    volatility_ratio: float = 1.0  # نسبت نوسان جاری به نوسان نرمال (1.0 = نرمال)
    is_high_impact_news_window: bool = False


@dataclass
class SlippageForecast:
    bid_price: float
    ask_price: float
    quoted_spread_pct: float
    effective_spread_pct: float
    expected_slippage_pct: float
    total_execution_friction_pct: float
    execution_cost_usd: float
    is_execution_safe: bool
    penalty_reason: Optional[str] = None


class DynamicSpreadSlippageForecaster:
    """
    پیش‌بین دینامیک اسپرد و اسلیپیج بر مبنای نقدینگی دفتر سفارشات،
    حجم سفارش، نوسانات بازار و رویدادهای پرریسک.
    """

    def __init__(
        self,
        base_slippage_pct: float = 0.05,       # 0.05% اسلیپیج پایه
        max_acceptable_friction_pct: float = 0.50, # سقف مجاز کل اصطکاک (اسپرد + اسلیپیج)
        impact_factor: float = 0.20,            # ضریب تأثیر حجم سفارش به عمق
        volatility_multiplier: float = 1.5      # ضریب حساسیت به نوسانات غیرعادی
    ):
        self.base_slippage_pct = max(0.0, float(base_slippage_pct))
        self.max_acceptable_friction_pct = max(0.01, float(max_acceptable_friction_pct))
        self.impact_factor = max(0.0, float(impact_factor))
        self.volatility_multiplier = max(1.0, float(volatility_multiplier))

    def forecast_slippage(self, state: MarketMicrostructureState) -> SlippageForecast:
        """
        محاسبه اسپرد مؤثر و پیش‌بینی اسلیپیج اجرای معامله.
        """
        if state.bid_price <= 0 or state.ask_price <= 0:
            raise ValueError("قیمت‌های Bid و Ask باید بزرگتر از صفر باشند.")
        if state.ask_price < state.bid_price:
            raise ValueError("قیمت Ask نمی‌تواند از قیمت Bid کمتر باشد.")
        if state.order_size < 0:
            raise ValueError("حجم سفارش نمی‌تواند منفی باشد.")

        mid_price = (state.bid_price + state.ask_price) / 2.0
        quoted_spread = state.ask_price - state.bid_price
        quoted_spread_pct = (quoted_spread / mid_price) * 100.0

        # ۱. تأثیر عدم تعادل نقدینگی و اندازه سفارش (Market Impact)
        depth = max(1e-6, state.depth_volume_top)
        volume_pressure = (state.order_size / depth)
        size_impact_pct = self.impact_factor * (volume_pressure ** 0.8)

        # ۲. تأثیر نوسانات شدید بازار
        vol_impact = 1.0
        if state.volatility_ratio > 1.0:
            vol_impact = 1.0 + (state.volatility_ratio - 1.0) * self.volatility_multiplier

        # ۳. جریمه پنجره خبر/رویداد با ریسک بالا
        news_penalty = 2.0 if state.is_high_impact_news_window else 1.0

        # تخمین اسلیپیج کل
        expected_slippage_pct = (self.base_slippage_pct + size_impact_pct) * vol_impact * news_penalty

        # اسپرد مؤثر با در نظر گرفتن نوسان لحظه‌ای
        effective_spread_pct = quoted_spread_pct * max(1.0, vol_impact * 0.7)

        # اصطکاک کل معامله (Spread + Slippage)
        total_friction_pct = effective_spread_pct + expected_slippage_pct
        
        # هزینه تخمینی معامله به دلار
        order_value_usd = state.order_size * mid_price
        execution_cost_usd = order_value_usd * (total_friction_pct / 100.0)

        # ارزیابی امنیت اجرا
        is_safe = total_friction_pct <= self.max_acceptable_friction_pct
        penalty_reason = None
        if not is_safe:
            penalty_reason = f"اصطکاک بیش از حد مجاز: {total_friction_pct:.3f}% > {self.max_acceptable_friction_pct:.3f}%"
        elif state.is_high_impact_news_window:
            penalty_reason = "هشدار: پنجره زمانی خبر با نوسان بالا"

        return SlippageForecast(
            bid_price=state.bid_price,
            ask_price=state.ask_price,
            quoted_spread_pct=round(quoted_spread_pct, 4),
            effective_spread_pct=round(effective_spread_pct, 4),
            expected_slippage_pct=round(expected_slippage_pct, 4),
            total_execution_friction_pct=round(total_friction_pct, 4),
            execution_cost_usd=round(execution_cost_usd, 4),
            is_execution_safe=is_safe,
            penalty_reason=penalty_reason
        )
