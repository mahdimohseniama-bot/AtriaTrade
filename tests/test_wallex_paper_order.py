import pytest
from src.adapters.wallex_paper import WallexPaperAdapter

def test_wallex_paper_buy_and_sell():
    adapter = WallexPaperAdapter(initial_balances={"USDT": 1000.0, "BTC": 0.0})
    
    # تنظیم قیمت بازار برای BTC-USDT
    adapter.set_market_price("BTC-USDT", 50000.0)
    
    # بررسی موجودی اولیه
    assert adapter.get_balance("USDT") == 1000.0
    assert adapter.get_balance("BTC") == 0.0
    
    # ثبت سفارش خرید 0.01 بیت‌کوین (ارزش کل ۵۰۰ دلار)
    buy_result = adapter.place_order(
        symbol="BTC-USDT",
        side="buy",
        order_type="market",
        amount=0.01,
        price=50000.0
    )
    
    # اصلاح وضعیت مورد انتظار به success
    assert buy_result["status"] == "success"
    
    # موجودی USDT باید کسر شده باشد (۵۰۰ دلار + کارمزد) و BTC افزوده شده باشد
    assert adapter.get_balance("BTC") == 0.01
    assert adapter.get_balance("USDT") < 500.0
    
    # ثبت سفارش فروش 0.01 بیت‌کوین
    sell_result = adapter.place_order(
        symbol="BTC-USDT",
        side="sell",
        order_type="market",
        amount=0.01,
        price=51000.0
    )
    
    assert sell_result["status"] == "success"
    assert adapter.get_balance("BTC") == 0.0
    print("\nWallex paper trading order execution test passed successfully.")
