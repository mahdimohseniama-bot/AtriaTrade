"""
ماژول اجرای سفارش‌ها (Order Executor)
هماهنگ با OrderManager، PositionTracker، RiskManager و PortfolioManager
"""
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

from src.core.order_manager import OrderManager, OrderSide, OrderType, OrderStatus, Order
from src.core.position_tracker import PositionTracker, Position
from src.core.risk_manager import RiskManager


def _get_field(obj: Any, *keys: str, default: Any = None) -> Any:
    """دریافت ایمن مقدار از آبجکت یا دیکشنری با کلیدهای مختلف"""
    for key in keys:
        if isinstance(obj, dict):
            if key in obj:
                return obj[key]
        else:
            try:
                val = getattr(obj, key)
                if val is not None:
                    return val
            except (AttributeError, KeyError):
                pass
            if hasattr(obj, "get") and callable(getattr(obj, "get")):
                val = obj.get(key)
                if val is not None:
                    return val
    return default


class OrderExecutor:
    def __init__(
        self,
        order_manager: Optional[OrderManager] = None,
        position_tracker: Optional[PositionTracker] = None,
        risk_manager: Optional[RiskManager] = None,
        portfolio: Optional[Any] = None,
    ):
        self.order_manager = order_manager if order_manager is not None else OrderManager()
        self.position_tracker = position_tracker if position_tracker is not None else PositionTracker()
        self.risk_manager = risk_manager
        self.portfolio = portfolio

    def execute_market_order(
        self,
        symbol: str,
        side: Any,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Dict[str, Any]:
        """اجرای سفارش Market با اعتبارسنجی ریسک"""
        # استخراج جهت سفارش
        if isinstance(side, OrderSide):
            side_enum = side
            side_str = side.value
        else:
            side_str = str(side).upper()
            try:
                side_enum = OrderSide(side_str)
            except Exception:
                side_enum = OrderSide.BUY if side_str == "BUY" else OrderSide.SELL

        # اعتبارسنجی ریسک
        if self.risk_manager is not None:
            if hasattr(self.risk_manager, "can_trade_today") and not self.risk_manager.can_trade_today():
                raise ValueError("سقف ضرر روزانه پر شده است و امکان معامله وجود ندارد.")

            if stop_loss is not None and stop_loss > 0:
                if side_str == "BUY" and stop_loss >= price:
                    raise ValueError("حد ضرر برای سفارش خرید باید کمتر از قیمت ورود باشد.")
                elif side_str == "SELL" and stop_loss <= price:
                    raise ValueError("حد ضرر برای سفارش فروش باید بیشتر از قیمت ورود باشد.")

            pos_val = quantity * price
            max_pct = getattr(self.risk_manager, "max_position_percent", 100.0)
            capital = getattr(self.risk_manager, "capital", 10000.0)
            max_val = (max_pct / 100.0) * capital
            if pos_val > max_val:
                raise ValueError(f"ارزش پوزیشن ({pos_val}) بیشتر از سقف مجاز ({max_val}) است.")

        # ثبت سفارش در OrderManager
        order = self.order_manager.create_order(
            symbol=symbol,
            side=side_enum,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        # به‌روزرسانی وضعیت سفارش
        order_id = _get_field(order, "order_id", "id", default=str(uuid.uuid4()))
        if isinstance(order, dict):
            order["status"] = OrderStatus.FILLED
            order["filled_price"] = price
            order["filled_quantity"] = quantity
        else:
            order.status = OrderStatus.FILLED
            order.filled_price = price
            order.filled_quantity = quantity

        # ثبت پوزیشن در PositionTracker
        self.position_tracker.open_position(
            symbol=symbol,
            side=side_str,
            quantity=quantity,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        return {
            "status": OrderStatus.FILLED.value,
            "filled_price": price,
            "filled_quantity": quantity,
            "order_id": order_id,
            "symbol": symbol,
            "side": side_str,
        }

    def place_and_execute_market_order(
        self,
        symbol: str,
        side: Any,
        quantity: float,
        current_price: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
    ) -> Dict[str, Any]:
        """متد کمکی برای تست‌های Trading Engine"""
        res = self.execute_market_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=current_price,
            stop_loss=sl,
            take_profit=tp,
        )
        pos = self.position_tracker.get_position(symbol)
        order = self.order_manager.get_order(res["order_id"])

        pos_dict = None
        if pos:
            pos_dict = {
                "symbol": _get_field(pos, "symbol", default=symbol),
                "entry_price": _get_field(pos, "entry_price", "price", default=current_price),
                "size": _get_field(pos, "quantity", "size", default=quantity),
                "side": _get_field(pos, "side", default="BUY"),
            }

        order_dict = {
            "order_id": _get_field(order, "order_id", default=res["order_id"]),
            "status": "FILLED",
            "symbol": symbol,
            "quantity": quantity,
            "price": current_price,
        }

        return {
            "order": order_dict,
            "position": pos_dict,
        }

    def process_limit_order(self, order_id: str, current_price: float) -> Dict[str, Any]:
        """بررسی و اجرای سفارش لیمیت بر اساس قیمت لحظه‌ای"""
        order = self.order_manager.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        status_obj = _get_field(order, "status")
        status_val = status_obj.value if isinstance(status_obj, OrderStatus) else str(status_obj).upper()

        if status_val not in ["PENDING", "OPEN"]:
            return {"status": status_val, "order_id": order_id}

        side_obj = _get_field(order, "side")
        side_str = side_obj.value if isinstance(side_obj, OrderSide) else str(side_obj).upper()

        order_price = float(_get_field(order, "price", default=0.0))
        order_qty = float(_get_field(order, "quantity", "size", default=0.0))
        order_symbol = _get_field(order, "symbol")
        order_sl = _get_field(order, "sl", "stop_loss", default=None)
        order_tp = _get_field(order, "tp", "take_profit", default=None)

        triggered = False
        if side_str == "BUY" and current_price <= order_price:
            triggered = True
        elif side_str == "SELL" and current_price >= order_price:
            triggered = True

        if triggered:
            if isinstance(order, dict):
                order["status"] = OrderStatus.FILLED
                order["filled_price"] = order_price
                order["filled_quantity"] = order_qty
            else:
                order.status = OrderStatus.FILLED
                order.filled_price = order_price
                order.filled_quantity = order_qty

            self.position_tracker.open_position(
                symbol=order_symbol,
                side=side_str,
                quantity=order_qty,
                entry_price=order_price,
                stop_loss=order_sl,
                take_profit=order_tp,
            )
            return {"status": OrderStatus.FILLED.value, "order_id": order_id}
        else:
            return {"status": OrderStatus.PENDING.value, "order_id": order_id}

    def evaluate_limit_orders(self, symbol: str, current_price: float) -> List[Dict[str, Any]]:
        """بررسی تمامی سفارش‌های لیمیت باز برای یک نماد"""
        executions = []
        try:
            orders = self.order_manager.get_open_orders()
        except TypeError:
            orders = self.order_manager.get_open_orders(symbol)

        for order in orders:
            order_sym = _get_field(order, "symbol")
            if order_sym != symbol:
                continue

            order_type_obj = _get_field(order, "order_type", "type")
            order_type_val = order_type_obj.value if isinstance(order_type_obj, OrderType) else str(order_type_obj).upper()
            
            if order_type_val == "LIMIT":
                oid = _get_field(order, "order_id", "id")
                res = self.process_limit_order(oid, current_price)
                if res.get("status") == OrderStatus.FILLED.value:
                    executions.append({
                        "order": {
                            "order_id": oid,
                            "status": "FILLED",
                            "symbol": order_sym,
                            "price": _get_field(order, "price"),
                            "quantity": _get_field(order, "quantity", "size"),
                        }
                    })
        return executions
