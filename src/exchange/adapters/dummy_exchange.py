import time
from ...exchange.base_exchange import BaseExchangeAdapter
from ...exchange.models import Ticker, OrderResponse

class DummyExchangeAdapter(BaseExchangeAdapter):
    """
    صرافی شبیه‌ساز مجازی برای Paper Trading و تست کدهای هسته.
    این کلاس نیازی به اینترنت ندارد و رفتار صرافی را تقلید می‌کند.
    """
    def __init__(self, **kwargs):
        self.name = "DUMMY"
        self.mock_prices = {"BTCUSDT": 60000.0, "ETHUSDT": 3000.0, "USDTIRT": 60000.0}

    def test_connection(self) -> bool:
        return True

    def get_ticker(self, symbol: str) -> Ticker:
        price = self.mock_prices.get(symbol, 100.0)
        return Ticker(
            symbol=symbol,
            bid=price - 0.5,
            ask=price + 0.5,
            last_price=price,
            volume=1500.0
        )

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = 0.0) -> OrderResponse:
        exec_price = price if price > 0 else self.mock_prices.get(symbol, 100.0)
        return OrderResponse(
            order_id=f"dummy_{int(time.time())}",
            symbol=symbol,
            status="FILLED",
            price=exec_price,
            quantity=quantity,
            filled_quantity=quantity,
            raw_data={"note": "mock execution successful"}
        )
