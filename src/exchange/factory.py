from typing import Dict, Type
from src.exchange.base_exchange import BaseExchangeAdapter

class ExchangeFactory:
    _adapters: Dict[str, Type[BaseExchangeAdapter]] = {}

    @classmethod
    def register(cls, name: str, adapter_class: Type[BaseExchangeAdapter]) -> None:
        cls._adapters[name.upper()] = adapter_class

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseExchangeAdapter:
        name_upper = name.upper()
        if name_upper not in cls._adapters:
            raise ValueError(f"Exchange adapter '{name}' is not registered. Available: {list(cls._adapters.keys())}")
        return cls._adapters[name_upper](**kwargs)
