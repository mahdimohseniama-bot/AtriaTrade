from src.exchange.adapters.nobitex import NobitexAdapter

def test_nobitex_symbol_formatting():
    adapter = NobitexAdapter()
    # بررسی فرمت استاندارد نوبیتکس
    assert adapter.format_symbol("BTCUSDT") == "btc-usdt"
    assert adapter.format_symbol("ETHUSDT") == "eth-usdt"
