"""
SMC Liquidity Sweep & Stop Hunt Detector (Capability 86)
Identifies false breakouts, liquidity grabs, and stop hunts at key support/resistance levels.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class SweepEvent:
    detected: bool
    sweep_type: Optional[str] = None  # "BULLISH_SWEEP" (hunt lows) or "BEARISH_SWEEP" (hunt highs)
    swept_level: float = 0.0
    wick_ratio: float = 0.0
    entry_price: float = 0.0
    suggested_stop_loss: float = 0.0
    reason: str = ""

class LiquiditySweepDetector:
    def __init__(self, min_wick_ratio: float = 0.3, min_sweep_pct: float = 0.0005):
        """
        :param min_wick_ratio: Minimum rejection wick ratio compared to total candle range.
        :param min_sweep_pct: Minimum penetration beyond the level to count as a sweep.
        """
        self.min_wick_ratio = float(min_wick_ratio)
        self.min_sweep_pct = float(min_sweep_pct)

    def detect_sweep(
        self,
        candle: Dict[str, float],
        key_high: Optional[float] = None,
        key_low: Optional[float] = None
    ) -> SweepEvent:
        """
        Evaluates a single candle against key price levels for liquidity sweeps.
        Candle dict expects: {'open': float, 'high': float, 'low': float, 'close': float}
        """
        o = float(candle.get("open", 0.0))
        h = float(candle.get("high", 0.0))
        l = float(candle.get("low", 0.0))
        c = float(candle.get("close", 0.0))
        
        candle_range = h - l
        if candle_range <= 0:
            return SweepEvent(detected=False, reason="Invalid or zero candle range")

        # 1. Check Bearish Sweep (Hunt above key_high)
        if key_high is not None and key_high > 0:
            if h > key_high and c < key_high:
                penetration = (h - key_high) / key_high
                upper_wick = h - max(o, c)
                wick_ratio = upper_wick / candle_range
                
                if penetration >= self.min_sweep_pct and wick_ratio >= self.min_wick_ratio:
                    return SweepEvent(
                        detected=True,
                        sweep_type="BEARISH_SWEEP",
                        swept_level=key_high,
                        wick_ratio=round(wick_ratio, 4),
                        entry_price=c,
                        suggested_stop_loss=h,
                        reason=f"Bearish liquidity sweep above {key_high} with {wick_ratio:.1%} upper wick"
                    )

        # 2. Check Bullish Sweep (Hunt below key_low)
        if key_low is not None and key_low > 0:
            if l < key_low and c > key_low:
                penetration = (key_low - l) / key_low
                lower_wick = min(o, c) - l
                wick_ratio = lower_wick / candle_range
                
                if penetration >= self.min_sweep_pct and wick_ratio >= self.min_wick_ratio:
                    return SweepEvent(
                        detected=True,
                        sweep_type="BULLISH_SWEEP",
                        swept_level=key_low,
                        wick_ratio=round(wick_ratio, 4),
                        entry_price=c,
                        suggested_stop_loss=l,
                        reason=f"Bullish liquidity sweep below {key_low} with {wick_ratio:.1%} lower wick"
                    )

        return SweepEvent(detected=False, reason="No liquidity sweep detected")
