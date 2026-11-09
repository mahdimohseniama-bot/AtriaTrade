import pytest
from src.adapters.paper_factory import PaperExchangeFactory

def test_wallex_paper_full_session():
    # Provide complete initial balances including btc
    initial_balances = {
        "tm": 200_000_000.0,
        "usdt": 5000.0,
        "btc": 0.05,
        "eth": 0.5
    }
    adapter = PaperExchangeFactory.create_adapter("wallex", initial_balances)
    assert adapter.get_balance("tm") == 200_000_000.0
    assert adapter.get_balance("btc") == 0.05
    
    # 1. Test Buy Order
    adapter.set_market_price("BTCTM", 6_500_000_000.0)
    buy_order = adapter.place_order("BTCTM", "buy", "market", 0.005)
    assert buy_order["status"] == "success"
    assert buy_order["result"]["status"] == "FILLED"
    assert adapter.get_balance("btc") == 0.05 + 0.005
    
    # 2. Test Sell Order
    sell_order = adapter.place_order("BTCTM", "sell", "limit", 0.01, 6_600_000_000.0)
    assert sell_order["status"] == "success"
    assert sell_order["result"]["status"] == "FILLED"
    assert adapter.get_balance("btc") == 0.05 + 0.005 - 0.01
    
    print("Wallex Paper Session Test Passed Successfully!")
