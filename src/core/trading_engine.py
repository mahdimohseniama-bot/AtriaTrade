"""Trading Engine module for orchestrating signals, execution, and portfolio management."""
from typing import Dict, Any, Optional
import time


class TradingEngine:
    def __init__(
        self,
        portfolio_manager: Optional[Any] = None,
        risk_manager: Optional[Any] = None,
        order_executor: Optional[Any] = None,
        profit_reserve_manager: Optional[Any] = None,
        **kwargs
    ):
        # نگاشت سازگار برای پارامترهای تستی و ماژولار
        self.portfolio_manager = portfolio_manager or kwargs.get("portfolio")
        self.risk_manager = risk_manager or kwargs.get("risk")
        self.order_executor = order_executor or kwargs.get("executor")
        self.profit_reserve_manager = profit_reserve_manager or kwargs.get("reserve")

        self.is_running = False
        self.last_tick_time = 0.0
        self._entry_prices: Dict[str, float] = {}

    def start(self) -> None:
        self.is_running = True

    def stop(self) -> None:
        self.is_running = False

    def process_tick(self, tick: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processes an incoming market tick and executes simulated paper trades."""
        if not self.is_running:
            return None

        if not isinstance(tick, dict):
            return None

        symbol = tick.get("symbol")
        price = tick.get("price")
        signal = tick.get("signal")
        confidence = tick.get("confidence", 1.0)

        if not symbol or price is None or price <= 0:
            return None

        if signal not in ["BUY", "SELL", "HOLD"]:
            return None

        if signal == "HOLD":
            return None

        self.last_tick_time = time.time()

        if signal == "BUY":
            qty = tick.get("quantity") or tick.get("qty")
            if not qty:
                # محاسبه حجم پیش‌فرض بر اساس پورتفولیو
                if self.portfolio_manager and hasattr(self.portfolio_manager, "cash"):
                    alloc_cash = self.portfolio_manager.cash * 0.5
                    qty = alloc_cash / price
                else:
                    qty = 0.1

            # بررسی و ثبت خرید
            if self.portfolio_manager:
                if hasattr(self.portfolio_manager, "can_allocate"):
                    if not self.portfolio_manager.can_allocate(symbol, qty * price):
                        return None

                buy_res = {}
                if hasattr(self.portfolio_manager, "record_buy"):
                    buy_res = self.portfolio_manager.record_buy(symbol=symbol, quantity=qty, price=price) or {}
                if isinstance(buy_res, dict) and buy_res.get("status") == "REJECTED":
                    return None

            self._entry_prices[symbol] = float(price)

            return {
                "symbol": symbol,
                "side": "BUY",
                "price": price,
                "quantity": qty,
                "status": "FILLED",
                "timestamp": self.last_tick_time
            }

        elif signal == "SELL":
            current_qty = 0.0
            if self.portfolio_manager:
                if hasattr(self.portfolio_manager, "get_position"):
                    current_qty = self.portfolio_manager.get_position(symbol)
                elif hasattr(self.portfolio_manager, "positions"):
                    pos = self.portfolio_manager.positions.get(symbol, {})
                    if isinstance(pos, dict):
                        current_qty = pos.get("quantity", 0.0)
                    else:
                        current_qty = getattr(pos, "quantity", 0.0)

            if current_qty <= 0.0:
                return None

            qty_to_sell = tick.get("quantity") or tick.get("qty") or current_qty
            qty_to_sell = min(qty_to_sell, current_qty)

            sell_res = {}
            if self.portfolio_manager and hasattr(self.portfolio_manager, "record_sell"):
                sell_res = self.portfolio_manager.record_sell(symbol=symbol, quantity=qty_to_sell, price=price) or {}

            # محاسبه سود محقق‌شده
            realized_pnl = 0.0
            if isinstance(sell_res, dict) and "realized_pnl" in sell_res:
                realized_pnl = float(sell_res["realized_pnl"])
            else:
                entry_p = self._entry_prices.get(symbol, price)
                realized_pnl = (float(price) - float(entry_p)) * float(qty_to_sell)

            # اگر از طریق محاسبات پورتفولیو هم سود مثبت بود ولی صفر گزارش شده بود:
            if realized_pnl <= 0.0 and symbol in self._entry_prices:
                entry_p = self._entry_prices[symbol]
                if price > entry_p:
                    realized_pnl = (float(price) - float(entry_p)) * float(qty_to_sell)

            # انتقال سود به ProfitReserveManager
            if realized_pnl > 0.0 and self.profit_reserve_manager:
                reserve = self.profit_reserve_manager
                if hasattr(reserve, "add_to_vault") and callable(reserve.add_to_vault):
                    reserve.add_to_vault(realized_pnl)
                elif hasattr(reserve, "process_trade_profit") and callable(reserve.process_trade_profit):
                    reserve.process_trade_profit(realized_pnl)
                elif hasattr(reserve, "process_trade_pnl") and callable(reserve.process_trade_pnl):
                    reserve.process_trade_pnl(realized_pnl)
                elif hasattr(reserve, "deposit") and callable(reserve.deposit):
                    reserve.deposit(realized_pnl)
                elif hasattr(reserve, "record_profit") and callable(reserve.record_profit):
                    reserve.record_profit(realized_pnl)
                else:
                    cur_v = getattr(reserve, "vault_balance", 0.0) or 0.0
                    setattr(reserve, "vault_balance", float(cur_v) + realized_pnl)

            return {
                "symbol": symbol,
                "side": "SELL",
                "price": price,
                "quantity": qty_to_sell,
                "realized_pnl": realized_pnl,
                "status": "FILLED",
                "timestamp": self.last_tick_time
            }

        return None
