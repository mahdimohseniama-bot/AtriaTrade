"""
SMC Breaker Block & Mitigation Engine (Capability 87)
Identifies failed/violated Order Blocks that flip polarity (Breaker Blocks)
and tests for retest/mitigation signals.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class BreakerSignal:
    detected: bool
    block_type: str  # "BULLISH_BREAKER", "BEARISH_BREAKER", "MITIGATION"
    zone_high: float
    zone_low: float
    entry_price: float
    suggested_stop_loss: float
    reason: str

class BreakerBlockEngine:
    def __init__(self, tolerance_pct: float = 0.0015):
        """
        :param tolerance_pct: Proximity buffer to consider price inside the breaker zone
        """
        self.tolerance_pct = tolerance_pct

    def detect_breaker(
        self,
        current_candle: Dict[str, float],
        broken_order_block: Dict[str, Any],
        market_structure: str = "BULLISH"
    ) -> BreakerSignal:
        """
        Detects if current price action mitigates or reacts to a broken Order Block (Breaker).
        broken_order_block format:
        {
            "original_type": "BEARISH_OB" or "BULLISH_OB",
            "high": float,
            "low": float
        }
        """
        high = current_candle.get("high", 0.0)
        low = current_candle.get("low", 0.0)
        close = current_candle.get("close", 0.0)

        if high <= low or not broken_order_block:
            return BreakerSignal(
                detected=False,
                block_type="NONE",
                zone_high=0.0,
                zone_low=0.0,
                entry_price=0.0,
                suggested_stop_loss=0.0,
                reason="Invalid candle or empty order block"
            )

        ob_high = float(broken_order_block.get("high", 0.0))
        ob_low = float(broken_order_block.get("low", 0.0))
        orig_type = broken_order_block.get("original_type", "")

        if ob_high <= ob_low:
            return BreakerSignal(
                detected=False,
                block_type="NONE",
                zone_high=0.0,
                zone_low=0.0,
                entry_price=0.0,
                suggested_stop_loss=0.0,
                reason="Invalid block bounds"
            )

        # Bullish Breaker: An old Bearish OB was broken upwards, now acts as Support
        if orig_type == "BEARISH_OB" and market_structure.upper() == "BULLISH":
            # Price retraces down into old OB zone [ob_low * (1-tol), ob_high * (1+tol)]
            if low <= ob_high * (1 + self.tolerance_pct) and close >= ob_low * (1 - self.tolerance_pct):
                return BreakerSignal(
                    detected=True,
                    block_type="BULLISH_BREAKER",
                    zone_high=ob_high,
                    zone_low=ob_low,
                    entry_price=close,
                    suggested_stop_loss=ob_low * (1 - self.tolerance_pct),
                    reason="Retest of violated bearish OB as bullish breaker support"
                )

        # Bearish Breaker: An old Bullish OB was broken downwards, now acts as Resistance
        elif orig_type == "BULLISH_OB" and market_structure.upper() == "BEARISH":
            # Price retraces up into old OB zone
            if high >= ob_low * (1 - self.tolerance_pct) and close <= ob_high * (1 + self.tolerance_pct):
                return BreakerSignal(
                    detected=True,
                    block_type="BEARISH_BREAKER",
                    zone_high=ob_high,
                    zone_low=ob_low,
                    entry_price=close,
                    suggested_stop_loss=ob_high * (1 + self.tolerance_pct),
                    reason="Retest of violated bullish OB as bearish breaker resistance"
                )

        return BreakerSignal(
            detected=False,
            block_type="NONE",
            zone_high=ob_high,
            zone_low=ob_low,
            entry_price=0.0,
            suggested_stop_loss=0.0,
            reason="Price not mitigating breaker block zone"
        )
