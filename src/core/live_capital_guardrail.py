import logging
from typing import Dict, Any

logger = logging.getLogger("LiveCapitalGuardrail")

class LiveCapitalGuardrail:
    def __init__(
        self,
        max_order_ratio: float = 0.25,
        min_reserve_ratio: float = 0.10,
        min_notional_irt: float = 100000.0
    ):
        self.max_order_ratio = max_order_ratio
        self.min_reserve_ratio = min_reserve_ratio
        self.min_notional_irt = min_notional_irt

    def validate_capital_allocation(
        self,
        total_balance: float,
        available_balance: float,
        order_price: float,
        order_quantity: float
    ) -> Dict[str, Any]:
        """
        Guards live capital against catastrophic over-allocation.
        """
        order_notional = order_price * order_quantity

        # 1. Exchange Minimum Notional Check
        if order_notional < self.min_notional_irt:
            logger.warning(f"Order notional {order_notional} IRT below min {self.min_notional_irt} IRT.")
            return {
                "permitted": False,
                "reason": "BELOW_MIN_NOTIONAL",
                "notional": order_notional
            }

        # 2. Maximum Single Order Exposure Check
        max_order_cap = total_balance * self.max_order_ratio
        if order_notional > max_order_cap:
            logger.warning(f"Order notional {order_notional} exceeds max cap {max_order_cap}.")
            return {
                "permitted": False,
                "reason": "EXCEEDS_MAX_ORDER_CAP",
                "notional": order_notional,
                "cap": max_order_cap
            }

        # 3. Reserve Cash Floor Protection
        min_reserve = total_balance * self.min_reserve_ratio
        remaining_balance = available_balance - order_notional
        if remaining_balance < min_reserve:
            logger.warning(
                f"Remaining balance {remaining_balance} drops below reserve floor {min_reserve}."
            )
            return {
                "permitted": False,
                "reason": "BREACHES_RESERVE_FLOOR",
                "remaining_balance": remaining_balance,
                "required_reserve": min_reserve
            }

        logger.info(f"Capital allocation approved for {order_notional} IRT.")
        return {
            "permitted": True,
            "order_notional": order_notional,
            "remaining_balance": remaining_balance
        }
