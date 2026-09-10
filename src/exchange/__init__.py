from src.exchange.base_exchange import BaseExchangeAdapter
from src.exchange.factory import ExchangeFactory
from src.exchange.adapters.dummy_exchange import DummyExchangeAdapter
from src.exchange.adapters.nobitex import NobitexAdapter

# Register built-in adapters
ExchangeFactory.register("DUMMY", DummyExchangeAdapter)
ExchangeFactory.register("NOBITEX", NobitexAdapter)

try:
    from src.exchange.adapters.binance_testnet import BinanceTestnetAdapter
    ExchangeFactory.register("BINANCE", BinanceTestnetAdapter)
except Exception:
    pass

__all__ = ["BaseExchangeAdapter", "ExchangeFactory", "NobitexAdapter", "DummyExchangeAdapter"]
