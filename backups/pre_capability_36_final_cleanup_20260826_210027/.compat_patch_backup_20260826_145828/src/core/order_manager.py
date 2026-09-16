"""AtriaTrade - Order Manager & Order Data Structure"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, List, Optional
import time


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Order:
    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float,
        status: str = "PENDING",
    ):
        self.order_id = str(order_id)
        self.symbol = symbol.upper()
        self.side = side.upper()
        self.order_type = order_type.upper()
        self.quantity = float(quantity)
        self.price = float(price)
        self.status = status.upper()
        self.created_at = time.time()
        self.filled_at: Optional[float] = None
        self.executed_price: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "order_type": self.order_type,
            "quantity": self.quantity,
            "price": self.price,
            "status": self.status,
            "created_at": self.created_at,
            "filled_at": self.filled_at,
            "executed_price": self.executed_price,
        }

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __setitem__(self, key: str, value: Any):
        if hasattr(self, key):
            setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)


class OrderManager:
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str = "MARKET",
        quantity: float = 0.0,
        price: float = 0.0,
        **kwargs,
    ) -> Order:
        amount = kwargs.get("amount", kwargs.get("size", quantity))
        unit_price = kwargs.get("entry_price", price)
        order_id = kwargs.get(
            "order_id",
            f"ord_{len(self.orders) + len(self.order_history) + 1}_{int(time.time() * 1000)}",
        )

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=amount,
            price=unit_price,
        )
        self.orders[order.order_id] = order
        return order

    def update_order_status(
        self,
        order_id: str,
        status: str,
        executed_price: Optional[float] = None,
    ) -> Optional[Order]:
        if order_id in self.orders:
            order = self.orders[order_id]
            order.status = status.upper()
            if executed_price is not None:
                order.executed_price = float(executed_price)
            if status.upper() in ["FILLED", "CANCELLED", "REJECTED"]:
                order.filled_at = time.time()
                self.order_history.append(self.orders.pop(order_id))
            return order
        return None

    def get_order(self, order_id: str) -> Optional[Order]:
        if order_id in self.orders:
            return self.orders[order_id]
        for ord_item in self.order_history:
            if ord_item.order_id == order_id:
                return ord_item
        return None

    def get_open_orders(self) -> List[Order]:
        return list(self.orders.values())
