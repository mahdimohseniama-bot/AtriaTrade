import pytest
from unittest.mock import patch, MagicMock
from src.adapters.wallex_paper import WallexPaperAdapter

def test_symbol_normalization():
    adapter = WallexPaperAdapter()
    assert adapter.normalize_symbol("USDT_TMN") == "USDTTMN"
    assert adapter.normalize_symbol("btc_tmn") == "BTCTMN"
    assert adapter.normalize_symbol(None) == "USDTTMN"

@patch("src.adapters.wallex_paper.requests.get")
def test_get_orderbook_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "result": {
            "bid": [{"price": 268000, "quantity": 10.0}],
            "ask": [{"price": 268500, "quantity": 5.0}]
        }
    }
    mock_get.return_value = mock_resp

    adapter = WallexPaperAdapter()
    ob = adapter.get_orderbook("USDTTMN")
    assert ob["success"] is True
    assert len(ob["bids"]) == 1
    assert ob["bids"][0]["price"] == 268000.0
    assert ob["asks"][0]["price"] == 268500.0

@patch("src.adapters.wallex_paper.requests.get")
def test_paper_execution_buy_and_sell(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "result": {
            "bid": [{"price": 260000, "quantity": 100}],
            "ask": [{"price": 260000, "quantity": 100}]
        }
    }
    mock_get.return_value = mock_resp

    adapter = WallexPaperAdapter()
    initial_tmn = adapter.get_balance("TMN")
    initial_usdt = adapter.get_balance("USDT")

    # Buy 10 USDT at 260,000 TMN
    buy_res = adapter.execute_paper_order(side="buy", symbol="USDTTMN", quantity=10.0)
    assert buy_res["status"] == "filled"
    assert adapter.get_balance("USDT") == initial_usdt + 10.0
    assert adapter.get_balance("TMN") == initial_tmn - (10.0 * 260000)

    # Sell 10 USDT at 260,000 TMN
    sell_res = adapter.execute_paper_order(side="sell", symbol="USDTTMN", quantity=10.0)
    assert sell_res["status"] == "filled"
    assert adapter.get_balance("USDT") == initial_usdt
    assert adapter.get_balance("TMN") == initial_tmn
