"""
Liquidity & Stop Hunt Engine for AtriaTrade (Capability 71).
Detects Equal Highs/Lows (EQH/EQL) and Liquidity Sweep (Stop Hunt) events.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from src.core.fvg_detector import Candle


class LiquidityType(str, Enum):
    EQUAL_HIGHS = "EQH"
    EQUAL_LOWS = "EQL"
    BUY_SIDE_LIQUIDITY = "BSL"
    SELL_SIDE_LIQUIDITY = "SSL"


class SweepType(str, Enum):
    BULLISH_SWEEP = "BULLISH_SWEEP"  # Swept low and closed above (Reversal Long)
    BEARISH_SWEEP = "BEARISH_SWEEP"  # Swept high and closed below (Reversal Short)


@dataclass(frozen=True)
class LiquidityPool:
    pool_type: LiquidityType
    price_level: float
    candle_indices: List[int]
    tolerance_pct: float


@dataclass(frozen=True)
class LiquiditySweepEvent:
    sweep_type: SweepType
    swept_level: float
    candle_index: int
    wick_penetration: float


class LiquidityEngine:
    """
    Identifies liquidity pools and detects stop sweeps.
    """

    def __init__(self, tolerance_pct: float = 0.0015):
        """
        :param tolerance_pct: حداکثر درصد اختلاف برای هم‌تراز دانستن سقف‌ها یا کف‌ها (مثلا 0.15%)
        """
        if tolerance_pct <= 0:
            raise ValueError("tolerance_pct باید بزرگتر از صفر باشد")
        self.tolerance_pct = tolerance_pct

    def detect_equal_highs_lows(self, candles: List[Candle]) -> List[LiquidityPool]:
        pools: List[LiquidityPool] = []
        n = len(candles)
        if n < 2:
            return pools

        # Detect Equal Highs
        for i in range(n - 1):
            for j in range(i + 1, min(i + 10, n)):
                h1, h2 = candles[i].high, candles[j].high
                diff = abs(h1 - h2) / ((h1 + h2) / 2.0)
                if diff <= self.tolerance_pct:
                    avg_level = (h1 + h2) / 2.0
                    pools.append(
                        LiquidityPool(
                            pool_type=LiquidityType.EQUAL_HIGHS,
                            price_level=round(avg_level, 4),
                            candle_indices=[i, j],
                            tolerance_pct=self.tolerance_pct
                        )
                    )

        # Detect Equal Lows
        for i in range(n - 1):
            for j in range(i + 1, min(i + 10, n)):
                l1, l2 = candles[i].low, candles[j].low
                diff = abs(l1 - l2) / ((l1 + l2) / 2.0)
                if diff <= self.tolerance_pct:
                    avg_level = (l1 + l2) / 2.0
                    pools.append(
                        LiquidityPool(
                            pool_type=LiquidityType.EQUAL_LOWS,
                            price_level=round(avg_level, 4),
                            candle_indices=[i, j],
                            tolerance_pct=self.tolerance_pct
                        )
                    )

        return pools

    def detect_sweeps(self, candles: List[Candle], key_level: float, is_high_level: bool) -> List[LiquiditySweepEvent]:
        """
        بررسی اینکه آیا کندل‌ها سطح مشخصی را جارو (Sweep) کرده و کلوز به داخل برگشته یا خیر.
        """
        events: List[LiquiditySweepEvent] = []
        for i, c in enumerate(candles):
            if is_high_level:
                # Bearish Sweep: High went above level, but Close remained below level
                if c.high > key_level and c.close < key_level:
                    penetration = round(c.high - key_level, 4)
                    events.append(
                        LiquiditySweepEvent(
                            sweep_type=SweepType.BEARISH_SWEEP,
                            swept_level=key_level,
                            candle_index=i,
                            wick_penetration=penetration
                        )
                    )
            else:
                # Bullish Sweep: Low went below level, but Close remained above level
                if c.low < key_level and c.close > key_level:
                    penetration = round(key_level - c.low, 4)
                    events.append(
                        LiquiditySweepEvent(
                            sweep_type=SweepType.BULLISH_SWEEP,
                            swept_level=key_level,
                            candle_index=i,
                            wick_penetration=penetration
                        )
                    )
        return events
