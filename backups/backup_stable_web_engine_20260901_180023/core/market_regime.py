"""Market Regime Filter module for AtriaTrade (Pure Python).

Detects market condition: BULL_TREND, BEAR_TREND, RANGING, HIGH_VOLATILITY.
Adjusts or suppresses trade signals accordingly.
"""

from typing import List, Dict, Any


class MarketRegime:
    BULL_TREND = "BULL_TREND"
    BEAR_TREND = "BEAR_TREND"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    UNKNOWN = "UNKNOWN"


class MarketRegimeFilter:
    def __init__(
        self,
        fast_window: int = 10,
        slow_window: int = 30,
        volatility_threshold_pct: float = 0.04,  # بیش از ۴٪ نوسان میانگین کندل = High Volatility
        trend_threshold_pct: float = 0.015       # اختلاف بیش از ۱.۵٪ بین سریع و کند = Trend
    ):
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.volatility_threshold_pct = float(volatility_threshold_pct)
        self.trend_threshold_pct = float(trend_threshold_pct)

    def _calculate_sma(self, values: List[float], window: int) -> float:
        if len(values) < window or window <= 0:
            return 0.0
        return sum(values[-window:]) / window

    def _calculate_average_true_range_pct(self, candles: List[Dict[str, Any]], window: int) -> float:
        """Calculates normalized average candle range (High - Low) / Close."""
        if len(candles) < window:
            return 0.0
        recent = candles[-window:]
        ranges = []
        for c in recent:
            high = float(c.get("high", c.get("close", 0)))
            low = float(c.get("low", c.get("close", 0)))
            close = float(c.get("close", 1.0))
            if close > 0:
                ranges.append((high - low) / close)
        return sum(ranges) / len(ranges) if ranges else 0.0

    def detect_regime(self, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detects the current market regime based on candle history."""
        if not candles or len(candles) < self.slow_window:
            return {
                "regime": MarketRegime.UNKNOWN,
                "reason": f"Insufficient candles (need at least {self.slow_window})",
                "volatility_pct": 0.0,
                "trend_strength_pct": 0.0
            }

        closes = [float(c["close"]) for c in candles]
        fast_sma = self._calculate_sma(closes, self.fast_window)
        slow_sma = self._calculate_sma(closes, self.slow_window)
        current_close = closes[-1]

        volatility_pct = self._calculate_average_true_range_pct(candles, self.fast_window)
        trend_diff_pct = (fast_sma - slow_sma) / slow_sma if slow_sma > 0 else 0.0

        # ۱. بررسی نوسان شدید (High Volatility)
        if volatility_pct >= self.volatility_threshold_pct:
            return {
                "regime": MarketRegime.HIGH_VOLATILITY,
                "volatility_pct": round(volatility_pct, 4),
                "trend_strength_pct": round(trend_diff_pct, 4),
                "fast_sma": round(fast_sma, 4),
                "slow_sma": round(slow_sma, 4)
            }

        # ۲. روند صعودی
        if trend_diff_pct >= self.trend_threshold_pct and current_close >= fast_sma:
            return {
                "regime": MarketRegime.BULL_TREND,
                "volatility_pct": round(volatility_pct, 4),
                "trend_strength_pct": round(trend_diff_pct, 4),
                "fast_sma": round(fast_sma, 4),
                "slow_sma": round(slow_sma, 4)
            }

        # ۳. روند نزولی
        if trend_diff_pct <= -self.trend_threshold_pct and current_close <= fast_sma:
            return {
                "regime": MarketRegime.BEAR_TREND,
                "volatility_pct": round(volatility_pct, 4),
                "trend_strength_pct": round(trend_diff_pct, 4),
                "fast_sma": round(fast_sma, 4),
                "slow_sma": round(slow_sma, 4)
            }

        # ۴. بازار رِنج / خنثی
        return {
            "regime": MarketRegime.RANGING,
            "volatility_pct": round(volatility_pct, 4),
            "trend_strength_pct": round(trend_diff_pct, 4),
            "fast_sma": round(fast_sma, 4),
            "slow_sma": round(slow_sma, 4)
        }

    def should_allow_signal(self, regime: str, signal_side: str) -> bool:
        """Determines if a BUY/SELL signal is permitted under the current regime."""
        side = signal_side.upper()
        if regime == MarketRegime.HIGH_VOLATILITY:
            # در نوسان بسیار بالا ورودهای جدید مسدود می‌شوند
            return False
        if regime == MarketRegime.BULL_TREND and side == "BUY":
            return True
        if regime == MarketRegime.BEAR_TREND and side == "SELL":
            return True
        if regime == MarketRegime.RANGING:
            # در بازار رنج هر دو جهت با احتیاط مجاز است
            return True
        return False
