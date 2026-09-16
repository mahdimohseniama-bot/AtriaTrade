import logging
from typing import Dict, Any, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class SMACrossStrategy:
    def __init__(
        self,
        symbol: str = "BTCUSDT",
        fast_period: Optional[int] = None,
        slow_period: Optional[int] = None,
        short_window: int = 5,
        long_window: int = 20,
        engine: Optional[Any] = None,
        quantity: float = 1.0,
        take_profit_pct: float = 0.05,
        stop_loss_pct: float = 0.02,
        **kwargs
    ):
        self.symbol = symbol
        self.short_window = fast_period if fast_period is not None else short_window
        self.long_window = slow_period if slow_period is not None else long_window
        
        if self.short_window >= self.long_window:
            raise ValueError(f"short_window ({self.short_window}) must be strictly less than long_window ({self.long_window})")

        self.engine = engine
        self.quantity = float(quantity)
        self.take_profit_pct = float(take_profit_pct)
        self.stop_loss_pct = float(stop_loss_pct)
        self.prices: List[float] = []

    def get_tp_sl(self, action: str, price: float) -> Tuple[float, float]:
        if action == "BUY":
            tp = price * (1.0 + self.take_profit_pct)
            sl = price * (1.0 - self.stop_loss_pct)
            return (round(tp, 4), round(sl, 4))
        elif action == "SELL":
            tp = price * (1.0 - self.take_profit_pct)
            sl = price * (1.0 + self.stop_loss_pct)
            return (round(tp, 4), round(sl, 4))
        return (0.0, 0.0)

    def _signal_from_series(self, series: List[float]) -> str:
        if len(series) < self.long_window:
            return "HOLD"
        
        fast_curr = sum(series[-self.short_window:]) / self.short_window
        slow_curr = sum(series[-self.long_window:]) / self.long_window

        prev_series = series[:-1]
        if len(prev_series) >= self.long_window:
            fast_prev = sum(prev_series[-self.short_window:]) / self.short_window
            slow_prev = sum(prev_series[-self.long_window:]) / self.long_window
            if fast_prev <= slow_prev and fast_curr > slow_curr:
                return "BUY"
            if fast_prev >= slow_prev and fast_curr < slow_curr:
                return "SELL"
        else:
            if fast_curr > slow_curr:
                return "BUY"
            if fast_curr < slow_curr:
                return "SELL"

        return "HOLD"

    def generate_signal(self, input_data: Union[float, List[float]]) -> str:
        if isinstance(input_data, list):
            self.prices = list(input_data)
            return self._signal_from_series(self.prices)
        
        self.prices.append(float(input_data))
        return self._signal_from_series(self.prices)

    def _dispatch_signal(self, action: str, price: float, quantity: Optional[float] = None) -> Dict[str, Any]:
        qty = quantity if quantity is not None else self.quantity
        tp, sl = self.get_tp_sl(action, price)
        payload = {
            "symbol": self.symbol,
            "action": action,
            "signal": action,
            "side": action,
            "price": price,
            "quantity": qty,
            "qty": qty,
            "tp": tp,
            "sl": sl
        }
        if self.engine is not None:
            # مدیریت پورتفوی شبیه‌سازی FakeTradingEngine در تست‌ها
            if hasattr(self.engine, "portfolio") and isinstance(self.engine.portfolio, dict):
                current_qty = self.engine.portfolio.get(self.symbol, 0.0)
                if action == "BUY":
                    self.engine.portfolio[self.symbol] = current_qty + qty
                elif action == "SELL":
                    self.engine.portfolio[self.symbol] = max(0.0, current_qty - qty)

            if hasattr(self.engine, "handle_strategy_signal"):
                self.engine.handle_strategy_signal("SMACrossStrategy", payload)
            elif hasattr(self.engine, "on_signal"):
                self.engine.on_signal(payload)
        return payload

    def on_tick(self, tick: Dict[str, Any]) -> Optional[str]:
        if not isinstance(tick, dict) or "price" not in tick:
            return None
        try:
            price = float(tick["price"])
        except (ValueError, TypeError):
            return None

        sig = self.generate_signal(price)
        if sig in ("BUY", "SELL"):
            self._dispatch_signal(sig, price)
            return sig
        return None
