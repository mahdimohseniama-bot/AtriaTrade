import pytest
import responses
from src.exchange import ExchangeFactory
from src.exchange.adapters.binance_testnet import BinanceTestnetAdapter
from src.exchange.models import Ticker

def test_binance_testnet_registered():
    adapter = ExchangeFactory.create("BINANCE_TESTNET")
    assert isinstance(adapter, BinanceTestnetAdapter)

@responses.activate
def test_binance_testnet_get_ticker():
    adapter = ExchangeFactory.create("BINANCE_TESTNET")
    
    # Mock کردن APIهای بایننس
    responses.add(
        responses.GET,
        "https://testnet.binance.vision/api/v3/ticker/price?symbol=BTCUSDT",
        json={"symbol": "BTCUSDT", "price": "61000.00"},
        status=200
    )
    responses.add(
        responses.GET,
        "https://testnet.binance.vision/api/v3/depth?symbol=BTCUSDT&limit=5",
        json={"bids": [["60999.00", "1.0"]], "asks": [["61001.00", "1.0"]]},
        status=200
    )

    ticker = adapter.get_ticker("BTCUSDT")
    assert isinstance(ticker, Ticker)
    assert ticker.symbol == "BTCUSDT"
    assert ticker.last_price == 61000.00
    assert ticker.bid == 60999.00
    assert ticker.ask == 61001.00

def test_binance_testnet_place_order_fails_without_keys():
    # چون کلید واقعی نداریم، باید خطای PermissionError بدهد
    adapter = ExchangeFactory.create("BINANCE_TESTNET", api_key="", secret_key="")
    with pytest.raises(PermissionError) as excinfo:
        adapter.place_order("BTCUSDT", "BUY", "MARKET", 0.1)
    
    assert "API keys are not configured" in str(excinfo.value)
