"""
Dynamic Volatility Regime & ATR Multiplier Optimizer for AtriaTrade.
Dynamically adjusts stop-loss, take-profit distances, and position risk
based on real-time ATR and historical volatility regimes.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class VolatilityRegime(str, Enum):
    LOW = "LOW_VOLATILITY"
    NORMAL = "NORMAL_VOLATILITY"
    HIGH = "HIGH_VOLATILITY"
    EXTREME = "EXTREME_VOLATILITY"


@dataclass(frozen=True)
class VolatilityOptimizationResult:
    regime: VolatilityRegime
    volatility_ratio: float
    dynamic_sl_multiplier: float      # e.g., 1.5x ATR for normal, 2.2x for high
    dynamic_tp_multiplier: float      # e.g., 2.5x ATR for normal, 3.5x for high
    risk_size_multiplier: float       # Position size adjustment (e.g. 0.5x in extreme volatility)
    is_safe_to_enter: bool
    warning_message: Optional[str] = None


class VolatilityRegimeOptimizer:
    """
    Optimizes trading stops and capital exposure according to market volatility.
    """

    def __init__(
        self,
        base_sl_atr_mult: float = 1.5,
        base_tp_atr_mult: float = 2.5,
        extreme_vol_threshold: float = 2.5,
        low_vol_threshold: float = 0.7
    ):
        if base_sl_atr_mult <= 0 or base_tp_atr_mult <= 0:
            raise ValueError("ضرایب پایه استاپ و تارگت باید بزرگتر از صفر باشند")
        if low_vol_threshold >= extreme_vol_threshold:
            raise ValueError("آستانه نوسان پایین باید کمتر از آستانه نوسان شدید باشد")

        self.base_sl_atr_mult = base_sl_atr_mult
        self.base_tp_atr_mult = base_tp_atr_mult
        self.extreme_vol_threshold = extreme_vol_threshold
        self.low_vol_threshold = low_vol_threshold

    def optimize(self, current_atr: float, baseline_atr: float) -> VolatilityOptimizationResult:
        if current_atr <= 0 or baseline_atr <= 0:
            raise ValueError("مقادیر ATR باید اعداد مثبت باشند")

        vol_ratio = round(current_atr / baseline_atr, 4)

        if vol_ratio >= self.extreme_vol_threshold:
            regime = VolatilityRegime.EXTREME
            sl_mult = round(self.base_sl_atr_mult * 1.6, 2)
            tp_mult = round(self.base_tp_atr_mult * 1.8, 2)
            risk_mult = 0.40  # کاهش ۶۰ درصدی حجم ورود برای ایمنی
            is_safe = False
            msg = "نوسانات شدید و غیرعادی؛ ورود به معامله پرریسک ارزیابی می‌شود"
        elif vol_ratio >= 1.4:
            regime = VolatilityRegime.HIGH
            sl_mult = round(self.base_sl_atr_mult * 1.3, 2)
            tp_mult = round(self.base_tp_atr_mult * 1.4, 2)
            risk_mult = 0.70  # کاهش ۳۰ درصدی حجم ورود
            is_safe = True
            msg = "نوسان بالا؛ استاپ‌ها گشادتر و حجم پوزیشن کنترل شده است"
        elif vol_ratio <= self.low_vol_threshold:
            regime = VolatilityRegime.LOW
            sl_mult = round(self.base_sl_atr_mult * 0.85, 2)
            tp_mult = round(self.base_tp_atr_mult * 0.90, 2)
            risk_mult = 1.0
            is_safe = True
            msg = "بازار کم‌نوسان و فشرده"
        else:
            regime = VolatilityRegime.NORMAL
            sl_mult = self.base_sl_atr_mult
            tp_mult = self.base_tp_atr_mult
            risk_mult = 1.0
            is_safe = True
            msg = None

        return VolatilityOptimizationResult(
            regime=regime,
            volatility_ratio=vol_ratio,
            dynamic_sl_multiplier=sl_mult,
            dynamic_tp_multiplier=tp_mult,
            risk_size_multiplier=risk_mult,
            is_safe_to_enter=is_safe,
            warning_message=msg
        )
