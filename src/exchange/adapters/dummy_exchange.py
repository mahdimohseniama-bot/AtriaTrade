import time
from typing import Dict, Any
from ..base_exchange import BaseExchangeAdapter
from ..models import Ticker, OrderResponse
from ..validation import normalize_symbol


class DummyExchangeAdapter(BaseExchangeAdapter):
    """صرافی شبیه‌ساز مجازی برای Paper Trading و تست کدهای هسته."""
    
    def __init__(self, **kwargs):
        self.name = "DUMMY"
        self.mock_prices = {
            "BTCUSDT": 60000.0,
            "ETHUSDT": 3000.0,
            "USDTIRT": 60000.0,
            "BTCTMN": 60000.0
        }

    def format_symbol(self, symbol: str) -> str:
        """تبدیل و نرمال‌سازی استاندارد نماد برای محیط دامی."""
        normalized, _, _ = normalize_symbol(symbol)
        return normalized

    def test_connection(self) -> bool:
        return True

    def get_ticker(self, symbol: str) -> Ticker:
        formatted = self.format_symbol(symbol)
        price = self.mock_prices.get(formatted, 100.0)
        return Ticker(
            symbol=formatted,
            bid=price - 0.5,
            ask=price + 0.5,
            last_price=price,
            volume=1500.0
        )

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = 0.0
    ) -> OrderResponse:
        formatted = self.format_symbol(symbol)
        exec_price = price if price > 0 else self.mock_prices.get(formatted, 100.0)
        return OrderResponse(
            order_id=f"dummy_{int(time.time() * 1000)}",
            symbol=formatted,
            status="FILLED",
            price=exec_price,
            quantity=quantity,
            filled_quantity=quantity,
            raw_data={"note": "mock execution successful"}
        )
