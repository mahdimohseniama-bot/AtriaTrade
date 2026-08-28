"""
Fair Value Gap (FVG) and Liquidity Void Detector for AtriaTrade.
Identifies 3-candle price imbalances and tracks mitigation levels.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class FVGType(str, Enum):
    BULLISH = "BULLISH_FVG"
    BEARISH = "BEARISH_FVG"


@dataclass(frozen=True)
class Candle:
    open: float
    high: float
    low: float
    close: float
    timestamp: Optional[int] = None


@dataclass(frozen=True)
class FairValueGap:
    gap_type: FVGType
    top_price: float
    bottom_price: float
    middle_candle_index: int
    gap_size: float
    is_mitigated: bool = False


class FVGDetector:
    """
    Scans candlestick sequences to detect, evaluate, and track Fair Value Gaps.
    """

    def __init__(self, min_gap_percent: float = 0.1):
        """
        :param min_gap_percent: حداقل اندازه شکاف بر حسب درصد برای فیلتر نویز
        """
        if min_gap_percent < 0:
            raise ValueError("حداقل درصد گپ نمی‌تواند منفی باشد")
        self.min_gap_percent = min_gap_percent

    def detect_fvgs(self, candles: List[Candle]) -> List[FairValueGap]:
        if len(candles) < 3:
            return []

        fvgs = []
        for i in range(len(candles) - 2):
            c1 = candles[i]
            c2 = candles[i + 1]
            c3 = candles[i + 2]

            # Bullish FVG: Low of candle 3 is higher than High of candle 1
            if c3.low > c1.high:
                gap_size = round(c3.low - c1.high, 4)
                gap_pct = (gap_size / c1.high) * 100
                if gap_pct >= self.min_gap_percent:
                    fvgs.append(
                        FairValueGap(
                            gap_type=FVGType.BULLISH,
                            top_price=c3.low,
                            bottom_price=c1.high,
                            middle_candle_index=i + 1,
                            gap_size=gap_size,
                            is_mitigated=False
                        )
                    )

            # Bearish FVG: High of candle 3 is lower than Low of candle 1
            elif c3.high < c1.low:
                gap_size = round(c1.low - c3.high, 4)
                gap_pct = (gap_size / c1.low) * 100
                if gap_pct >= self.min_gap_percent:
                    fvgs.append(
                        FairValueGap(
                            gap_type=FVGType.BEARISH,
                            top_price=c1.low,
                            bottom_price=c3.high,
                            middle_candle_index=i + 1,
                            gap_size=gap_size,
                            is_mitigated=False
                        )
                    )

        return fvgs

    def check_mitigation(self, fvg: FairValueGap, future_candles: List[Candle]) -> bool:
        """
        بررسی می‌کند آیا کندل‌های بعدی وارد ناحیه FVG شده و آن را پر کرده‌اند یا خیر.
        """
        for candle in future_candles:
            if fvg.gap_type == FVGType.BULLISH:
                if candle.low <= fvg.bottom_price:
                    return True
            elif fvg.gap_type == FVGType.BEARISH:
                if candle.high >= fvg.top_price:
                    return True
        return False
