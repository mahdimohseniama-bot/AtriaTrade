from .models import Ticker, OrderResponse
from .base_exchange import BaseExchangeAdapter
from .factory import ExchangeFactory
from .adapters.dummy_exchange import DummyExchangeAdapter
from .adapters.binance_testnet import BinanceTestnetAdapter
from .adapters.nobitex import NobitexAdapter
from .adapters.wallex import WallexAdapter

# Register adapters in ExchangeFactory
ExchangeFactory.register("DUMMY", DummyExchangeAdapter)
ExchangeFactory.register("BINANCE_TESTNET", BinanceTestnetAdapter)
ExchangeFactory.register("NOBITEX", NobitexAdapter)
ExchangeFactory.register("WALLEX", WallexAdapter)

__all__ = ["Ticker", "OrderResponse", "BaseExchangeAdapter", "ExchangeFactory"]
