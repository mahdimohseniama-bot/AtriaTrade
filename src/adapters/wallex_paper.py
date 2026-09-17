import time
import requests
from typing import Dict, Any, Optional

class WallexPaperAdapter:
    """
    آداپتور رسمی والکس جهت دریافت دیتا و شبیه‌سازی ترید پیپر
    """
    DEPTH_URL = "https://api.wallex.ir/v1/depth"

    def __init__(self, symbol: str = "USDTTMN", initial_balance: float = 50_000_000.0):
        self.symbol = symbol.upper()
        self.balance = float(initial_balance)
        self.headers = {"User-Agent": "Mozilla/5.0 (AtriaTrade/Bot)"}
        self.positions: Dict[str, Dict[str, Any]] = {}
        self._pos_counter = 0

    def fetch_ticker(self) -> Optional[Dict[str, float]]:
        try:
            url = f"{self.DEPTH_URL}?symbol={self.symbol}"
            res = requests.get(url, headers=self.headers, timeout=6)
            data = res.json().get("result", {})
            bids = data.get("bid", [])
            asks = data.get("ask", [])
            if not bids or not asks:
                return None
            best_bid = float(bids[0]["price"])
            best_ask = float(asks[0]["price"])
            return {
                "bid": best_bid,
                "ask": best_ask,
                "mid": (best_bid + best_ask) / 2.0,
                "timestamp": time.time()
            }
        except Exception:
            return None

    def execute_market_order(self, side: str, amount_toman: float) -> Dict[str, Any]:
        ticker = self.fetch_ticker()
        if not ticker:
            return {"status": "REJECTED", "reason": "TICKER_UNAVAILABLE"}

        price = ticker["ask"] if side == "BUY" else ticker["bid"]

        if side == "BUY":
            if amount_toman > self.balance:
                return {"status": "REJECTED", "reason": "INSUFFICIENT_BALANCE"}
            self._pos_counter += 1
            pos_id = f"WALLEX_{self.symbol}_{self._pos_counter}"
            coin_qty = amount_toman / price
            self.balance -= amount_toman
            self.positions[pos_id] = {
                "side": "BUY",
                "entry_price": price,
                "qty": coin_qty,
                "invested": amount_toman,
                "open_time": time.time()
            }
            return {
                "status": "FILLED",
                "position_id": pos_id,
                "side": "BUY",
                "price": price,
                "qty": coin_qty,
                "remaining_balance": self.balance
            }

        elif side == "SELL":
            if not self.positions:
                return {"status": "REJECTED", "reason": "NO_OPEN_POSITIONS"}
            pos_id, pos = self.positions.popitem()
            proceeds = pos["qty"] * price
            pnl = proceeds - pos["invested"]
            self.balance += proceeds
            return {
                "status": "CLOSED",
                "position_id": pos_id,
                "side": "SELL",
                "exit_price": price,
                "pnl": round(pnl, 2),
                "remaining_balance": round(self.balance, 2)
            }

        return {"status": "REJECTED", "reason": "INVALID_SIDE"}
