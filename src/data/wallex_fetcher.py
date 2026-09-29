"""
Wallex Market Data Fetcher & Live Candle Adapter.
Resilient HTTP client with custom timeout, retry, and fallback parsing.
"""
import time
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.core.fvg_detector import Candle


@dataclass
class WallexMarketStats:
    symbol: str
    bid_price: float
    ask_price: float
    last_price: float
    volume_24h: float
    timestamp: float


class WallexDataFetcher:
    BASE_URL = "https://api.wallex.ir"

    def __init__(self, timeout: float = 8.0, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AtriaTrade/1.0",
            "Accept": "application/json"
        })

    def get_order_book(self, symbol: str = "USDTTMN") -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}/v1/depth"
        params = {"symbol": symbol}
        
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success", False):
                        return data.get("result", {})
            except Exception:
                time.sleep(0.5 * attempt)
        return None

    def get_ohlc_candles(self, symbol: str = "USDTTMN", resolution: str = "60", limit: int = 50) -> List[Candle]:
        """
        Fetch OHLC candles from Wallex UDF.
        Resolution: 1, 5, 15, 60, 240, 1D
        """
        url = f"{self.BASE_URL}/v1/udf/history"
        now = int(time.time())
        res_seconds = int(resolution) * 60 if resolution.isdigit() else 86400
        from_time = now - (res_seconds * limit)

        params = {
            "symbol": symbol,
            "resolution": resolution,
            "from": from_time,
            "to": now
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    raw = resp.json()
                    if raw.get("s") == "ok":
                        candles: List[Candle] = []
                        times = raw.get("t", [])
                        opens = raw.get("o", [])
                        highs = raw.get("h", [])
                        lows = raw.get("l", [])
                        closes = raw.get("c", [])

                        for i in range(len(times)):
                            candles.append(Candle(
                                timestamp=float(times[i]),
                                open=float(opens[i]),
                                high=float(highs[i]),
                                low=float(lows[i]),
                                close=float(closes[i])
                            ))
                        return candles
            except Exception:
                time.sleep(0.5 * attempt)
        return []

    def get_market_stats(self, symbol: str = "USDTTMN") -> Optional[WallexMarketStats]:
        book = self.get_order_book(symbol)
        if not book:
            return None
        
        bid_orders = book.get("bid", [])
        ask_orders = book.get("ask", [])
        
        best_bid = float(bid_orders[0]["price"]) if bid_orders else 0.0
        best_ask = float(ask_orders[0]["price"]) if ask_orders else 0.0
        last_price = (best_bid + best_ask) / 2 if (best_bid and best_ask) else (best_bid or best_ask)

        return WallexMarketStats(
            symbol=symbol,
            bid_price=best_bid,
            ask_price=best_ask,
            last_price=last_price,
            volume_24h=0.0,
            timestamp=time.time()
        )
