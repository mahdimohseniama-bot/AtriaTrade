import pytest
from unittest.mock import MagicMock, patch
from src.adapters.wallex_paper import WallexPaperAdapter
from src.adapters.paper_factory import PaperExchangeFactory

def test_paper_factory_wallex():
    adapter = PaperExchangeFactory.create_adapter("wallex")
    assert isinstance(adapter, WallexPaperAdapter)

@patch("src.adapters.wallex_paper.requests.get")
def test_wallex_paper_workflow(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "result": {
            "bid": [{"price": 600000.0, "quantity": 1.5}],
            "ask": [{"price": 601000.0, "quantity": 2.0}]
        }
    }
    mock_get.return_value = mock_resp

    adapter = PaperExchangeFactory.create_adapter("wallex")
    
    # 1. Check orderbook
    ob = adapter.get_orderbook("USDTTMN")
    assert "bids" in ob
    assert ob["bids"][0]["price"] == 600000.0

    # 2. Record initial balance
    initial_usdt = adapter.get_balance("USDT")

    # 3. Place market order using standard adapter method
    buy_amount = 1.0
    res = adapter.place_order(
        symbol="USDTTMN",
        side="buy",
        order_type="market",
        amount=buy_amount
    )
    assert res["status"] == "success"
    assert res["result"]["status"] == "FILLED"

    # 4. Verify balance increment
    usdt_bal = adapter.get_balance("USDT")
    assert usdt_bal == initial_usdt + buy_amount
