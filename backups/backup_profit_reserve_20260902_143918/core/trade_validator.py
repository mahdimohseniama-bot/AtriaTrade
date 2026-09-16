"""
Trade validation layer for AtriaTrade.

Simulation-only validation.
This module does not create or send exchange orders.
"""

from typing import Any, Dict, Optional


class TradeValidator:
    """Validate a simulated trade before it enters the execution pipeline."""

    def __init__(
        self,
        max_daily_loss_percent: float = 5.0,
        max_capital_allocation_percent: float = 25.0,
        minimum_risk_reward_ratio: float = 1.0,
    ) -> None:
        if not 0 < max_daily_loss_percent <= 100:
            raise ValueError("max_daily_loss_percent must be between 0 and 100")
        if not 0 < max_capital_allocation_percent <= 100:
            raise ValueError(
                "max_capital_allocation_percent must be between 0 and 100"
            )
        if minimum_risk_reward_ratio <= 0:
            raise ValueError("minimum_risk_reward_ratio must be greater than zero")

        self.max_daily_loss_percent = float(max_daily_loss_percent)
        self.max_capital_allocation_percent = float(
            max_capital_allocation_percent
        )
        self.minimum_risk_reward_ratio = float(minimum_risk_reward_ratio)

    def validate(
        self,
        *,
        side: str,
        entry_price: float,
        stop_loss_price: float,
        take_profit_price: float,
        capital: float,
        allocated_capital: float,
        current_daily_loss_percent: float = 0.0,
        position_size: Optional[float] = None,
    ) -> Dict[str, Any]:
        errors = []
        normalized_side = str(side).upper()

        if normalized_side not in ("BUY", "SELL"):
            errors.append("side must be BUY or SELL")

        if entry_price <= 0:
            errors.append("entry_price must be greater than zero")

        if capital <= 0:
            errors.append("capital must be greater than zero")

        if allocated_capital <= 0:
            errors.append("allocated_capital must be greater than zero")

        if capital > 0:
            allocation_percent = allocated_capital / capital * 100.0
        else:
            allocation_percent = 0.0

        if allocation_percent > self.max_capital_allocation_percent:
            errors.append("capital allocation exceeds configured maximum")

        if current_daily_loss_percent < 0:
            errors.append("current_daily_loss_percent cannot be negative")
        elif current_daily_loss_percent >= self.max_daily_loss_percent:
            errors.append("maximum daily loss limit reached")

        if normalized_side == "BUY":
            if stop_loss_price >= entry_price:
                errors.append("BUY stop loss must be below entry price")
            if take_profit_price <= entry_price:
                errors.append("BUY take profit must be above entry price")
        elif normalized_side == "SELL":
            if stop_loss_price <= entry_price:
                errors.append("SELL stop loss must be above entry price")
            if take_profit_price >= entry_price:
                errors.append("SELL take profit must be below entry price")

        risk_distance = abs(entry_price - stop_loss_price)
        reward_distance = abs(take_profit_price - entry_price)

        if risk_distance <= 0:
            errors.append("risk distance must be greater than zero")
        else:
            risk_reward_ratio = reward_distance / risk_distance
            if risk_reward_ratio < self.minimum_risk_reward_ratio:
                errors.append("risk reward ratio is below the minimum")
        if position_size is not None and position_size <= 0:
            errors.append("position_size must be greater than zero")

        return {
            "valid": not errors,
            "allowed": not errors,
            "side": normalized_side,
            "entry_price": float(entry_price),
            "stop_loss_price": float(stop_loss_price),
            "take_profit_price": float(take_profit_price),
            "allocation_percent": round(allocation_percent, 8),
            "risk_distance": round(risk_distance, 8),
            "reward_distance": round(reward_distance, 8),
            "risk_reward_ratio": (
                round(reward_distance / risk_distance, 8)
                if risk_distance > 0
                else 0.0
            ),
            "errors": errors,
            "reason": "Trade validation passed" if not errors else errors[0],
        }
