"""
ExecutionSimulator - AtriaTrade

Simulation-only execution engine for:
- Paper Trading
- Backtesting
- Testnet preparation

This module never connects to an exchange and never submits real orders.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


class ExecutionSimulator:
    """Execute BUY and SELL orders against a virtual portfolio."""

    VALID_MODES = {"paper", "backtest", "testnet"}

    def __init__(
        self,
        initial_cash: float = 10000.0,
        fee_pct: float = 0.1,
        mode: str = "paper",
    ) -> None:
        if initial_cash < 0:
            raise ValueError("initial_cash cannot be negative.")

        if fee_pct < 0 or fee_pct >= 100:
            raise ValueError("fee_pct must be between 0 and 100.")

        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in self.VALID_MODES:
            raise ValueError(
                f"mode must be one of: {sorted(self.VALID_MODES)}"
            )

        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.fee_pct = float(fee_pct)
        self.mode = normalized_mode

        self.positions: Dict[str, float] = {}
        self.average_prices: Dict[str, float] = {}
        self.realized_pnl = 0.0
        self.trade_count = 0
        self.history: List[Dict[str, Any]] = []

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _number(value: Any, name: str) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be numeric.") from exc

        if result != result or result in (float("inf"), float("-inf")):
            raise ValueError(f"{name} must be finite.")

        return result

    def _record_rejection(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        reason: str,
    ) -> Dict[str, Any]:
        result = {
            "timestamp": self._timestamp(),
            "mode": self.mode,
            "status": "rejected",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "fee": 0.0,
            "cash_after": self.cash,
            "realized_pnl": 0.0,
            "reason": reason,
            "order_submitted": False,
            "simulated": True,
        }

        self.history.append(result)
        return result

    def execute(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
    ) -> Dict[str, Any]:
        """
        Execute one virtual order.

        The returned record describes a simulation only.
        """
        symbol = str(symbol).strip().upper()
        side = str(side).strip().upper()
        quantity = self._number(quantity, "quantity")
        price = self._number(price, "price")

        if not symbol:
            raise ValueError("symbol cannot be empty.")

        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL.")

        if quantity <= 0:
            raise ValueError("quantity must be greater than zero.")

        if price <= 0:
            raise ValueError("price must be greater than zero.")

        gross_value = quantity * price
        fee = gross_value * self.fee_pct / 100.0

        if side == "BUY":
            total_cost = gross_value + fee

            if total_cost > self.cash:
                return self._record_rejection(
                    symbol,
                    side,
                    quantity,
                    price,
                    "insufficient_cash",
                )

            old_quantity = self.positions.get(symbol, 0.0)
            old_average = self.average_prices.get(symbol, 0.0)
            new_quantity = old_quantity + quantity

            if new_quantity > 0:
                new_average = (
                    (old_quantity * old_average) + gross_value
                ) / new_quantity
            else:
                new_average = price

            self.cash -= total_cost
            self.positions[symbol] = new_quantity
            self.average_prices[symbol] = new_average
            realized_pnl = 0.0

        else:
            current_quantity = self.positions.get(symbol, 0.0)

            if quantity > current_quantity:
                return self._record_rejection(
                    symbol,
                    side,
                    quantity,
                    price,
                    "insufficient_position",
                )

            average_price = self.average_prices.get(symbol, 0.0)
            self.cash += gross_value - fee
            self.positions[symbol] = current_quantity - quantity

            if self.positions[symbol] <= 1e-12:
                self.positions.pop(symbol, None)
                self.average_prices.pop(symbol, None)

            realized_pnl = (
                (price - average_price) * quantity
            ) - fee

            self.realized_pnl += realized_pnl

        self.trade_count += 1

        result = {
            "timestamp": self._timestamp(),
            "mode": self.mode,
            "status": "filled",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "gross_value": gross_value,
            "fee": fee,
            "cash_after": self.cash,
            "position_after": self.positions.get(symbol, 0.0),
            "realized_pnl": realized_pnl,
            "order_submitted": False,
            "simulated": True,
        }

        self.history.append(result)
        return result

    def mark_to_market(self, prices: Dict[str, float]) -> float:
        """Return total virtual equity using current market prices."""
        equity = self.cash

        for symbol, quantity in self.positions.items():
            if symbol in prices:
                price = self._number(prices[symbol], f"price[{symbol}]")
                if price < 0:
                    raise ValueError("Market price cannot be negative.")
                equity += quantity * price

        return equity

    def get_status(self, prices: Dict[str, float] | None = None) -> Dict[str, Any]:
        """Return the current simulator state."""
        equity = self.mark_to_market(prices or {})

        return {
            "mode": self.mode,
            "initial_cash": self.initial_cash,
            "cash": self.cash,
            "equity": equity,
            "positions": dict(self.positions),
            "realized_pnl": self.realized_pnl,
            "trade_count": self.trade_count,
            "history_count": len(self.history),
            "order_submitted": False,
            "real_trading_enabled": False,
        }
