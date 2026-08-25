import pytest
from src.exchange import ExchangeFactory, BaseExchangeAdapter
from src.exchange.models import Ticker, OrderResponse

def test_exchange_factory_registration():
    # بررسی می‌کنیم که صرافی مجازی با موفقیت در سیستم ثبت شده باشد
    adapter = ExchangeFactory.create("DUMMY")
    assert isinstance(adapter, BaseExchangeAdapter)
    assert adapter.test_connection() is True

def test_dummy_exchange_get_ticker():
    # تست دریافت قیمت استاندارد
    adapter = ExchangeFactory.create("DUMMY")
    ticker = adapter.get_ticker("BTCUSDT")
    assert isinstance(ticker, Ticker)
    assert ticker.symbol == "BTCUSDT"
    assert ticker.last_price == 60000.0
    assert ticker.ask > ticker.bid

def test_dummy_exchange_place_order():
    # تست ثبت سفارش مجازی
    adapter = ExchangeFactory.create("DUMMY")
    response = adapter.place_order("BTCUSDT", "BUY", "MARKET", 0.01)
    
    assert isinstance(response, OrderResponse)
    assert response.status == "FILLED"
    assert response.quantity == 0.01
    assert "dummy_" in response.order_id

def test_unregistered_exchange_raises_error():
    # تست امنیت: صرافی ثبت نشده باید سیستم را بلوکه کند
    with pytest.raises(ValueError):
        ExchangeFactory.create("INVALID_EXCHANGE")
