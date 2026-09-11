import pytest
from unittest.mock import MagicMock, patch
from src.exchange.adapters.wallex import WallexAdapter
from src.exchange.models import Ticker, OrderResponse


@pytest.fixture
def wallex_adapter():
    return WallexAdapter(api_key="test_api_key_123")


def test_wallex_adapter_initialization(wallex_adapter):
    assert wallex_adapter.api_key == "test_api_key_123"
    assert wallex_adapter.base_url == "https://api.wallex.ir"
    assert wallex_adapter.LIVE_ORDER_EXECUTION_ENABLED is False
    assert wallex_adapter.format_symbol("BTC-USDT") == "BTCUSDT"
    assert wallex_adapter.format_symbol("BTC/IRT") == "BTCTMN"


def test_test_connection_success(wallex_adapter):
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch.object(wallex_adapter.session, "get", return_value=mock_resp) as mock_get:
        assert wallex_adapter.test_connection() is True
        mock_get.assert_called_once_with("https://api.wallex.ir/v1/markets", timeout=5)


def test_test_connection_failure(wallex_adapter):
    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch.object(wallex_adapter.session, "get", return_value=mock_resp):
        assert wallex_adapter.test_connection() is False


def test_get_ticker_success(wallex_adapter):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "symbols": {
                "BTCUSDT": {
                    "stats": {
                        "bidPrice": "62000.5",
                        "askPrice": "62010.0",
                        "lastPrice": "62005.0",
                        "24h_volume": "1420.5"
                    }
                }
            }
        }
    }

    with patch.object(wallex_adapter.session, "get", return_value=mock_resp):
        ticker = wallex_adapter.get_ticker("BTC/USDT")
        assert isinstance(ticker, Ticker)
        assert ticker.symbol == "BTCUSDT"
        assert ticker.bid == 62000.5
        assert ticker.ask == 62010.0
        assert ticker.last_price == 62005.0
        assert ticker.volume == 1420.5


def test_place_order_safety_killswitch(wallex_adapter):
    with pytest.raises(PermissionError, match="Live order execution is disabled"):
        wallex_adapter.place_order(
            symbol="BTC/USDT",
            side="BUY",
            order_type="LIMIT",
            quantity=0.01,
            price=60000.0
        )


def test_place_order_success_when_enabled(wallex_adapter):
    wallex_adapter.LIVE_ORDER_EXECUTION_ENABLED = True

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "id": "wx_ord_999",
            "clientOrderId": "wx_ord_999"
        }
    }

    with patch.object(wallex_adapter.session, "post", return_value=mock_resp) as mock_post:
        resp = wallex_adapter.place_order(
            symbol="BTC/USDT",
            side="BUY",
            order_type="LIMIT",
            quantity=0.01,
            price=60000.0
        )
        assert isinstance(resp, OrderResponse)
        assert resp.order_id == "wx_ord_999"
        assert resp.symbol == "BTCUSDT"
        assert resp.status == "OPEN"
        assert resp.quantity == 0.01
        assert resp.price == 60000.0
        mock_post.assert_called_once()
