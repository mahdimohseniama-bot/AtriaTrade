from abc import ABC, abstractmethod
from src.exchange.models import Ticker, OrderResponse

class BaseExchangeAdapter(ABC):
    @abstractmethod
    def test_connection(self) -> bool:
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> Ticker:
        pass

    @abstractmethod
    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = 0.0) -> OrderResponse:
        pass

    @abstractmethod
    def format_symbol(self, symbol: str) -> str:
        """استانداردسازی نماد معاملاتی"""
        pass
