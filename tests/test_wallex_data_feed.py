import pytest
from unittest.mock import MagicMock, patch
from src.adapters.wallex_data_feed import WallexDataFeed

def test_wallex_data_feed_success():
    feed = WallexDataFeed()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "result": {
            "ask": [{"price": "70500", "quantity": "100"}],
            "bid": [{"price": "70400", "quantity": "120"}]
        }
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch.object(feed.session, "get", return_value=mock_response):
        res = feed.get_orderbook("USDTTMN")
        assert res["status"] == "success"
        price = feed.get_ticker_price("USDTTMN")
        assert price == 70450.0

def test_wallex_data_feed_error_handling():
    feed = WallexDataFeed()
    with patch.object(feed.session, "get", side_effect=Exception("Network unreachable")):
        res = feed.get_orderbook("USDTTMN")
        assert res["status"] == "error"
        assert "Network unreachable" in res["message"]
        assert feed.get_ticker_price("USDTTMN") is None
