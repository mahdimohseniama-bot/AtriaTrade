import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("WallexLiveOrchestrator")

class WallexLiveOrchestrator:
    def __init__(self, adapter, capital_manager, risk_manager=None):
        self.adapter = adapter
        self.capital_manager = capital_manager
        self.risk_manager = risk_manager
        self.active_positions: Dict[str, Dict[str, Any]] = {}

    def extract_price(self, ticker: Any) -> float:
        if isinstance(ticker, dict):
            price = ticker.get("lastPrice") or ticker.get("last_price") or ticker.get("price")
            if price is not None:
                return float(price)
            raise KeyError("Ticker dict does not contain 'lastPrice' or 'last_price'")
        elif hasattr(ticker, "last_price"):
            return float(ticker.last_price)
        elif hasattr(ticker, "lastPrice"):
            return float(ticker.lastPrice)
        raise AttributeError("Unsupported ticker format: unable to extract current price")

    def process_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        ticker = self.adapter.get_ticker(symbol)
        current_price = self.extract_price(ticker)
        
        position = self.active_positions.get(symbol)
        if not position:
            return None

        side = position.get("side", "BUY")
        entry_price = position["entry_price"]
        sl = position.get("stop_loss")
        tp = position.get("take_profit")
        quantity = position.get("quantity", 0.0)

        closed = False
        exit_reason = None
        exit_price = current_price

        if side == "BUY":
            if sl is not None and current_price <= sl:
                closed = True
                exit_reason = "STOP_LOSS"
            elif tp is not None and current_price >= tp:
                closed = True
                exit_reason = "TAKE_PROFIT"
        elif side == "SELL":
            if sl is not None and current_price >= sl:
                closed = True
                exit_reason = "STOP_LOSS"
            elif tp is not None and current_price <= tp:
                closed = True
                exit_reason = "TAKE_PROFIT"

        if closed:
            if side == "BUY":
                pnl = (exit_price - entry_price) * quantity
            else:
                pnl = (entry_price - exit_price) * quantity

            self.capital_manager.record_trade_result(pnl=pnl, fee=0.0)
            del self.active_positions[symbol]

            result = {
                "symbol": symbol,
                "status": "CLOSED",
                "exit_reason": exit_reason,
                "exit_price": exit_price,
                "pnl": pnl
            }
            logger.info(f"Position closed: {result}")
            return result

        return {
            "symbol": symbol,
            "status": "OPEN",
            "current_price": current_price
        }

    def open_paper_position(self, symbol: str, side: str, entry_price: float, quantity: float, stop_loss: float, take_profit: float):
        self.active_positions[symbol] = {
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "quantity": quantity,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }
        logger.info(f"Position opened: {self.active_positions[symbol]}")
