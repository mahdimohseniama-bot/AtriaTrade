"""
Dynamic Slippage and Latency Simulator for AtriaTrade.
Calculates dynamic execution prices based on order volume, market depth, and volatility.
"""
from typing import Dict, Any, Optional
import math


class MarketDepthSlippageSimulator:
    """
    Simulates dynamic market impact slippage and latency on paper execution.
    """

    def __init__(
        self,
        base_slippage_pct: float = 0.0005,  # 0.05% base spread
        depth_impact_factor: float = 0.05,   # Impact multiplier per unit of depth ratio
        max_slippage_pct: float = 0.03,      # Max slippage cap at 3%
        base_latency_ms: float = 50.0        # 50ms default baseline latency
    ):
        self.base_slippage_pct = max(0.0, float(base_slippage_pct))
        self.depth_impact_factor = max(0.0, float(depth_impact_factor))
        self.max_slippage_pct = max(0.0, float(max_slippage_pct))
        self.base_latency_ms = max(0.0, float(base_latency_ms))

    def calculate_effective_slippage(
        self,
        order_volume: float,
        available_depth_volume: float,
        volatility_factor: float = 1.0
    ) -> float:
        """
        Calculate the percentage slippage based on volume ratio and volatility.
        """
        if order_volume <= 0:
            return self.base_slippage_pct

        safe_depth = max(available_depth_volume, order_volume * 0.1, 1e-6)
        volume_ratio = order_volume / safe_depth
        
        # Non-linear quadratic impact for large volume orders
        depth_impact = (volume_ratio ** 1.5) * self.depth_impact_factor
        vol_adj = max(0.1, float(volatility_factor))
        
        total_slippage = (self.base_slippage_pct + depth_impact) * vol_adj
        return min(self.max_slippage_pct, total_slippage)

    def calculate_executed_price(
        self,
        side: str,
        target_price: float,
        order_volume: float,
        available_depth_volume: float,
        volatility_factor: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculates final executed price including direction-aware slippage.
        """
        side_norm = side.strip().upper()
        if side_norm not in ["BUY", "SELL"]:
            raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'.")

        if target_price <= 0:
            raise ValueError("Target price must be strictly positive.")

        slippage_pct = self.calculate_effective_slippage(
            order_volume=order_volume,
            available_depth_volume=available_depth_volume,
            volatility_factor=volatility_factor
        )

        if side_norm == "BUY":
            # Buyers get slipped upwards (worse fill)
            executed_price = target_price * (1.0 + slippage_pct)
        else:
            # Sellers get slipped downwards (worse fill)
            executed_price = target_price * (1.0 - slippage_pct)

        return {
            "side": side_norm,
            "target_price": round(target_price, 8),
            "executed_price": round(executed_price, 8),
            "slippage_pct": round(slippage_pct, 6),
            "slippage_amount": round(abs(executed_price - target_price), 8),
            "estimated_latency_ms": self.base_latency_ms
        }
