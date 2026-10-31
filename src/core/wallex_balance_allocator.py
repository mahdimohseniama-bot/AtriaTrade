import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("AtriaTrade.WallexBalanceAllocator")

@dataclass
class AllocationResult:
    is_allowed: bool
    allocated_amount: float
    remaining_free: float = 0.0
    capped_by_risk: bool = False
    rejection_reason: Optional[str] = None

class WallexBalanceAllocator:
    """
    Capital Allocation & Free Balance Guard for Wallex Live Engine.
    Prevents negative-balance lockouts and strictly enforces position sizing caps.
    """
    def __init__(
        self,
        balance_provider: Any,
        max_allocation_pct: float = 0.25,
        min_order_quote: float = 5.0
    ):
        self.provider = balance_provider
        self.max_allocation_pct = max_allocation_pct
        self.min_order_quote = min_order_quote

    def get_free_balance(self, currency: str = "USDT") -> float:
        try:
            balances = self.provider.get_balances()
        except Exception as exc:
            logger.error(f"Failed to query balances from provider: {exc}")
            return 0.0

        curr_data = balances.get(currency, 0.0)
        if isinstance(curr_data, dict):
            return float(curr_data.get("free", 0.0))
        elif isinstance(curr_data, (int, float)):
            return float(curr_data)
        return 0.0

    def allocate(
        self,
        symbol: str,
        quote_currency: str = "USDT",
        requested_amount_quote: float = 0.0
    ) -> AllocationResult:
        free_bal = self.get_free_balance(quote_currency)
        logger.info(f"Balance check: {quote_currency} free={free_bal:.2f} | Requested={requested_amount_quote:.2f}")

        if free_bal < self.min_order_quote:
            logger.warning(f"Free balance {free_bal:.2f} below min order requirement {self.min_order_quote:.2f}")
            return AllocationResult(
                is_allowed=False,
                allocated_amount=0.0,
                remaining_free=free_bal,
                rejection_reason="INSUFFICIENT_FREE_BALANCE"
            )

        # Calculate max allowable by portfolio risk ceiling
        max_allowed_by_risk = free_bal * self.max_allocation_pct
        capped = False
        target_amount = requested_amount_quote

        if target_amount > max_allowed_by_risk:
            target_amount = max_allowed_by_risk
            capped = True

        if target_amount < self.min_order_quote:
            logger.warning(f"Risk-capped allocation {target_amount:.2f} below min order {self.min_order_quote:.2f}")
            return AllocationResult(
                is_allowed=False,
                allocated_amount=0.0,
                remaining_free=free_bal,
                rejection_reason="INSUFFICIENT_FREE_BALANCE"
            )

        remaining = free_bal - target_amount
        return AllocationResult(
            is_allowed=True,
            allocated_amount=round(target_amount, 4),
            remaining_free=round(remaining, 4),
            capped_by_risk=capped,
            rejection_reason=None
        )
