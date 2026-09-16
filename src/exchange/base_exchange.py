from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import Ticker, OrderResponse

class BaseExchangeAdapter(ABC):
    """
    رابط استاندارد برای تمامی صرافی‌ها.
    هر صرافی جدید (ایرانی یا خارجی) باید این متدها را پیاده‌سازی کند.
    """
    
    @abstractmethod
    def test_connection(self) -> bool:
        """بررسی اتصال به سرور صرافی"""
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> Ticker:
        """دریافت قیمت زنده و اطلاعات نماد"""
        pass

    @abstractmethod
    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = 0.0) -> OrderResponse:
        """ارسال سفارش به صرافی"""
        pass
