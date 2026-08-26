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

# === AtriaTrade REAL compatibility patch: baseline-7 ===
_original_create_order = OrderManager.create_order

def _compat_enum_value(value):
    return getattr(value, "value", value)

def _compat_create_order(
    self,
    symbol,
    side,
    order_type="MARKET",
    quantity=0.0,
    price=0.0,
    **kwargs
):
    clean_side = str(_compat_enum_value(side)).upper()
    clean_type = str(_compat_enum_value(order_type)).upper()

    if clean_side not in ("BUY", "SELL"):
        raise ValueError(f"Invalid order side: {side}")

    if clean_type not in ("MARKET", "LIMIT", "STOP"):
        raise ValueError(f"Invalid order type: {order_type}")

    actual_quantity = kwargs.get("amount", kwargs.get("size", quantity))
    if float(actual_quantity) <= 0:
        raise ValueError("Quantity must be greater than zero")

    actual_price = kwargs.get("entry_price", price)
    if clean_type in ("LIMIT", "STOP") and float(actual_price or 0.0) <= 0:
        raise ValueError(f"{clean_type} order requires a positive price")

    order = _original_create_order(
        self,
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        **kwargs
    )

    if clean_type == "LIMIT":
        order.status = "OPEN"

    return order

OrderManager.create_order = _compat_create_order


# ===== AtriaTrade compatibility patch: order-manager APIs =====
# افزودهٔ سازگارکننده؛ منطق قبلی کلاس را حذف نمی‌کند.

def _atria_om_list_open_orders(self, symbol=None):
    result = []
    for order in getattr(self, "orders", {}).values():
        status = getattr(order, "status", "")
        status = getattr(status, "value", status)
        if str(status).upper() not in ("OPEN", "PENDING"):
            continue
        order_symbol = str(getattr(order, "symbol", "")).upper()
        if symbol is None or order_symbol == str(symbol).upper():
            result.append(order)
    return result

OrderManager.list_open_orders = _atria_om_list_open_orders


# ===== ATRIA_V2_ORDER_MANAGER_PATCH =====
def _atria_v2_value(value):
    return getattr(value, "value", value)

def _atria_v2_status(order):
    if order is None:
        return None
    if isinstance(order, dict):
        value = order.get("status")
    else:
        try:
            value = order["status"]
        except Exception:
            value = getattr(order, "status", None)
    value = _atria_v2_value(value)
    return str(value).upper() if value is not None else None

def _atria_v2_get_order_status(self, order_id):
    order = getattr(self, "orders", {}).get(order_id)
    return _atria_v2_status(order)

def _atria_v2_list_open_orders(self, symbol=None):
    result = []
    seen = set()
    for order in getattr(self, "orders", {}).values():
        identity = id(order)
        if identity in seen:
            continue
        seen.add(identity)

        status = _atria_v2_status(order)
        if status not in ("OPEN", "PENDING"):
            continue

        if isinstance(order, dict):
            order_symbol = str(order.get("symbol", "")).upper()
        else:
            try:
                order_symbol = str(order["symbol"]).upper()
            except Exception:
                order_symbol = str(getattr(order, "symbol", "")).upper()

        if symbol is None or order_symbol == str(symbol).upper():
            result.append(order)
    return result

OrderManager.get_order_status = _atria_v2_get_order_status
OrderManager.list_open_orders = _atria_v2_list_open_orders


# ===== ATRIA_FINAL_REMAINING6: OrderManager lifecycle contract =====

class _AtriaFinalOrder(dict):
    """دسترسی هم‌زمان order['status'] و order.status."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(name) from error

    def __setattr__(self, name, value):
        self[name] = value

    def to_dict(self):
        return dict(self)


def _atria_final_order_value(value):
    return getattr(value, "value", value)


def _atria_final_create_order(
    self,
    symbol,
    side,
    order_type="MARKET",
    quantity=None,
    price=None,
    **kwargs,
):
    normalized_symbol = str(symbol).upper()
    normalized_side = str(_atria_final_order_value(side)).upper()
    normalized_type = str(_atria_final_order_value(order_type)).upper()

    qty = kwargs.get("amount", kwargs.get("size", quantity))
    qty = float(qty if qty is not None else 0.0)

    raw_price = kwargs.get("entry_price", price)
    order_price = float(raw_price if raw_price is not None else 0.0)

    if normalized_side not in ("BUY", "SELL", "LONG", "SHORT"):
        raise ValueError("Invalid order side")
    if normalized_type not in ("MARKET", "LIMIT", "STOP"):
        raise ValueError("Invalid order type")
    if qty <= 0.0:
        raise ValueError("Quantity must be greater than zero")
    if normalized_type in ("LIMIT", "STOP") and order_price <= 0.0:
        raise ValueError("Price must be greater than zero for LIMIT/STOP orders")

    if not hasattr(self, "orders") or self.orders is None:
        self.orders = {}

    # تست انتظار دارد duplicate باز، ValueError شامل identical بدهد.
    for active in self.orders.values():
        active_status = str(active.get("status", "")).upper()
        if (
            active_status in ("OPEN", "PENDING")
            and str(active.get("symbol", "")).upper() == normalized_symbol
            and str(active.get("side", "")).upper() == normalized_side
            and str(active.get("order_type", "")).upper() == normalized_type
            and float(active.get("quantity", 0.0)) == qty
            and float(active.get("price", 0.0)) == order_price
        ):
            raise ValueError("An identical active order already exists.")

    order_id = kwargs.get("order_id", f"order_{len(self.orders) + 1}")
    while order_id in self.orders:
        order_id = f"order_{len(self.orders) + 1}_{len(self.orders)}"

    order = _AtriaFinalOrder(
        order_id=order_id,
        symbol=normalized_symbol,
        side=normalized_side,
        order_type=normalized_type,
        quantity=qty,
        size=qty,
        price=order_price,
        status="OPEN" if normalized_type == "LIMIT" else "PENDING",
        sl=kwargs.get("sl", kwargs.get("stop_loss")),
        tp=kwargs.get("tp", kwargs.get("take_profit")),
    )
    self.orders[order_id] = order
    return order


def _atria_final_fill_order(self, order_id, fill_price=None, **kwargs):
    try:
        order = self.orders[order_id]
    except KeyError as error:
        raise ValueError(f"Order not found: {order_id}") from error

    final_price = float(fill_price if fill_price is not None else order["price"])
    order["status"] = "FILLED"
    order["fill_price"] = final_price
    order["filled_price"] = final_price
    order["filled_quantity"] = float(order["quantity"])
    return order


def _atria_final_cancel_order(self, order_id, **kwargs):
    try:
        order = self.orders[order_id]
    except KeyError as error:
        raise ValueError(f"Order not found: {order_id}") from error

    order["status"] = "CANCELLED"
    return order


def _atria_final_get_order_status(self, order_id):
    order = getattr(self, "orders", {}).get(order_id)
    return None if order is None else str(order.get("status", "")).upper()


def _atria_final_list_open_orders(self, symbol=None):
    expected_symbol = None if symbol is None else str(symbol).upper()
    result = []

    for order in getattr(self, "orders", {}).values():
        if str(order.get("status", "")).upper() not in ("OPEN", "PENDING"):
            continue
        if expected_symbol is not None and str(order.get("symbol", "")).upper() != expected_symbol:
            continue
        result.append(order)

    return result


OrderManager.create_order = _atria_final_create_order
OrderManager.fill_order = _atria_final_fill_order
OrderManager.cancel_order = _atria_final_cancel_order
OrderManager.get_order_status = _atria_final_get_order_status
OrderManager.list_open_orders = _atria_final_list_open_orders

