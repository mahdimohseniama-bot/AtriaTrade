from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import Ticker, OrderResponse

class BaseExchangeAdapter(ABC):
    """رابط استاندارد برای تمامی صرافی‌ها.
    هر صرافی جدید (ایرانی یا خارجی) باید این متدها را پیاده‌سازی کند."""

    @abstractmethod
    def test_connection(self) -> bool:
        """بررسی اتصال به سرور صرافی"""

    @abstractmethod
    def get_ticker(self, symbol: str) -> Ticker:
        """دریافت قیمت زنده و اطلاعات نماد"""

    @abstractmethod
    def place_order(self, symbol: str, side: str, order_type: str,
                    quantity: float, price: float = 0.0) -> OrderResponse:
        """ارسال سفارش به صرافی"""

    @abstractmethod
    def format_symbol(self, symbol: str) -> str:
        """تبدیل و اعتبارسنجی نماد مطابق استاندارد صرافی"""
