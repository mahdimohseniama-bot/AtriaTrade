"""
Multi-Factor Strategy Aggregator for AtriaTrade.
Combines Order Flow, Liquidity Sweeps, and Trend Signals to make high-conviction decisions.
"""
from typing import Dict, Any, List

class StrategyAggregator:
    def __init__(self, min_confidence_score: float = 0.70):
        self.min_confidence_score = min_confidence_score

    def aggregate_signals(self, 
                          trend_signal: str, 
                          order_flow_imbalance: float, 
                          liquidity_sweep: Dict[str, Any],
                          volume_profile_poc: float,
                          current_price: float) -> Dict[str, Any]:
        """
        Aggregates multi-factor market components into a unified signal.
        """
        score = 0.0
        factors = []
        action = "HOLD"

        # 1. Trend Factor (Weight: 0.3)
        if trend_signal == "BUY":
            score += 0.3
            factors.append("BULLISH_TREND")
        elif trend_signal == "SELL":
            score -= 0.3
            factors.append("BEARISH_TREND")

        # 2. Order Flow Imbalance Factor (Weight: 0.35)
        # Imbalance > 0 -> Buy pressure, < 0 -> Sell pressure
        if order_flow_imbalance >= 0.2:
            score += 0.35
            factors.append("BUY_ORDER_FLOW_IMBALANCE")
        elif order_flow_imbalance <= -0.2:
            score -= 0.35
            factors.append("SELL_ORDER_FLOW_IMBALANCE")

        # 3. Liquidity Sweep Factor (Weight: 0.35)
        sweep_type = liquidity_sweep.get("sweep_type")
        if sweep_type == "BULLISH_SWEEP":
            score += 0.35
            factors.append("BULLISH_LIQUIDITY_SWEEP")
        elif sweep_type == "BEARISH_SWEEP":
            score -= 0.35
            factors.append("BEARISH_LIQUIDITY_SWEEP")

        # Decision Threshold
        abs_score = round(abs(score), 2)
        if score >= self.min_confidence_score:
            action = "BUY"
        elif score <= -self.min_confidence_score:
            action = "SELL"
        else:
            action = "HOLD"

        return {
            "status": "AGGREGATED",
            "action": action,
            "confidence_score": abs_score,
            "is_actionable": action != "HOLD",
            "factors": factors,
            "current_price": current_price,
            "volume_profile_poc": volume_profile_poc
        }
