"""
FVG Tracker & Efficient Price Path Analyzer (Capability 93)
Tracks 3-candle Fair Value Gaps (Bullish/Bearish), calculates mitigation/fill ratios,
and identifies FVG Inversions (SMC / ICT concepts).
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional


class FVGType(str, Enum):
    BULLISH = "BULLISH"  # BISI: Buy Side Imbalance Sell Side Inefficiency
    BEARISH = "BEARISH"  # SIBI: Sell Side Imbalance Buy Side Inefficiency


class FVGStatus(str, Enum):
    UNTOUCHED = "UNTOUCHED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FULLY_FILLED = "FULLY_FILLED"
    INVERTED = "INVERTED"


@dataclass
class FairValueGap:
    gap_id: str
    gap_type: FVGType
    top_price: float
    bottom_price: float
    candle_index: int
    timestamp: Optional[int]
    status: FVGStatus = FVGStatus.UNTOUCHED
    filled_ratio: float = 0.0
    mitigated_at_index: Optional[int] = None

    @property
    def gap_size(self) -> float:
        return max(0.0, self.top_price - self.bottom_price)

    @property
    def midpoint(self) -> float:
        """Consequent Encroachment (CE) / 50% equilibrium level."""
        return (self.top_price + self.bottom_price) / 2.0


class FVGTrackerEngine:
    """
    Scans candlestick datasets for Fair Value Gaps and monitors their life cycle.
    """

    def __init__(self, min_gap_size_pct: float = 0.001):
        """
        :param min_gap_size_pct: Minimum gap size relative to mid price (e.g. 0.001 = 0.1%)
        """
        self.min_gap_size_pct = min_gap_size_pct
        self.gaps: List[FairValueGap] = []

    def scan_gaps(self, ohlcv: List[Dict[str, Any]]) -> List[FairValueGap]:
        """
        Scans OHLCV list for 3-candle FVG patterns.
        ohlcv candles require: 'high', 'low', 'close', 'open' (and optional 'timestamp')
        """
        if not ohlcv or len(ohlcv) < 3:
            return []

        self.gaps.clear()

        for i in range(2, len(ohlcv)):
            c1 = ohlcv[i - 2]
            c2 = ohlcv[i - 1]
            c3 = ohlcv[i]

            high_1 = float(c1["high"])
            low_1 = float(c1["low"])

            high_3 = float(c3["high"])
            low_3 = float(c3["low"])

            # 1. Bullish FVG: Low of candle 3 is above High of candle 1
            if low_3 > high_1:
                bottom = high_1
                top = low_3
                mid = (top + bottom) / 2.0
                if mid > 0 and ((top - bottom) / mid) >= self.min_gap_size_pct:
                    gap = FairValueGap(
                        gap_id=f"fvg_bull_{i-1}",
                        gap_type=FVGType.BULLISH,
                        top_price=top,
                        bottom_price=bottom,
                        candle_index=i - 1,
                        timestamp=c2.get("timestamp"),
                    )
                    self.gaps.append(gap)

            # 2. Bearish FVG: High of candle 3 is below Low of candle 1
            elif high_3 < low_1:
                bottom = high_3
                top = low_1
                mid = (top + bottom) / 2.0
                if mid > 0 and ((top - bottom) / mid) >= self.min_gap_size_pct:
                    gap = FairValueGap(
                        gap_id=f"fvg_bear_{i-1}",
                        gap_type=FVGType.BEARISH,
                        top_price=top,
                        bottom_price=bottom,
                        candle_index=i - 1,
                        timestamp=c2.get("timestamp"),
                    )
                    self.gaps.append(gap)

        return self.gaps

    def update_mitigation(self, future_ohlcv: List[Dict[str, Any]]) -> None:
        """
        Updates the fill ratio and status of tracked gaps against subsequent candles.
        """
        if not self.gaps or not future_ohlcv:
            return

        for gap in self.gaps:
            if gap.status == FVGStatus.FULLY_FILLED or gap.status == FVGStatus.INVERTED:
                continue

            for idx, candle in enumerate(future_ohlcv):
                c_idx = candle.get("index", idx)
                if c_idx <= gap.candle_index:
                    continue

                c_high = float(candle["high"])
                c_low = float(candle["low"])
                c_close = float(candle["close"])
                gap_size = gap.gap_size
                if gap_size == 0:
                    continue

                if gap.gap_type == FVGType.BULLISH:
                    # Bullish gap is filled downward (price dips into the gap from above)
                    if c_low < gap.top_price:
                        penetration = gap.top_price - max(c_low, gap.bottom_price)
                        ratio = min(1.0, penetration / gap_size)
                        gap.filled_ratio = max(gap.filled_ratio, ratio)

                        if c_low <= gap.bottom_price:
                            gap.status = FVGStatus.FULLY_FILLED
                            gap.mitigated_at_index = c_idx
                            if c_close < gap.bottom_price:
                                gap.status = FVGStatus.INVERTED
                        else:
                            gap.status = FVGStatus.PARTIALLY_FILLED

                elif gap.gap_type == FVGType.BEARISH:
                    # Bearish gap is filled upward (price rallies into the gap from below)
                    if c_high > gap.bottom_price:
                        penetration = min(c_high, gap.top_price) - gap.bottom_price
                        ratio = min(1.0, penetration / gap_size)
                        gap.filled_ratio = max(gap.filled_ratio, ratio)

                        if c_high >= gap.top_price:
                            gap.status = FVGStatus.FULLY_FILLED
                            gap.mitigated_at_index = c_idx
                            if c_close > gap.top_price:
                                gap.status = FVGStatus.INVERTED
                        else:
                            gap.status = FVGStatus.PARTIALLY_FILLED

    def get_active_gaps(self, unmitigated_only: bool = True) -> List[FairValueGap]:
        """Returns currently active gaps based on mitigation state."""
        if not unmitigated_only:
            return self.gaps

        return [g for g in self.gaps if g.status in (FVGStatus.UNTOUCHED, FVGStatus.PARTIALLY_FILLED)]
