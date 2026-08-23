"""
Advanced Risk Manager for AtriaTrade.

Calculates position sizing, stop loss, take profit,
and enforces safety constraints for simulation and paper trading.

Simulation-only module.
No exchange connection.
No real trading.
"""

from typing import Any, Dict, Optional


class RiskManager:
    """
    Advanced Risk Management Engine.

    Parameters:
    - default_risk_per_trade_percent: percentage of total capital risked per trade (e.g. 1.0 = 1%)
    - max_capital_allocation_percent: maximum capital percentage allocated to a single trade (e.g. 20.0 = 20%)
    - default_risk_reward_ratio: ratio of profit target to risk distance (e.g. 2.0 = 2:1 R:R)
    - max_daily_loss_percent: maximum cumulative daily loss allowed before risk halt
    """

    def __init__(
        self,
        default_risk_per_trade_percent: float = 1.0,
        max_capital_allocation_percent: float = 25.0,
        default_risk_reward_ratio: float = 2.0,
        max_daily_loss_percent: float = 5.0,
    ) -> None:
        if default_risk_per_trade_percent <= 0 or default_risk_per_trade_percent > 100:
            raise ValueError("default_risk_per_trade_percent must be between 0 and 100")
        if max_capital_allocation_percent <= 0 or max_capital_allocation_percent > 100:
            raise ValueError("max_capital_allocation_percent must be between 0 and 100")
        if default_risk_reward_ratio <= 0:
            raise ValueError("default_risk_reward_ratio must be greater than 0")
        if max_daily_loss_percent <= 0 or max_daily_loss_percent > 100:
            raise ValueError("max_daily_loss_percent must be between 0 and 100")

        self.risk_per_trade_pct = float(default_risk_per_trade_percent)
        self.max_capital_alloc_pct = float(max_capital_allocation_percent)
        self.risk_reward_ratio = float(default_risk_reward_ratio)
        self.max_daily_loss_pct = float(max_daily_loss_percent)

    def calculate_levels(
        self,
        entry_price: float,
        side: str = "BUY",
        stop_loss_distance_percent: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        risk_reward_ratio: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        Calculate precise Stop Loss and Take Profit prices.
        """
        if entry_price <= 0:
            raise ValueError("entry_price must be greater than zero")

        side = side.upper()
        if side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")

        rr = float(risk_reward_ratio or self.risk_reward_ratio)
        if rr <= 0:
            raise ValueError("risk_reward_ratio must be positive")

        if stop_loss_price is not None:
            sl = float(stop_loss_price)
            if side == "BUY" and sl >= entry_price:
                raise ValueError("BUY stop_loss_price must be below entry_price")
            if side == "SELL" and sl <= entry_price:
                raise ValueError("SELL stop_loss_price must be above entry_price")
            risk_dist = abs(entry_price - sl)
        elif stop_loss_distance_percent is not None:
            if stop_loss_distance_percent <= 0 or stop_loss_distance_percent >= 100:
                raise ValueError("stop_loss_distance_percent must be between 0 and 100")
            risk_dist = entry_price * (stop_loss_distance_percent / 100.0)
            sl = entry_price - risk_dist if side == "BUY" else entry_price + risk_dist
        else:
            raise ValueError("Must provide either stop_loss_distance_percent or stop_loss_price")

        if side == "BUY":
            tp = entry_price + (risk_dist * rr)
        else:
            tp = entry_price - (risk_dist * rr)
            if tp <= 0:
                tp = 0.0001

        return {
            "entry_price": float(entry_price),
            "stop_loss": round(float(sl), 8),
            "take_profit": round(float(tp), 8),
            "risk_distance": round(float(risk_dist), 8),
            "risk_reward_ratio": rr,
        }

    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss_price: float,
        side: str = "BUY",
        risk_percent: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate position size and allocated capital based on defined risk.
        Enforces maximum capital allocation cap.
        """
        if capital <= 0:
            raise ValueError("capital must be greater than zero")
        if entry_price <= 0:
            raise ValueError("entry_price must be greater than zero")

        side = side.upper()
        if side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")

        risk_pct = float(risk_percent or self.risk_per_trade_pct)
        if risk_pct <= 0 or risk_pct > 100:
            raise ValueError("risk_percent must be between 0 and 100")

        risk_amount = capital * (risk_pct / 100.0)

        if side == "BUY":
            if stop_loss_price >= entry_price:
                raise ValueError("BUY stop_loss_price must be strictly below entry_price")
            risk_per_unit = entry_price - stop_loss_price
        else:
            if stop_loss_price <= entry_price:
                raise ValueError("SELL stop_loss_price must be strictly above entry_price")
            risk_per_unit = stop_loss_price - entry_price

        raw_units = risk_amount / risk_per_unit
        allocated_capital = raw_units * entry_price

        # Cap by maximum capital allocation
        max_allowed_capital = capital * (self.max_capital_alloc_pct / 100.0)
        is_capped = False

        if allocated_capital > max_allowed_capital:
            allocated_capital = max_allowed_capital
            raw_units = allocated_capital / entry_price
            risk_amount = raw_units * risk_per_unit
            is_capped = True

        return {
            "allowed": True,
            "units": round(float(raw_units), 8),
            "allocated_capital": round(float(allocated_capital), 8),
            "risk_amount": round(float(risk_amount), 8),
            "risk_percent": round(float((risk_amount / capital) * 100.0), 4),
            "is_capped": is_capped,
            "max_allowed_capital": round(float(max_allowed_capital), 8),
        }

    def validate_daily_risk(
        self,
        current_daily_loss_percent: float,
    ) -> Dict[str, Any]:
        """
        Check if trading should be halted due to hitting daily loss limits.
        """
        halt = current_daily_loss_percent >= self.max_daily_loss_pct
        return {
            "trading_allowed": not halt,
            "current_loss_percent": float(current_daily_loss_percent),
            "max_daily_loss_percent": self.max_daily_loss_pct,
            "reason": "Max daily loss limit reached" if halt else "Within safe risk boundaries",
        }
