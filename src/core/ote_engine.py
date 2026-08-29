"""
Optimal Trade Entry (OTE) and Fibonacci Confluence Engine for AtriaTrade (Capability 72).
Calculates key Fibonacci retracement levels (0.618, 0.705, 0.786) and evaluates OTE zones.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class TrendDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


@dataclass(frozen=True)
class OTEZone:
    direction: TrendDirection
    swing_low: float
    swing_high: float
    fib_618: float
    fib_705: float
    fib_786: float
    optimal_entry: float  # Key sweet spot (70.5%)
    stop_loss_level: float
    take_profit_level: float


class OTEEngine:
    """
    Computes SMC Optimal Trade Entry zones and Fibonacci levels.
    """

    def __init__(self, sweet_spot_fib: float = 0.705):
        if not (0.0 < sweet_spot_fib < 1.0):
            raise ValueError("sweet_spot_fib باید مقداری بین ۰ و ۱ باشد")
        self.sweet_spot_fib = sweet_spot_fib

    def calculate_retracement_levels(self, swing_low: float, swing_high: float, direction: TrendDirection) -> Dict[str, float]:
        """
        محاسبه ترازهای استاندارد فیبوناچی
        """
        if swing_low >= swing_high:
            raise ValueError("swing_low باید اکیداً کوچکتر از swing_high باشد")

        diff = swing_high - swing_low

        if direction == TrendDirection.BULLISH:
            # در روند صعودی: قیمت از سقف به سمت کف اصلاح می‌کند
            return {
                "0.0": round(swing_high, 4),
                "0.382": round(swing_high - 0.382 * diff, 4),
                "0.500": round(swing_high - 0.500 * diff, 4),
                "0.618": round(swing_high - 0.618 * diff, 4),
                "0.705": round(swing_high - 0.705 * diff, 4),
                "0.786": round(swing_high - 0.786 * diff, 4),
                "1.0": round(swing_low, 4),
            }
        else:
            # در روند نزولی: قیمت از کف به سمت سقف اصلاح می‌کند (رالی صعودی موقت)
            return {
                "0.0": round(swing_low, 4),
                "0.382": round(swing_low + 0.382 * diff, 4),
                "0.500": round(swing_low + 0.500 * diff, 4),
                "0.618": round(swing_low + 0.618 * diff, 4),
                "0.705": round(swing_low + 0.705 * diff, 4),
                "0.786": round(swing_low + 0.786 * diff, 4),
                "1.0": round(swing_high, 4),
            }

    def generate_ote_zone(self, swing_low: float, swing_high: float, direction: TrendDirection) -> OTEZone:
        """
        تولید محدوده ورود OTE همراه با حد سود و حد ضرر پیشنهادی اسمارت‌مانی
        """
        levels = self.calculate_retracement_levels(swing_low, swing_high, direction)

        if direction == TrendDirection.BULLISH:
            sl = round(swing_low * 0.998, 4)  # کمی پایین‌تر از سوئینگ کف
            tp = round(swing_high, 4)         # سقف قبلی به عنوان تارگت اول
            sweet_entry = levels["0.705"]
        else:
            sl = round(swing_high * 1.002, 4) # کمی بالاتر از سوئینگ سقف
            tp = round(swing_low, 4)          # کف قبلی به عنوان تارگت اول
            sweet_entry = levels["0.705"]

        return OTEZone(
            direction=direction,
            swing_low=swing_low,
            swing_high=swing_high,
            fib_618=levels["0.618"],
            fib_705=levels["0.705"],
            fib_786=levels["0.786"],
            optimal_entry=sweet_entry,
            stop_loss_level=sl,
            take_profit_level=tp
        )

    def is_price_in_ote_zone(self, current_price: float, ote_zone: OTEZone) -> bool:
        """
        بررسی اینکه آیا قیمت فعلی در زون طلایی 61.8% تا 78.6% قرار دارد یا خیر.
        """
        if ote_zone.direction == TrendDirection.BULLISH:
            # در روند صعودی زون بین fib_786 (پایین‌تر) و fib_618 (بالاتر) است
            return ote_zone.fib_786 <= current_price <= ote_zone.fib_618
        else:
            # در روند نزولی زون بین fib_618 (پایین‌تر) و fib_786 (بالاتر) است
            return ote_zone.fib_618 <= current_price <= ote_zone.fib_786
