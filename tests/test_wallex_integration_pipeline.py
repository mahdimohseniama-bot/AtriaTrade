import pytest
from src.adapters.wallex_paper import WallexPaperAdapter

def test_wallex_full_pipeline_smoke():
    adapter = WallexPaperAdapter(initial_balances={"usdt": 5000.0, "btc": 0.1})
    
    # Verify adapter ticker formatting and spread realism
    ticker = adapter.get_ticker("BTCUSDT")
    assert "bidPrice" in ticker
    assert "askPrice" in ticker
    assert ticker["bidPrice"] > 0
    assert ticker["askPrice"] >= ticker["bidPrice"]
    
    # Verify normalized balance management
    balances = adapter.get_balances()
    assert adapter.get_balance("usdt") == 5000.0
    assert adapter.get_balance("btc") == 0.1
    
    # Place a simulated paper market buy order
    order = adapter.place_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        amount=0.01,
        price=ticker["askPrice"]
    )
    assert order is not None
    assert order.get("status") in ("FILLED", "closed", "success")
    
    # Ensure balance deducted for quote and increased for base
    assert adapter.get_balance("usdt") < 5000.0
    assert adapter.get_balance("btc") > 0.1
