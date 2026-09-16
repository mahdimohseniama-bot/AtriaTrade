from typing import Any, Dict, Optional

from src.core.order_executor import OrderExecutor
from src.core.position_tracker import PositionTracker
from src.core.risk_manager import RiskConfig, RiskManager


class PaperTradingSession:
    def __init__(
        self,
        initial_balance: float = 10000.0,
        risk_config: Optional[RiskConfig] = None,
        order_executor: Optional[OrderExecutor] = None,
        position_tracker: Optional[PositionTracker] = None,
        **kwargs: Any,
    ) -> None:
        self.initial_balance = float(initial_balance)
        self.balance = float(initial_balance)
        self.risk_config = risk_config or RiskConfig(**kwargs)
        self.risk_manager = RiskManager(self.risk_config)
        self.position_tracker = position_tracker or PositionTracker()
        self.order_executor = order_executor or OrderExecutor(
            position_tracker=self.position_tracker,
            risk_manager=self.risk_manager,
        )
        self.market_prices: Dict[str, float] = {}

    def get_balance(self) -> float:
        return float(self.balance)

    def get_equity(self) -> float:
        position_value = 0.0
        for symbol, position in self.position_tracker.positions.items():
            quantity = float(position.get("quantity", position.get("size", 0.0)))
            entry = float(position.get("entry_price", 0.0))
            market = float(self.market_prices.get(symbol, entry))

            if position.get("side", "BUY") == "SELL":
                # ارزش اقتصادی Short = وثیقه اولیه + سود/زیان آن
                position_value += quantity * entry + quantity * (entry - market)
            else:
                position_value += quantity * market

        return float(self.balance + position_value)

    def update_market_prices(self, prices: Dict[str, float]) -> None:
        for symbol, price in prices.items():
            self.market_prices[str(symbol).upper()] = float(price)

    def execute_order(
        self,
        symbol: str,
        side: Any,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        qty = kwargs.get("size", quantity)
        if qty is None or price is None:
            raise ValueError("quantity/size and price are required")

        qty = float(qty)
        price = float(price)
        side_value = str(getattr(side, "value", side)).upper()

        # در خرید، مبلغ سفارش از موجودی نقدی کسر می‌شود.
        if side_value == "BUY":
            self.balance -= qty * price

        self.market_prices[str(symbol).upper()] = price
        return self.order_executor.place_and_execute_market_order(
            symbol=symbol,
            side=side_value,
            quantity=qty,
            current_price=price,
            sl=sl,
            tp=tp,
        )

# Backward-compatible public API:
# تست‌ها و ماژول‌های قدیمی پروژه از نام PaperSession استفاده می‌کنند.
PaperSession = PaperTradingSession
