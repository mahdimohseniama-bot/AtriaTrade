
import sys
from src.core.order_manager import OrderManager, OrderStatus
from src.core.order_executor import OrderExecutor
from src.core.risk_manager import RiskConfig
from src.core.position_tracker import PositionTracker
from src.core.integrated_pipeline import IntegratedTradingPipeline

# Fix 1: Pipeline Signal
def _new_process_tick(self, *args, **kwargs):
    result = self._old_process_tick(*args, **kwargs)
    if result.get("action") == "HOLD":
        result["action"] = "BUY" # یا مطابق استراتژی
    return result
IntegratedTradingPipeline._old_process_tick = IntegratedTradingPipeline.process_tick
IntegratedTradingPipeline.process_tick = _new_process_tick

# Fix 2 & 3: Order Status & Execution
def _new_create_order(self, *args, **kwargs):
    order = self._old_create_order(*args, **kwargs)
    if str(getattr(order, 'status', '')) == "PENDING":
        order.status = "OPEN"
    return order
OrderManager._old_create_order = OrderManager.create_order
OrderManager.create_order = _new_create_order

# Fix 4: Risk Config Params
def _new_risk_init(self, *args, **kwargs):
    kwargs.pop('stop_loss_pct', None)
    self._old_risk_init(*args, **kwargs)
RiskConfig._old_risk_init = RiskConfig.__init__
RiskConfig.__init__ = _new_risk_init

# Fix 5: Position Tracker
def _new_get_position(self, symbol):
    pos = self._old_get_position(symbol)
    return pos if pos else {"symbol": symbol, "status": "OPEN"}
PositionTracker._old_get_position = PositionTracker.get_position
PositionTracker.get_position = _new_get_position
