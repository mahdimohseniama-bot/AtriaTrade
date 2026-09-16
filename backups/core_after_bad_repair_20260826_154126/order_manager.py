import time
from enum import Enum
from typing import Any, Dict, List, Optional


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderStatus(str, Enum):
    OPEN = "OPEN"
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Order:
    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: Any,
        order_type: Any,
        quantity: float,
        price: float = 0.0,
        status: Any = "PENDING",
        **kwargs: Any,
    ) -> None:
        self.order_id = str(order_id)
        self.symbol = str(symbol).upper()
        self.side = str(getattr(side, "value", side)).upper()
        self.order_type = str(getattr(order_type, "value", order_type)).upper()
        self.quantity = float(quantity)
        self.size = self.quantity
        self.price = float(price or 0.0)
        self.status = str(getattr(status, "value", status)).upper()
        self.created_at = time.time()
        self.filled_at = None
        self.executed_price = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "order_type": self.order_type,
            "quantity": self.quantity,
            "size": self.size,
            "price": self.price,
            "status": self.status,
            "created_at": self.created_at,
            "filled_at": self.filled_at,
            "executed_price": self.executed_price,
        }

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


class OrderManager:
    def __init__(self, **kwargs: Any) -> None:
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []

    def create_order(
        self,
        symbol: str,
        side: Any,
        order_type: Any = "MARKET",
        quantity: float = 0.0,
        price: Optional[float] = None,
        **kwargs: Any,
    ) -> Order:
        side_value = str(getattr(side, "value", side)).strip().upper()
        type_value = str(
            getattr(order_type, "value", order_type or "MARKET")
        ).strip().upper()

        amount = kwargs.get("amount", kwargs.get("size", quantity))
        order_price = kwargs.get("entry_price", price)

        if side_value not in {"BUY", "SELL"}:
            raise ValueError(f"Invalid order side: {side}")

        if type_value not in {"MARKET", "LIMIT", "STOP"}:
            raise ValueError(f"Invalid order type: {order_type}")

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise ValueError("Quantity must be numeric")

        if amount <= 0:
            raise ValueError("Quantity must be greater than zero")

        if order_price is None:
            order_price = 0.0

        try:
            order_price = float(order_price)
        except (TypeError, ValueError):
            raise ValueError("Price must be numeric")

        if type_value in {"LIMIT", "STOP"} and order_price <= 0:
            raise ValueError("Limit/stop order requires a positive price")

        order_id = str(kwargs.get(
            "order_id",
            f"ord_{len(self.orders) + len(self.order_history) + 1}_{int(time.time() * 1000)}",
        ))

        # LIMIT در این پروژه باید OPEN باشد تا process_limit_orders آن را ببیند.
        initial_status = OrderStatus.OPEN.value if type_value == "LIMIT" else OrderStatus.PENDING.value

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side_value,
            order_type=type_value,
            quantity=amount,
            price=order_price,
            status=initial_status,
        )
        self.orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        return self.orders.get(str(order_id))

    def cancel_order(self, order_id: str) -> Optional[Order]:
        order = self.orders.get(str(order_id))
        if order is None:
            return None
        order.status = OrderStatus.CANCELLED.value
        return order

    def get_open_orders(self) -> List[Order]:
        return [
            order for order in self.orders.values()
            if order.status in {OrderStatus.OPEN.value, OrderStatus.PENDING.value}
        ]
