import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("AtriaTrade.WallexOrderGuard")

class WallexOrderGuard:
    def __init__(self, min_order_value_usdt: float = 5.0, max_spread_pct: float = 0.8):
        self.min_order_value_usdt = min_order_value_usdt
        self.max_spread_pct = max_spread_pct

    def validate_spread(self, best_bid: float, best_ask: float) -> Tuple[bool, str]:
        """Validates if orderbook spread is within safe threshold."""
        if best_bid <= 0 or best_ask <= 0 or best_bid > best_ask:
            return False, "Invalid bid/ask pricing"
        
        mid = (best_bid + best_ask) / 2.0
        spread_pct = ((best_ask - best_bid) / mid) * 100.0
        
        if spread_pct > self.max_spread_pct:
            msg = f"Spread too wide: {spread_pct:.2f}% > {self.max_spread_pct:.2f}%"
            logger.warning(msg)
            return False, msg
            
        return True, "Spread within limits"

    def validate_order_size(self, amount: float, price: float) -> Tuple[bool, str]:
        """Validates order notional value against exchange minimum limits."""
        if amount <= 0 or price <= 0:
            return False, "Invalid amount or price"
            
        notional_value = amount * price
        if notional_value < self.min_order_value_usdt:
            msg = f"Order value {notional_value:.2f} USDT below minimum {self.min_order_value_usdt:.2f} USDT"
            logger.warning(msg)
            return False, msg
            
        return True, "Order size acceptable"

    def is_order_safe(self, amount: float, price: float, best_bid: float, best_ask: float) -> Tuple[bool, str]:
        spread_ok, spread_msg = self.validate_spread(best_bid, best_ask)
        if not spread_ok:
            return False, spread_msg
            
        size_ok, size_msg = self.validate_order_size(amount, price)
        if not size_ok:
            return False, size_msg
            
        return True, "Order verified safe"
