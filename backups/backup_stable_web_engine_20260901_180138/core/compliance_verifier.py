import math
from typing import Dict, Any, Tuple, Optional


class ComplianceVerifier:
    """
    Pre-Trade Compliance & Sanity Verifier.
    Performs absolute sanity checks before any order is submitted to execution layers.
    """
    def __init__(
        self,
        min_notional: float = 5.0,
        max_notional: float = 100000.0,
        max_price_deviation_pct: float = 0.10  # 10% max deviation from current market price
    ):
        self.min_notional = min_notional
        self.max_notional = max_notional
        self.max_price_deviation_pct = max_price_deviation_pct

    def verify_order(
        self,
        order: Dict[str, Any],
        current_market_price: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates an order against pre-trade compliance and sanity limits.
        """
        price = float(order.get("price", 0.0))
        amount = float(order.get("amount", 0.0))
        order_type = order.get("type", "LIMIT").upper()

        if amount <= 0:
            return False, "Order amount must be strictly positive."

        # For market orders, evaluate with current market price
        eval_price = price if order_type == "LIMIT" and price > 0 else current_market_price
        if eval_price <= 0:
            return False, "Invalid evaluation price."

        notional_value = amount * eval_price

        # Min notional check
        if notional_value < self.min_notional:
            return False, f"Order notional ({notional_value:.2f}) is below minimum allowed ({self.min_notional})."

        # Max notional check
        if notional_value > self.max_notional:
            return False, f"Order notional ({notional_value:.2f}) exceeds maximum allowed ({self.max_notional})."

        # Fat-finger price deviation check for Limit orders
        if order_type == "LIMIT" and current_market_price > 0:
            deviation = abs(price - current_market_price) / current_market_price
            if deviation > self.max_price_deviation_pct:
                return False, f"Order price ({price}) deviates {deviation*100:.1f}% from market price ({current_market_price}), exceeding allowed limit of {self.max_price_deviation_pct*100:.1f}%."

        return True, None
