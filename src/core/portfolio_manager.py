"""
PortfolioManager - AtriaTrade

Manages cash allocation, position records, equity calculations, and drawdown metrics.
Designed strictly for Paper Trading, Backtesting, and Testnet simulation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class PortfolioManager:
    """Portfolio state and allocation tracker."""

    def __init__(
        self,
        initial_cash: float = 10000.0,
        max_asset_weight: float = 0.3,
        rebalance_threshold: float = 0.05,
    ) -> None:
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.max_asset_weight = float(max_asset_weight)
        self.rebalance_threshold = float(rebalance_threshold)

        # positions: {symbol: {"quantity": float, "avg_entry_price": float}}
        self.positions: Dict[str, Dict[str, float]] = {}
        self.peak_equity = float(initial_cash)

    def can_allocate(self, symbol: str, required_amount: float) -> bool:
        """Check if capital allocation satisfies cash balance constraints."""
        amount = float(required_amount)
        if amount <= 0:
            return False
        return self.cash >= amount

    def record_buy(self, symbol: str, quantity: float, price: float, fee: float = 0.0) -> None:
        """Record buy execution and deduct cash."""
        sym = str(symbol).strip().upper()
        qty = float(quantity)
        px = float(price)
        total_cost = (qty * px) + float(fee)

        self.cash -= total_cost

        if sym not in self.positions:
            self.positions[sym] = {"quantity": qty, "avg_entry_price": px}
        else:
            current_qty = self.positions[sym]["quantity"]
            current_avg = self.positions[sym]["avg_entry_price"]
            new_qty = current_qty + qty
            if new_qty > 0:
                new_avg = ((current_qty * current_avg) + (qty * px)) / new_qty
            else:
                new_avg = px
            self.positions[sym] = {"quantity": new_qty, "avg_entry_price": new_avg}

    def record_sell(self, symbol: str, quantity: float, price: float, fee: float = 0.0) -> None:
        """Record sell execution and add cash proceeds."""
        sym = str(symbol).strip().upper()
        qty = float(quantity)
        px = float(price)
        proceeds = (qty * px) - float(fee)

        self.cash += proceeds

        if sym in self.positions:
            remaining_qty = self.positions[sym]["quantity"] - qty
            if remaining_qty <= 1e-8:
                del self.positions[sym]
            else:
                self.positions[sym]["quantity"] = remaining_qty

    def get_holding_quantity(self, symbol: str) -> float:
        """Get quantity held for a given symbol."""
        sym = str(symbol).strip().upper()
        return self.positions.get(sym, {}).get("quantity", 0.0)

    def calculate_total_equity(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        """Calculate total portfolio equity given latest asset prices."""
        prices = current_prices or {}
        positions_val = 0.0
        for sym, pos in self.positions.items():
            price = float(prices.get(sym, pos["avg_entry_price"]))
            positions_val += pos["quantity"] * price

        equity = self.cash + positions_val
        if equity > self.peak_equity:
            self.peak_equity = equity
        return equity

    def calculate_drawdown(self, current_equity: Optional[float] = None) -> float:
        """
        Calculate percentage drawdown from peak equity.
        If current_equity is not provided, computes from existing known state.
        """
        if current_equity is None:
            eq = self.calculate_total_equity()
        else:
            eq = float(current_equity)

        if eq > self.peak_equity:
            self.peak_equity = eq

        if self.peak_equity <= 0:
            return 0.0

        dd_pct = ((self.peak_equity - eq) / self.peak_equity) * 100.0
        return max(0.0, dd_pct)

    def get_summary(self, current_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Summary of current portfolio status."""
        equity = self.calculate_total_equity(current_prices)
        drawdown = self.calculate_drawdown(equity)
        return {
            "cash": self.cash,
            "equity": equity,
            "peak_equity": self.peak_equity,
            "drawdown_pct": drawdown,
            "positions_count": len(self.positions),
            "positions": dict(self.positions),
        }
