from .base_exchange import BaseExchangeAdapter
from .models import Ticker, OrderResponse
from .factory import ExchangeFactory
from .health import ExchangeHealthMonitor, ExchangeHealthStatus
from .adapters.dummy_exchange import DummyExchangeAdapter
from .adapters.wallex import WallexAdapter
from .adapters.nobitex import NobitexAdapter
from .adapters.binance_testnet import BinanceTestnetAdapter

# ثبت استاندارد و رسمی آداپتورها در فکتوری مرکزی
ExchangeFactory.register("DUMMY", DummyExchangeAdapter)
ExchangeFactory.register("WALLEX", WallexAdapter)
ExchangeFactory.register("NOBITEX", NobitexAdapter)
ExchangeFactory.register("BINANCE_TESTNET", BinanceTestnetAdapter)

__all__ = [
    "BaseExchangeAdapter",
    "Ticker",
    "OrderResponse",
    "ExchangeFactory",
    "ExchangeHealthMonitor",
    "ExchangeHealthStatus",
    "DummyExchangeAdapter",
    "WallexAdapter",
    "NobitexAdapter",
    "BinanceTestnetAdapter",
]
