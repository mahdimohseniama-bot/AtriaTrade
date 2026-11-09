import pytest
from src.exchange import ExchangeFactory
from src.exchange.adapters.wallex import WallexAdapter

def test_factory_creates_wallex_adapter():
    adapter = ExchangeFactory.create("wallex", api_token="test_wallex_token_123")
    assert isinstance(adapter, WallexAdapter)
    assert adapter.api_token == "test_wallex_token_123"
    assert adapter._get_headers().get("X-API-KEY") == "test_wallex_token_123"

def test_factory_creates_wallex_without_token():
    adapter = ExchangeFactory.create("wallex")
    assert isinstance(adapter, WallexAdapter)
    assert adapter.api_token is None
    assert adapter._get_headers() == {}

def test_factory_unsupported_exchange_raises():
    with pytest.raises(ValueError, match="Exchange adapter .* is not registered"):
        ExchangeFactory.create("unknown_crypto_exchange")
