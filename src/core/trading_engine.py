"""Trading Engine module for AtriaTrade."""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TradingEngine:
    def __init__(self, **kwargs):
        self.portfolio_manager = kwargs.get("portfolio_manager") or kwargs.get("portfolio")
        self.order_executor = kwargs.get("order_executor") or kwargs.get("executor")
        self.risk_manager = kwargs.get("risk_manager") or kwargs.get("risk")
        self.profit_reserve_manager = (
            kwargs.get("profit_reserve_manager")
            or kwargs.get("profit_reserve")
            or kwargs.get("reserve")
        )
        self.regime_detector = kwargs.get("regime_detector") or kwargs.get("regime")
        self.is_running = False

    def start(self) -> None:
        self.is_running = True
        logger.info("TradingEngine started successfully.")

    def stop(self) -> None:
        self.is_running = False
        logger.info("TradingEngine stopped successfully.")

    def process_tick(self, tick: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.is_running:
            return None

        symbol = tick.get("symbol")
        price = float(tick.get("price", 0.0))
        signal = tick.get("signal", "HOLD").upper()
        confidence = float(tick.get("confidence", 0.0))

        if signal == "HOLD" or price <= 0.0:
            return None

        if signal == "BUY":
            available_cash = self.portfolio_manager.cash if self.portfolio_manager else 0.0
            if available_cash <= 0.0:
                logger.warning(f"Insufficient cash to execute BUY for {symbol}.")
                return None

            allocation_allowed = True
            if self.portfolio_manager and hasattr(self.portfolio_manager, "can_allocate"):
                alloc_res = self.portfolio_manager.can_allocate(symbol, available_cash * 0.1)
                if isinstance(alloc_res, dict):
                    allocation_allowed = alloc_res.get("allowed", False)
                else:
                    allocation_allowed = bool(alloc_res)

            if not allocation_allowed:
                logger.warning(f"Allocation rejected for {symbol}.")
                return None

            order_size_cash = available_cash * 0.1
            quantity = order_size_cash / price

            if self.order_executor:
                self.order_executor.execute_market_order(symbol, "BUY", quantity, price)

            trade_res = None
            if self.portfolio_manager:
                trade_res = self.portfolio_manager.record_buy(symbol, quantity, price)

            return trade_res or {"status": "FILLED", "action": "BUY", "quantity": quantity, "price": price}

        elif signal == "SELL":
            current_qty = 0.0
            if self.portfolio_manager:
                current_qty = self.portfolio_manager.get_position(symbol)

            if current_qty <= 0.0:
                logger.warning(f"No open position to SELL for {symbol}.")
                return None

            if self.order_executor:
                self.order_executor.execute_market_order(symbol, "SELL", current_qty, price)

            sell_res = None
            if self.portfolio_manager:
                sell_res = self.portfolio_manager.record_sell(symbol, current_qty, price)

            if sell_res and self.profit_reserve_manager:
                realized_pnl = sell_res.get("realized_pnl", 0.0)
                if realized_pnl > 0.0:
                    if hasattr(self.profit_reserve_manager, "add_to_vault"):
                        self.profit_reserve_manager.add_to_vault(realized_pnl)
                    elif hasattr(self.profit_reserve_manager, "transfer_to_vault"):
                        self.profit_reserve_manager.transfer_to_vault(realized_pnl)
                    elif hasattr(self.profit_reserve_manager, "process_trade_profit"):
                        self.profit_reserve_manager.process_trade_profit(realized_pnl)

            return sell_res or {"status": "FILLED", "action": "SELL", "quantity": current_qty, "price": price}

        return None
