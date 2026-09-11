from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from src.data.market_fetcher import MarketFetcher


class WallexPaperAdapter:
    """
    آداپتور معاملات کاغذی (Paper Trading) متصل به دیتای زنده صرافی والکس.
    داده‌های بازار واقعی هستند، اما بالانس و اجرای سفارشات در حافظه شبیه‌سازی می‌شوند.
    """

    def __init__(self, initial_balance_usdt: float = 100.0, fee_rate: float = 0.001):
        self.balance_usdt = float(initial_balance_usdt)
        self.initial_balance = float(initial_balance_usdt)
        self.fee_rate = fee_rate
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.order_history: List[Dict[str, Any]] = []
        self.market_fetcher = MarketFetcher(use_paper_trading=False)

    def get_latest_price(self, symbol: str) -> float:
        """دریافت آخرین قیمت بازار از طریق آخرین کندل ۱ دقیقه والکس."""
        try:
            candles = self.market_fetcher.fetch_ohlcv(
                exchange_name="WALLEX",
                symbol=symbol,
                timeframe="1m",
                limit=1,
            )
            if candles:
                return float(candles[-1]["close"])
        except Exception:
            pass
        return 0.0

    def get_market_candles(
        self,
        symbol: str,
        timeframe: str = "15m",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """دریافت کندل‌های تاریخی و لایو از والکس."""
        return self.market_fetcher.fetch_ohlcv(
            exchange_name="WALLEX",
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

    def open_position(
        self,
        symbol: str,
        side: str,
        amount_usdt: float,
        leverage: int = 1,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Dict[str, Any]:
        """باز کردن پوزیشن پیپر تریدینگ با قیمت زنده والکس."""
        side = side.upper()
        if side not in ["BUY", "SELL", "LONG", "SHORT"]:
            raise ValueError(f"Invalid side: {side}")

        current_price = self.get_latest_price(symbol)
        if current_price <= 0:
            raise RuntimeError(f"Cannot fetch valid market price for {symbol}")

        fee = amount_usdt * self.fee_rate
        total_cost = amount_usdt + fee

        if total_cost > self.balance_usdt:
            raise ValueError(f"Insufficient funds: required {total_cost:.2f}, balance {self.balance_usdt:.2f}")

        self.balance_usdt -= total_cost
        position_id = f"pos_{int(time.time() * 1000)}"

        position = {
            "id": position_id,
            "symbol": symbol.upper(),
            "side": side,
            "entry_price": current_price,
            "amount_usdt": amount_usdt,
            "leverage": leverage,
            "effective_value": amount_usdt * leverage,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "open_time": time.time(),
            "status": "OPEN",
        }

        self.positions[position_id] = position
        return position

    def close_position(self, position_id: str) -> Dict[str, Any]:
        """بستن پوزیشن بر اساس قیمت لحظه‌ای و محاسبه PnL."""
        if position_id not in self.positions:
            raise KeyError(f"Position {position_id} not found.")

        pos = self.positions.pop(position_id)
        current_price = self.get_latest_price(pos["symbol"])
        if current_price <= 0:
            current_price = pos["entry_price"]

        entry = pos["entry_price"]
        side = pos["side"]
        lev = pos["leverage"]
        margin = pos["amount_usdt"]

        # محاسبه سود/زیان درصدی
        if side in ["BUY", "LONG"]:
            pnl_percent = ((current_price - entry) / entry) * lev
        else:
            pnl_percent = ((entry - current_price) / entry) * lev

        raw_pnl = margin * pnl_percent
        exit_fee = (margin + raw_pnl) * self.fee_rate
        net_pnl = raw_pnl - exit_fee

        returned_capital = margin + net_pnl
        self.balance_usdt += max(0.0, returned_capital)

        pos["exit_price"] = current_price
        pos["close_time"] = time.time()
        pos["pnl_usdt"] = net_pnl
        pos["status"] = "CLOSED"

        self.order_history.append(pos)
        return pos
