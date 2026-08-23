from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class SimulatedOrder:
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    requested_price: float
    executed_price: Optional[float]
    fee: float
    status: str
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OrderSimulator:
    """
    شبیه‌ساز سفارش برای Paper Trading.
    کاملاً آفلاین، بدون اتصال به صرافی، شبکه یا حساب واقعی.
    """

    VALID_SIDES = {"BUY", "SELL"}
    VALID_ORDER_TYPES = {"MARKET", "LIMIT"}

    def __init__(
        self,
        fee_percent: float = 0.1,
        slippage_percent: float = 0.05,
    ) -> None:
        if fee_percent < 0:
            raise ValueError("fee_percent cannot be negative")

        if slippage_percent < 0:
            raise ValueError("slippage_percent cannot be negative")

        self.fee_percent = float(fee_percent)
        self.slippage_percent = float(slippage_percent)
        self.orders: Dict[str, SimulatedOrder] = {}

    def _validate_basic_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float,
    ) -> None:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol must be a non-empty string")

        if side not in self.VALID_SIDES:
            raise ValueError("side must be BUY or SELL")

        if order_type not in self.VALID_ORDER_TYPES:
            raise ValueError("order_type must be MARKET or LIMIT")

        if quantity <= 0:
            raise ValueError("quantity must be greater than zero")

        if price <= 0:
            raise ValueError("price must be greater than zero")

    def _market_execution_price(
        self,
        side: str,
        price: float,
    ) -> float:
        slippage = self.slippage_percent / 100.0

        if side == "BUY":
            return price * (1.0 + slippage)

        return price * (1.0 - slippage)

    def _calculate_fee(
        self,
        execution_price: float,
        quantity: float,
    ) -> float:
        gross_value = execution_price * quantity
        return gross_value * (self.fee_percent / 100.0)

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float,
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        normalized_side = str(side).upper().strip()
        normalized_order_type = str(order_type).upper().strip()

        self._validate_basic_order(
            symbol=symbol,
            side=normalized_side,
            order_type=normalized_order_type,
            quantity=quantity,
            price=price,
        )

        if limit_price is not None and limit_price <= 0:
            raise ValueError("limit_price must be greater than zero")

        order_id = str(uuid4())

        if normalized_order_type == "MARKET":
            executed_price = self._market_execution_price(
                side=normalized_side,
                price=float(price),
            )

            fee = self._calculate_fee(
                execution_price=executed_price,
                quantity=float(quantity),
            )

            order = SimulatedOrder(
                order_id=order_id,
                symbol=symbol,
                side=normalized_side,
                order_type=normalized_order_type,
                quantity=float(quantity),
                requested_price=float(price),
                executed_price=executed_price,
                fee=fee,
                status="FILLED",
                reason="Market order filled in paper trading",
            )

        else:
            effective_limit_price = (
                float(limit_price)
                if limit_price is not None
                else float(price)
            )

            should_fill = (
                normalized_side == "BUY"
                and float(price) <= effective_limit_price
            ) or (
                normalized_side == "SELL"
                and float(price) >= effective_limit_price
            )

            if should_fill:
                executed_price = effective_limit_price
                fee = self._calculate_fee(
                    execution_price=executed_price,
                    quantity=float(quantity),
                )
                status = "FILLED"
                reason = "Limit condition satisfied in paper trading"
            else:
                executed_price = None
                fee = 0.0
                status = "NEW"
                reason = "Limit condition not satisfied"

            order = SimulatedOrder(
                order_id=order_id,
                symbol=symbol,
                side=normalized_side,
                order_type=normalized_order_type,
                quantity=float(quantity),
                requested_price=float(price),
                executed_price=executed_price,
                fee=fee,
                status=status,
                reason=reason,
            )

        self.orders[order_id] = order
        return order.to_dict()

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        order = self.orders.get(order_id)

        if order is None:
            raise KeyError(f"Unknown order_id: {order_id}")

        if order.status == "NEW":
            order.status = "CANCELED"
            order.reason = "Canceled by paper trading controller"

        return order.to_dict()

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        order = self.orders.get(order_id)

        if order is None:
            return None

        return order.to_dict()

    def get_active_orders(self) -> List[Dict[str, Any]]:
        return [
            order.to_dict()
            for order in self.orders.values()
            if order.status == "NEW"
        ]

    def get_filled_orders(self) -> List[Dict[str, Any]]:
        return [
            order.to_dict()
            for order in self.orders.values()
            if order.status == "FILLED"
        ]

    def get_all_orders(self) -> List[Dict[str, Any]]:
        return [
            order.to_dict()
            for order in self.orders.values()
        ]
