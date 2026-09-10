from typing import Dict, Type
from src.exchange.adapters.nobitex import NobitexAdapter
from src.exchange.adapters.binance_testnet import BinanceTestnetAdapter
from src.exchange.adapters.dummy_exchange import DummyExchangeAdapter

class ExchangeFactory:
    _registry = {
        "nobitex": NobitexAdapter,
        "binance_testnet": BinanceTestnetAdapter,
        "dummy": DummyExchangeAdapter
    }

    @classmethod
    def create(cls, exchange_name: str, **kwargs):
        key = exchange_name.lower()
        if key not in cls._registry:
            raise ValueError(f"Exchange '{exchange_name}' is not supported.")
        adapter_cls = cls._registry[key]
        return adapter_cls(**kwargs)

    @classmethod
    def register(cls, name: str, adapter_cls: Type):
        cls._registry[name.lower()] = adapter_cls
