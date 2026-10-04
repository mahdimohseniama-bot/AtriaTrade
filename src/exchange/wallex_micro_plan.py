from dataclasses import dataclass
from typing import Optional

@dataclass
class MicroOrderPlan:
    symbol: str
    side: str
    target_price: float
    quantity: float
    total_value: float
    stop_loss: float
    take_profit: float
    is_valid: bool = True
    rejection_reason: Optional[str] = None

class WallexMicroPlanEngine:
    def __init__(self, min_notional_tmn: float = 100_000.0, max_capital_pct: float = 0.05):
        self.min_notional_tmn = float(min_notional_tmn)
        self.max_capital_pct = float(max_capital_pct)

    def generate_plan(
        self,
        symbol: str,
        side: str,
        best_price: float,
        available_balance: float,
        risk_rr_ratio: float = 2.0,
        sl_pct: float = 0.02
    ) -> MicroOrderPlan:
        side_upper = side.upper()
        best_price = float(best_price)
        available_balance = float(available_balance)
        risk_rr_ratio = float(risk_rr_ratio)
        sl_pct = float(sl_pct)

        if available_balance < self.min_notional_tmn:
            return MicroOrderPlan(
                symbol=symbol,
                side=side_upper,
                target_price=best_price,
                quantity=0.0,
                total_value=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                is_valid=False,
                rejection_reason="INSUFFICIENT_BALANCE_FOR_MIN_NOTIONAL"
            )

        allocated_capital = available_balance * self.max_capital_pct
        if allocated_capital < self.min_notional_tmn:
            allocated_capital = self.min_notional_tmn

        if allocated_capital > available_balance:
            allocated_capital = available_balance

        quantity = allocated_capital / best_price if best_price > 0 else 0.0
        total_value = best_price * quantity

        if side_upper == "BUY":
            sl_price = round(best_price * (1.0 - sl_pct), 2)
            tp_price = round(best_price * (1.0 + (sl_pct * risk_rr_ratio)), 2)
        else:
            sl_price = round(best_price * (1.0 + sl_pct), 2)
            tp_price = round(best_price * (1.0 - (sl_pct * risk_rr_ratio)), 2)

        return MicroOrderPlan(
            symbol=symbol,
            side=side_upper,
            target_price=best_price,
            quantity=quantity,
            total_value=total_value,
            stop_loss=sl_price,
            take_profit=tp_price,
            is_valid=True,
            rejection_reason=None
        )
