import pytest
from src.adapters.wallex_paper import WallexPaperAdapter

def test_wallex_ticker_price_nonzero():
    adapter = WallexPaperAdapter()
    ticker = adapter.get_ticker("BTCUSDT")
    assert "last" in ticker
    assert ticker["last"] > 0.0
    assert ticker["bid"] > 0.0
    assert ticker["ask"] > 0.0

def test_wallex_paper_order_nonzero_price():
    adapter = WallexPaperAdapter()
    order = adapter.create_order("BTCUSDT", "buy", "market", 0.001)
    assert order["status"] == "filled"
    assert order["price"] > 0.0
