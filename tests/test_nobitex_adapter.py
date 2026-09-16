import pytest
import responses

from src.exchange.adapters.nobitex import NobitexAdapter
from src.exchange.factory import ExchangeFactory
from src.exchange.models import Ticker


def test_nobitex_adapter_registered():
    adapter = ExchangeFactory.create("NOBITEX")

    assert isinstance(adapter, NobitexAdapter)


@responses.activate
def test_nobitex_get_ticker():
    adapter = ExchangeFactory.create("NOBITEX")

    mock_response = {
        "status": "ok",
        "stats": {
            "btc-usdt": {
                "latest": "62000.50",
                "bestBuy": "62000.00",
                "bestSell": "62001.00",
                "volumeSrc": "1.5",
            }
        },
    }

    responses.add(
        responses.GET,
        "https://api.nobitex.ir/market/stats?srcCurrency=btc&dstCurrency=usdt",
        json=mock_response,
        status=200,
    )

    ticker = adapter.get_ticker("BTC-USDT")

    assert isinstance(ticker, Ticker)
    assert ticker.symbol == "BTCUSDT"
    assert ticker.last_price == 62000.50
    assert ticker.bid == 62000.00
    assert ticker.ask == 62001.00
    assert ticker.volume == 1.5


def test_nobitex_place_order_permission_error_without_token():
    adapter = NobitexAdapter(api_token="")

    with pytest.raises(PermissionError, match="API token is not configured"):
        adapter.place_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="LIMIT",
            quantity=0.01,
            price=60000.0,
        )


def test_nobitex_live_order_is_blocked_even_with_token():
    adapter = NobitexAdapter(api_token="safe_test_token_only")

    with pytest.raises(PermissionError, match="Live order execution is disabled"):
        adapter.place_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="LIMIT",
            quantity=0.01,
            price=60000.0,
        )
