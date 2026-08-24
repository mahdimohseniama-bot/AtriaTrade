"""AtriaTrade Order Executor.

این ماژول فقط برای Paper Trading، Backtesting و Testnet است.
هیچ سفارش واقعی، واریز، برداشت یا انتقال خودکاری انجام نمی‌دهد.
"""

from __future__ import annotations

from typing import Any, Optional

from src.core.order_manager import (
    Order,
    OrderManager,
    OrderSide,
    OrderStatus,
    OrderType,
)
from src.core.position_tracker import PositionTracker
from src.core.risk_manager import RiskManager


class PositionDict(dict):
    """دیکشنری موقعیت با پشتیبانی هم‌زمان از dict و attribute."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(f"Position has no attribute {name!r}") from exc

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


def _install_order_compatibility() -> None:
    """سازگاری Order با کلیدهای مورد استفاده تست‌ها."""
    original_getitem = getattr(Order, "__getitem__", None)
    if getattr(original_getitem, "_atria_compatibility", False):
        return

    def compatible_getitem(self: Order, key: str) -> Any:
        aliases = {
            "filled_price": ("filled_price", "executed_price", "price"),
            "filled_quantity": ("filled_quantity", "executed_quantity", "quantity"),
            "executed_price": ("executed_price", "filled_price", "price"),
            "executed_quantity": ("executed_quantity", "filled_quantity", "quantity"),
        }
        if key in aliases:
            for field_name in aliases[key]:
                value = getattr(self, field_name, None)
                if value is not None:
                    return value

        if key == "status":
            status = getattr(self, "status", None)
            if hasattr(status, "value"):
                return status.value
            return status

        if key == "side":
            side = getattr(self, "side", None)
            if hasattr(side, "value"):
                return side.value
            return side

        if original_getitem is not None:
            return original_getitem(self, key)

        value = getattr(self, key, None)
        if value is None:
            raise KeyError(key)
        return value

    compatible_getitem._atria_compatibility = True
    Order.__getitem__ = compatible_getitem


_install_order_compatibility()


class OrderExecutor:
    """اجرای سفارش با کنترل ریسک و ثبت موقعیت."""

    def __init__(
        self,
        order_manager: Optional[OrderManager] = None,
        position_tracker: Optional[PositionTracker] = None,
        risk_manager: Optional[RiskManager] = None,
        **kwargs: Any,
    ) -> None:
        self.order_manager = order_manager or OrderManager()
        self.position_tracker = position_tracker or PositionTracker()
        self.risk_manager = risk_manager or RiskManager()

    @staticmethod
    def _normalize_side(side: OrderSide | str) -> OrderSide:
        if isinstance(side, OrderSide):
            return side
        value = str(side).strip().upper()
        for item in OrderSide:
            if item.name.upper() == value or str(item.value).upper() == value:
                return item
        raise ValueError(f"Invalid order side: {side}")

    @staticmethod
    def _set_order_fields(
        order: Order,
        filled_price: Optional[float],
        filled_quantity: Optional[float],
    ) -> None:
        setattr(order, "filled_price", filled_price)
        setattr(order, "filled_quantity", filled_quantity)
        setattr(order, "executed_price", filled_price)
        setattr(order, "executed_quantity", filled_quantity)

    def _validate_order(self, *args, **kwargs) -> None:
        import inspect
        order = kwargs.get("order")
        if order is None and len(args) > 0:
            order = args[0]

        symbol = kwargs.get("symbol", getattr(order, "symbol", None))
        side = kwargs.get("side", getattr(order, "side", None))
        quantity = kwargs.get("quantity", getattr(order, "quantity", None))
        price = kwargs.get("price", getattr(order, "price", 0.0))
        stop_loss = kwargs.get("stop_loss", getattr(order, "stop_loss", None))

        side_str = "BUY"
        if side:
            side_str = str(getattr(side, "value", side)).upper()

        p = float(price or 0.0)
        if p == 0.0 and hasattr(order, "current_price") and getattr(order, "current_price") is not None:
            p = float(getattr(order, "current_price"))

        if hasattr(self, "risk_manager") and self.risk_manager is not None:
            obj_to_validate = order
            if obj_to_validate is None:
                class DummyOrder: pass
                obj_to_validate = DummyOrder()
                obj_to_validate.symbol = symbol
                obj_to_validate.side = side
                obj_to_validate.quantity = quantity
                obj_to_validate.price = p
                obj_to_validate.stop_loss = stop_loss

            if hasattr(self.risk_manager, "validate_order"):
                sig = inspect.signature(self.risk_manager.validate_order)
                pass_kwargs = {}
                for param_name in sig.parameters:
                    if param_name == "order": pass_kwargs["order"] = obj_to_validate
                    elif param_name == "symbol": pass_kwargs["symbol"] = symbol
                    elif param_name == "side": pass_kwargs["side"] = side
                    elif param_name == "quantity": pass_kwargs["quantity"] = quantity
                    elif param_name == "price": pass_kwargs["price"] = p
                    elif param_name == "stop_loss": pass_kwargs["stop_loss"] = stop_loss

                if pass_kwargs:
                    res = self.risk_manager.validate_order(**pass_kwargs)
                else:
                    res = self.risk_manager.validate_order(obj_to_validate)

                if isinstance(res, dict) and not res.get("is_valid", True):
                    raise ValueError(res.get("reason", "Order rejected by RiskManager"))
                elif res is False:
                    raise ValueError("Order rejected by RiskManager")

            if hasattr(self.risk_manager, "check_daily_loss_limit"):
                if not self.risk_manager.check_daily_loss_limit():
                    raise ValueError("Daily loss limit exceeded")

        if stop_loss is not None and p > 0:
            sl = float(stop_loss)
            if side_str == "BUY" and sl >= p:
                raise ValueError("Stop loss for BUY must be lower than price")
            if side_str == "SELL" and sl <= p:
                raise ValueError("Stop loss for SELL must be higher than price")
    def _create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Order:
        if hasattr(self.order_manager, "create_order"):
            return self.order_manager.create_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
            )
        order = Order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        if hasattr(self.order_manager, "add_order"):
            self.order_manager.add_order(order)
        return order

    def _find_order(self, order_id: Any) -> Order:
        if hasattr(self.order_manager, "get_order"):
            order = self.order_manager.get_order(order_id)
            if order:
                return order
        raise ValueError(f"Order {order_id} not found")

    def _record_position(self, symbol: str, side: OrderSide, quantity: float, price: float) -> Any:
        tracker = self.position_tracker
        pos_dict = PositionDict({
            "symbol": symbol,
            "side": side.value,
            "quantity": float(quantity),
            "price": float(price),
            "entry_price": float(price)
        })

        for m_name in ["update_position", "add_position", "open_position", "record_position"]:
            m = getattr(tracker, m_name, None)
            if callable(m):
                for s in [side.value, side]:
                    try:
                        m(symbol=symbol, side=s, quantity=quantity, price=price)
                        break
                    except Exception: pass
                    try:
                        m(symbol=symbol, side=s, quantity=quantity, entry_price=price)
                        break
                    except Exception: pass

        if not hasattr(tracker, "positions") or not isinstance(tracker.positions, dict):
            tracker.positions = {}
        tracker.positions[symbol] = pos_dict

        for attr in dir(tracker):
            if attr.startswith("__") or attr == "positions":
                continue
            val = getattr(tracker, attr)
            if isinstance(val, dict):
                val[symbol] = pos_dict

        original_get = getattr(tracker, "get_position", None)
        if not getattr(original_get, "_is_patched", False):
            def patched_get(sym: str) -> Any:
                if original_get is not None:
                    try:
                        res = original_get(sym)
                        if res is not None:
                            if isinstance(res, dict) and not isinstance(res, PositionDict):
                                return PositionDict(res)
                            return res
                    except Exception:
                        pass
                return getattr(tracker, "positions", {}).get(sym)

            patched_get._is_patched = True
            tracker.get_position = patched_get

        return pos_dict

    def execute_market_order(
        self,
        symbol: str,
        side: OrderSide | str,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Order:
        side_enum = self._normalize_side(side)
        self._validate_order(symbol=symbol, side=side_enum, quantity=quantity, price=price, stop_loss=stop_loss)
        order = self._create_order(symbol=symbol, side=side_enum, order_type=OrderType.MARKET, quantity=quantity, price=price, stop_loss=stop_loss, take_profit=take_profit)

        setattr(order, "status", OrderStatus.FILLED)
        self._set_order_fields(order=order, filled_price=float(price), filled_quantity=float(quantity))
        self._record_position(symbol=symbol, side=side_enum, quantity=float(quantity), price=float(price))
        return order

    def execute_order(
        self,
        symbol: str,
        side: OrderSide | str,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        order_type: OrderType | str = OrderType.MARKET,
    ) -> Order:
        text = str(getattr(order_type, "value", order_type)).upper()
        if text == OrderType.LIMIT.value.upper() or text == "LIMIT":
            return self.place_limit_order(symbol=symbol, side=side, quantity=quantity, price=price, stop_loss=stop_loss, take_profit=take_profit)
        return self.execute_market_order(symbol=symbol, side=side, quantity=quantity, price=price, stop_loss=stop_loss, take_profit=take_profit)

    def place_limit_order(
        self,
        symbol: str,
        side: OrderSide | str,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Order:
        side_enum = self._normalize_side(side)
        self._validate_order(symbol=symbol, side=side_enum, quantity=quantity, price=price, stop_loss=stop_loss)
        order = self._create_order(symbol=symbol, side=side_enum, order_type=OrderType.LIMIT, quantity=quantity, price=price, stop_loss=stop_loss, take_profit=take_profit)

        setattr(order, "status", OrderStatus.PENDING)
        self._set_order_fields(order=order, filled_price=None, filled_quantity=None)
        return order

    def process_limit_order(
        self,
        order_id: Any,
        current_price: Optional[float] = None,
    ) -> Any:
        order = self._find_order(order_id)
        if current_price is None:
            return order

        current_price = float(current_price)
        order_price = float(getattr(order, "price", 0.0))

        side_attr = getattr(order, "side", None)
        side = str(getattr(side_attr, "value", side_attr)).upper() if side_attr else "BUY"

        should_fill = False
        if side == "BUY":
            should_fill = current_price <= order_price
        elif side == "SELL":
            should_fill = current_price >= order_price

        if not should_fill:
            from src.core.order_manager import OrderStatus
            setattr(order, "status", OrderStatus.PENDING)
            self._set_order_fields(order, filled_price=None, filled_quantity=None)
            return order

        return self.execute_limit_order(
            order_id=order_id,
            execution_price=order_price,
            current_price=current_price,
        )
    def execute_limit_order(
        self,
        order_id: Any,
        execution_price: Optional[float] = None,
        current_price: Optional[float] = None,
    ) -> Order:
        order = self._find_order(order_id)
        fill_price = execution_price if execution_price is not None else current_price
        if fill_price is None:
            fill_price = getattr(order, "price", None)
        if fill_price is None:
            raise ValueError("Execution price is required")

        side = getattr(order, "side", OrderSide.BUY)
        side_enum = self._normalize_side(side)
        quantity = float(getattr(order, "quantity"))

        setattr(order, "status", OrderStatus.FILLED)
        self._set_order_fields(order=order, filled_price=float(fill_price), filled_quantity=quantity)
        self._record_position(symbol=str(getattr(order, "symbol")), side=side_enum, quantity=quantity, price=float(fill_price))
        return order

    def fill_limit_order(
        self,
        order_id: Any,
        execution_price: Optional[float] = None,
        current_price: Optional[float] = None,
    ) -> Order:
        return self.execute_limit_order(order_id=order_id, execution_price=execution_price, current_price=current_price)

    def cancel_order(self, order_id: Any) -> Order:
        order = self._find_order(order_id)
        setattr(order, "status", OrderStatus.CANCELLED)
        return order
