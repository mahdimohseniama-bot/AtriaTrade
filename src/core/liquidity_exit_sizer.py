"""
Smart Liquidity-Aware Exit Sizer for AtriaTrade (Capability 80).
Optimizes large position exits to prevent market impact and slippage.
"""

from typing import List, Dict, Any, Optional
import math


class LiquidityExitSizer:
    def __init__(self, max_depth_impact_ratio: float = 0.05, min_slice_size: float = 0.001):
        """
        :param max_depth_impact_ratio: Max portion of available top-book liquidity to take in one slice.
        :param min_slice_size: Minimum viable order slice size.
        """
        self.max_depth_impact_ratio = max_depth_impact_ratio
        self.min_slice_size = min_slice_size

    def calculate_exit_slices(
        self,
        total_quantity: float,
        orderbook_depth_qty: float,
        is_emergency: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates optimal exit chunking based on available market depth.
        """
        if total_quantity <= 0:
            return {
                "num_slices": 0,
                "slice_sizes": [],
                "execution_mode": "NOOP",
                "reason": "ZERO_OR_NEGATIVE_QUANTITY"
            }

        # Emergency override: sweep immediately
        if is_emergency:
            return {
                "num_slices": 1,
                "slice_sizes": [round(total_quantity, 6)],
                "execution_mode": "EMERGENCY_SWEEP",
                "reason": "HARD_STOP_ACTIVE"
            }

        if orderbook_depth_qty <= 0:
            # Fallback if depth is unknown
            return {
                "num_slices": 1,
                "slice_sizes": [round(total_quantity, 6)],
                "execution_mode": "DIRECT_MARKET",
                "reason": "NO_DEPTH_INFO"
            }

        max_allowed_slice = max(self.min_slice_size, orderbook_depth_qty * self.max_depth_impact_ratio)

        if total_quantity <= max_allowed_slice:
            return {
                "num_slices": 1,
                "slice_sizes": [round(total_quantity, 6)],
                "execution_mode": "DIRECT_MARKET",
                "reason": "WITHIN_LIQUIDITY_TOLERANCE"
            }

        # Slice into chunks
        num_slices = math.ceil(total_quantity / max_allowed_slice)
        slice_sizes = []
        remaining = total_quantity

        for i in range(num_slices):
            chunk = min(remaining, max_allowed_slice)
            if chunk >= self.min_slice_size:
                slice_sizes.append(round(chunk, 6))
                remaining -= chunk

        if remaining > 1e-6:
            if slice_sizes:
                slice_sizes[-1] = round(slice_sizes[-1] + remaining, 6)
            else:
                slice_sizes.append(round(remaining, 6))

        return {
            "num_slices": len(slice_sizes),
            "slice_sizes": slice_sizes,
            "execution_mode": "SLICED_TWAP",
            "reason": f"LIQUIDITY_CONSTRAINED_{len(slice_sizes)}_SLICES"
        }
