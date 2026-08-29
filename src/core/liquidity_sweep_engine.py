"""Liquidity Sweeps and Stop Hunt Detection Engine for AtriaTrade.

Identifies liquidity grabs, false breakouts, and institutional stop hunts
around key swing highs and swing lows.
"""

from typing import Any, Dict, List, Optional


class LiquiditySweepEngine:
    """Detects liquidity sweeps and stop hunt wick-reversals."""

    def __init__(self, swing_lookback: int = 5, sweep_tolerance_pct: float = 0.002):
        """
        Initialize LiquiditySweepEngine.

        :param swing_lookback: Number of candles required on each side to define a swing point.
        :param sweep_tolerance_pct: Min price excursion beyond swing to count as a sweep.
        """
        self.swing_lookback = max(2, int(swing_lookback))
        self.sweep_tolerance_pct = float(sweep_tolerance_pct)

    def find_swing_points(self, candles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Find prominent swing highs and swing lows in historical candles."""
        swing_highs = []
        swing_lows = []
        n = len(candles)
        k = self.swing_lookback

        if n < 2 * k + 1:
            return {"highs": swing_highs, "lows": swing_lows}

        for i in range(k, n - k):
            current_high = float(candles[i]["high"])
            current_low = float(candles[i]["low"])

            # Check swing high
            is_high = True
            for j in range(i - k, i + k + 1):
                if j != i and float(candles[j]["high"]) >= current_high:
                    is_high = False
                    break
            if is_high:
                swing_highs.append({"index": i, "price": current_high})

            # Check swing low
            is_low = True
            for j in range(i - k, i + k + 1):
                if j != i and float(candles[j]["low"]) <= current_low:
                    is_low = False
                    break
            if is_low:
                swing_lows.append({"index": i, "price": current_low})

        return {"highs": swing_highs, "lows": swing_lows}

    def analyze_latest_sweep(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the latest candle for potential liquidity sweep / stop hunt.

        :param candles: List of OHLCV candles.
        :return: Dict containing sweep detection results.
        """
        if not candles or len(candles) < (2 * self.swing_lookback + 2):
            return {
                "status": "INSUFFICIENT_DATA",
                "sweep_type": "NONE",
                "swept_level": 0.0,
                "confidence": 0.0,
            }

        # Analyze historical swings excluding current candle
        swings = self.find_swing_points(candles[:-1])
        latest = candles[-1]
        l_open = float(latest["open"])
        l_high = float(latest["high"])
        l_low = float(latest["low"])
        l_close = float(latest["close"])

        # Check Bearish Sweep (Price swept Swing High, but closed back below it)
        for sh in reversed(swings["highs"]):
            level = sh["price"]
            if l_high > level and l_close < level:
                penetration = (l_high - level) / level
                if penetration >= self.sweep_tolerance_pct:
                    return {
                        "status": "SWEEP_DETECTED",
                        "sweep_type": "BEARISH_SWEEP",
                        "swept_level": round(level, 4),
                        "wick_excursion": round(l_high, 4),
                        "confidence": 0.85,
                    }

        # Check Bullish Sweep (Price swept Swing Low, but closed back above it)
        for sl in reversed(swings["lows"]):
            level = sl["price"]
            if l_low < level and l_close > level:
                penetration = (level - l_low) / level
                if penetration >= self.sweep_tolerance_pct:
                    return {
                        "status": "SWEEP_DETECTED",
                        "sweep_type": "BULLISH_SWEEP",
                        "swept_level": round(level, 4),
                        "wick_excursion": round(l_low, 4),
                        "confidence": 0.85,
                    }

        return {
            "status": "NO_SWEEP",
            "sweep_type": "NONE",
            "swept_level": 0.0,
            "confidence": 0.0,
        }
