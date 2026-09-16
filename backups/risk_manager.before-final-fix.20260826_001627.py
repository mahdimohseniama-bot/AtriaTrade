"""
Risk management utilities for AtriaTrade.

This module supports both:
- current project API
- legacy/test API used by unit tests
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional


@dataclass
class RiskConfig:
    """تنظیمات مدیریت ریسک."""

    initial_capital: float = 10_000.0
    max_risk_per_trade_percent: float = 1.0
    max_position_percent: float = 50.0
    max_daily_loss_percent: float = 5.0
    min_order_value: float = 0.0
    max_open_positions: int = 10

    @property
    def max_risk_percent(self) -> float:
        return self.max_risk_per_trade_percent


class RiskManager:
    """مدیریت ریسک سفارش، اندازه پوزیشن و زیان روزانه."""

    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        initial_capital: Optional[float] = None,
        capital: Optional[float] = None,
        default_risk_reward_ratio: float = 2.0,
        default_risk_per_trade_percent: Optional[float] = None,
        max_capital_allocation_percent: Optional[float] = None,
        max_position_percent: Optional[float] = None,
        max_daily_loss_percent: Optional[float] = None,
        max_risk_percent: Optional[float] = None,
        max_risk_per_trade_percent: Optional[float] = None,
        min_order_value: Optional[float] = None,
        max_open_positions: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        # aliases from older/newer code
        if "risk_reward_ratio" in kwargs:
            default_risk_reward_ratio = kwargs["risk_reward_ratio"]
        if default_risk_per_trade_percent is None and "risk_per_trade_percent" in kwargs:
            default_risk_per_trade_percent = kwargs["risk_per_trade_percent"]
        if max_capital_allocation_percent is None and "max_capital_allocation_percent" in kwargs:
            max_capital_allocation_percent = kwargs["max_capital_allocation_percent"]

        # resolve capital priority: capital > initial_capital > config.initial_capital > default
        if capital is not None:
            resolved_capital = float(capital)
        elif initial_capital is not None:
            resolved_capital = float(initial_capital)
        elif config is not None:
            resolved_capital = float(config.initial_capital)
        else:
            resolved_capital = 10_000.0

        if config is None:
            config = RiskConfig(initial_capital=resolved_capital)
        else:
            config = RiskConfig(
                initial_capital=resolved_capital,
                max_risk_per_trade_percent=float(config.max_risk_per_trade_percent),
                max_position_percent=float(config.max_position_percent),
                max_daily_loss_percent=float(config.max_daily_loss_percent),
                min_order_value=float(config.min_order_value),
                max_open_positions=int(config.max_open_positions),
            )

        # risk percent aliases
        if max_risk_per_trade_percent is not None:
            config.max_risk_per_trade_percent = float(max_risk_per_trade_percent)
        elif max_risk_percent is not None:
            config.max_risk_per_trade_percent = float(max_risk_percent)
        elif default_risk_per_trade_percent is not None:
            config.max_risk_per_trade_percent = float(default_risk_per_trade_percent)

        # position allocation aliases
        if max_capital_allocation_percent is not None:
            config.max_position_percent = float(max_capital_allocation_percent)
        elif max_position_percent is not None:
            config.max_position_percent = float(max_position_percent)

        if max_daily_loss_percent is not None:
            config.max_daily_loss_percent = float(max_daily_loss_percent)

        if min_order_value is not None:
            config.min_order_value = float(min_order_value)

        if max_open_positions is not None:
            config.max_open_positions = int(max_open_positions)

        # validations
        if config.initial_capital <= 0:
            raise ValueError("initial capital must be greater than zero")
        if not 0 < config.max_risk_per_trade_percent <= 100:
            raise ValueError("max risk percent must be between 0 and 100")
        if not 0 < config.max_position_percent <= 100:
            raise ValueError("max position percent must be between 0 and 100")
        if not 0 < config.max_daily_loss_percent <= 100:
            raise ValueError("max daily loss percent must be between 0 and 100")

        self.config = config

        self.initial_capital = config.initial_capital
        self.capital = config.initial_capital

        self.default_risk_reward_ratio = float(default_risk_reward_ratio)
        self.default_risk_per_trade_percent = float(config.max_risk_per_trade_percent)

        self.max_risk_percent = float(config.max_risk_per_trade_percent)
        self.max_risk_per_trade_percent = float(config.max_risk_per_trade_percent)

        self.max_position_percent = float(config.max_position_percent)
        self.max_capital_allocation_percent = float(config.max_position_percent)

        self.max_daily_loss_percent = float(config.max_daily_loss_percent)

        self._loss_date: date = date.today()
        self._daily_loss: float = 0.0

    def _ensure_current_day(self) -> None:
        today = date.today()
        if today != self._loss_date:
            self._loss_date = today
            self._daily_loss = 0.0

    def record_daily_loss(self, loss: float) -> float:
        value = float(loss)
        self._daily_loss = max(0.0, self._daily_loss + value)
        return self._daily_loss

    def get_today_loss(self) -> float:
        self._ensure_current_day()
        return float(self._daily_loss)

    def get_daily_loss(self) -> float:
        return self.get_today_loss()

    def get_max_daily_loss(self) -> float:
        return self.initial_capital * self.max_daily_loss_percent / 100.0

    def can_trade_today(self) -> bool:
        return self.get_today_loss() < self.get_max_daily_loss()

    def reset_daily_loss(self) -> None:
        self._loss_date = date.today()
        self._daily_loss = 0.0

    def max_position_value(self) -> float:
        return self.capital * self.max_position_percent / 100.0

    def max_risk_value(self) -> float:
        return self.capital * self.max_risk_percent / 100.0

    def validate_daily_risk(self, current_daily_loss_percent: float) -> Dict[str, Any]:
        loss = float(current_daily_loss_percent)
        allowed = loss < self.max_daily_loss_percent
        return {
            "trading_allowed": allowed,
            "reason": "" if allowed else "Max daily loss limit reached",
            "current_daily_loss_percent": loss,
            "max_daily_loss_percent": self.max_daily_loss_percent,
        }

    def _normalize_side(self, side: Optional[str]) -> str:
        normalized = str(side or "").upper().strip()
        if "." in normalized:
            normalized = normalized.split(".")[-1]
        return normalized

    def calculate_levels(
        self,
        entry_price: float,
        side: str,
        stop_loss_distance_percent: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        risk_reward_ratio: Optional[float] = None,
    ) -> Dict[str, float]:
        entry = float(entry_price)
        rr = float(
            risk_reward_ratio
            if risk_reward_ratio is not None
            else self.default_risk_reward_ratio
        )

        if entry <= 0:
            raise ValueError("entry_price must be positive")
        if rr <= 0:
            raise ValueError("risk_reward_ratio must be positive")

        side_norm = self._normalize_side(side)
        if side_norm not in {"BUY", "SELL", "LONG", "SHORT"}:
            raise ValueError("side must be BUY or SELL")

        if stop_loss_price is not None:
            stop = float(stop_loss_price)
            if stop <= 0:
                raise ValueError("stop_loss_price must be positive")
            risk_distance = abs(entry - stop)
        elif stop_loss_distance_percent is not None:
            distance_percent = float(stop_loss_distance_percent)
            if distance_percent <= 0:
                raise ValueError("stop_loss_distance_percent must be positive")
            risk_distance = entry * distance_percent / 100.0
            stop = entry - risk_distance if side_norm in {"BUY", "LONG"} else entry + risk_distance
        else:
            raise ValueError("either stop_loss_distance_percent or stop_loss_price is required")

        if risk_distance <= 0:
            raise ValueError("risk distance must be greater than zero")

        if side_norm in {"BUY", "LONG"}:
            if stop >= entry:
                raise ValueError("for BUY orders stop_loss must be below price")
            take_profit = entry + (risk_distance * rr)
        else:
            if stop <= entry:
                raise ValueError("for SELL orders stop_loss must be above price")
            take_profit = entry - (risk_distance * rr)

        return {
            "entry_price": entry,
            "side": side_norm,
            "stop_loss": float(stop),
            "take_profit": float(take_profit),
            "risk_distance": float(risk_distance),
            "risk_reward_ratio": rr,
        }

    def calculate_position_size(
        self,
        capital: Optional[float] = None,
        entry_price: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        risk_percent: Optional[float] = None,
        side: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Compatible with both:
        - new test API: returns dict with units/allocated_capital/risk_amount/is_capped
        - older project API: returns float quantity when called without capital/stop_loss_price style
        """
        if capital is None and "balance" in kwargs:
            capital = kwargs["balance"]
        if capital is None and "account_balance" in kwargs:
            capital = kwargs["account_balance"]
        if entry_price is None and "price" in kwargs:
            entry_price = kwargs["price"]
        if stop_loss_price is None and "stop_loss_price" in kwargs:
            stop_loss_price = kwargs["stop_loss_price"]
        if stop_loss is None and "stop_loss" in kwargs:
            stop_loss = kwargs["stop_loss"]
        if risk_percent is None and "risk_per_trade_percent" in kwargs:
            risk_percent = kwargs["risk_per_trade_percent"]
        if risk_percent is_percent = kwargs["default_risk_per_trade_percent"]

        # old style uses = kwargs["default_risk_per_trade_percent"]

        # old style uses stop_loss, new style uses stop_loss_price
        effective_stop = stop_loss_price if stop_loss_price is not None else stop_loss

        # detect whether test/new API is being used
        dict_mode = capital is not None or stop_loss_price is not None or "capital" in kwargs

        if entry_price is None:
            raise TypeError("calculate_position_size() missing required argument: 'entry_price'")
        if effective_stop is None:
            raise TypeError("calculate_position_size() missing required argument: 'stop_loss_price'")

        capital_f = float(capital if capital is not None else self.capital)
        entry = float(entry_price)
        stop = float(effective_stop)
        risk_pct = float(risk_percent if risk_percent is not None else self.default_risk_per_trade_percent)

        if capital_f <= 0:
            raise ValueError("capital must be positive")
        if entry <= 0:
            raise ValueError("entry_price must be positive")
        if stop <= 0:
            raise ValueError("stop_loss_price must be positive")
        if risk_pct <= 0:
            raise ValueError("risk_percent must be positive")

        risk_per_unit = abs(entry - stop)
        if risk_per_unit <= 0:
            raise ValueError("entry price and stop loss cannot be equal")

        target_risk_amount = capital_f * risk_pct / 100.0
        raw_units = target_risk_amount / risk_per_unit
        raw_allocated_capital = raw_units * entry
        max_allocated_capital = capital_f * self.max_position_percent / 100.0

        is_capped = raw_allocated_capital > max_allocated_capital
        units = min(raw_units, max_allocated_capital / entry)
        allocated_capital = units * entry
        risk_amount = units * risk_per_unit

        if dict_mode:
            return {
                "units": float(units),
                "allocated_capital": float(allocated_capital),
                "risk_amount": float(risk_amount),
                "is_capped": bool(is_capped),
            }

        return float(units)

    def validate_order(
        self,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        side: Optional[str] = None,
        symbol: Optional[str] = None,
        **kwargs: Any,
    ) -> bool:
        """
        Legacy compatibility validator.
        Returns True when valid, otherwise raises ValueError.
        """
        # support alternate calling styles
        if quantity is None and "capital" in kwargs:
            quantity = kwargs.get("quantity")
        if price is None and "entry_price" in kwargs:
            price = kwargs["entry_price"]
        if stop_loss is None and "stop_loss_price" in kwargs:
            stop_loss = kwargs["stop_loss_price"]

        if not self.can_trade_today():
            raise ValueError("daily loss limit exceeded")

        if symbol is not None and not str(symbol).strip():
            raise ValueError("symbol is required")

        if quantity is None:
            raise TypeError("validate_order() missing required argument: 'quantity'")
        if price is None:
            raise TypeError("validate_order() missing required argument: 'price'")

        quantity_f = float(quantity)
        price_f = float(price)

        if quantity_f <= 0:
            raise ValueError("quantity must be greater than zero")
        if price_f <= 0:
            raise ValueError("price must be greater than zero")

        position_value = quantity_f * price_f
        if position_value < self.config.min_order_value:
            raise ValueError("order value is below minimum order value")
        if position_value > self.max_position_value():
            raise ValueError("position value exceeds maximum allowed limit")

        if stop_loss is not None:
            stop_f = float(stop_loss)
            if stop_f <= 0:
                raise ValueError("stop_loss must be greater than zero")

            side_norm = self._normalize_side(side)
            if side_norm in {"BUY", "LONG"} and stop_f >= price_f:
                raise ValueError("for BUY orders stop_loss must be below price")
            if side_norm in {"SELL", "SHORT"} and stop_f <= price_f:
                raise ValueError("for SELL orders stop_loss must be above price")

        return True

    def check_order_risk(
        self,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        side: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> bool:
        return self.validate_order(
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            side=side,
            symbol=symbol,
        )

    def can_open_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        side: Optional[str] = None,
        **kwargs: Any,
    ) -> bool:
        return self.validate_order(
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            side=side,
            symbol=symbol,
            **kwargs,
        )

    def get_risk_summary(self) -> Dict[str, Any]:
        return {
            "capital": float(self.capital),
            "daily_loss": float(self.get_today_loss()),
            "max_daily_loss": float(self.get_max_daily_loss()),
            "max_position_value": float(self.max_position_value()),
            "max_risk_value": float(self.max_risk_value()),
            "can_trade_today": self.can_trade_today(),
        }
