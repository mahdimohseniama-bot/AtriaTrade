"""مدیریت سفارش‌ها (Paper / Testnet) — AtriaTrade
شامل تعریف سمت، نوع و وضعیت سفارش به‌همراه کلاس OrderManager
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class Order:
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    order_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: OrderStatus = OrderStatus.PENDING
    filled_price: Optional[float] = None
    filled_quantity: Optional[float] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    filled_at: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "status": self.status.value,
            "filled_price": self.filled_price,
            "filled_quantity": self.filled_quantity,
            "created_at": self.created_at,
            "filled_at": self.filled_at,
            "reason": self.reason,
        }


def _coerce_side(side) -> OrderSide:
    """پذیرش OrderSide یا رشته BUY/SELL"""
    if isinstance(side, OrderSide):
        return side
    if isinstance(side, str):
        return OrderSide(side.upper())
    raise ValueError("side باید OrderSide یا رشته BUY/SELL باشد")


def _coerce_type(order_type) -> OrderType:
    """پذیرش OrderType یا رشته معتبر"""
    if isinstance(order_type, OrderType):
        return order_type
    if isinstance(order_type, str):
        return OrderType(order_type.upper())
    raise ValueError("order_type باید OrderType یا رشته معتبر باشد")


class OrderManager:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def create_order(
        self,
        symbol: str,
        side,
        order_type,
        quantity: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Order:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol باید یک رشته غیرخالی باشد")
        side = _coerce_side(side)
        order_type = _coerce_type(order_type)
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            raise ValueError("quantity باید عددی بزرگ‌تر از صفر باشد")
        if order_type == OrderType.LIMIT and (price is None or price <= 0):
            raise ValueError("سفارش LIMIT به price معتبر نیاز دارد")

        order = Order(
            symbol=symbol.strip().upper(),
            side=side,
            order_type=order_type,
            quantity=float(quantity),
            price=float(price) if price is not None else None,
            stop_loss=float(stop_loss) if stop_loss is not None else None,
            take_profit=float(take_profit) if take_profit is not None else None,
        )
        self._orders[order.order_id] = order
        return order

    def fill_order(
        self,
        order_id: str,
        fill_price: float,
        fill_quantity: Optional[float] = None,
    ) -> Order:
        order = self.get_order(order_id)
        if order.status not in (OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED):
            raise ValueError(f"فقط سفارش در انتظار قابل Fill است؛ وضعیت فعلی: {order.status.value}")
        if fill_price is None or fill_price <= 0:
            raise ValueError("fill_price باید بزرگ‌تر از صفر باشد")
        qty = order.quantity if fill_quantity is None else fill_quantity
        if qty <= 0 or qty > order.quantity:
            raise ValueError("fill_quantity نامعتبر است")

        order.filled_price = float(fill_price)
        order.filled_quantity = float(qty)
        order.filled_at = datetime.now(timezone.utc).isoformat()
        order.status = OrderStatus.FILLED if qty == order.quantity else OrderStatus.PARTIALLY_FILLED
        return order

    def cancel_order(self, order_id: str, reason: Optional[str] = None) -> Order:
        order = self.get_order(order_id)
        if order.status == OrderStatus.FILLED:
            raise ValueError("سفارش Fill‌شده قابل لغو نیست")
        order.status = OrderStatus.CANCELED
        order.reason = reason
        return order

    def reject_order(self, order_id: str, reason: str) -> Order:
        order = self.get_order(order_id)
        order.status = OrderStatus.REJECTED
        order.reason = reason
        return order

    def get_order(self, order_id: str) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise KeyError(f"سفارشی با شناسه {order_id} یافت نشد")
        return order

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        orders = [o for o in self._orders.values() if o.status == OrderStatus.PENDING]
        if symbol:
            orders = [o for o in orders if o.symbol == symbol.upper()]
        return orders

    def get_all_orders(self, symbol: Optional[str] = None) -> list:
        orders = list(self._orders.values())
        if symbol:
            orders = [o for o in orders if o.symbol == symbol.upper()]
        return orders

    def get_status(self) -> dict:
        return {
            "total_orders": len(self._orders),
            "open_orders": len(self.get_open_orders()),
            "filled_orders": sum(1 for o in self._orders.values() if o.status == OrderStatus.FILLED),
            "canceled_orders": sum(1 for o in self._orders.values() if o.status == OrderStatus.CANCELED),
            "rejected_orders": sum(1 for o in self._orders.values() if o.status == OrderStatus.REJECTED),
        }
