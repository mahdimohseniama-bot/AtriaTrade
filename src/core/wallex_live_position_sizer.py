from typing import Dict, Any

class WallexLivePositionSizer:
    """
    Computes strict position size for micro-capital trading (e.g. 10-20 USDT/TM),
    enforcing minimum exchange notional and risk limits per trade.
    """
    def __init__(
        self,
        max_capital_allocation: float = 20.0,
        risk_per_trade_pct: float = 0.02,
        min_order_notional: float = 5.0,
        taker_fee_pct: float = 0.0025
    ):
        self.max_capital_allocation = max_capital_allocation
        self.risk_per_trade_pct = risk_per_trade_pct
        self.min_order_notional = min_order_notional
        self.taker_fee_pct = taker_fee_pct

    def compute_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        side: str = "BUY"
    ) -> Dict[str, Any]:
        if entry_price <= 0 or stop_loss_price <= 0:
            return {"allowed": False, "reason": "INVALID_PRICES", "size": 0.0}

        # Effective trading balance capped by max capital allocation safety guard
        tradable_balance = min(account_balance, self.max_capital_allocation)
        if tradable_balance < self.min_order_notional:
            return {
                "allowed": False,
                "reason": "BALANCE_BELOW_MIN_NOTIONAL",
                "tradable_balance": tradable_balance,
                "min_order_notional": self.min_order_notional,
                "size": 0.0
            }

        risk_budget = tradable_balance * self.risk_per_trade_pct
        price_risk_per_unit = abs(entry_price - stop_loss_price)

        if price_risk_per_unit <= 0:
            return {"allowed": False, "reason": "ZERO_PRICE_RISK", "size": 0.0}

        # Size determined strictly by risk budget
        risk_based_units = risk_budget / price_risk_per_unit

        # Position size capped by available allocated capital
        max_affordable_units = (tradable_balance * (1.0 - self.taker_fee_pct)) / entry_price
        target_units = min(risk_based_units, max_affordable_units)
        order_notional = target_units * entry_price

        if order_notional < self.min_order_notional:
            # Fallback check: if risking minimum notional is safe within capital bounds
            if self.min_order_notional <= tradable_balance:
                target_units = self.min_order_notional / entry_price
                order_notional = self.min_order_notional
            else:
                return {
                    "allowed": False,
                    "reason": "ORDER_NOTIONAL_TOO_LOW",
                    "order_notional": order_notional,
                    "min_required": self.min_order_notional,
                    "size": 0.0
                }

        fee_estimate = order_notional * self.taker_fee_pct

        return {
            "allowed": True,
            "reason": "SIZE_CALCULATED_SUCCESSFULLY",
            "size": round(target_units, 6),
            "notional": round(order_notional, 4),
            "estimated_fee": round(fee_estimate, 4),
            "risk_amount": round(risk_budget, 4)
        }
