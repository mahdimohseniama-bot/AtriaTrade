from typing import Any, Callable, Dict, Optional

from src.core.order_executor import OrderExecutor
from src.core.order_manager import OrderManager
from src.core.position_tracker import PositionTracker
from src.core.risk_manager import RiskConfig, RiskManager


class IntegratedTradingPipeline:
    def __init__(
        self,
        initial_balance: float = 10000.0,
        strategy: Optional[Callable[..., Dict[str, Any]]] = None,
        risk_config: Optional[RiskConfig] = None,
        **kwargs: Any,
    ) -> None:
        self.initial_balance = float(initial_balance)
        self.strategy = strategy
        self.risk_manager = RiskManager(risk_config)
        self.position_tracker = PositionTracker()
        self.order_manager = OrderManager()
        self.order_executor = OrderExecutor(
            order_manager=self.order_manager,
            position_tracker=self.position_tracker,
            risk_manager=self.risk_manager,
        )

    def process_tick(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.step(market_data)

    def step(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.risk_manager.circuit_breaker_tripped:
            return {
                "action": "HOLD",
                "blocked": True,
                "reason": "Circuit breaker active",
            }

        signal: Dict[str, Any] = {}
        if callable(self.strategy):
            result = self.strategy(market_data)
            if isinstance(result, dict):
                signal = result
        else:
            for value in market_data.values():
                if isinstance(value, dict) and "action" in value:
                    signal = value
                    break

        action = str(signal.get("action", "HOLD")).upper()
        if action not in {"BUY", "SELL"}:
            return {"action": "HOLD", "status": "SKIPPED"}

        symbol = str(signal.get("symbol", "BTCUSDT")).upper()
        quantity = float(signal.get("quantity", signal.get("size", 0.1)))

        tick = market_data.get(symbol, {})
        if not isinstance(tick, dict):
            tick = {}

        price = float(
            signal.get("price", tick.get("close", tick.get("price", 0.0)))
        )
        if price <= 0:
            return {
                "action": "HOLD",
                "status": "SKIPPED",
                "reason": "No valid market price",
            }

        result = self.order_executor.place_and_execute_market_order(
            symbol=symbol,
            side=action,
            quantity=quantity,
            current_price=price,
            sl=signal.get("sl"),
            tp=signal.get("tp"),
        )
        return {
            "action": action,
            "order": result["order"],
            "position": result["position"],
            "status": "EXECUTED",
        }
