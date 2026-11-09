from __future__ import annotations

import time
from typing import Any, Dict


class WallexPaperAdapter:
    def __init__(self, initial_balance: float = 1000.0) -> None:
        self.balance = initial_balance
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self._order_counter = 0

    def get_ticker(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        # Fallback to realistic mock price if network/API fails or offline in Iran
        try:
            # Here we can add real API call later; for paper robustness, return robust mock feed if 0
            return {"symbol": symbol, "last_price": 65420.0, "bid": 65415.0, "ask": 65425.0}
        except Exception:
            return {"symbol": symbol, "last_price": 65420.0, "bid": 65415.0, "ask": 65425.0}

    def get_balance(self) -> float:
        return self.balance

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float,
    ) -> Dict[str, Any]:
        self._order_counter += 1
        order_id = f"wallex_paper_{self._order_counter}"
        order = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "price": price,
            "status": "FILLED",
            "timestamp": time.time(),
        }
        self.orders[order_id] = order
        return order
