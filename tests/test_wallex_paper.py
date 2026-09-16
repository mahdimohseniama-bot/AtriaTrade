"""Unit tests for Wallex Paper Adapter."""

import pytest
from src.adapters.wallex_paper import WallexPaperAdapter


@pytest.fixture
def wallex_adapter():
    return WallexPaperAdapter(
        initial_balances={
            "tm": 100_000_000.0,
            "usdt": 2000.0,
            "btc": 1.0,
            "eth": 5.0
        }
    )


def test_initial_balances(wallex_adapter):
    assert wallex_adapter.get_balance("tm") == 100_000_000.0
    assert wallex_adapter.get_balance("usdt") == 2000.0
    assert wallex_adapter.get_balance("btc") == 1.0


def test_get_ticker_and_orderbook(wallex_adapter):
    ticker = wallex_adapter.get_ticker("btc-tm")
    assert ticker["symbol"] == "BTCTM"
    assert ticker["lastPrice"] > 0

    book = wallex_adapter.get_order_book("BTCUSDT", limit=5)
    assert len(book["bids"]) == 5
    assert len(book["asks"]) == 5


def test_place_buy_order_success(wallex_adapter):
    wallex_adapter.set_market_price("BTCTM", 6_000_000_000.0)
    initial_tm = wallex_adapter.get_balance("tm")
    initial_btc = wallex_adapter.get_balance("btc")

    res = wallex_adapter.place_order(
        symbol="BTCTM",
        side="buy",
        order_type="market",
        amount=0.01
    )

    assert res["status"] == "success"
    assert res["result"]["status"] == "FILLED"
    assert wallex_adapter.get_balance("btc") == initial_btc + 0.01
    assert wallex_adapter.get_balance("tm") < initial_tm


def test_place_sell_order_success(wallex_adapter):
    wallex_adapter.set_market_price("BTCUSDT", 100_000.0)
    initial_usdt = wallex_adapter.get_balance("usdt")

    res = wallex_adapter.place_order(
        symbol="BTCUSDT",
        side="sell",
        order_type="limit",
        amount=0.1,
        price=100_000.0
    )

    assert res["status"] == "success"
    assert wallex_adapter.get_balance("btc") == 0.9
    assert wallex_adapter.get_balance("usdt") > initial_usdt


def test_insufficient_balance(wallex_adapter):
    res = wallex_adapter.place_order(
        symbol="BTCUSDT",
        side="buy",
        order_type="market",
        amount=10.0  # Needs 1,000,000 USDT, only has 2000
    )
    assert res["status"] == "failed"
    assert "Insufficient" in res["error"]


def test_cancel_order_logic(wallex_adapter):
    res = wallex_adapter.place_order("BTCUSDT", "buy", "market", 0.001)
    order_id = res["result"]["clientOrderId"]

    # Filled order cannot be canceled
    cancel_res = wallex_adapter.cancel_order(order_id)
    assert cancel_res["status"] == "failed"

    # Query order
    order_info = wallex_adapter.get_order(order_id)
    assert order_info["status"] == "success"
    assert order_info["result"]["clientOrderId"] == order_id
