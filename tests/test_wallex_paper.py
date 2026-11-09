import pytest
from src.adapters.wallex_paper import WallexPaperAdapter


def test_wallex_paper_ticker():
    adapter = WallexPaperAdapter(initial_balance=500.0)
    ticker = adapter.get_ticker("BTCUSDT")
    assert "last_price" in ticker
    assert ticker["last_price"] > 0.0


def test_wallex_paper_balance():
    adapter = WallexPaperAdapter(initial_balance=750.0)
    assert adapter.get_balance() == 750.0


def test_wallex_paper_create_order():
    adapter = WallexPaperAdapter(initial_balance=1000.0)
    order = adapter.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=0.01,
        price=65000.0,
    )
    assert order["status"] == "FILLED"
    assert order["symbol"] == "BTCUSDT"
    assert order["quantity"] == 0.01
    assert order["price"] == 65000.0
    assert "wallex_paper_" in order["order_id"]
