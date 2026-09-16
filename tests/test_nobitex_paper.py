"""Comprehensive tests for Nobitex Paper Adapter (Capability 47)."""

import pytest
from src.adapters.nobitex_paper import NobitexPaperAdapter


def test_adapter_initialization():
    """Verify default and custom wallet initialization."""
    adapter = NobitexPaperAdapter()
    balances = adapter.get_all_balances()
    assert balances["rls"] == 500_000_000.0
    assert balances["usdt"] == 1000.0
    assert balances["btc"] == 0.05

    custom = NobitexPaperAdapter({"rls": 100_000, "usdt": 50})
    assert custom.get_balance("rls") == 100_000
    assert custom.get_balance("usdt") == 50
    assert custom.get_balance("btc") == 0.0


def test_symbol_normalization():
    """Verify symbol string standardizations."""
    adapter = NobitexPaperAdapter()
    assert adapter.normalize_symbol("btc-irt") == "BTCIRT"
    assert adapter.normalize_symbol("eth_usdt") == "ETHUSDT"
    assert adapter.normalize_symbol("usdt/rls") == "USDTRLS"


def test_ticker_and_orderbook():
    """Verify ticker retrieval and simulated orderbook structure."""
    adapter = NobitexPaperAdapter()
    adapter.set_market_price("BTCIRT", 7_000_000_000.0)

    ticker = adapter.get_ticker("btcirt")
    assert ticker["symbol"] == "BTCIRT"
    assert ticker["last"] == 7_000_000_000.0
    assert ticker["bid"] < ticker["last"]
    assert ticker["ask"] > ticker["last"]

    orderbook = adapter.get_order_book("BTCIRT", limit=5)
    assert len(orderbook["bids"]) == 5
    assert len(orderbook["asks"]) == 5
    assert orderbook["bids"][0][0] < ticker["last"]
    assert orderbook["asks"][0][0] > ticker["last"]


def test_successful_buy_order_and_balance_update():
    """Verify simulated BUY order execution and wallet deduction with fees."""
    initial_usdt = 1000.0
    adapter = NobitexPaperAdapter({"usdt": initial_usdt, "btc": 0.0})
    adapter.set_market_price("BTCUSDT", 50_000.0)

    # Buy 0.01 BTC at 50,000 USDT -> cost = 500 USDT, taker fee = 0.25% (1.25 USDT)
    res = adapter.place_order("BTCUSDT", side="buy", order_type="market", amount=0.01)
    assert res["status"] == "success"
    assert res["order"]["status"] == "FILLED"
    assert res["order"]["fee"] == pytest.approx(1.25)

    assert adapter.get_balance("btc") == pytest.approx(0.01)
    assert adapter.get_balance("usdt") == pytest.approx(initial_usdt - 501.25)


def test_successful_sell_order_and_balance_update():
    """Verify simulated SELL order execution and proceeds calculation."""
    adapter = NobitexPaperAdapter({"usdt": 100.0, "btc": 0.02})
    adapter.set_market_price("BTCUSDT", 60_000.0)

    # Sell 0.01 BTC at 60,000 USDT -> gross = 600 USDT, taker fee = 1.5 USDT -> net = 598.5 USDT
    res = adapter.place_order("BTCUSDT", side="sell", order_type="market", amount=0.01)
    assert res["status"] == "success"
    assert res["order"]["status"] == "FILLED"

    assert adapter.get_balance("btc") == pytest.approx(0.01)
    assert adapter.get_balance("usdt") == pytest.approx(100.0 + 598.5)


def test_insufficient_funds_rejection():
    """Verify rejection when wallet does not have enough balance."""
    adapter = NobitexPaperAdapter({"usdt": 50.0, "btc": 0.0})
    adapter.set_market_price("BTCUSDT", 50_000.0)

    # Attempt to buy 0.01 BTC ($500) with only $50
    res = adapter.place_order("BTCUSDT", side="buy", order_type="market", amount=0.01)
    assert res["status"] == "failed"
    assert "Insufficient" in res["error"]
    assert adapter.get_balance("btc") == 0.0
    assert adapter.get_balance("usdt") == 50.0


def test_invalid_order_amount_and_side():
    """Verify handling of non-positive amount or invalid order side."""
    adapter = NobitexPaperAdapter()
    res_zero = adapter.place_order("BTCUSDT", side="buy", order_type="market", amount=0)
    assert res_zero["status"] == "failed"

    res_side = adapter.place_order("BTCUSDT", side="invalid_side", order_type="market", amount=0.01)
    assert res_side["status"] == "failed"


def test_order_status_and_cancel():
    """Verify order querying and cancellation behaviour."""
    adapter = NobitexPaperAdapter({"usdt": 1000.0, "btc": 0.0})
    adapter.set_market_price("BTCUSDT", 50_000.0)

    order_res = adapter.place_order("BTCUSDT", side="buy", order_type="limit", amount=0.001, price=50_000.0)
    order_id = order_res["order"]["order_id"]

    status_res = adapter.get_order_status(order_id)
    assert status_res["status"] == "success"
    assert status_res["order"]["order_id"] == order_id

    # Trying to cancel a filled order
    cancel_res = adapter.cancel_order(order_id)
    assert cancel_res["status"] == "failed"
    assert "already filled" in cancel_res["error"]

    # Non-existing order cancel
    not_found = adapter.cancel_order("non_existent_id")
    assert not_found["status"] == "failed"
