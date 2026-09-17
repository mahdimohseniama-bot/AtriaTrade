import pytest
from src.adapters.paper_factory import PaperFactory

def test_wallex_factory_creation():
    adapter = PaperFactory.create_adapter("wallex", symbol="USDTTMN", initial_balance=25_000_000.0)
    assert adapter is not None
    assert adapter.balance == 25_000_000.0
    assert adapter.symbol == "USDTTMN"

def test_wallex_order_lifecycle():
    initial_cash = 10_000_000.0
    adapter = PaperFactory.create_adapter("wallex", symbol="USDTTMN", initial_balance=initial_cash)
    
    # تست خرید مارکت
    buy_amount = 2_000_000.0
    buy_res = adapter.execute_market_order("BUY", buy_amount)
    assert buy_res["status"] == "FILLED"
    assert buy_res["qty"] > 0
    # در اسپات، پس از خرید باید موجودی نقد کاهش یافته و تتر اضافه شده باشد
    assert adapter.balance < initial_cash
    
    # تست فروش مارکت و نقد کردن
    sell_res = adapter.execute_market_order("SELL", 0)
    assert sell_res["status"] in ["FILLED", "CLOSED", "success"]
    assert adapter.balance > 0
