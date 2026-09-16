"""
Risk Manager for AtriaTrade.

Supported environments:
- Backtesting
- Paper Trading
- Testnet

This module does not place real orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional


@dataclass
class RiskConfig:
    """Risk management configuration."""

    initial_capital: float = 10_000.0
    max_risk_per_trade_percent: float = 1.0
    max_position_percent: float = 50.0
    max_daily_loss_percent: float = 5.0
    min_order_value: float = 0.0
    max_open_positions: int = 10

    @property
    def max_risk_percent(self) -> float:
        """Backward-compatible alias."""
        return self.max_risk_per_trade_percent


class RiskManager:
    """Manage position risk, order validation and daily loss limits."""

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
        # Backward-compatible aliases
        if "risk_reward_ratio" in kwargs:
            default_risk_reward_ratio = float(
                kwargs["risk_reward_ratio"]
            )

        if (
            default_risk_per_trade_percent is None
            and "risk_per_trade_percent" in kwargs
        ):
            default_risk_per_trade_percent = float(
                kwargs["risk_per_trade_percent"]
            )

        if (
            max_capital_allocation_percent is None
            and "max_capital_allocation_percent" in kwargs
        ):
            max_capital_allocation_percent = float(
                kwargs["max_capital_allocation_percent"]
            )

        # Capital priority:
        # capital > initial_capital > config.initial_capital > default
        if capital is not None:
            resolved_capital = float(capital)
        elif initial_capital is not None:
            resolved_capital = float(initial_capital)
        elif config is not None:
            resolved_capital = float(config.initial_capital)
        else:
            resolved_capital = 10_000.0

        if config is None:
            config = RiskConfig(
                initial_capital=resolved_capital
            )
        else:
            # Copy config to avoid mutating the caller's object
            config = RiskConfig(
                initial_capital=resolved_capital,
                max_risk_per_trade_percent=float(
                    config.max_risk_per_trade_percent
                ),
                max_position_percent=float(
                    config.max_position_percent
                ),
                max_daily_loss_percent=float(
                    config.max_daily_loss_percent
                ),
                min_order_value=float(config.min_order_value),
                max_open_positions=int(config.max_open_positions),
            )

        # Risk-per-trade overrides
        if max_risk_per_trade_percent is not None:
            config.max_risk_per_trade_percent = float(
                max_risk_per_trade_percent
            )
        elif max_risk_percent is not None:
            config.max_risk_per_trade_percent = float(
                max_risk_percent
            )
        elif default_risk_per_trade_percent is not None:
            config.max_risk_per_trade_percent = float(
                default_risk_per_trade_percent
            )

        # Position-allocation overrides
        if max_capital_allocation_percent is not None:
            config.max_position_percent = float(
                max_capital_allocation_percent
            )
        elif max_position_percent is not None:
            config.max_position_percent = float(
                max_position_percent
            )

        if max_daily_loss_percent is not None:
            config.max_daily_loss_percent = float(
                max_daily_loss_percent
            )

        if min_order_value is not None:
            config.min_order_value = float(min_order_value not None:
            config.max is not None:
            config.max_open_positions = int(max_open_positions)

        # Configuration validation
        if config.initial_capital <= 0:
            raise ValueError(
                "initial capital must be greater than zero"
            )

        if not 0 < config.max_risk_per_trade_percent <= 100:
            raise ValueError(
                "max risk percent must be between 0 and 100"
            )

        if not 0 < config.max_position_percent <= 100:
            raise ValueError(
                "max position percent must be between 0 and 100"
            )

        if not 0 < config.max_daily_loss_percent <= 100:
            raise ValueError(
                "max daily loss percent must be between 0 and 100"
            )

        if config.min_order_value < 0:
            raise ValueError(
                "min order value cannot be negative"
            )

        if config.max_open_positions <= 0:
            raise ValueError(
                "max open positions must be greater than zero"
            )

        if float(default_risk_reward_ratio) <= 0:
            raise ValueError(
                "default risk reward ratio must be greater than zero"
            )

        self.config = config

        self.initial_capital = float(config.initial_capital)
        self.capital = float(config.initial_capital)

        self.default_risk_reward_ratio = float(
            default_risk_reward_ratio
        )
        self.default_risk_per_trade_percent = float(
            config.max_risk_per_trade_percent
        )

        self.max_risk_percent = float(
            config.max_risk_per_trade_percent
        )
        self.max_risk_per_trade_percent = float(
            config.max_risk_per_trade_percent
        )

        self.max_position_percent = float(
            config.max_position_percent
        )
        self.max_capital_allocation_percent = float(
            config.max_position_percent
        )

        self.max_daily_loss_percent = float(
            config.max_daily_loss_percent
        )

        self._loss_date: date = date.today()
        self._daily_loss: float = 0.0

    def _ensure_current_day(self) -> None:
        """Reset the daily loss when the calendar day changes."""
        today = date.today()

        if today != self._loss_date:
            self._loss_date = today
            self._daily_loss = 0.0

    def record_daily_loss(self, loss: float) -> float:
        """Record a loss and return the accumulated daily loss."""
        value = float(loss)
        self._daily_loss = max(
            0.0,
            self._daily_loss + value,
        )
        return float(self._daily_loss)

    def get_today_loss(self) -> float:
        """Return today's accumulated loss."""
        self._ensure_current_day()
        return float(self._daily_loss)

    def get_daily_loss(self) -> float:
        """Backward-compatible alias."""
        return self.get_today_loss()

    def get_max_daily_loss(self) -> float:
        """Return maximum daily loss in capital units."""
        return float(
            self.initial_capital
            * self.max_daily_loss_percent
            / 100.0
        )

    def can_trade_today(self) -> bool:
        """
        Return whether trading is allowed.

        At the exact limit, trading is blocked.
        """
        return self.get_today_loss() < self.get_max_daily_loss()

    def reset_daily_loss(self) -> None:
        """Reset today's accumulated loss."""
        self._loss_date = date.today()
        self._daily_loss = 0.0

    def max_position_value(self) -> float:
        """Return maximum capital allocation for one position."""
        return float(
            self.capital
            * self.max_position_percent
            / 100.0
        )

    def max_risk_value(self) -> float:
        """Return maximum risk value per trade."""
        return float(
            self.capital
            * self.max_risk_percent
            / 100.0
        )

    def validate_daily_risk(
        self,
        current_daily_loss_percent: float,
    ) -> Dict[str, Any]:
        """
        Validate daily loss percentage.

        The limit is strict:
        - 3.2% with a 5% limit => allowed
        - 5.0% with a 5% limit => blocked
 < self.max current_loss = float(current_daily_loss_percent)
        trading_allowed = (
            current_loss < self.max_daily_loss_percent
        )

        if trading_allowed:
            reason = ""
        else:
            reason = "Max daily loss limit reached"

        return {
            "trading_allowed": trading_allowed,
            "reason": reason,
            "current_daily_loss_percent": current_loss,
            "max_daily_loss_percent": (
                self.max_daily_loss_percent
            ),
        }

    @staticmethod
    def _normalize_side(side: Optional[str]) -> str:
        """Normalize BUY/SELL and LONG/SHORT values."""
        normalized = str(side or "").strip().upper()

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
        """
        Calculate stop-loss and take-profit levels.

        Example:
            entry=100, BUY, distance=2%, RR=2
            stop_loss=98, take_profit=104
        """
        entry = float(entry_price)

        if entry <= 0:
            raise ValueError(
                "entry_price must be greater than zero"
            )

        normalized_side = self._normalize_side(side)

        if normalized_side not in {
            "BUY",
            "SELL",
            "LONG",
            "SHORT",
        }:
            raise ValueError("side must be BUY or SELL")

        ratio = float(
            risk_reward_ratio
            if risk_reward_ratio is not None
            else self.default_risk_reward_ratio
        )

        if ratio <= 0:
            raise ValueError(
                "risk_reward_ratio must be greater than zero"
            )

        if stop_loss_price is not None:
            stop_loss = float(stop_loss_price)

            if stop_loss <= 0:
                raise ValueError(
                    "stop_loss_price must be greater than zero"
                )

            risk_distance = abs(entry - stop_loss)

        elif stop_loss_distance_percent is not None:
            distance_percent = float(
                stop_loss_distance_percent
            )

            if distance_percent <= 0:
                raise ValueError(
                    "stop_loss_distance_percent must be "
                    "greater than zero"
                )

            risk_distance = (
                entry * distance_percent / 100.0
            )

            if normalized_side in {"BUY", "LONG"}:
                stop_loss = entry - risk_distance
            else:
                stop_loss = entry + risk_distance

        else:
            raise ValueError(
                "either stop_loss_distance_percent or "
                "stop_loss_price is required"
            )

        if risk_distance <= 0:
            raise ValueError(
                "entry price and stop loss cannot be equal"
            )

        if normalized_side in {"BUY", "LONG"}:
            if stop_loss >= entry:
                raise ValueError(
                    "for BUY orders stop_loss must be below price"
                )

            take_profit = entry + (
                risk_distance * ratio
            )
        else:
            if stop_loss <= entry:
                raise ValueError(
                    "for SELL orders stop_loss must be above price"
                )

            take_profit = entry - (
                risk_distance * ratio
            )

        return {
            "entry_price": float(entry),
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "risk_distance": float(risk_distance),
            "risk_reward_ratio": float(ratio),
        }

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: Optional[float] = None,
        risk_percent: Optional[float] = None,
        capital: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        side: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Calculate position size.

        New/test API:
            Returns a dictionary when capital or stop_loss_price
            is explicitly supplied.

        Legacy API:
            Returns a float when using entry_price and stop_loss.
        """
        if capital is None and "balance" in kwargs:
            capital = kwargs["balance"]

        if capital is None and "account_balance" in kwargs:
            capital = kwargs["account_balance"]

        if stop_loss_price is None and "stop_loss_price" in kwargs:
            stop_loss_price = kwargs["stop_loss_price"]

        if stop_loss is None and "stop_loss" in kwargs:
            stop_loss = kwargs["stop_loss"]

        if (
            risk_percent is None
            and "risk_per_trade_percent" in kwargs
        ):
            risk_percent = kwargs[
                "risk_per_trade_percent"
            ]

        if (
            risk_percent is None
            and "default_risk_per_trade_percent" in kwargs
        ):
            risk_percent = kwargs[
                "default_risk_per_trade_percent"
            ]

        entry = float(entry_price)

        effective_stop = (
            stop_loss_price
            if stop_loss_price is not None
            else stop_loss
        )

        if effective_stop is None:
            raise TypeError(
                "calculate_position_size() missing "
                "required argument: 'stop_loss_price'"
            )

        stop = float(effective_stop)
        capital_value = float(
            self.capital if capital is None else capital
        )

        if capital_value <= 0:
            raise ValueError(
                "capital must be greater than zero"
            )

        if entry <= 0 or stop <= 0:
            raise ValueError(
                "prices must be greater than zero"
            )

        risk_per_unit = abs(entry - stop)

        if risk_per_unit <= 0:
            raise ValueError(
                "entry price and stop loss cannot be equal"
            )

        percent = float(
            self.default_risk_per_trade_percent
            if risk_percent is None
            else risk_percent
        )

        if percent <= 0:
            raise ValueError(
                "risk_percent must be greater than zero"
            )

        target_risk_amount = (
            capital_value * percent / 100.0
        )

        raw_units = (
            target_risk_amount / risk_per_unit
        )

        raw_allocated_capital = raw_units * entry

        maximum_allocated_capital = (
            capital_value
            * self.max_position_percent
            / 100.0
        )

        is_capped = (
            raw_allocated_capital
            > maximum_allocated_capital
        )

        units = min(
            raw_units,
            maximum_allocated_capital / entry,
        )

        allocated_capital = units * entry
        actual_risk_amount = units * risk_per_unit

        # Test/new API returns a dictionary
        if capital is not None or stop_loss_price is not None:
            return {
                "units": float(units),
                "allocated_capital": float(
                    allocated_capital
                ),
                "risk_amount": float(
                    actual_risk_amount
                ),
                "is_capped": bool(is_capped),
            }

        # Legacy API returns a float
        return float(units)

    def validate_order(
        self,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        side: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> bool:
        """Validate an order and return True when valid."""
        if not self.can_trade_today():
            raise ValueError(
                "daily loss limit exceeded"
            )

        quantity_value = float(quantity)
        price_value = float(price)

        if quantity_value <= 0:
            raise ValueError(
                "quantity must be greater than zero"
            )

        if price_value <= 0:
            raise ValueError(
                "price must be greater than zero"
            )

        position_value = quantity_value * price_value

        if position_value < self.config.min_order_value:
            raise ValueError(
                "order value is below minimum order value"
            )

        if position_value > self.max_position_value():
            raise ValueError(
                "position value exceeds maximum allowed limit"
            )

        if stop_loss is not None:
            stop_loss_value = float(stop_loss)

            if stop_loss_value <= 0:
                raise ValueError(
                    "stop_loss must be greater than zero"
                )

            normalized_side = self._normalize_side(side)

            if normalized_side in {"BUY", "LONG"}:
                if stop_loss_value >= price_value:
                    raise ValueError(
                        "for BUY orders stop_loss must be "
                        "below price"
                    )

            elif normalized_side in {"SELL", "SHORT"}:
                if stop_loss_value <= price_value:
                    raise ValueError(
                        "for SELL orders stop_loss must be "
                        "above price"
                    )

        return True

    def check_order_risk(
        self,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        side: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> bool:
        """Backward-compatible wrapper."""
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
        """Validate whether a position can be opened."""
        return self.validate_order(
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            side=side,
            symbol=symbol,
        )

    def get_risk_summary(self) -> Dict[str, Any]:
        """Return a complete risk summary."""
        return {
            "capital": float(self.capital),
            "daily_loss": float(self.get_today_loss()),
            "max_daily_loss": float(
                self.get_max_daily_loss()
            ),
            "max_position_value": float(
                self.max_position_value()
            ),
            "max_risk_value": float(
                self.max_risk_value()
            ),
            "can_trade_today": bool(
                self.can_trade_today()
            ),
        }
