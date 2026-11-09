from .base_exchange import BaseExchangeAdapter
from .models import Ticker, OrderResponse
from .factory import ExchangeFactory
from .adapters.dummy_exchange import DummyExchangeAdapter
from .adapters.binance_testnet import BinanceTestnetAdapter
from .adapters.nobitex import NobitexAdapter
from .adapters.wallex import WallexAdapter

ExchangeFactory.register("DUMMY", DummyExchangeAdapter)
ExchangeFactory.register("BINANCE_TESTNET", BinanceTestnetAdapter)
ExchangeFactory.register("NOBITEX", NobitexAdapter)
ExchangeFactory.register("WALLEX", WallexAdapter)

__all__ = [
    "BaseExchangeAdapter",
    "Ticker",
    "OrderResponse",
    "ExchangeFactory",
    "DummyExchangeAdapter",
    "BinanceTestnetAdapter",
    "NobitexAdapter",
    "WallexAdapter",
]
