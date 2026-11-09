import pytest
from unittest.mock import patch, MagicMock
from src.exchange.adapters.wallex import WallexAdapter

@pytest.fixture
def wallex_adapter():
    return WallexAdapter(api_token="test_wallex_token")

def test_wallex_adapter_initialization(wallex_adapter):
    assert wallex_adapter is not None
    assert wallex_adapter.api_token == "test_wallex_token"
    assert wallex_adapter.base_url == "https://api.wallex.ir/v1"
    assert wallex_adapter.headers["X-API-KEY"] == "test_wallex_token"

@patch("requests.get")
def test_wallex_test_connection_success(mock_get, wallex_adapter):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp
    assert wallex_adapter.test_connection() is True

@patch("requests.get")
def test_wallex_test_connection_failure(mock_get, wallex_adapter):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_get.return_value = mock_resp
    assert wallex_adapter.test_connection() is False

@patch("requests.get")
def test_wallex_get_ticker(mock_get, wallex_adapter):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "symbols": {
                "BTCUSDT": {
                    "stats": {
                        "lastPrice": "65000.50",
                        "bidPrice": "64990.00",
                        "askPrice": "65010.00",
                        "24h_volume": "120.5"
                    }
                }
            }
        },
        "success": True
    }
    mock_get.return_value = mock_resp

    ticker = wallex_adapter.get_ticker("BTCUSDT")
    assert ticker.symbol == "BTCUSDT"
    assert ticker.last_price == 65000.50
    assert ticker.bid == 64990.00
    assert ticker.ask == 65010.00
    assert ticker.volume == 120.5

@patch("requests.get")
def test_wallex_get_order_book(mock_get, wallex_adapter):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "ask": [{"price": "65010", "quantity": "0.5"}],
            "bid": [{"price": "64990", "quantity": "0.8"}]
        }
    }
    mock_get.return_value = mock_resp

    orderbook = wallex_adapter.get_order_book("BTCUSDT")
    assert "ask" in orderbook
    assert "bid" in orderbook
    assert len(orderbook["ask"]) == 1
    assert len(orderbook["bid"]) == 1

def test_wallex_place_order_guard_disabled(wallex_adapter):
    with pytest.raises(PermissionError) as exc_info:
        wallex_adapter.place_order("BTCUSDT", "BUY", "LIMIT", 0.01, 65000.0)
    assert "Live order execution is disabled" in str(exc_info.value)

@patch("requests.post")
def test_wallex_place_order_success(mock_post, wallex_adapter):
    wallex_adapter.LIVE_ORDER_EXECUTION_ENABLED = True
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "result": {"orderId": "wlx_778899"}
    }
    mock_post.return_value = mock_resp

    res = wallex_adapter.place_order("BTCUSDT", "BUY", "LIMIT", 0.005, 64000.0)
    assert res.order_id == "wlx_778899"
    assert res.symbol == "BTCUSDT"
    assert res.quantity == 0.005
    assert res.price == 64000.0
    wallex_adapter.LIVE_ORDER_EXECUTION_ENABLED = False

@patch("requests.delete")
def test_wallex_cancel_order_success(mock_delete, wallex_adapter):
    wallex_adapter.LIVE_ORDER_EXECUTION_ENABLED = True
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_delete.return_value = mock_resp

    success = wallex_adapter.cancel_order("wlx_778899")
    assert success is True
    wallex_adapter.LIVE_ORDER_EXECUTION_ENABLED = False
