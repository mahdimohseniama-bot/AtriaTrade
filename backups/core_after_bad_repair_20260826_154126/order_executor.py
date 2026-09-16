import time
from typing import Any, Dict, List, Optional

from src.core.order_manager import Order, OrderManager, OrderStatus, OrderType
from src.core.position_tracker import PositionTracker
from src.core.risk_manager import RiskManager


class OrderExecutor:
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

    def execute_market_order(
        self,
        symbol: str,
        side: Any,
        quantity: float,
        price: Optional[float] = None,
        current_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        **kwargs: Any,
    ) -> Order:
        execution_price = current_price if current_price is not None else price
        if execution_price is None:
            raise ValueError("price or current_price is required")

        valid, reason = self.risk_manager.validate_order(
            symbol=symbol, side=side, quantity=quantity, price=float(execution_price)
        )
        if not valid:
            raise ValueError(reason)

        order = self.order_manager.create_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=float(execution_price),
        )
        order.status = OrderStatus.FILLED.value
        order.filled_at = time.time()
        order.executed_price = float(execution_price)

        self.position_tracker.update_position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=float(execution_price),
            sl=kwargs.get("sl", stop_loss),
            tp=kwargs.get("tp", take_profit),
        )
        return order

    def place_and_execute_market_order(
        self,
        symbol: str,
        side: Any,
        quantity: Optional[float] = None,
        current_price: Optional[float] = None,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        qty = kwargs.get("size", quantity)
        if qty is None:
            raise ValueError("quantity or size is required")

        execution_price = current_price if current_price is not None else price
        order = self.execute_market_order(
            symbol=symbol,
            side=side,
            quantity=float(qty),
            price=execution_price,
            stop_loss=sl if sl is not None else stop_loss,
            take_profit=tp if tp is not None else take_profit,
        )
        position = self.position_tracker.get_position(symbol)

        return {
            "order": order.to_dict(),
            "position": position,
            "status": OrderStatus.FILLED.value,
        }

    def process_limit_orders(
        self,
        current_market_prices: Optional[Dict[str, float]] = None,
        **kwargs: Any,
    ) -> List[Order]:
        prices = current_market_prices or kwargs.get("market_prices", {})
        triggered: List[Order] = []

        for order in list(self.order_manager.orders.values()):
            if order.order_type != OrderType.LIMIT.value:
                continue
            if order.status != OrderStatus.OPEN.value:
                continue

            market_price = prices.get(order.symbol)
            if market_price is None:
                continue

            market_price = float(market_price)
            should_fill = (
                (order.side == "BUY" and market_price <= order.price)
                or (order.side == "SELL" and market_price >= order.price)
            )
            if not should_fill:
                continue

            order.status = OrderStatus.FILLED.value
            order.filled_at = time.time()
            order.executed_price = market_price

            self.position_tracker.update_position(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                entry_price=order.price,
            )
            triggered.append(order)

        return triggered
