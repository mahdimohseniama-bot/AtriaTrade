"""
AtriaTrade - Portfolio Manager
Manages portfolio balances, holdings, asset allocation, and trade recording.
"""

from typing import Dict, Any, Optional

class PortfolioManager:
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = float(initial_balance)
        self.cash = float(initial_balance)
        self.holdings: Dict[str, float] = {}
        self.history: list = []

    @property
    def balance(self) -> float:
        return self.cash

    def can_allocate(self, *args, **kwargs) -> bool:
        """
        Supports:
        can_allocate(symbol, amount)
        can_allocate(symbol, quantity, price)
        can_allocate(cost)
        or keyword arguments.
        """
        cost = 0.0
        if len(args) == 1:
            cost = float(args[0])
        elif len(args) == 2:
            cost = float(args[1])
        elif len(args) >= 3:
            cost = float(args[1]) * float(args[2])
        else:
            if "cost" in kwargs:
                cost = float(kwargs["cost"])
            elif "quantity" in kwargs and "price" in kwargs:
                cost = float(kwargs["quantity"]) * float(kwargs["price"])
            elif "amount" in kwargs:
                cost = float(kwargs["amount"])

        return self.cash >= cost

    def record_buy(self, symbol: str, quantity: float, price: float, fee: float = 0.0) -> Dict[str, Any]:
        total_cost = (float(quantity) * float(price)) + float(fee)
        sym = symbol.upper()
        if self.cash < total_cost:
            return {"status": "FAILED", "reason": "Insufficient funds", "total_cost": total_cost}

        self.cash -= total_cost
        self.holdings[sym] = self.holdings.get(sym, 0.0) + float(quantity)
        record = {
            "action": "BUY",
            "symbol": sym,
            "quantity": float(quantity),
            "price": float(price),
            "fee": float(fee),
            "total_cost": total_cost,
            "remaining_cash": self.cash
        }
        self.history.append(record)
        return record

    def record_sell(self, symbol: str, quantity: float, price: float, fee: float = 0.0) -> Dict[str, Any]:
        sym = symbol.upper()
        current_holding = self.holdings.get(sym, 0.0)
        qty = float(quantity)
        if current_holding < qty:
            return {"status": "FAILED", "reason": "Insufficient holdings", "holding": current_holding}

        total_proceeds = (qty * float(price)) - float(fee)
        self.holdings[sym] = current_holding - qty
        if self.holdings[sym] <= 0:
            del self.holdings[sym]
        self.cash += total_proceeds
        record = {
            "action": "SELL",
            "symbol": sym,
            "quantity": qty,
            "price": float(price),
            "fee": float(fee),
            "total_proceeds": total_proceeds,
            "remaining_cash": self.cash
        }
        self.history.append(record)
        return record

    def get_total_value(self, price_map: Optional[Dict[str, float]] = None) -> float:
        price_map = price_map or {}
        assets_val = 0.0
        for sym, qty in self.holdings.items():
            assets_val += qty * price_map.get(sym, 0.0)
        return self.cash + assets_val

    def get_portfolio_summary(self, price_map: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        total_val = self.get_total_value(price_map)
        return {
            "cash": self.cash,
            "holdings": self.holdings.copy(),
            "total_value": total_val,
            "unrealized_profit": total_val - self.initial_balance
        }
