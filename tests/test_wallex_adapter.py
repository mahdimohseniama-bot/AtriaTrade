import pytest
from unittest.mock import patch, MagicMock
from src.exchange.adapters.wallex import WallexAdapter
from src.exchange.factory import ExchangeFactory
from src.exchange.models import Ticker, OrderResponse

@pytest.fixture
def wallex_adapter():
    return WallexAdapter(api_token="*******")

def test_wallex_factory_registration():
    adapter = ExchangeFactory.create("WALLEX", api_token="*******")
    assert isinstance(adapter, WallexAdapter)
    assert adapter.api_token == "*******"

def test_wallex_headers(wallex_adapter):
    headers = wallex_adapter._get_headers() if hasattr(wallex_adapter, '_get_headers') else getattr(wallex_adapter, 'headers', {})
    assert "*******" in str(headers)

@patch("requests.get")
def test_wallex_test_connection_success(mock_get, wallex_adapter):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp
    assert wallex_adapter.test_connection() is True

@patch("requests.get")
def test_wallex_test_connection_failure(mock_get, wallex_adapter):
    mock_get.side_effect = Exception("Connection timeout")
    assert wallex_adapter.test_connection() is False

@patch("requests.get")
def test_wallex_fetch_ticker_mock(mock_get, wallex_adapter):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "result": {
            "symbols": {
                "BTCUSDT": {
                    "stats": {
                        "lastPrice": "65000.5",
                        "bidPrice": "64990.0",
                        "askPrice": "65010.0",
                        "24h_volume": "120.5"
                    }
                }
            }
        }
    }
    mock_get.return_value = mock_resp

    ticker = wallex_adapter.get_ticker("BTCUSDT")
    assert ticker is not None
    assert ticker.last_price == 65000.5
    assert ticker.bid == 64990.0
    assert ticker.ask == 65010.0

@patch("requests.get")
def test_wallex_get_order_book_mock(mock_get, wallex_adapter):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "result": {
            "ask": [{"price": "65010.0", "quantity": "0.5"}],
            "bid": [{"price": "64990.0", "quantity": "1.2"}]
        }
    }
    mock_get.return_value = mock_resp

    ob = wallex_adapter.get_order_book("BTCUSDT")
    assert "ask" in ob
    assert "bid" in ob
    assert len(ob["ask"]) == 1

def test_wallex_place_order_permission_guard(wallex_adapter):
    with pytest.raises(PermissionError):
        wallex_adapter.place_order("BTCUSDT", "BUY", "LIMIT", 0.01, 65000.0)
