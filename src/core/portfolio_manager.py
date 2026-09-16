import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self, initial_cash: float = 10000.0, max_asset_weight: float = 0.5, **kwargs):
        self.cash: float = float(kwargs.get("initial_balance", initial_cash))
        self.max_asset_weight: float = float(max_asset_weight)
        self.positions: Dict[str, Dict[str, float]] = {}
        self.peak_equity: float = self.cash
        self.equity: float = self.cash
        self.drawdown: float = 0.0
        self.realized_pnl: float = 0.0
        self.trade_count: int = 0

    @property
    def holdings(self) -> Dict[str, Dict[str, float]]:
        return self.positions

    def get_balance(self) -> float:
        return self.cash

    def get_position(self, symbol: str) -> float:
        pos = self.positions.get(symbol, 0.0)
        if isinstance(pos, dict):
            return float(pos.get("quantity", 0.0))
        return float(pos)

    def get_holding_quantity(self, symbol: str) -> float:
        return self.get_position(symbol)

    def get_equity(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        if current_prices is None:
            current_prices = {}
        total = self.cash
        for sym, pos in self.positions.items():
            qty = pos.get("quantity", 0.0) if isinstance(pos, dict) else float(pos)
            price = current_prices.get(sym, pos.get("avg_price", 0.0) if isinstance(pos, dict) else 0.0)
            total += qty * price
        self.equity = total
        if total > self.peak_equity:
            self.peak_equity = total
        self.calculate_drawdown(self.equity)
        return self.equity

    def calculate_total_equity(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        return self.get_equity(current_prices)

    def calculate_drawdown(self, equity_val: Optional[Any] = None) -> float:
        if isinstance(equity_val, (int, float)):
            current_eq = float(equity_val)
        elif isinstance(equity_val, dict):
            current_eq = self.get_equity(equity_val)
        else:
            current_eq = self.equity

        if self.peak_equity <= 0:
            self.drawdown = 0.0
            return 0.0

        dd = ((self.peak_equity - current_eq) / self.peak_equity) * 100.0
        self.drawdown = max(0.0, dd)
        return self.drawdown

    def get_summary(self, current_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        equity = self.get_equity(current_prices)
        dd_pct = self.calculate_drawdown(equity)
        return {
            "cash": self.cash,
            "total_equity": equity,
            "equity": equity,
            "drawdown": dd_pct / 100.0,
            "drawdown_pct": dd_pct,
            "peak_equity": self.peak_equity,
            "realized_pnl": self.realized_pnl,
            "trade_count": self.trade_count,
            "positions": self.positions
        }

    def can_allocate(self, symbol: str, amount: float, current_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        equity = self.get_equity(current_prices)
        max_allowed = equity * self.max_asset_weight
        current_holding_val = 0.0
        if symbol in self.positions:
            pos = self.positions[symbol]
            qty = pos.get("quantity", 0.0) if isinstance(pos, dict) else float(pos)
            px = (current_prices or {}).get(symbol, pos.get("avg_price", 0.0) if isinstance(pos, dict) else 0.0)
            current_holding_val = qty * px

        if (current_holding_val + amount) > max_allowed:
            return {
                "allowed": False,
                "reason": f"Exceeds max asset weight limit ({self.max_asset_weight * 100}%)"
            }
        if amount > self.cash:
            return {
                "allowed": False,
                "reason": "Insufficient cash balance"
            }
        return {"allowed": True, "reason": "OK"}

    def record_buy(self, symbol: str, quantity: float, price: float, fee: float = 0.0) -> Dict[str, Any]:
        total_cost = (quantity * price) + fee
        if self.cash < total_cost:
            return {
                "status": "REJECTED",
                "reason": "Insufficient cash to cover cost and fees"
            }

        self.cash -= total_cost
        if symbol not in self.positions:
            self.positions[symbol] = {"quantity": quantity, "avg_price": price}
        else:
            current_pos = self.positions[symbol]
            old_qty = current_pos["quantity"]
            old_avg = current_pos["avg_price"]
            new_qty = old_qty + quantity
            new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty if new_qty > 0 else price
            self.positions[symbol] = {"quantity": new_qty, "avg_price": new_avg}

        self.trade_count += 1
        return {
            "status": "FILLED",
            "action": "BUY",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "fee": fee,
            "total_cost": total_cost,
            "cost": total_cost,
            "cash": self.cash
        }

    def record_sell(self, symbol: str, quantity: float, price: float, fee: float = 0.0) -> Dict[str, Any]:
        current_qty = self.get_position(symbol)
        if current_qty < quantity or quantity <= 0:
            return {
                "status": "REJECTED",
                "reason": "Insufficient position quantity to sell"
            }

        pos = self.positions[symbol]
        avg_price = pos["avg_price"]
        pnl = (price - avg_price) * quantity - fee

        proceeds = (quantity * price) - fee
        self.cash += proceeds
        self.realized_pnl += pnl

        remaining_qty = current_qty - quantity
        if remaining_qty <= 1e-8:
            self.positions.pop(symbol, None)
        else:
            self.positions[symbol]["quantity"] = remaining_qty

        self.trade_count += 1
        return {
            "status": "FILLED",
            "action": "SELL",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "fee": fee,
            "realized_pnl": pnl,
            "cash": self.cash
        }
