from .adapters.dummy_exchange import DummyExchangeAdapter
from .adapters.binance_testnet import BinanceTestnetAdapter
from .adapters.nobitex import NobitexAdapter
from .adapters.wallex import WallexAdapter
from .factory import ExchangeFactory

ExchangeFactory.register("DUMMY", DummyExchangeAdapter)
ExchangeFactory.register("BINANCE_TESTNET", BinanceTestnetAdapter)
ExchangeFactory.register("NOBITEX", NobitexAdapter)
ExchangeFactory.register("WALLEX", WallexAdapter)
