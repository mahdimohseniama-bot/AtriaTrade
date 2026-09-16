from typing import Dict, Type
from .base_exchange import BaseExchangeAdapter

class ExchangeFactory:
    _adapters: Dict[str, Type[BaseExchangeAdapter]] = {}

    @classmethod
    def register(cls, name: str, adapter_class: Type[BaseExchangeAdapter]) -> None:
        """ثبت یک صرافی جدید در سیستم"""
        cls._adapters[name.upper()] = adapter_class

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseExchangeAdapter:
        """ساخت و بازگرداندن نمونه‌ای از صرافی مورد نظر"""
        name_upper = name.upper()
        if name_upper not in cls._adapters:
            raise ValueError(f"Exchange adapter '{name}' is not registered. Available: {list(cls._adapters.keys())}")
        return cls._adapters[name_upper](**kwargs)
