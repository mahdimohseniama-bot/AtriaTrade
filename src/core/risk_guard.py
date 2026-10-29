import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("RiskGuard")

class WallexRiskGuard:
    """
    Pre-trade Risk Guard enforcing strict risk limits for Wallex trading pipeline:
    - Max risk per trade (% of total capital)
    - Mandatory stop-loss validation
    - Daily drawdown circuit breaking
    - Minimum / Maximum position sizing bounds
    """

    def __init__(self, max_risk_pct_per_trade: float = 0.02,
                 max_daily_drawdown_pct: float = 0.05,
                 min_notional_tmn: float = 100000.0,
                 max_notional_tmn: float = 50000000.0):
        self.max_risk_pct_per_trade = max_risk_pct_per_trade
        self.max_daily_drawdown_pct = max_daily_drawdown_pct
        self.min_notional_tmn = min_notional_tmn
        self.max_notional_tmn = max_notional_tmn
        self.daily_loss_tmn = 0.0
        self.circuit_breaker_tripped = False

    def evaluate_order(self, capital: float, entry_price: float,
                       stop_loss_price: float, quantity: float, side: str) -> Dict[str, Any]:
        """
        Evaluates whether an order complies with portfolio risk rules.
        """
        if self.circuit_breaker_tripped:
            return {"allowed": False, "reason": "CIRCUIT_BREAKER_TRIPPED"}

        if capital <= 0 or entry_price <= 0 or quantity <= 0:
            return {"allowed": False, "reason": "INVALID_PARAMETERS"}

        side = side.upper()
        if side not in ("BUY", "SELL"):
            return {"allowed": False, "reason": "INVALID_SIDE"}

        # Validate Stop Loss direction
        if side == "BUY" and stop_loss_price >= entry_price:
            return {"allowed": False, "reason": "INVALID_STOP_LOSS_FOR_BUY"}
        if side == "SELL" and stop_loss_price <= entry_price:
            return {"allowed": False, "reason": "INVALID_STOP_LOSS_FOR_SELL"}

        notional = entry_price * quantity
        if notional < self.min_notional_tmn:
            return {"allowed": False, "reason": "BELOW_MIN_NOTIONAL", "notional": notional}
        if notional > self.max_notional_tmn:
            return {"allowed": False, "reason": "ABOVE_MAX_NOTIONAL", "notional": notional}

        # Calculate risk amount
        risk_per_unit = abs(entry_price - stop_loss_price)
        total_trade_risk = risk_per_unit * quantity
        max_allowed_risk = capital * self.max_risk_pct_per_trade

        if total_trade_risk > max_allowed_risk:
            return {
                "allowed": False,
                "reason": "EXCEEDS_MAX_RISK_PER_TRADE",
                "trade_risk": total_trade_risk,
                "max_allowed": max_allowed_risk
            }

        return {
            "allowed": True,
            "notional": notional,
            "estimated_risk": total_trade_risk
        }

    def record_loss(self, loss_amount_tmn: float, current_capital: float) -> None:
        if loss_amount_tmn > 0:
            self.daily_loss_tmn += loss_amount_tmn
            if self.daily_loss_tmn >= (current_capital * self.max_daily_drawdown_pct):
                self.circuit_breaker_tripped = True
                logger.warning("CIRCUIT_BREAKER_TRIPPED: Daily drawdown limit reached!")
