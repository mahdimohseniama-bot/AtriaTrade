import random
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("AtriaTrade.MarketFetcher")

class MarketFetcher:
    """
    Mock MarketFetcher for Paper Trading and Offline Development.
    Provides simulated real-time market data without network dependency.
    """
    def __init__(self):
        self.mock_prices = {
            'BTC/USDT': 64250.0,
            'ETH/USDT': 3450.0,
            'XAU/USD': 2510.0,
            'SOL/USDT': 145.0
        }
        logger.info("MarketFetcher initialized in MOCK mode.")

    def get_last_price(self, symbol: str) -> float:
        """
        Returns a simulated live price with slight realistic fluctuations.
        """
        symbol_upper = symbol.upper().strip()
        base_price = self.mock_prices.get(symbol_upper, 100.0)
        # نوسان جزئی و طبیعی شبیه‌ساز (مثبت/منفی 0.1 درصد)
        delta = base_price * random.uniform(-0.001, 0.001)
        current_price = round(base_price + delta, 2)
        return current_price

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Returns full simulated ticker structure compatible with CCXT/Exchange standard.
        """
        last_price = self.get_last_price(symbol)
        return {
            "symbol": symbol,
            "last": last_price,
            "bid": round(last_price * 0.9998, 2),
            "ask": round(last_price * 1.0002, 2),
            "high": round(last_price * 1.02, 2),
            "low": round(last_price * 0.98, 2),
            "volume": round(random.uniform(50.0, 500.0), 4),
            "status": "mock_live"
        }

    def get_market_stats(self) -> Dict[str, Any]:
        return {
            "status": "online",
            "mode": "paper_mock",
            "active_pairs": list(self.mock_prices.keys())
        }
