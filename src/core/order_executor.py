"""اجرای سفارش‌ها با بررسی ریسک — AtriaTrade"""
from __future__ import annotations

from typing import Optional

from src.core.order_manager import OrderManager, OrderSide, OrderType, OrderStatus
from src.core.position_tracker import PositionTracker
from src.core.risk_manager import RiskManager


class OrderExecutor:
    def __init__(
        self,
        order_manager: Optional[OrderManager] = None,
        position_tracker: Optional[PositionTracker] = None,
        risk_manager: Optional[RiskManager] = None,
    ) -> None:
        self.order_manager = order_manager if order_manager is not None else OrderManager()
        self.position_tracker = position_tracker if position_tracker is not None else PositionTracker()
        self.risk_manager = risk_manager if risk_manager is not None else RiskManager()

    def _check_risk(self, symbol: str, side, entry_price: float, stop_loss: float, quantity: float) -> None:
        """بررسی ریسک؛ در صورت رد شدن ValueError صادر می‌شود"""
        decision = self.risk_manager.validate_trade_risk(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            stop_loss=stop_loss,
            quantity=quantity,
        )
        if not decision.get("allowed", False):
            raise ValueError(decision.get("reason", "ریسک معامله تأیید نشد"))

    def execute_market_order(
        self,
        symbol: str,
        side,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> dict:
        # بررسی ریسک فقط وقتی حد ضرر مشخص شده باشد
        if stop_loss is not None:
            self._check_risk(symbol, side, price, stop_loss, quantity)

        order = self.order_manager.create_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        filled = self.order_manager.fill_order(order.order_id, fill_price=price)
        self.position_tracker.open_position(
            symbol=symbol,
            side=side,
            entry_price=price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        return filled.to_dict()

    def process_limit_order(self, order_id: str, current_price: float) -> dict:
        order = self.order_manager.get_order(order_id)
        if order.status != OrderStatus.PENDING:
            return order.to_dict()

        # بررسی رسیدن قیمت به حد سفارش
        if order.side == OrderSide.BUY and current_price > order.price:
            return order.to_dict()
        if order.side == OrderSide.SELL and current_price < order.price:
            return order.to_dict()

        # بررسی ریسک هنگام Fill
        if order.stop_loss is not None:
            decision = self.risk_manager.validate_trade_risk(
                symbol=order.symbol,
                side=order.side,
                entry_price=current_price,
                stop_loss=order.stop_loss,
                quantity=order.quantity,
            )
            if not decision.get("allowed", False):
                canceled = self.order_manager.cancel_order(
                    order_id,
                    reason=decision.get("reason", "ریسک تأیید نشد"),
                )
                return canceled.to_dict()

        filled = self.order_manager.fill_order(order_id, fill_price=current_price)
        self.position_tracker.open_position(
            symbol=order.symbol,
            side=order.side,
            entry_price=current_price,
            quantity=order.quantity,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
        )
        return filled.to_dict()

    def cancel_order(self, order_id: str, reason: Optional[str] = None) -> dict:
        return self.order_manager.cancel_order(order_id, reason=reason).to_dict()

    def get_status(self) -> dict:
        return {
            "orders": self.order_manager.get_status(),
            "positions": self.position_tracker.get_status(),
            "risk": self.risk_manager.get_status(),
        }
