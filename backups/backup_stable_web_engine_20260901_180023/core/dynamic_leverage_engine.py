"""
Dynamic Leverage & Position Sizing Engine for AtriaTrade.
Calculates risk-adjusted position size and safe leverage based on account equity,
stop-loss distance, and volatility constraints.
"""
from typing import Dict, Any

class DynamicLeverageEngine:
    def __init__(self, max_risk_per_trade_pct: float = 0.02, max_leverage: float = 10.0):
        """
        :param max_risk_per_trade_pct: Maximum fraction of equity to risk per trade (e.g. 0.02 = 2%)
        :param max_leverage: Absolute maximum leverage permitted by risk policy
        """
        self.max_risk_pct = max_risk_per_trade_pct
        self.max_leverage = max_leverage

    def calculate_sizing(self, 
                         account_equity: float, 
                         entry_price: float, 
                         stop_loss_price: float, 
                         allocated_margin: float) -> Dict[str, Any]:
        """
        Calculates position size and recommended leverage based on stop-loss distance.
        """
        if account_equity <= 0 or entry_price <= 0 or stop_loss_price <= 0 or allocated_margin <= 0:
            return {"status": "INVALID_INPUT", "position_size": 0.0, "leverage": 1.0}

        sl_distance = abs(entry_price - stop_loss_price)
        if sl_distance == 0:
            return {"status": "ZERO_SL_DISTANCE", "position_size": 0.0, "leverage": 1.0}

        sl_distance_pct = sl_distance / entry_price
        max_allowed_loss = account_equity * self.max_risk_pct

        # Required nominal position value so that loss at SL equals max_allowed_loss
        nominal_position_size = max_allowed_loss / sl_distance_pct

        # Recommended leverage = nominal position size / allocated margin
        recommended_leverage = nominal_position_size / allocated_margin

        # Clamp leverage to max policy
        effective_leverage = min(recommended_leverage, self.max_leverage)
        effective_leverage = max(1.0, round(effective_leverage, 2))

        # Recalculate final nominal position size
        final_nominal_size = allocated_margin * effective_leverage
        quantity = final_nominal_size / entry_price
        potential_loss = final_nominal_size * sl_distance_pct

        return {
            "status": "CALCULATED",
            "account_equity": account_equity,
            "allocated_margin": allocated_margin,
            "effective_leverage": effective_leverage,
            "nominal_position_value": round(final_nominal_size, 2),
            "quantity": round(quantity, 6),
            "potential_loss": round(potential_loss, 2),
            "risk_pct_of_equity": round((potential_loss / account_equity) * 100, 2)
        }
