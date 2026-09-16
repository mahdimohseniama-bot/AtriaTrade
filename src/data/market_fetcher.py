from __future__ import annotations

import time
from typing import Any, Dict, List

class MarketFetcher:
    """
    ماژول دریافت داده‌های بازار (OHLCV).
    در حالت Paper Trading داده‌های شبیه‌سازی‌شده تولید می‌کند.
    هیچ‌گونه فراخوانی واقعی به API بدون اجازه انجام نمی‌شود.
    """

    def __init__(self, use_paper_trading: bool = True):
        self.use_paper_trading = use_paper_trading

    def fetch_ohlcv(
        self,
        exchange_name: str,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """دریافت داده‌های کندل‌استیک بازار."""
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer.")
        
        if not symbol or not timeframe:
            raise ValueError("Symbol and timeframe cannot be empty.")

        if self.use_paper_trading:
            return self._generate_mock_ohlcv(symbol, timeframe, limit)
        
        raise NotImplementedError("Live data fetching is disabled.")

    def _generate_mock_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """تولید داده‌های شبیه‌سازی شده برای بک‌تست و پیپر تریدینگ."""
        data = []
        now = int(time.time() * 1000)
        
        interval_ms = 60000 
        if timeframe == "1h":
            interval_ms = 3600000
        elif timeframe == "1d":
            interval_ms = 86400000

        for i in range(limit):
            timestamp = now - ((limit - i) * interval_ms)
            # تعیین یک قیمت پایه فرضی برای شبیه‌سازی واقع‌گرایانه
            base_price = 50000.0 if "BTC" in symbol.upper() else 2000.0
            
            data.append({
                "timestamp": timestamp,
                "open": base_price,
                "high": base_price + 50.0,
                "low": base_price - 50.0,
                "close": base_price + 25.0,
                "volume": 10.5
            })
        
        return data
