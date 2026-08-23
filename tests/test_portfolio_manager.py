"""
Unit and Functional Tests for PortfolioManager - AtriaTrade
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.portfolio_manager import PortfolioManager


def test_initialization():
    pm = PortfolioManager(initial_cash=10000.0, max_asset_weight=0.25)
    assert pm.cash == 10000.0
    assert pm.peak_equity == 10000.0
    assert pm.max_asset_weight == 0.25
    assert len(pm.holdings) == 0
    print("PASS: test_initialization")


def test_allocation_limits():
    pm = PortfolioManager(initial_cash=10000.0, max_asset_weight=0.20)
    prices = {"BTC/USDT": 50000.0}

    # Can allocate up to 20% = $2,000
    res_valid = pm.can_allocate("BTC/USDT", 2000.0, prices)
    assert res_valid["allowed"] is True

    # Cannot allocate 25% = $2,500
    res_invalid = pm.can_allocate("BTC/USDT", 2500.0, prices)
    assert res_invalid["allowed"] is False
    assert "Exceeds max asset weight" in res_invalid["reason"]
    print("PASS: test_allocation_limits")


def test_buy_and_sell_cycle():
    pm = PortfolioManager(initial_cash=10000.0, max_asset_weight=0.50)
    
    # Buy 0.1 BTC at 50,000 ($5,000 cost)
    buy_res = pm.record_buy(symbol="BTC/USDT", quantity=0.1, price=50000.0)
    assert pm.cash == 5000.0
    assert pm.get_holding_quantity("BTC/USDT") == 0.1
    assert buy_res["total_cost"] == 5000.0

    # Sell 0.1 BTC at 55,000 ($5,500 proceeds, $500 profit)
    sell_res = pm.record_sell(symbol="BTC/USDT", quantity=0.1, price=55000.0)
    assert pm.cash == 10500.0
    assert pm.get_holding_quantity("BTC/USDT") == 0.0
    assert "BTC/USDT" not in pm.holdings
    assert sell_res["realized_pnl"] == 500.0
    print("PASS: test_buy_and_sell_cycle")


def test_equity_and_drawdown():
    pm = PortfolioManager(initial_cash=10000.0, max_asset_weight=0.50)
    
    # Buy 0.1 BTC at 50,000 ($5,000 cash remaining)
    pm.record_buy("BTC/USDT", 0.1, 50000.0)

    # Price drops to 40,000: Holdings = $4,000, Total Equity = $9,000
    prices_down = {"BTC/USDT": 40000.0}
    equity = pm.calculate_total_equity(prices_down)
    assert equity == 9000.0
    
    drawdown = pm.calculate_drawdown(equity)
    assert drawdown == 10.0  # 10% drawdown from peak 10000.0

    # Summary validation
    summary = pm.get_summary(prices_down)
    assert summary["drawdown_pct"] == 10.0
    assert summary["cash"] == 5000.0
    assert summary["total_equity"] == 9000.0
    print("PASS: test_equity_and_drawdown")


if __name__ == "__main__":
    print("START: PortfolioManager Tests")
    test_initialization()
    test_allocation_limits()
    test_buy_and_sell_cycle()
    test_equity_and_drawdown()
    print("ALL PortfolioManager TESTS PASSED SUCCESSFULLY!")
