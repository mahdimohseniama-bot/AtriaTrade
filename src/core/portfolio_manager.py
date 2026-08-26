from __future__ import annotations

from typing import Any, Dict, Optional


class PortfolioManager:
    def __init__(
        self,
        initial_balance: Optional[float] = None,
        initial_cash: Optional[float] = None,
        max_asset_weight: float = 1.0,
        **kwargs: Any,
    ) -> None:
        if initial_cash is not None:
            starting_cash = float(initial_cash)
        elif initial_balance is not None:
            starting_cash = float(initial_balance)
        else:
            starting_cash = 10000.0

        if starting_cash < 0:
            raise ValueError("initial cash cannot be negative")

        if not 0 < float(max_asset_weight) <= 1:
            raise ValueError("max_asset_weight must be between 0 and 1")

        self.initial_balance = starting_cash
        self.initial_cash = starting_cash
        self.cash = starting_cash
        self.max_asset_weight = float(max_asset_weight)
        self.peak_equity = starting_cash

        self.holdings: Dict[str, float] = {}
        self.history: list[Dict[str, Any]] = []

        self._asset_cost_basis: Dict[str, float] = {}

    @property
    def balance(self) -> float:
        return float(self.cash)

    @staticmethod
    def _symbol(symbol: str) -> str:
        return str(symbol).strip().upper()

    def get_holding_quantity(self, symbol: str) -> float:
        return float(self.holdings.get(self._symbol(symbol), 0.0))

    def calculate_total_equity(
        self,
        price_map: Optional[Dict[str, float]] = None,
    ) -> float:
        prices = price_map or {}
        holdings_value = 0.0

        for symbol, quantity in self.holdings.items():
            price = float(prices.get(symbol, 0.0))
            holdings_value += quantity * price

        total_equity = float(self.cash + holdings_value)

        if total_equity > self.peak_equity:
            self.peak_equity = total_equity

        return total_equity

    def get_total_value(
        self,
        price_map: Optional[Dict[str, float]] = None,
    ) -> float:
        return self.calculate_total_equity(price_map)

    def calculate_drawdown(self, equity: float) -> float:
        current_equity = float(equity)

        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            return 0.0

        if self.peak_equity <= 0:
            return 0.0

        return float(
            (self.peak_equity - current_equity)
            / self.peak_equity
            * 100.0
        )

    def can_allocate(self, *args: Any, **kwargs: Any) -> Any:
        """
        New API:
            can_allocate(symbol, amount, price_map) -> dict

        Legacy API:
            can_allocate(cost)
            can_allocate(symbol, amount)
            can_allocate(symbol, quantity, price)
            -> bool
        """
        if len(args) >= 3 and isinstance(args[2], dict):
            symbol = self._symbol(args[0])
            additional_amount = float(args[1])
            prices = args[2]

            if additional_amount < 0:
                return {
                    "allowed": False,
                    "reason": "Amount cannot be negative",
                }

            total_equity = self.calculate_total_equity(prices)

            if total_equity <= 0:
                return {
                    "allowed": False,
                    "reason": "Portfolio equity must be positive",
                }

            existing_value = (
                self.get_holding_quantity(symbol)
                * float(prices.get(symbol, 0.0))
            )

            proposed_value = existing_value + additional_amount
            max_value = total_equity * self.max_asset_weight

            allowed = proposed_value <= max_value

            return {
                "allowed": bool(allowed),
                "reason": (
                    ""
                    if allowed
                    else "Exceeds max asset weight"
                ),
                "symbol": symbol,
                "current_asset_value": float(existing_value),
                "proposed_asset_value": float(proposed_value),
                "max_asset_value": float(max_value),
            }

        cost = 0.0

        if len(args) == 1:
            cost = float(args[0])
        elif len(args) == 2:
            cost = float(args[1])
        elif len(args) >= 3:
            cost = float(args[1]) * float(args[2])
        elif "cost" in kwargs:
            cost = float(kwargs["cost"])
        elif "quantity" in kwargs and "price" in kwargs:
            cost = float(kwargs["quantity"]) * float(kwargs["price"])
        elif "amount" in kwargs:
            cost = float(kwargs["amount"])

        return self.cash >= cost

    def record_buy(
        self,
        symbol: str,
        quantity: float,
        price: float,
        fee: float = 0.0,
    ) -> Dict[str, Any]:
        sym = self._symbol(symbol)
        qty = float(quantity)
        unit_price = float(price)
        fee_value = float(fee)

        if qty <= 0 or unit_price <= 0 or fee_value < 0:
            raise ValueError("quantity and price must be positive")

        total_cost = qty * unit_price + fee_value

        if self.cash < total_cost:
            return {
                "status": "FAILED",
                "reason": "Insufficient funds",
                "total_cost": float(total_cost),
            }

        previous_qty = self.holdings.get(sym, 0.0)
        previous_basis = self._asset_cost_basis.get(sym, 0.0)

        self.cash -= total_cost
        self.holdings[sym] = previous_qty + qty
        self._asset_cost_basis[sym] = previous_basis + total_cost

        record = {
            "action": "BUY",
            "symbol": sym,
            "quantity": qty,
            "price": unit_price,
            "fee": fee_value,
            "total_cost": float(total_cost),
            "remaining_cash": float(self.cash),
        }

        self.history.append(record)
        return record

    def record_sell(
        self,
        symbol: str,
        quantity: float,
        price: float,
        fee: float = 0.0,
    ) -> Dict[str, Any]:
        sym = self._symbol(symbol)
        qty = float(quantity)
        unit_price = float(price)
        fee_value = float(fee)

        if qty <= 0 or unit_price <= 0 or fee_value < 0:
            raise ValueError("quantity and price must be positive")

        current_qty = self.holdings.get(sym, 0.0)

        if current_qty < qty:
            return {
                "status": "FAILED",
                "reason": "Insufficient holdings",
                "holding": float(current_qty),
            }

        current_basis = self._asset_cost_basis.get(sym, 0.0)
        cost_basis_sold = current_basis * (qty / current_qty)
        total_proceeds = qty * unit_price - fee_value
        realized_pnl = total_proceeds - cost_basis_sold

        remaining_qty = current_qty - qty
        remaining_basis = current_basis - cost_basis_sold

        if remaining_qty <= 1e-12:
            self.holdings.pop(sym, None)
            self._asset_cost_basis.pop(sym, None)
        else:
            self.holdings[sym] = remaining_qty
            self._asset_cost_basis[sym] = remaining_basis

        self.cash += total_proceeds

        record = {
            "action": "SELL",
            "symbol": sym,
            "quantity": qty,
            "price": unit_price,
            "fee": fee_value,
            "total_proceeds": float(total_proceeds),
            "realized_pnl": float(realized_pnl),
            "remaining_cash": float(self.cash),
        }

        self.history.append(record)
        return record

    def get_summary(
        self,
        price_map: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        total_equity = self.calculate_total_equity(price_map)
        drawdown_pct = self.calculate_drawdown(total_equity)

        return {
            "cash": float(self.cash),
            "holdings": self.holdings.copy(),
            "total_equity": float(total_equity),
            "peak_equity": float(self.peak_equity),
            "drawdown_pct": float(drawdown_pct),
            "unrealized_profit": float(
                total_equity - self.initial_cash
            ),
        }

    def get_portfolio_summary(
        self,
        price_map: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        summary = self.get_summary(price_map)

        return {
            "cash": summary["cash"],
            "holdings": summary["holdings"],
            "total_value": summary["total_equity"],
            "unrealized_profit": summary["unrealized_profit"],
        }
