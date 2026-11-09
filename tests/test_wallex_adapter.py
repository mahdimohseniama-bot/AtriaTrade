from unittest.mock import patch, MagicMock
import pytest
import requests
from src.exchange.adapters.wallex import WallexAdapter
from src.exchange.models import Ticker


def test_wallex_adapter_init_without_token():
    adapter = WallexAdapter()
    assert adapter.api_token is None
    assert adapter._get_headers() == {}
    assert adapter.LIVE_ORDER_EXECUTION_ENABLED is False


def test_wallex_adapter_init_with_token():
    adapter = WallexAdapter(api_token="test_token_123")
    assert adapter.api_token == "test_token_123"
    assert adapter._get_headers() == {"X-API-KEY": "test_token_123"}


@patch("src.exchange.adapters.wallex.requests.get")
def test_wallex_test_connection_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    adapter = WallexAdapter()
    assert adapter.test_connection() is True


@patch("src.exchange.adapters.wallex.requests.get")
def test_wallex_test_connection_failure(mock_get):
    mock_get.side_effect = requests.RequestException("Network error")
    adapter = WallexAdapter()
    assert adapter.test_connection() is False


@patch("src.exchange.adapters.wallex.requests.get")
def test_wallex_get_ticker_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "symbols": {
                "BTCTMN": {
                    "stats": {
                        "bidPrice": "62000000000",
                        "askPrice": "62100000000",
                        "lastPrice": "62050000000",
                        "24h_volume": "14.5",
                    }
                }
            }
        }
    }
    mock_get.return_value = mock_resp

    adapter = WallexAdapter()
    ticker = adapter.get_ticker("BTCTMN")

    assert isinstance(ticker, Ticker)
    assert ticker.symbol == "BTCTMN"
    assert ticker.bid == 62000000000.0
    assert ticker.ask == 62100000000.0
    assert ticker.last_price == 62050000000.0
    assert ticker.volume == 14.5


@patch("src.exchange.adapters.wallex.requests.get")
def test_wallex_get_ticker_symbol_not_found(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"result": {"symbols": {}}}
    mock_get.return_value = mock_resp

    adapter = WallexAdapter()
    with pytest.raises(ValueError, match="Symbol UNKNOWNTMN not found on Wallex"):
        adapter.get_ticker("UNKNOWNTMN")


@patch("src.exchange.adapters.wallex.requests.get")
def test_wallex_get_order_book_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "ask": [{"price": "62100000000", "quantity": "0.1"}],
            "bid": [{"price": "62000000000", "quantity": "0.2"}],
        }
    }
    mock_get.return_value = mock_resp

    adapter = WallexAdapter()
    ob = adapter.get_order_book("BTCTMN")

    assert "ask" in ob
    assert "bid" in ob
    assert len(ob["ask"]) == 1


def test_wallex_place_order_guard_no_token():
    adapter = WallexAdapter()
    with pytest.raises(PermissionError, match="API token is not configured for Wallex"):
        adapter.place_order("BTCTMN", "BUY", "LIMIT", 0.01, 62000000000)


def test_wallex_place_order_guard_live_disabled():
    adapter = WallexAdapter(api_token="valid_key")
    with pytest.raises(PermissionError, match="Live order execution is disabled for Wallex"):
        adapter.place_order("BTCTMN", "BUY", "LIMIT", 0.01, 62000000000)
